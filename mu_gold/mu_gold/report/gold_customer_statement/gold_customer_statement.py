import frappe
from frappe import _
from frappe.utils import flt


def execute(filters=None):
    filters = filters or {}
    validate_filters(filters)

    columns = get_columns()
    data, totals, opening_balance = get_data(filters)
    report_summary = get_report_summary(totals, opening_balance)

    return columns, data, None, None, report_summary


def validate_filters(filters):
    if not filters.get("company"):
        frappe.throw(_("Please select a Company"))
    if not filters.get("customer"):
        frappe.throw(_("Please select a Customer"))


def get_columns():
    return [
        {
            "fieldname": "date",
            "label": _("التاريخ والوقت"),
            "fieldtype": "Datetime",
            "width": 145,
        },
        {
            "fieldname": "description",
            "label": _("الوصف والبيان"),
            "fieldtype": "Data",
            "width": 220,
        },
        {
            "fieldname": "reference_name",
            "label": _("رقم المستند"),
            "fieldtype": "Dynamic Link",
            "options": "reference_type",
            "width": 160,
        },
        {
            "fieldname": "carat",
            "label": _("العيار"),
            "fieldtype": "Data",
            "width": 75,
        },
        # ── GOLD DEBIT (gold went TO customer) ────────────────────────────
        {
            "fieldname": "debit_21",
            "label": _("مدين جرام-21"),
            "fieldtype": "Float",
            "precision": 4,
            "width": 130,
        },
        # ── GOLD CREDIT (gold came BACK from customer) ─────────────────────
        {
            "fieldname": "credit_21",
            "label": _("دائن جرام-21"),
            "fieldtype": "Float",
            "precision": 4,
            "width": 130,
        },
        # ── GOLD RUNNING BALANCE ───────────────────────────────────────────
        {
            "fieldname": "balance_21",
            "label": _("رصيد الذهب جرام-21"),
            "fieldtype": "Float",
            "precision": 4,
            "width": 135,
        },
        # ── CASH DEBIT (invoice amount owed by customer) ───────────────────
        {
            "fieldname": "cash_debit",
            "label": _("مدين نقد"),
            "fieldtype": "Currency",
            "width": 115,
        },
        # ── CASH CREDIT (payments received from customer) ──────────────────
        {
            "fieldname": "cash_credit",
            "label": _("دائن نقد"),
            "fieldtype": "Currency",
            "width": 115,
        },
        # ── CASH RUNNING BALANCE ───────────────────────────────────────────
        {
            "fieldname": "cash_balance",
            "label": _("رصيد النقد"),
            "fieldtype": "Currency",
            "width": 120,
        },
    ]


def get_data(filters):
    conditions = (
        "gcl.is_cancelled = 0 "
        "AND gcl.docstatus = 1 "
        "AND gcl.company = %(company)s "
        "AND gcl.customer = %(customer)s"
    )
    values = {
        "company": filters["company"],
        "customer": filters["customer"],
    }

    # ── Opening balance: everything BEFORE from_date ───────────────────────
    opening_gold = 0.0
    opening_cash = 0.0

    if filters.get("from_date"):
        opening_gold = flt(frappe.db.sql("""
            SELECT IFNULL(SUM(equivalent_21_change), 0)
            FROM `tabGold Customer Ledger`
            WHERE is_cancelled = 0 AND docstatus = 1
              AND company = %(company)s AND customer = %(customer)s
              AND date < %(from_date)s
        """, values | {"from_date": filters["from_date"]})[0][0])

        # Cash opening: sum of invoice amounts before from_date
        opening_cash = flt(frappe.db.sql("""
            SELECT IFNULL(SUM(
                CASE
                    WHEN gcl.movement_type = 'ISSUE' THEN IFNULL(si.grand_total, 0)
                    WHEN gcl.movement_type = 'RECEIPT' THEN -IFNULL(si.grand_total, 0)
                    ELSE 0
                END
            ), 0)
            FROM `tabGold Customer Ledger` gcl
            LEFT JOIN `tabSales Invoice` si ON si.name = gcl.invoice_ref
            WHERE gcl.is_cancelled = 0 AND gcl.docstatus = 1
              AND gcl.company = %(company)s AND gcl.customer = %(customer)s
              AND gcl.date < %(from_date)s
        """, values | {"from_date": filters["from_date"]})[0][0])

        conditions += " AND gcl.date >= %(from_date)s"
        values["from_date"] = filters["from_date"]

    if filters.get("to_date"):
        conditions += " AND gcl.date <= %(to_date)s"
        values["to_date"] = filters["to_date"]

    rows = frappe.db.sql(f"""
        SELECT
            gcl.date,
            gcl.creation,
            gcl.movement_type,
            gcl.reference_type,
            gcl.reference_name,
            gcl.carat,
            gcl.actual_weight,
            gcl.equivalent_21_change,
            gcl.balance_after,
            gcl.invoice_ref,
            IFNULL(si.grand_total, 0)      AS invoice_amount,
            IFNULL(si.outstanding_amount, 0) AS outstanding_amount
        FROM `tabGold Customer Ledger` gcl
        LEFT JOIN `tabSales Invoice` si ON si.name = gcl.invoice_ref
        WHERE {conditions}
        ORDER BY gcl.date ASC, gcl.creation ASC
    """, values, as_dict=True)

    data = []

    # Opening row
    if filters.get("from_date") and (opening_gold or opening_cash):
        data.append({
            "date": None,
            "description": _("رصيد افتتاحي"),
            "reference_name": None,
            "carat": "",
            "debit_weight": None, "debit_21": None,
            "credit_weight": None, "credit_21": None,
            "balance_21": flt(opening_gold, 4),
            "cash_debit": None, "cash_credit": None,
            "cash_balance": flt(opening_cash, 2),
            "reference_type": None,
            "bold": 1,
        })

    running_gold = opening_gold
    running_cash = opening_cash

    # Accumulators for totals (exclude opening and total rows)
    total_debit_wt  = 0.0
    total_debit_21  = 0.0
    total_credit_wt = 0.0
    total_credit_21 = 0.0
    total_cash_debit  = 0.0
    total_cash_credit = 0.0

    for row in rows:
        eq = flt(row.equivalent_21_change, 4)
        weight = flt(row.actual_weight, 4)
        is_issue = (row.movement_type == "ISSUE")

        running_gold = flt(row.balance_after, 4)

        # Cash logic:
        #   ISSUE   → مدين نقد (customer owes us invoice amount)
        #   RECEIPT → دائن نقد (we settle / return cash to customer)
        cash_debit  = flt(row.invoice_amount, 2) if is_issue else 0.0
        cash_credit = flt(row.invoice_amount, 2) if not is_issue else 0.0

        # Payments received reduce outstanding (cash credit)
        paid_amount = flt(row.invoice_amount, 2) - flt(row.outstanding_amount, 2)
        if is_issue and paid_amount > 0:
            cash_credit = paid_amount

        running_cash = flt(running_cash + cash_debit - cash_credit, 2)

        desc = _("تسليم ذهب - فاتورة مبيعات") if is_issue else _("استلام ذهب - سند إرجاع")

        data.append({
            "date": row.creation,
            "description": desc,
            "reference_type": row.reference_type,
            "reference_name": row.reference_name,
            "carat": row.carat or "",
            "debit_21":      flt(eq, 4) if is_issue else None,
            "credit_21":     flt(abs(eq), 4) if not is_issue else None,
            "balance_21":    running_gold,
            "cash_debit":    cash_debit or None,
            "cash_credit":   cash_credit or None,
            "cash_balance":  running_cash,
        })

        # Accumulate totals
        if is_issue:
            total_debit_wt  += weight
            total_debit_21  += flt(eq, 4)
            total_cash_debit += cash_debit
        else:
            total_credit_wt  += weight
            total_credit_21  += flt(abs(eq), 4)
            total_cash_credit += cash_credit

    # Totals row
    if data:
        data.append({
            "date": None,
            "description": _("الإجمالي"),
            "reference_name": None,
            "carat": "",
            "debit_21":      flt(total_debit_21, 4)   or None,
            "credit_21":     flt(total_credit_21, 4)  or None,
            "balance_21":    running_gold,
            "cash_debit":    flt(total_cash_debit, 2) or None,
            "cash_credit":   flt(total_cash_credit, 2) or None,
            "cash_balance":  running_cash,
            "bold": 1,
        })

    totals = {
        "total_debit_21":    total_debit_21,
        "total_credit_21":   total_credit_21,
        "total_cash_debit":  total_cash_debit,
        "total_cash_credit": total_cash_credit,
        "running_gold":      running_gold,
        "running_cash":      running_cash,
    }

    return data, totals, opening_gold


def get_report_summary(totals, opening_balance):
    net_gold = flt(totals["total_debit_21"] - totals["total_credit_21"] + opening_balance, 4)
    net_cash = flt(totals["running_cash"], 2)

    return [
        {
            "value": flt(totals["total_debit_21"], 4),
            "label": _("إجمالي الذهب المسلّم (جرام-21)"),
            "datatype": "Float",
            "indicator": "Orange",
        },
        {
            "value": flt(totals["total_credit_21"], 4),
            "label": _("إجمالي الذهب المستلم (جرام-21)"),
            "datatype": "Float",
            "indicator": "Green",
        },
        {
            "value": net_gold,
            "label": _("رصيد الذهب الحالي (جرام-21)"),
            "datatype": "Float",
            "indicator": "Blue" if net_gold >= 0 else "Red",
        },
        {
            "value": flt(totals["total_cash_debit"], 2),
            "label": _("إجمالي النقد المدين"),
            "datatype": "Currency",
            "indicator": "Orange",
        },
        {
            "value": flt(totals["total_cash_credit"], 2),
            "label": _("إجمالي النقد الدائن"),
            "datatype": "Currency",
            "indicator": "Green",
        },
        {
            "value": net_cash,
            "label": _("رصيد النقد الحالي"),
            "datatype": "Currency",
            "indicator": "Blue" if net_cash >= 0 else "Red",
        },
    ]

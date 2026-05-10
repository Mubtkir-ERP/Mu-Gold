import frappe
from frappe import _
from frappe.utils import flt


def execute(filters=None):
    filters = filters or {}
    columns = [
        {"fieldname": "customer", "label": _("Customer"), "fieldtype": "Link",
         "options": "Customer", "width": 160},
        {"fieldname": "customer_name", "label": _("Customer Name"),
         "fieldtype": "Data", "width": 180},
        {"fieldname": "equivalent_21_balance", "label": _("Balance (Eq-21 g)"),
         "fieldtype": "Float", "precision": 6, "width": 160},
        {"fieldname": "qty_18", "label": _("Open 18k (g)"),
         "fieldtype": "Float", "precision": 6, "width": 120},
        {"fieldname": "qty_21", "label": _("Open 21k (g)"),
         "fieldtype": "Float", "precision": 6, "width": 120},
        {"fieldname": "qty_22", "label": _("Open 22k (g)"),
         "fieldtype": "Float", "precision": 6, "width": 120},
        {"fieldname": "qty_24", "label": _("Open 24k (g)"),
         "fieldtype": "Float", "precision": 6, "width": 120},
        {"fieldname": "accounting_value", "label": _("Accounting Value (SAR)"),
         "fieldtype": "Currency", "width": 180},
    ]

    company_filter = ""
    values = {}
    if filters.get("company"):
        company_filter = " AND company = %(company)s"
        values["company"] = filters["company"]

    # ── رصيد كل عميل (آخر سطر في الدفتر) ────────────────────────────────────
    balance_data = frappe.db.sql(f"""
        SELECT t1.customer, c.customer_name, t1.balance_after
        FROM `tabGold Customer Ledger` t1
        JOIN `tabCustomer` c ON t1.customer = c.name
        WHERE t1.is_cancelled = 0 AND t1.docstatus = 1
        {company_filter.replace('company','t1.company')}
        AND t1.creation = (
            SELECT MAX(t2.creation)
            FROM `tabGold Customer Ledger` t2
            WHERE t2.customer = t1.customer
            AND t2.is_cancelled = 0 AND t2.docstatus = 1
        )
        HAVING t1.balance_after > 0
        ORDER BY t1.balance_after DESC
    """, values, as_dict=True)

    # ── الكميات المفتوحة حسب العيار لكل عميل ─────────────────────────────────
    carat_data = frappe.db.sql(f"""
        SELECT customer, carat, SUM(equivalent_21_change) as qty
        FROM `tabGold Customer Ledger`
        WHERE is_cancelled = 0 AND docstatus = 1
        {company_filter}
        GROUP BY customer, carat
    """, values, as_dict=True)

    carat_map = {}
    for row in carat_data:
        if row.customer not in carat_map:
            carat_map[row.customer] = {}
        carat_map[row.customer][str(row.carat)] = flt(row.qty)

    # ── القيمة المحاسبية من حسابات العهدة ────────────────────────────────────
    gl_data = frappe.db.sql("""
        SELECT party as customer, SUM(debit) - SUM(credit) as gl_balance
        FROM `tabGL Entry`
        WHERE party_type = 'Customer'
        AND account LIKE '%عهدة%' OR account LIKE '%لدى العملاء%'
        GROUP BY party
    """, as_dict=True)
    gl_map = {r.customer: flt(r.gl_balance) for r in gl_data if r.customer}

    data = []
    for row in balance_data:
        cust_carats = carat_map.get(row.customer, {})
        data.append({
            "customer": row.customer,
            "customer_name": row.customer_name,
            "equivalent_21_balance": flt(row.balance_after),
            "qty_18": flt(cust_carats.get("18", 0)),
            "qty_21": flt(cust_carats.get("21", 0)),
            "qty_22": flt(cust_carats.get("22", 0)),
            "qty_24": flt(cust_carats.get("24", 0)),
            "accounting_value": gl_map.get(row.customer, 0.0),
        })

    return columns, data

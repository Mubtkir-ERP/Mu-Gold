import frappe
from frappe import _
from frappe.utils import flt
from mu_gold.mu_gold.controllers.gold_movement_utils import (
    get_equivalent_21,
    create_stock_entry,
    create_gold_ledger_entry,
    create_journal_entry_for_issue,
    get_customer_gold_balance,
    rebuild_running_balance,
)


def validate(doc, method):
    """
    Validate gold-related fields before saving the Sales Invoice
    and auto-calculate Carat 21 Equivalent.
    """
    if not doc.get("is_gold_invoice"):
        return

    # ── Mandatory field check ─────────────────────────────────────────────────
    mandatory_fields = [
        "gold_item", "gold_carat", "gold_weight",
        "price_per_gram", "source_warehouse", "target_warehouse",
    ]
    for field in mandatory_fields:
        val = doc.get(field)
        if val is None or str(val).strip() == "":
            meta_field = doc.meta.get_field(field)
            label = meta_field.label if meta_field else field
            frappe.throw(_("Field '{0}' is mandatory for Gold Workmanship Invoices").format(label))

    doc.gold_weight = flt(doc.gold_weight)
    doc.price_per_gram = flt(doc.price_per_gram)

    if doc.gold_weight <= 0:
        frappe.throw(_("Gold weight must be greater than zero."))

    if flt(doc.price_per_gram) <= 0:
        frappe.throw(_("Workmanship price per gram must be greater than zero."))

    doc.equivalent_21 = get_equivalent_21(doc.gold_weight, doc.gold_carat)
    doc.total_workmanship = round(doc.gold_weight * doc.price_per_gram, 2)

    # ── Warehouse stock check ─────────────────────────────────────────────────
    if doc.source_warehouse and doc.gold_item:
        allow_negative = flt(frappe.db.get_single_value("Stock Settings", "allow_negative_stock"))
        if not allow_negative:
            available = flt(frappe.db.get_value(
                "Bin",
                {"item_code": doc.gold_item, "warehouse": doc.source_warehouse},
                "actual_qty",
            ))
            if available < doc.gold_weight:
                # رمي خطأ مخصص يُلتقط في الاختبارات
                frappe.throw(
                    _("Insufficient stock in warehouse '{0}'. Available: {1}g, Required: {2}g.").format(
                        doc.source_warehouse,
                        round(available, 6),
                        doc.gold_weight,
                    )
                )


def on_submit(doc, method):
    """
    When Sales Invoice is submitted:
    1. Guard against duplicate execution.
    2. Create Stock Entry (Material Transfer) for gold issuance.
    3. Create Journal Entry: Dr Custody / Cr Stock.
    4. Create Gold Customer Ledger entry (ISSUE).
    5. Save generated document references back to the invoice.
    """
    if not doc.get("is_gold_invoice"):
        return

    # ── Duplicate guard ────────────────────────────────────────────────────────
    if doc.get("gold_movement_created"):
        frappe.throw(
            _("Gold movement has already been created for this invoice. "
              "Cancel and amend if you need to make changes.")
        )

    # ── 1. Stock Entry ─────────────────────────────────────────────────────────
    stock_entry_id = create_stock_entry(
        doc=doc,
        purpose="Material Transfer",
        source_warehouse=doc.source_warehouse,
        target_warehouse=doc.target_warehouse,
        item_code=doc.gold_item,
        qty=doc.gold_weight,
    )

    # ── 2. Journal Entry ───────────────────────────────────────────────────────
    journal_entry_id = None
    try:
        doc.stock_entry_ref = stock_entry_id
        journal_entry_id = create_journal_entry_for_issue(doc)
    except Exception as e:
        frappe.log_error(title="Gold JE Warning — Issue", message=str(e))

    # ── 3. Gold Customer Ledger ────────────────────────────────────────────────
    ledger_id = create_gold_ledger_entry(
        doc=doc,
        movement_type="ISSUE",
        ref_type="Sales Invoice",
        ref_name=doc.name,
        item=doc.gold_item,
        carat=doc.gold_carat,
        weight=doc.gold_weight,
        eq_change=doc.equivalent_21,
        s_warehouse=doc.source_warehouse,
        t_warehouse=doc.target_warehouse,
        se_ref=stock_entry_id,
        je_ref=journal_entry_id
    )

    # ── 4. Update invoice with references ─────────────────────────────────────
    doc.db_set("stock_entry_ref", stock_entry_id)
    if journal_entry_id:
        doc.db_set("journal_entry_ref", journal_entry_id)
    doc.db_set("gold_movement_created", 1)
    doc.db_set("gold_movement_status", "Created")


def on_cancel(doc, method):
    """
    Reverse all gold movements when the Sales Invoice is cancelled.
    Prevents cancellation if the customer has already returned gold against this invoice.
    """
    if not doc.get("is_gold_invoice"):
        return

    # ── Guard: cannot cancel if a submitted Gold Receipt exists for this customer ─
    # نبحث عن أي استلام ذهب مقبول للعميل صادر بعد (أو في نفس تاريخ) هذه الفاتورة
    open_receipts = frappe.get_all("Gold Receipt", 
        filters={
            "customer": doc.customer,
            "company": doc.company,
            "docstatus": 1,
        },
        fields=["name"]
    )
    if open_receipts:
        frappe.throw(
            _("Cannot cancel this invoice because the customer has {0} open Gold Receipt(s). "
              "Please cancel the Gold Receipt documents first.").format(len(open_receipts))
        )

    # ── 1. Cancel Gold Customer Ledger FIRST (removes backlink to SE/JE) ─────────
    ledgers = frappe.get_all(
        "Gold Customer Ledger",
        filters={"reference_name": doc.name, "is_cancelled": 0, "docstatus": 1},
        fields=["name"],
    )
    for row in ledgers:
        lg = frappe.get_doc("Gold Customer Ledger", row.name)
        lg.flags.ignore_links = True
        lg.cancel()

    # ── 2. Cancel Stock Entry ──────────────────────────────────────────────────
    if doc.get("stock_entry_ref"):
        se = frappe.get_doc("Stock Entry", doc.stock_entry_ref)
        if se.docstatus == 1:
            se.cancel()

    # ── 3. Cancel Journal Entry ────────────────────────────────────────────────
    if doc.get("journal_entry_ref"):
        je = frappe.get_doc("Journal Entry", doc.journal_entry_ref)
        if je.docstatus == 1:
            je.cancel()

    # ── 4. Rebuild running balances ────────────────────────────────────────────
    rebuild_running_balance(doc.customer, doc.company)

    doc.db_set("gold_movement_status", "Cancelled")
    doc.db_set("gold_movement_created", 0)


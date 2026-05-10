import frappe
from frappe import _
from frappe.utils import flt
from mu_gold.mu_gold.controllers.gold_movement_utils import (
    get_equivalent_21,
    create_stock_entry,
    create_gold_ledger_entry,
    create_journal_entry_for_receipt,
    get_customer_gold_balance,
    rebuild_running_balance,
)


def validate(doc, method):
    mandatory_fields = [
        "customer", "gold_item", "carat",
        "weight", "source_warehouse", "target_warehouse",
    ]
    for field in mandatory_fields:
        if not doc.get(field):
            meta_field = doc.meta.get_field(field)
            label = meta_field.label if meta_field else field
            frappe.throw(_("Field '{0}' is mandatory").format(label))

    doc.weight = flt(doc.weight)

    if doc.weight <= 0:
        frappe.throw(_("Returned weight must be greater than zero."))

    doc.equivalent_21 = get_equivalent_21(doc.weight, doc.carat)

    current_balance = get_customer_gold_balance(doc.customer, doc.company)
    if flt(doc.equivalent_21) > flt(current_balance) + 0.000001:
        if "Gold Manager" not in frappe.get_roles(frappe.session.user):
            frappe.throw(
                _("Returned Gold Eq-21 ({0}g) exceeds customer open balance ({1}g). "
                  "Only Gold Managers can override this limit.").format(
                    round(doc.equivalent_21, 6),
                    round(current_balance, 6),
                )
            )


def on_submit(doc, method):
    # ── 1. Stock Entry ─────────────────────────────
    stock_entry_id = create_stock_entry(
        doc=doc,
        purpose="Material Transfer",
        source_warehouse=doc.source_warehouse,
        target_warehouse=doc.target_warehouse,
        item_code=doc.gold_item,
        qty=doc.weight,
    )

    # ── 2. Journal Entry ───────────────────────────────────────────────────────
    journal_entry_id = None
    try:
        doc.stock_entry_ref = stock_entry_id
        journal_entry_id = create_journal_entry_for_receipt(doc)
    except Exception as e:
        frappe.log_error(title="Gold JE Warning — Receipt", message=str(e))

    # ── 3. Gold Customer Ledger (negative change) ──────────────
    eq_change = -1 * flt(doc.equivalent_21)

    ledger_id = create_gold_ledger_entry(
        doc=doc,
        movement_type="RECEIPT",
        ref_type="Gold Receipt",
        ref_name=doc.name,
        item=doc.gold_item,
        carat=doc.carat,
        weight=doc.weight,
        eq_change=eq_change,
        s_warehouse=doc.source_warehouse,
        t_warehouse=doc.target_warehouse,
        se_ref=stock_entry_id,
        je_ref=journal_entry_id,
        receipt_ref=doc.name
    )

    # ── 4. Save references ─────────────────────────────────────────────────────
    doc.db_set("stock_entry_ref", stock_entry_id)
    if journal_entry_id:
        doc.db_set("journal_entry_ref", journal_entry_id)
    doc.db_set("status", "Completed")


def on_cancel(doc, method):
    # ── 1. Cancel Gold Customer Ledger FIRST ──────────────────────────────────
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

    # ── 4. Rebuild balances ────────────────────────────────────────────────────
    rebuild_running_balance(doc.customer, doc.company)
    doc.db_set("status", "Cancelled")

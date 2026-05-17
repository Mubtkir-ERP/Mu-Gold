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

    # ── Validate warehouses are different ────────────────────────────────────
    if doc.source_warehouse and doc.target_warehouse:
        if doc.source_warehouse == doc.target_warehouse:
            frappe.throw(
                _("Source Warehouse and Target Warehouse cannot be the same. "
                  "Source = stock vault, Target = customer custody warehouse.")
            )

    # ── Enforce child table: override pricing rules and margins completely ────
    #    ERPNext's pricing rule engine runs BEFORE validate and can alter the
    #    rate/margin on the item row. We forcefully reset everything here so
    #    the invoice always reflects exactly what the user typed in price_per_gram.
    doc.ignore_pricing_rule = 1  # prevent re-application on subsequent saves
    if doc.items:
        price = flt(doc.price_per_gram)
        qty   = flt(doc.gold_weight)
        for row in doc.items:
            if row.item_code == doc.gold_item:
                # Clear any margin / discount that pricing rules may have injected
                row.margin_type              = ""
                row.margin_rate_or_amount    = 0
                row.rate_with_margin         = price
                row.base_rate_with_margin    = price
                row.discount_percentage      = 0
                row.discount_amount          = 0
                row.distributed_discount_amount = 0
                row.pricing_rules            = ""
                # Enforce the correct rate
                row.qty                = qty
                row.rate               = price
                row.price_list_rate    = price
                row.base_price_list_rate = price
                row.stock_uom_rate     = price
                row.amount             = flt(qty * price)
                row.net_rate           = price
                row.net_amount         = flt(qty * price)
                row.base_rate          = price
                row.base_amount        = flt(qty * price)
                row.base_net_rate      = price
                row.base_net_amount    = flt(qty * price)

        # Recalculate header totals to match enforced row values
        if hasattr(doc, "calculate_taxes_and_totals"):
            doc.calculate_taxes_and_totals()

    # ── Warehouse stock check (Multi-UOM tracks base units in ledger bins) ────
    if doc.source_warehouse:
        allow_negative = flt(frappe.db.get_single_value("Stock Settings", "allow_negative_stock"))
        if not allow_negative:
            check_item = "ذهب كسر" if frappe.db.exists("Item", "ذهب كسر") else doc.gold_item
            available = flt(frappe.db.get_value(
                "Bin",
                {"item_code": check_item, "warehouse": doc.source_warehouse},
                "actual_qty",
            ))
            if available < doc.equivalent_21:
                frappe.throw(
                    _("Insufficient stock of unified base item in warehouse '{0}'. Available Base Units: {1}, Required Base Units: {2}.").format(
                        doc.source_warehouse,
                        round(available, 6),
                        round(doc.equivalent_21, 6),
                    )
                )


def on_submit(doc, method):
    """
    When Sales Invoice is submitted:
    1. Guard against duplicate execution.
    2. Create Stock Entry using the Multi-UOM pattern (Unified Item + chosen UOM/Factor).
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

    # ── 1. Stock Entry (Multi-UOM pattern with secondary UOM and conversion factor) ─
    std_item = "ذهب كسر" if frappe.db.exists("Item", "ذهب كسر") else doc.gold_item
    uom_name = doc.gold_carat if doc.gold_carat and doc.gold_carat.startswith("جرام-") else "جرام-21"
    carat_str = uom_name.replace("جرام-", "")
    
    factors = {"24": 1.142857, "22": 1.047619, "21": 1.0, "18": 0.857143}
    factor = factors.get(carat_str, 1.0)

    stock_entry_id = create_stock_entry(
        doc=doc,
        purpose="Material Transfer",
        source_warehouse=doc.source_warehouse,
        target_warehouse=doc.target_warehouse,
        item_code=std_item,
        qty=doc.gold_weight,
        uom=uom_name,
        conversion_factor=factor,
    )

    # ── 2. Journal Entry ───────────────────────────────────────────────────────
    journal_entry_id = None
    try:
        doc.stock_entry_ref = stock_entry_id
        journal_entry_id = create_journal_entry_for_issue(doc)
    except Exception as e:
        frappe.log_error(title="Gold JE Warning — Issue", message=str(e))

    # ── 3. Gold Customer Ledger ────────────────────────────────────────────────
    if not doc.equivalent_21:
        doc.equivalent_21 = get_equivalent_21(doc.gold_weight, doc.gold_carat)
        
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
    doc.db_set("equivalent_21", doc.equivalent_21)
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


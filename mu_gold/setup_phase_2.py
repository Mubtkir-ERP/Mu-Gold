import frappe


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def _field(fieldname, fieldtype, label, **kwargs):
    d = {"fieldname": fieldname, "fieldtype": fieldtype, "label": label}
    d.update(kwargs)
    return d


def _ensure_doctype(name, meta):
    """Create Doctype only if it does not already exist."""
    if frappe.db.exists("DocType", name):
        print(f"DocType '{name}' already exists — skipping.")
        return False
    doc = frappe.new_doc("DocType")
    doc.update(meta)
    doc.insert(ignore_permissions=True)
    print(f"Created DocType '{name}'")
    return True


# ─────────────────────────────────────────────────────────────────────────────
# PHASE 2-A  :  Gold Customer Ledger
# ─────────────────────────────────────────────────────────────────────────────
def create_gold_customer_ledger():
    name = "Gold Customer Ledger"
    fields = [
        _field("company",            "Link",     "الشركة",              options="Company",        in_list_view=1, reqd=1),
        _field("date",               "Date",     "التاريخ",             reqd=1,                    in_list_view=1),
        _field("customer",           "Link",     "العميل",              options="Customer",        in_list_view=1, reqd=1),
        _field("movement_type",      "Select",   "نوع الحركة",
               options="\nISSUE\nRECEIPT\nADJUSTMENT\nCONVERSION\nCANCELLATION", reqd=1, in_list_view=1),
        _field("col_break_1",        "Column Break", ""),
        _field("reference_type",     "Link",     "نوع المرجع",          options="DocType"),
        _field("reference_name",     "Dynamic Link", "رقم المرجع",       options="reference_type"),
        _field("gold_item",          "Link",     "صنف الذهب",           options="Item"),
        _field("carat",              "Data",     "العيار"),
        _field("sec_weights",        "Section Break", "بيانات الوزن"),
        _field("actual_weight",      "Float",    "الوزن الفعلي (جرام)", precision=6),
        _field("equivalent_21_change","Float",   "التغير في مكافئ 21",  precision=6),
        _field("balance_after",      "Float",    "الرصيد بعد الحركة (مكافئ 21)", precision=6),
        _field("col_break_2",        "Column Break", ""),
        _field("source_warehouse",   "Link",     "المستودع المصدر",     options="Warehouse"),
        _field("target_warehouse",   "Link",     "المستودع الهدف",      options="Warehouse"),
        _field("sec_links",          "Section Break", "الروابط"),
        _field("stock_entry_ref",    "Link",     "رابط حركة المخزون",   options="Stock Entry"),
        _field("journal_entry_ref",  "Link",     "رابط القيد المحاسبي", options="Journal Entry"),
        _field("invoice_ref",        "Link",     "رابط الفاتورة",       options="Sales Invoice"),
        _field("payment_ref",        "Link",     "رابط سند القبض",      options="Payment Entry"),
        _field("col_break_3",        "Column Break", ""),
        _field("notes",              "Text",     "الملاحظات"),
        _field("is_cancelled",       "Check",    "ملغى",                default=0),
    ]

    meta = {
        "name": name,
        "module": "Mu Gold",
        "is_submittable": 1,
        "track_changes": 1,
        "fields": fields,
        "permissions": [
            {"role": "System Manager", "read": 1, "write": 1, "create": 1, "submit": 1, "cancel": 1},
        ],
    }
    _ensure_doctype(name, meta)


# ─────────────────────────────────────────────────────────────────────────────
# PHASE 2-B  :  Gold Receipt
# ─────────────────────────────────────────────────────────────────────────────
def create_gold_receipt():
    name = "Gold Receipt"
    fields = [
        _field("company",           "Link",  "الشركة",                options="Company",   reqd=1, in_list_view=1),
        _field("date",              "Date",  "التاريخ",               reqd=1,               in_list_view=1),
        _field("customer",          "Link",  "العميل",                options="Customer",  reqd=1, in_list_view=1),
        _field("col_break_1",       "Column Break", ""),
        _field("status",            "Select","الحالة",
               options="\nDraft\nSubmitted\nCancelled",              in_list_view=1),
        _field("sec_gold",          "Section Break", "تفاصيل الذهب"),
        _field("gold_item",         "Link",  "صنف الذهب المرجع",      options="Item",      reqd=1),
        _field("carat",             "Data",  "العيار المرجع",         reqd=1),
        _field("weight",            "Float", "الوزن المرجع (جرام)",   precision=6,         reqd=1),
        _field("equivalent_21",     "Float", "مكافئ عيار 21",         precision=6),
        _field("col_break_2",       "Column Break", ""),
        _field("target_warehouse",  "Link",  "المستودع الهدف",        options="Warehouse", reqd=1),
        _field("sec_links",         "Section Break", "الروابط"),
        _field("stock_entry_ref",   "Link",  "رابط حركة المخزون",     options="Stock Entry"),
        _field("journal_entry_ref", "Link",  "رابط القيد المحاسبي",   options="Journal Entry"),
        _field("col_break_3",       "Column Break", ""),
        _field("notes",             "Text",  "الملاحظات"),
    ]

    meta = {
        "name": name,
        "module": "Mu Gold",
        "is_submittable": 1,
        "track_changes": 1,
        "fields": fields,
        "permissions": [
            {"role": "System Manager", "read": 1, "write": 1, "create": 1, "submit": 1, "cancel": 1},
        ],
    }
    _ensure_doctype(name, meta)


# ─────────────────────────────────────────────────────────────────────────────
# PHASE 3  :  Custom Fields on Sales Invoice
# ─────────────────────────────────────────────────────────────────────────────
def create_custom_fields():
    custom_fields = [
        {
            "dt": "Sales Invoice",
            "fieldname": "is_gold_invoice",
            "fieldtype": "Check",
            "label": "فاتورة مشغولات ذهب",
            "insert_after": "company",
            "default": "0",
        },
        {
            "dt": "Sales Invoice",
            "fieldname": "gold_section",
            "fieldtype": "Section Break",
            "label": "تفاصيل الذهب",
            "insert_after": "is_gold_invoice",
            "depends_on": "eval:doc.is_gold_invoice==1",
        },
        {
            "dt": "Sales Invoice",
            "fieldname": "gold_item",
            "fieldtype": "Link",
            "label": "صنف الذهب المصروف",
            "options": "Item",
            "insert_after": "gold_section",
            "depends_on": "eval:doc.is_gold_invoice==1",
        },
        {
            "dt": "Sales Invoice",
            "fieldname": "gold_carat",
            "fieldtype": "Data",
            "label": "العيار",
            "insert_after": "gold_item",
            "depends_on": "eval:doc.is_gold_invoice==1",
        },
        {
            "dt": "Sales Invoice",
            "fieldname": "gold_weight",
            "fieldtype": "Float",
            "label": "الوزن بالجرام",
            "precision": "6",
            "insert_after": "gold_carat",
            "depends_on": "eval:doc.is_gold_invoice==1",
        },
        {
            "dt": "Sales Invoice",
            "fieldname": "equivalent_21",
            "fieldtype": "Float",
            "label": "مكافئ عيار 21",
            "precision": "6",
            "insert_after": "gold_weight",
            "read_only": 1,
            "depends_on": "eval:doc.is_gold_invoice==1",
        },
        {
            "dt": "Sales Invoice",
            "fieldname": "gold_col_break",
            "fieldtype": "Column Break",
            "label": "",
            "insert_after": "equivalent_21",
        },
        {
            "dt": "Sales Invoice",
            "fieldname": "price_per_gram",
            "fieldtype": "Currency",
            "label": "سعر المشغول لكل جرام",
            "insert_after": "gold_col_break",
            "depends_on": "eval:doc.is_gold_invoice==1",
        },
        {
            "dt": "Sales Invoice",
            "fieldname": "total_workmanship",
            "fieldtype": "Currency",
            "label": "إجمالي المشغولات",
            "insert_after": "price_per_gram",
            "read_only": 1,
            "depends_on": "eval:doc.is_gold_invoice==1",
        },
        {
            "dt": "Sales Invoice",
            "fieldname": "source_warehouse",
            "fieldtype": "Link",
            "label": "المستودع المصدر",
            "options": "Warehouse",
            "insert_after": "total_workmanship",
            "depends_on": "eval:doc.is_gold_invoice==1",
        },
        {
            "dt": "Sales Invoice",
            "fieldname": "target_warehouse",
            "fieldtype": "Link",
            "label": "مستودع العهدة",
            "options": "Warehouse",
            "insert_after": "source_warehouse",
            "depends_on": "eval:doc.is_gold_invoice==1",
        },
        {
            "dt": "Sales Invoice",
            "fieldname": "gold_status_section",
            "fieldtype": "Section Break",
            "label": "حالة حركة الذهب",
            "insert_after": "target_warehouse",
            "depends_on": "eval:doc.is_gold_invoice==1",
        },
        {
            "dt": "Sales Invoice",
            "fieldname": "gold_movement_created",
            "fieldtype": "Check",
            "label": "تم إنشاء حركة الذهب",
            "insert_after": "gold_status_section",
            "read_only": 1,
        },
        {
            "dt": "Sales Invoice",
            "fieldname": "gold_movement_status",
            "fieldtype": "Select",
            "label": "حالة حركة الذهب",
            "options": "\nPending\nCreated\nCancelled",
            "insert_after": "gold_movement_created",
            "read_only": 1,
        },
        {
            "dt": "Sales Invoice",
            "fieldname": "gold_col_break_2",
            "fieldtype": "Column Break",
            "label": "",
            "insert_after": "gold_movement_status",
        },
        {
            "dt": "Sales Invoice",
            "fieldname": "stock_entry_ref",
            "fieldtype": "Link",
            "label": "رابط حركة المخزون",
            "options": "Stock Entry",
            "insert_after": "gold_col_break_2",
            "read_only": 1,
        },
        {
            "dt": "Sales Invoice",
            "fieldname": "journal_entry_ref",
            "fieldtype": "Link",
            "label": "رابط القيد المحاسبي",
            "options": "Journal Entry",
            "insert_after": "stock_entry_ref",
            "read_only": 1,
        },
    ]

    for cf in custom_fields:
        dt = cf["dt"]
        fn = cf["fieldname"]
        if frappe.db.exists("Custom Field", {"dt": dt, "fieldname": fn}):
            print(f"Custom Field '{fn}' on '{dt}' already exists — skipping.")
            continue
        doc = frappe.new_doc("Custom Field")
        doc.update(cf)
        doc.insert(ignore_permissions=True)
        print(f"Created Custom Field '{fn}' on '{dt}'")


# ─────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────
def run():
    create_gold_customer_ledger()
    create_gold_receipt()
    frappe.db.commit()
    print("Phase 2 — Doctypes created.")
    create_custom_fields()
    frappe.db.commit()
    print("Phase 3 — Custom Fields created.")
    print("Done.")

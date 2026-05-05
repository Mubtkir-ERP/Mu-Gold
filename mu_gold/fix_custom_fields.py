import frappe

FIELD_UPDATES = [
    # fieldname, new label, new insert_after
    ("is_gold_invoice",       "Is Gold Workmanship Invoice",    "last_scanned_warehouse"),
    ("gold_section",          "Gold Details",                    "is_gold_invoice"),
    ("gold_item",             "Gold Item Issued",                "gold_section"),
    ("gold_carat",            "Carat",                           "gold_item"),
    ("gold_weight",           "Weight (Grams)",                  "gold_carat"),
    ("equivalent_21",         "Carat 21 Equivalent",             "gold_weight"),
    ("gold_col_break",        "",                                "equivalent_21"),
    ("price_per_gram",        "Workmanship Price per Gram",      "gold_col_break"),
    ("total_workmanship",     "Total Workmanship Amount",        "price_per_gram"),
    ("source_warehouse",      "Source Warehouse",                "total_workmanship"),
    ("target_warehouse",      "Custodial Warehouse (Target)",    "source_warehouse"),
    ("gold_status_section",   "Gold Movement Status",            "target_warehouse"),
    ("gold_movement_created", "Gold Movement Created",           "gold_status_section"),
    ("gold_movement_status",  "Gold Movement Status",            "gold_movement_created"),
    ("gold_col_break_2",      "",                                "gold_movement_status"),
    ("stock_entry_ref",       "Stock Entry Reference",           "gold_col_break_2"),
    ("journal_entry_ref",     "Journal Entry Reference",         "stock_entry_ref"),
]

def run():
    for fieldname, label, insert_after in FIELD_UPDATES:
        cf_name = f"Sales Invoice-{fieldname}"
        if frappe.db.exists("Custom Field", cf_name):
            frappe.db.set_value("Custom Field", cf_name, {
                "label": label,
                "insert_after": insert_after,
            })
            print(f"Updated '{fieldname}' → label='{label}', insert_after='{insert_after}'")
        else:
            print(f"MISSING: Custom Field '{cf_name}' not found")
    frappe.db.commit()
    print("Done.")

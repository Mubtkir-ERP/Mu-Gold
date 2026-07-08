import frappe

def execute():
    fields_to_copy = [
        "is_gold_invoice",
        "gold_section",
        "gold_item",
        "gold_item_description",
        "gold_carat",
        "gold_weight",
        "equivalent_21",
        "gold_col_break",
        "price_per_gram",
        "total_workmanship"
    ]

    for fieldname in fields_to_copy:
        try:
            cf = frappe.get_doc("Custom Field", f"Sales Invoice-{fieldname}")
            
            new_name = f"Purchase Invoice-{fieldname}"
            if not frappe.db.exists("Custom Field", new_name):
                new_cf = frappe.copy_doc(cf)
                new_cf.dt = "Purchase Invoice"
                new_cf.name = new_name
                new_cf.insert(ignore_permissions=True)
            else:
                doc = frappe.get_doc("Custom Field", new_name)
                # update fields
                for prop in ["label", "fieldtype", "options", "depends_on", "hidden", "insert_after", "read_only", "fetch_from"]:
                    doc.set(prop, cf.get(prop))
                doc.save(ignore_permissions=True)
        except Exception as e:
            print(f"Failed to copy {fieldname}: {e}")

    # For Purchase Invoice, we should also hide the gold_item_description just like we did in Sales Invoice
    frappe.db.set_value("Custom Field", "Purchase Invoice-gold_item_description", "hidden", 1)

    print("Successfully added gold fields to Purchase Invoice.")

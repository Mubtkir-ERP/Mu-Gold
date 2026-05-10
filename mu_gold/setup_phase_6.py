import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_field

def run():
    reports = [
        {"name": "Gold Customer Statement", "ref_doctype": "Gold Customer Ledger", "report_type": "Script Report", "module": "Mu Gold"},
        {"name": "Comprehensive Customer Statement", "ref_doctype": "Customer", "report_type": "Script Report", "module": "Mu Gold"},
        {"name": "Stock By Carat", "ref_doctype": "Bin", "report_type": "Script Report", "module": "Mu Gold"},
        {"name": "Gold At Customers", "ref_doctype": "Gold Customer Ledger", "report_type": "Script Report", "module": "Mu Gold"},
        {"name": "Gold Reconciliation", "ref_doctype": "Gold Customer Ledger", "report_type": "Script Report", "module": "Mu Gold"},
    ]
    
    for rp in reports:
        if not frappe.db.exists("Report", rp["name"]):
            doc = frappe.new_doc("Report")
            doc.report_name = rp["name"]
            doc.ref_doctype = rp["ref_doctype"]
            doc.report_type = rp["report_type"]
            doc.module = rp["module"]
            doc.is_standard = "Yes"
            doc.insert(ignore_permissions=True)
            print(f"Created Report: {rp['name']}")
        else:
            print(f"Report {rp['name']} already exists.")

    print("Phase 6 Reports setup completed.")

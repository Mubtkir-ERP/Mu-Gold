import frappe

def run():
    roles = [
        "Gold Sales User", 
        "Gold Stock User", 
        "Gold Manager"
    ]
    
    for role_name in roles:
        if not frappe.db.exists("Role", role_name):
            doc = frappe.new_doc("Role")
            doc.role_name = role_name
            doc.desk_access = 1
            doc.insert(ignore_permissions=True)
            print(f"Created Role: {role_name}")
        else:
            print(f"Role {role_name} already exists.")
            
    # Add permissions for Gold Customer Ledger
    if not frappe.db.exists("Custom DocPerm", {"parent": "Gold Customer Ledger"}):
        for role in ["Gold Sales User", "Gold Stock User", "Gold Manager"]:
            frappe.get_doc({
                "doctype": "Custom DocPerm",
                "parent": "Gold Customer Ledger",
                "parenttype": "DocType",
                "parentfield": "permissions",
                "role": role,
                "read": 1,
                "write": 1 if role == "Gold Manager" else 0,
                "create": 0,
                "submit": 0
            }).insert(ignore_permissions=True)
            
    # Add permissions for Gold Receipt
    if not frappe.db.exists("Custom DocPerm", {"parent": "Gold Receipt"}):
        for role in ["Gold Stock User", "Gold Manager"]:
            frappe.get_doc({
                "doctype": "Custom DocPerm",
                "parent": "Gold Receipt",
                "parenttype": "DocType",
                "parentfield": "permissions",
                "role": role,
                "read": 1,
                "write": 1,
                "create": 1,
                "submit": 1,
                "cancel": 1
            }).insert(ignore_permissions=True)
            
    # Refresh to apply permissions
    frappe.clear_cache()
    print("Permissions setup completed.")

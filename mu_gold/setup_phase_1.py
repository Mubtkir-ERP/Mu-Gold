import frappe

def create_item_attribute():
    if not frappe.db.exists("Item Attribute", "العيار"):
        doc = frappe.new_doc("Item Attribute")
        doc.attribute_name = "العيار"
        doc.numeric_values = 0
        for v in ["18", "21", "22", "24"]:
            doc.append("item_attribute_values", {"attribute_value": v, "abbr": v})
        doc.insert(ignore_permissions=True)
        print("Created Item Attribute 'العيار'")

def create_item_template_and_variants():
    # Item Group
    if not frappe.db.exists("Item Group", "ذهب"):
        doc = frappe.new_doc("Item Group")
        doc.item_group_name = "ذهب"
        root_group = frappe.db.get_value("Item Group", {"parent_item_group": ["in", ["", None]]}) or frappe.db.get_all("Item Group")[0].name
        doc.parent_item_group = "Products" if frappe.db.exists("Item Group", "Products") else root_group
        doc.is_group = 0
        doc.insert(ignore_permissions=True)
        
    if not frappe.db.exists("Item", "كسر ذهب"):
        doc = frappe.new_doc("Item")
        doc.item_code = "كسر ذهب"
        doc.item_name = "كسر ذهب"
        doc.item_group = "ذهب"
        doc.stock_uom = "Gram"
        doc.has_variants = 1
        doc.append("attributes", {"attribute": "العيار"})
        doc.insert(ignore_permissions=True)
        print("Created Item Template 'كسر ذهب'")
        
    for v in ["18", "21", "22", "24"]:
        variant_code = f"كسر ذهب {v}"
        if not frappe.db.exists("Item", variant_code):
            doc = frappe.new_doc("Item")
            doc.item_code = variant_code
            doc.item_name = variant_code
            doc.item_group = "ذهب"
            doc.variant_of = "كسر ذهب"
            doc.has_variants = 0
            doc.stock_uom = "Gram"
            doc.append("attributes", {"attribute": "العيار", "attribute_value": v})
            doc.insert(ignore_permissions=True)
            print(f"Created Item Variant '{variant_code}'")

def create_service_item():
    if not frappe.db.exists("Item Group", "خدمات"):
        doc = frappe.new_doc("Item Group")
        doc.item_group_name = "خدمات"
        root_group = frappe.db.get_value("Item Group", {"parent_item_group": ["in", ["", None]]}) or frappe.db.get_all("Item Group")[0].name
        doc.parent_item_group = "Services" if frappe.db.exists("Item Group", "Services") else root_group
        doc.is_group = 0
        doc.insert(ignore_permissions=True)
        
    if not frappe.db.exists("Item", "مشغولات ذهب"):
        doc = frappe.new_doc("Item")
        doc.item_code = "مشغولات ذهب"
        doc.item_name = "مشغولات ذهب"
        doc.item_group = "خدمات"
        doc.is_stock_item = 0
        doc.stock_uom = "Gram"
        doc.insert(ignore_permissions=True)
        print("Created Service Item 'مشغولات ذهب'")

def create_accounts():
    company = "Mu"
    stock_parent = "اصول المخزون - M"
    asset_parent = "أصول متداولة - M"
    income_parent = "إيراد مباشر - M"
    diff_parent = "دخل غير مباشرة - M"

    # Customer Vault Group
    if not frappe.db.exists("Account", "عهد ذهب لدى العملاء - M"):
        doc = frappe.new_doc("Account")
        doc.account_name = "عهد ذهب لدى العملاء"
        doc.company = company
        doc.parent_account = asset_parent
        doc.is_group = 1
        doc.insert(ignore_permissions=True)
        print("Created Customer Vault Account Group")

    for v in ["18", "21", "22", "24"]:
        # Inventory
        inv_acc = f"مخزون كسر ذهب {v}"
        if not frappe.db.exists("Account", f"{inv_acc} - M"):
            doc = frappe.new_doc("Account")
            doc.account_name = inv_acc
            doc.company = company
            doc.parent_account = stock_parent
            doc.account_type = "Stock"
            doc.insert(ignore_permissions=True)
            print(f"Created Account '{inv_acc}'")
            
        # Vault
        vault_acc = f"ذهب لدى العملاء {v}"
        if not frappe.db.exists("Account", f"{vault_acc} - M"):
            doc = frappe.new_doc("Account")
            doc.account_name = vault_acc
            doc.company = company
            doc.parent_account = "عهد ذهب لدى العملاء - M"
            doc.insert(ignore_permissions=True)
            print(f"Created Account '{vault_acc}'")

    if not frappe.db.exists("Account", "إيراد مشغولات الذهب - M"):
        doc = frappe.new_doc("Account")
        doc.account_name = "إيراد مشغولات الذهب"
        doc.company = company
        doc.parent_account = income_parent
        doc.account_type = "Income Account"
        doc.insert(ignore_permissions=True)
        print("Created Account 'إيراد مشغولات الذهب'")
        
    diffs = ["فروقات تحويل العيار", "فروقات تقريب الذهب", "تسويات ذهب العملاء"]
    for d in diffs:
        if not frappe.db.exists("Account", f"{d} - M"):
            doc = frappe.new_doc("Account")
            doc.account_name = d
            doc.company = company
            doc.parent_account = diff_parent
            doc.insert(ignore_permissions=True)
            print(f"Created Account '{d}'")

def create_warehouses():
    company = "Mu"
    parent_wh = "جميع المخازن - M"
    
    # Gold Warehouses
    for v in ["18", "21", "22", "24"]:
        wh_name = f"مستودع ذهب {v}"
        if not frappe.db.exists("Warehouse", f"{wh_name} - M"):
            doc = frappe.new_doc("Warehouse")
            doc.warehouse_name = wh_name
            doc.company = company
            doc.parent_warehouse = parent_wh
            doc.insert(ignore_permissions=True)
            print(f"Created Warehouse '{wh_name}'")
            
        vault_wh = f"عهدة ذهب عند العملاء {v}"
        if not frappe.db.exists("Warehouse", f"{vault_wh} - M"):
            doc = frappe.new_doc("Warehouse")
            doc.warehouse_name = vault_wh
            doc.company = company
            doc.parent_warehouse = parent_wh
            doc.insert(ignore_permissions=True)
            print(f"Created Warehouse '{vault_wh}'")

def run():
    frappe.flags.in_test = True
    create_item_attribute()
    create_item_template_and_variants()
    create_service_item()
    create_accounts()
    create_warehouses()
    frappe.db.commit()
    print("Setup Phase 1 Complete.")

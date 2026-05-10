import frappe
from mu_gold.mu_gold.controllers.gold_movement_utils import get_equivalent_21

def run():
    frappe.flags.in_test = True
    customer = "عميل ذهب"
    company = "Mu"
    source_wh = "مستودع ذهب 21 - M"
    target_wh = "عهدة ذهب عند العملاء 21 - M"
    target_wh_18 = "عهدة ذهب عند العملاء 18 - M"
    source_wh_18 = "مستودع ذهب 18 - M"

    # Case 3 Setup
    # Ensure there is an item for 18
    if not frappe.db.exists("Item", "كسر ذهب 18"):
        frappe.get_doc({
            "doctype": "Item",
            "item_code": "كسر ذهب 18",
            "item_group": "ذهب كسر",
            "is_stock_item": 1,
            "stock_uom": "Gram",
            "has_variants": 0
        }).insert(ignore_permissions=True)
        print("Created item كسر ذهب 18")

    # Ensure warehouses exist for 18
    if not frappe.db.exists("Warehouse", source_wh_18):
        frappe.get_doc({
            "doctype": "Warehouse",
            "warehouse_name": "مستودع ذهب 18",
            "company": company,
            "parent_warehouse": "مستودعات الشركة - M"
        }).insert(ignore_permissions=True)
        frappe.get_doc({
            "doctype": "Warehouse",
            "warehouse_name": "عهدة ذهب عند العملاء 18",
            "company": company,
            "parent_warehouse": "المستودعات الخارجية - M"
        }).insert(ignore_permissions=True)

    print("Running MVP Verification...")
    
    # Check balance before any new return
    last_balance = frappe.db.get_list("Gold Customer Ledger", 
        filters={"customer": customer},
        order_by="creation desc", limit=1, fields=["balance_after"]
    )
    
    bal = last_balance[0].balance_after if last_balance else 0
    print(f"Current Balance for {customer}: {bal} Equivalent 21")

    # Let's create a return for 58.333333g of 18 Carat
    doc = frappe.new_doc("Gold Receipt")
    from frappe.utils import today
    doc.date = today()
    doc.company = company
    doc.customer = customer
    doc.gold_item = "كسر ذهب 18"
    doc.carat = "18"
    doc.weight = 58.333333
    doc.source_warehouse = target_wh_18 # Customer returns FROM his vault
    doc.target_warehouse = source_wh_18 # TO the company stock vault
    
    # We must ensure customer has stock in his vault? Wait, the customer vault for 18 might be empty, 
    # but the frappe allows negative stock if enabled, or we must inject stock into the vault first.
    # In reality, the customer owes equivalent 21, but returns 18. Physical gold comes from Customer Vault 18?
    # This implies the customer must have had 18 in his vault. If he received 21, his vault has 21.
    # The spec: "استلام من العميل (مستودع عهدة الهدف)" -> he returns to stock. 
    # Actually, he returns gold that goes into `source_wh_18`. 
    
    # To avoid stock errors, let's enable allow_negative_stock temporarily in stock settings
    stock_settings = frappe.get_doc("Stock Settings")
    old_allow = stock_settings.allow_negative_stock
    if not old_allow:
        stock_settings.allow_negative_stock = 1
        stock_settings.save(ignore_permissions=True)
    
    doc.insert(ignore_permissions=True)
    doc.submit()
    
    print(f"Submitted Gold Receipt: {doc.name}")
    print(f"  Receipt Equivalent 21: {doc.equivalent_21}")
    
    last_balance = frappe.db.get_list("Gold Customer Ledger", 
        filters={"customer": customer},
        order_by="creation desc", limit=1, fields=["balance_after"]
    )
    new_bal = last_balance[0].balance_after if last_balance else 0
    print(f"New Balance for {customer}: {new_bal} Equivalent 21")
    
    # Restore stock settings
    if not old_allow:
        stock_settings.allow_negative_stock = 0
        stock_settings.save(ignore_permissions=True)

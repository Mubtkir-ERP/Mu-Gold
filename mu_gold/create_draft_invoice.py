import frappe

def run():
    frappe.flags.in_test = True
    company = frappe.get_all("Company")[0].name
    
    # 1. Create the customer if not exists
    customer_name = "عميل ذهب"
    if not frappe.db.exists("Customer", customer_name):
        doc = frappe.new_doc("Customer")
        doc.customer_name = customer_name
        doc.customer_type = "Company"
        doc.customer_group = frappe.db.get_list("Customer Group", limit=1)[0].name if frappe.db.exists("Customer Group") else None
        doc.territory = frappe.db.get_list("Territory", limit=1)[0].name if frappe.db.exists("Territory") else None
        doc.insert(ignore_permissions=True)
        print(f"Created Customer: {customer_name}")
    else:
        print(f"Customer {customer_name} already exists")

    # 2. Check Service Item
    service_item = "مشغولات ذهب"
    if not frappe.db.exists("Item", service_item):
        print(f"Error: Item {service_item} not found!")
        return
        
    gold_item = "كسر ذهب 21"
    
    source_wh = f"مستودع ذهب 21 - M"  # assuming standard - M suffix from company abbreviation
    if not frappe.db.exists("Warehouse", source_wh):
         source_wh = "مستودع ذهب 21 - M" # fallback to default 

    target_wh = f"عهدة ذهب عند العملاء 21 - M"
    
    # Create Draft Sales Invoice
    si = frappe.new_doc("Sales Invoice")
    si.company = company
    si.customer = customer_name
    si.is_gold_invoice = 1
    
    # Sales Invoice Items (Service)
    si.append("items", {
        "item_code": service_item,
        "qty": 50,
        "rate": 2.0,
    })
    
    # Gold Custom Fields
    si.gold_item = gold_item
    si.gold_carat = "21"
    si.gold_weight = 50.0
    si.equivalent_21 = 50.0
    si.price_per_gram = 2.0
    si.total_workmanship = 100.0
    si.source_warehouse = source_wh
    si.target_warehouse = target_wh
    
    si.insert(ignore_permissions=True)
    frappe.db.commit()
    print(f"Created Draft Sales Invoice: {si.name}")


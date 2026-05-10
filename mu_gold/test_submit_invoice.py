import frappe

def run():
    frappe.flags.in_test = True
    
    # 1. Provide sufficient stock in source warehouse to avoid insufficient stock error
    item_code = "كسر ذهب 21"
    wh = "مستودع ذهب 21 - M"
    
    # Simple stock entry receipt to ensure we have stock
    se_receipt = frappe.new_doc("Stock Entry")
    se_receipt.purpose = "Material Receipt"
    se_receipt.stock_entry_type = "Material Receipt"
    se_receipt.company = "Mu"
    se_receipt.append("items", {
        "item_code": item_code,
        "qty": 1000,
        "t_warehouse": wh,
        "basic_rate": 200
    })
    se_receipt.insert(ignore_permissions=True)
    se_receipt.submit()
    print(f"Added 1000g stock for {item_code}")

    # 2. Get the draft invoice created earlier and submit it
    si_name = frappe.get_all("Sales Invoice", filters={"is_gold_invoice": 1, "docstatus": 0}, limit=1)[0].name
    si = frappe.get_doc("Sales Invoice", si_name)
    si.submit()
    print(f"Submitted Invoice: {si.name}")
    print(f"  Stock Entry Ref: {si.stock_entry_ref}")
    print(f"  Gold Movement Status: {si.gold_movement_status}")
    
    # 3. Check Gold Customer Ledger
    ledger = frappe.get_all("Gold Customer Ledger", filters={"reference_name": si.name})
    if ledger:
        print(f"Created Ledger Entry: {ledger[0].name}")
    else:
        print("FAILED to create Ledger Entry.")

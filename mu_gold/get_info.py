import frappe

def run():
    frappe.init(site="mu-gold")
    frappe.connect()
    company = frappe.get_all("Company")[0].name
    print(f"Company: {company}")
    
    # Check parents
    stock_group = frappe.get_all("Account", filters={"company": company, "account_type": "Stock", "is_group": 1}, fields=["name"])
    print(f"Stock Groups: {stock_group}")
    
    asset_group = frappe.get_all("Account", filters={"company": company, "root_type": "Asset", "is_group": 1, "account_type": "Receivable"}, fields=["name"])
    if not asset_group:
        asset_group = frappe.get_all("Account", filters={"company": company, "root_type": "Asset", "is_group": 1}, fields=["name"])
    print(f"Asset Groups: {asset_group}")
    
    income_group = frappe.get_all("Account", filters={"company": company, "root_type": "Income", "is_group": 1}, fields=["name"])
    print(f"Income Groups: {income_group}")
    
    expense_group = frappe.get_all("Account", filters={"company": company, "root_type": "Expense", "is_group": 1}, fields=["name"])
    print(f"Expense Groups: {expense_group}")
    
    warehouse_group = frappe.get_all("Warehouse", filters={"company": company, "is_group": 1}, fields=["name"])
    print(f"Warehouse Groups: {warehouse_group}")

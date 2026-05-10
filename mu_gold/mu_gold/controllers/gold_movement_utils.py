import frappe
from frappe.utils import flt
from frappe import _

def get_equivalent_21(weight, carat):
    """Calculate Carat 21 equivalent weight correctly"""
    if not carat:
        return 0.0
    return flt(weight) * flt(carat) / 21.0

def create_stock_entry(doc, purpose, source_warehouse, target_warehouse, item_code, qty):
    se = frappe.new_doc("Stock Entry")
    se.purpose = purpose
    se.stock_entry_type = purpose
    se.posting_date = doc.posting_date if hasattr(doc, 'posting_date') else doc.date
    se.company = doc.company
    se.add_to_transit = 0
    
    se.append("items", {
        "item_code": item_code,
        "qty": qty,
        "s_warehouse": source_warehouse,
        "t_warehouse": target_warehouse,
        "allow_zero_valuation_rate": 1
    })
    
    se.insert(ignore_permissions=True)
    se.submit()
    return se.name

def get_customer_gold_balance(customer, company):
    last_entry = frappe.db.get_list("Gold Customer Ledger", 
        filters={"customer": customer, "company": company, "docstatus": 1, "is_cancelled": 0},
        order_by="date desc, creation desc", limit=1, fields=["balance_after"]
    )
    if last_entry:
        return flt(last_entry[0].balance_after)
    return 0.0

def rebuild_running_balance(customer, company):
    entries = frappe.get_all("Gold Customer Ledger", 
        filters={"customer": customer, "company": company, "docstatus": 1, "is_cancelled": 0},
        order_by="date asc, creation asc"
    )
    running_balance = 0.0
    for row in entries:
        doc = frappe.get_doc("Gold Customer Ledger", row.name)
        running_balance += flt(doc.equivalent_21_change)
        frappe.db.set_value("Gold Customer Ledger", doc.name, "balance_after", running_balance, update_modified=False)

def create_gold_ledger_entry(doc, movement_type, ref_type, ref_name, item, carat, weight, eq_change, s_warehouse, t_warehouse, se_ref=None, je_ref=None, receipt_ref=None):
    customer = doc.customer
    prev_balance = get_customer_gold_balance(customer, doc.company)
        
    ledg = frappe.new_doc("Gold Customer Ledger")
    ledg.company = doc.company
    ledg.date = doc.posting_date if hasattr(doc, 'posting_date') else doc.date
    ledg.customer = customer
    ledg.movement_type = movement_type
    ledg.reference_type = ref_type
    ledg.reference_name = ref_name
    
    ledg.gold_item = item
    ledg.carat = carat
    ledg.actual_weight = weight
    ledg.equivalent_21_change = eq_change
    ledg.balance_after = prev_balance + eq_change
    
    ledg.source_warehouse = s_warehouse
    ledg.target_warehouse = t_warehouse
    
    # تعبئة الروابط المرجعية
    ledg.stock_entry_ref = se_ref
    ledg.journal_entry_ref = je_ref
    
    if ref_type == "Sales Invoice":
        ledg.invoice_ref = ref_name
    elif ref_type == "Gold Receipt":
        ledg.receipt_ref = receipt_ref or ref_name
        
    ledg.insert(ignore_permissions=True)
    ledg.submit()
    return ledg.name

def create_journal_entry_for_issue(doc):
    je = frappe.new_doc("Journal Entry")
    je.voucher_type = "Journal Entry"
    je.company = doc.company
    je.posting_date = doc.posting_date
    je.user_remark = f"Gold Value Transfer to Custody (Carat {doc.gold_carat}): {doc.name}"
    
    # تحديد العيار للبحث عن الحسابات المناسبة
    carat = str(doc.gold_carat)
    
    # 1. البحث عن حساب المخزون لنفس العيار
    stock_account = frappe.db.get_value("Account", {
        "account_type": "Stock", 
        "account_name": ["like", f"%{carat}%"],
        "company": doc.company,
        "is_group": 0
    })
    if not stock_account: # Fallback
        stock_account = frappe.db.get_value("Account", {"account_type": "Stock", "company": doc.company, "is_group": 0})
    
    # 2. البحث عن حساب عهدة ذهب لنفس العيار
    custody_account = frappe.db.get_value("Account", {
        "account_name": ["like", f"%عهدة%"],
        "account_name": ["like", f"%{carat}%"],
        "company": doc.company,
        "is_group": 0
    })
    if not custody_account: # Fallback 1: أي حساب عهدة
        custody_account = frappe.db.get_value("Account", {"account_name": ["like", "%عهدة ذهب%"], "company": doc.company})
    if not custody_account: # Fallback 2: أي حساب أصول
        custody_account = frappe.db.get_value("Account", {"account_type": "Asset", "company": doc.company, "is_group": 0})

    if not stock_account or not custody_account:
        return None
        
    val_rate = flt(frappe.db.get_value("Stock Ledger Entry", 
        {"voucher_type": "Stock Entry", "voucher_no": doc.stock_entry_ref, "item_code": doc.gold_item, "warehouse": doc.source_warehouse}, 
        "valuation_rate"))
    if not val_rate: val_rate = 1.0
    
    amount = flt(doc.gold_weight) * val_rate
    
    # القيد: مدين (عهدة ذهب نفس العيار) / دائن (مخزون كسر نفس العيار)
    je.append("accounts", {
        "account": custody_account, 
        "debit_in_account_currency": amount, 
        "credit_in_account_currency": 0,
        "user_remark": f"Gold Carat {carat} issued to {doc.customer}"
    })
    je.append("accounts", {
        "account": stock_account, 
        "debit_in_account_currency": 0, 
        "credit_in_account_currency": amount
    })
    je.insert(ignore_permissions=True)
    je.submit()
    return je.name

def create_journal_entry_for_receipt(doc):
    je = frappe.new_doc("Journal Entry")
    je.voucher_type = "Journal Entry"
    je.company = doc.company
    je.posting_date = doc.date
    je.user_remark = f"Gold Return from Custody (Carat {doc.carat}): {doc.name}"
    
    carat = str(doc.carat)
    
    # 1. حساب المخزون نفس العيار
    stock_account = frappe.db.get_value("Account", {
        "account_type": "Stock", 
        "account_name": ["like", f"%{carat}%"],
        "company": doc.company,
        "is_group": 0
    })
    if not stock_account:
        stock_account = frappe.db.get_value("Account", {"account_type": "Stock", "company": doc.company, "is_group": 0})
        
    # 2. حساب عهدة نفس العيار
    custody_account = frappe.db.get_value("Account", {
        "account_name": ["like", f"%عهدة%"],
        "account_name": ["like", f"%{carat}%"],
        "company": doc.company,
        "is_group": 0
    })
    if not custody_account:
        custody_account = frappe.db.get_value("Account", {"account_name": ["like", "%عهدة ذهب%"], "company": doc.company})
    if not custody_account:
        custody_account = frappe.db.get_value("Account", {"account_type": "Asset", "company": doc.company, "is_group": 0})

    if not stock_account or not custody_account:
        return None
        
    val_rate = flt(frappe.db.get_value("Stock Ledger Entry", 
        {"voucher_type": "Stock Entry", "voucher_no": doc.stock_entry_ref, "item_code": doc.gold_item, "warehouse": doc.target_warehouse}, 
        "valuation_rate"))
    if not val_rate: val_rate = 1.0
    
    amount = flt(doc.weight) * val_rate
    
    je.append("accounts", {
        "account": stock_account, 
        "debit_in_account_currency": amount, 
        "credit_in_account_currency": 0
    })
    je.append("accounts", {
        "account": custody_account, 
        "debit_in_account_currency": 0, 
        "credit_in_account_currency": amount,
        "user_remark": f"Gold Carat {carat} returned from {doc.customer}"
    })
    je.insert(ignore_permissions=True)
    je.submit()
    return je.name

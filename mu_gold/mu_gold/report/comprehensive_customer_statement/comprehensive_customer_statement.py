import frappe
from frappe import _

def execute(filters=None):
    columns = [
        {"fieldname": "customer", "label": _("Customer"), "fieldtype": "Link", "options": "Customer", "width": 150},
        {"fieldname": "customer_name", "label": _("Customer Name"), "fieldtype": "Data", "width": 150},
        {"fieldname": "financial_balance", "label": _("Financial Debt (Currency)"), "fieldtype": "Currency", "width": 150},
        {"fieldname": "gold_issued", "label": _("Total Gold Issued (Eq 21)"), "fieldtype": "Float", "precision": 6, "width": 150},
        {"fieldname": "gold_received", "label": _("Total Gold Received (Eq 21)"), "fieldtype": "Float", "precision": 6, "width": 150},
        {"fieldname": "current_gold_balance", "label": _("Gold Balance (Eq 21)"), "fieldtype": "Float", "precision": 6, "width": 150},
        {"fieldname": "pay_in_18", "label": _("If Pay In 18k (Grams)"), "fieldtype": "Float", "precision": 6, "width": 150},
        {"fieldname": "pay_in_21", "label": _("If Pay In 21k (Grams)"), "fieldtype": "Float", "precision": 6, "width": 150},
        {"fieldname": "pay_in_22", "label": _("If Pay In 22k (Grams)"), "fieldtype": "Float", "precision": 6, "width": 150},
        {"fieldname": "pay_in_24", "label": _("If Pay In 24k (Grams)"), "fieldtype": "Float", "precision": 6, "width": 150},
    ]
    
    # Financial Balance (AR)
    ar_data = frappe.db.sql("""
        SELECT gle.party as customer, SUM(gle.debit) - SUM(gle.credit) as ar_balance
        FROM `tabGL Entry` gle
        INNER JOIN `tabAccount` acc ON acc.name = gle.account
        WHERE gle.party_type = 'Customer'
          AND acc.account_type = 'Receivable'
          AND gle.is_cancelled = 0
        GROUP BY gle.party
    """, as_dict=True)
    ar_map = {r.customer: r.ar_balance for r in ar_data if r.customer}
    
    # Gold Ledger Aggregations
    gold_data = frappe.db.sql("""
        SELECT 
            customer,
            SUM(CASE WHEN movement_type = 'ISSUE' THEN equivalent_21_change ELSE 0 END) as total_issued,
            SUM(CASE WHEN movement_type = 'RECEIPT' THEN ABS(equivalent_21_change) ELSE 0 END) as total_received
        FROM `tabGold Customer Ledger`
        WHERE is_cancelled = 0 AND docstatus = 1
        GROUP BY customer
    """, as_dict=True)
    
    # Current Gold Balances (Window function emulation from previous report)
    balance_data = frappe.db.sql("""
        SELECT t1.customer, t1.balance_after
        FROM `tabGold Customer Ledger` t1
        WHERE t1.is_cancelled = 0 AND t1.docstatus = 1
        AND t1.creation = (
            SELECT MAX(t2.creation) FROM `tabGold Customer Ledger` t2
            WHERE t2.customer = t1.customer AND t2.is_cancelled = 0 AND t2.docstatus = 1
        )
    """, as_dict=True)
    balance_map = {r.customer: r.balance_after for r in balance_data if r.customer}
    
    data = []
    processed_customers = set()
    
    for row in gold_data:
        customer = row.customer
        if not customer: continue
        processed_customers.add(customer)
        cname = frappe.db.get_value("Customer", customer, "customer_name")
        curr_bal = balance_map.get(customer, 0.0)
        
        data.append({
            "customer": customer,
            "customer_name": cname,
            "financial_balance": ar_map.get(customer, 0.0),
            "gold_issued": row.total_issued,
            "gold_received": row.total_received,
            "current_gold_balance": curr_bal,
            "pay_in_18": (curr_bal * 21) / 18 if curr_bal > 0 else 0,
            "pay_in_21": curr_bal,
            "pay_in_22": (curr_bal * 21) / 22 if curr_bal > 0 else 0,
            "pay_in_24": (curr_bal * 21) / 24 if curr_bal > 0 else 0,
        })
        
    for customer, ar_bal in ar_map.items():
        if customer and customer not in processed_customers:
            cname = frappe.db.get_value("Customer", customer, "customer_name")
            data.append({
                "customer": customer,
                "customer_name": cname,
                "financial_balance": ar_bal,
                "gold_issued": 0, "gold_received": 0, "current_gold_balance": 0,
                "pay_in_18": 0, "pay_in_21": 0, "pay_in_22": 0, "pay_in_24": 0,
            })

    return columns, data

import frappe
from frappe import _

def execute(filters=None):
    columns = [
        {"fieldname": "customer", "label": _("Customer"), "fieldtype": "Link", "options": "Customer", "width": 200},
        {"fieldname": "customer_name", "label": _("Customer Name"), "fieldtype": "Data", "width": 200},
        {"fieldname": "operational_eq_21", "label": _("Eq 21 (Operational)"), "fieldtype": "Float", "precision": 6, "width": 150},
        {"fieldname": "gl_balance", "label": _("Accounting Balance (Currency)"), "fieldtype": "Currency", "width": 200},
    ]
    
    # Gold Ledger Operational Balances
    ledger_data = frappe.db.sql("""
        SELECT 
            t1.customer,
            c.customer_name,
            t1.balance_after as equivalent_21_balance
        FROM `tabGold Customer Ledger` t1
        JOIN `tabCustomer` c ON t1.customer = c.name
        WHERE t1.is_cancelled = 0 AND t1.docstatus = 1
        AND t1.creation = (
            SELECT MAX(t2.creation)
            FROM `tabGold Customer Ledger` t2
            WHERE t2.customer = t1.customer
            AND t2.is_cancelled = 0 AND t2.docstatus = 1
        )
    """, as_dict=True)

    # GL balances for Customer Vault accounts
    gl_data = frappe.db.sql("""
        SELECT 
            party as customer,
            sum(debit) - sum(credit) as gl_balance
        FROM `tabGL Entry`
        WHERE party_type = 'Customer' AND account LIKE 'ذهب لدى العملاء%'
        GROUP BY party
    """, as_dict=True)
    
    gl_map = {row.customer: row.gl_balance for row in gl_data if row.customer}
    
    data = []
    processed_customers = set()
    
    for row in ledger_data:
        customer = row.customer
        processed_customers.add(customer)
        data.append({
            "customer": customer,
            "customer_name": row.customer_name,
            "operational_eq_21": row.equivalent_21_balance,
            "gl_balance": gl_map.get(customer, 0.0)
        })
        
    for doc in gl_data:
        if doc.customer and doc.customer not in processed_customers:
            cname = frappe.db.get_value("Customer", doc.customer, "customer_name")
            data.append({
                "customer": doc.customer,
                "customer_name": cname,
                "operational_eq_21": 0.0,
                "gl_balance": doc.gl_balance
            })

    return columns, data

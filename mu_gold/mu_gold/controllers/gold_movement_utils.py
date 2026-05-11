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

def _get_custody_account(carat, company):
    """البحث عن حساب ذهب لدى العملاء بالعيار المحدد"""
    carat = str(carat)
    # محاولة 1: حساب يحتوي كلمة 'عهدة' ورقم العيار
    acc = frappe.db.get_value("Account", {
        "account_name": ["like", f"%عهدة%{carat}%"],
        "company": company,
        "is_group": 0
    })
    if acc:
        return acc
    # محاولة 2: حساب يحتوي 'ذهب لدى العملاء' ورقم العيار
    acc = frappe.db.get_value("Account", {
        "account_name": ["like", f"%لدى العملاء%{carat}%"],
        "company": company,
        "is_group": 0
    })
    if acc:
        return acc
    # محاولة 3: أي حساب عهدة
    return frappe.db.get_value("Account", {
        "account_name": ["like", "%عهدة ذهب%"],
        "company": company,
        "is_group": 0
    })


def _get_stock_account(carat, company):
    """البحث عن حساب مخزون بالعيار المحدد"""
    carat = str(carat)
    acc = frappe.db.get_value("Account", {
        "account_type": "Stock",
        "account_name": ["like", f"%{carat}%"],
        "company": company,
        "is_group": 0
    })
    if not acc:
        acc = frappe.db.get_value("Account", {
            "account_type": "Stock",
            "company": company,
            "is_group": 0
        })
    return acc


def _get_workmanship_amount_for_receipt(doc):
    """
    احتساب قيمة المشغولات المتناسبة مع وزن الاستلام.

    المنطق:
      - نجلب آخر فاتورة مشغولات مفتوحة للعميل بنفس العيار
      - نحسب: سعر الجرام × وزن الاستلام
      - إذا لم تتوفر فاتورة، نستخدم متوسط سعر الجرام من كل فواتير العميل
      - الحد الأدنى: 0.01 ريال لتجنب قيد بصفر
    """
    customer = doc.customer
    carat    = str(doc.carat)
    weight   = flt(doc.weight)

    # البحث عن فواتير مشغولات لهذا العميل بنفس العيار (مرتحلة)
    invoices = frappe.db.sql("""
        SELECT name, gold_weight, price_per_gram, total_workmanship
        FROM `tabSales Invoice`
        WHERE customer = %s
          AND gold_carat = %s
          AND is_gold_invoice = 1
          AND docstatus = 1
        ORDER BY posting_date DESC
        LIMIT 5
    """, (customer, carat), as_dict=True)

    if invoices:
        # متوسط سعر الجرام من آخر 5 فواتير
        total_price = sum(flt(inv.price_per_gram) for inv in invoices)
        avg_price   = total_price / len(invoices) if invoices else 0
        amount      = round(weight * avg_price, 2) if avg_price else 0
        return amount if amount > 0 else None

    # fallback: أي فاتورة للعميل بأي عيار
    row = frappe.db.sql("""
        SELECT price_per_gram FROM `tabSales Invoice`
        WHERE customer = %s AND is_gold_invoice = 1 AND docstatus = 1
        ORDER BY posting_date DESC LIMIT 1
    """, customer, as_dict=True)
    if row and flt(row[0].price_per_gram) > 0:
        return round(weight * flt(row[0].price_per_gram), 2)

    return None


def create_journal_entry_for_issue(doc):
    je = frappe.new_doc("Journal Entry")
    je.voucher_type = "Journal Entry"
    je.company = doc.company
    je.posting_date = doc.posting_date
    je.user_remark = f"Gold Value Transfer to Custody (Carat {doc.gold_carat}): {doc.name}"

    carat = str(doc.gold_carat)
    stock_account   = _get_stock_account(carat, doc.company)
    custody_account = _get_custody_account(carat, doc.company)

    if not stock_account or not custody_account:
        return None

    # القيمة = سعر المشغول × الوزن (من الفاتورة مباشرة)
    amount = round(flt(doc.gold_weight) * flt(doc.price_per_gram), 2)
    if amount <= 0:
        amount = 1.0  # قيمة رمزية لتجنب قيد بصفر

    # القيد: مدين (ذهب لدى العملاء) / دائن (مخزون)
    je.append("accounts", {
        "account": custody_account,
        "debit_in_account_currency": amount,
        "credit_in_account_currency": 0,
        "user_remark": f"Workmanship value — Carat {carat} issued to {doc.customer}"
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
    """
    القيد العكسي عند استلام الذهب من العميل:
      مدين:  مخزون كسر ذهب [عيار]        ← يرجع للمخزون
      دائن:  ذهب لدى العملاء [عيار]       ← تنخفض العهدة

    المبلغ = قيمة المشغولات النسبية (سعر الجرام × وزن المُرجع)
    """
    je = frappe.new_doc("Journal Entry")
    je.voucher_type = "Journal Entry"
    je.company = doc.company
    je.posting_date = doc.date
    je.user_remark = f"Reverse Workmanship — Gold Return Carat {doc.carat}: {doc.name}"

    carat = str(doc.carat)
    stock_account   = _get_stock_account(carat, doc.company)
    custody_account = _get_custody_account(carat, doc.company)

    if not stock_account or not custody_account:
        frappe.log_error(
            title="Gold Receipt — JE Accounts Not Found",
            message=f"Could not find stock/custody accounts for Carat {carat}, Company {doc.company}"
        )
        return None

    # احتساب قيمة المشغولات المقابلة للوزن المُرجع
    amount = _get_workmanship_amount_for_receipt(doc)
    if not amount or amount <= 0:
        frappe.log_error(
            title="Gold Receipt — JE Amount Warning",
            message=f"No workmanship price found for customer {doc.customer} carat {carat}. JE skipped."
        )
        return None

    # القيد العكسي: مدين مخزون / دائن عهدة
    je.append("accounts", {
        "account": stock_account,
        "debit_in_account_currency": amount,
        "credit_in_account_currency": 0,
        "user_remark": f"Gold Carat {carat} returned by {doc.customer} — {doc.weight}g"
    })
    je.append("accounts", {
        "account": custody_account,
        "debit_in_account_currency": 0,
        "credit_in_account_currency": amount,
        "user_remark": f"Reverse workmanship value — {doc.name}"
    })
    je.insert(ignore_permissions=True)
    je.submit()
    return je.name

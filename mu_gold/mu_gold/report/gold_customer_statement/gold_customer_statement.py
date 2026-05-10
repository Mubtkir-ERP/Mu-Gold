import frappe
from frappe import _
from frappe.utils import flt


def execute(filters=None):
    filters = filters or {}
    columns = [
        {"fieldname": "date", "label": _("Date"), "fieldtype": "Date", "width": 100},
        {"fieldname": "movement_type", "label": _("Movement"), "fieldtype": "Data", "width": 100},
        {"fieldname": "reference_type", "label": _("Ref Type"), "fieldtype": "Data", "width": 120},
        {"fieldname": "reference_name", "label": _("Ref No"), "fieldtype": "Dynamic Link",
         "options": "reference_type", "width": 160},
        {"fieldname": "gold_item", "label": _("Item"), "fieldtype": "Link",
         "options": "Item", "width": 150},
        {"fieldname": "carat", "label": _("Carat"), "fieldtype": "Data", "width": 70},
        {"fieldname": "actual_weight", "label": _("Actual Weight (g)"),
         "fieldtype": "Float", "precision": 6, "width": 130},
        {"fieldname": "equivalent_21_change", "label": _("Eq-21 Change"),
         "fieldtype": "Float", "precision": 6, "width": 120},
        {"fieldname": "balance_after", "label": _("Running Balance (Eq-21)"),
         "fieldtype": "Float", "precision": 6, "width": 160},
        {"fieldname": "source_warehouse", "label": _("Source Warehouse"),
         "fieldtype": "Link", "options": "Warehouse", "width": 180},
        {"fieldname": "target_warehouse", "label": _("Target Warehouse"),
         "fieldtype": "Link", "options": "Warehouse", "width": 180},
        {"fieldname": "notes", "label": _("Notes"), "fieldtype": "Data", "width": 200},
    ]

    conditions = "is_cancelled = 0 AND docstatus = 1"
    values = {}

    if filters.get("customer"):
        conditions += " AND customer = %(customer)s"
        values["customer"] = filters["customer"]
    if filters.get("company"):
        conditions += " AND company = %(company)s"
        values["company"] = filters["company"]
    if filters.get("from_date"):
        conditions += " AND date >= %(from_date)s"
        values["from_date"] = filters["from_date"]
    if filters.get("to_date"):
        conditions += " AND date <= %(to_date)s"
        values["to_date"] = filters["to_date"]

    data = frappe.db.sql(f"""
        SELECT
            date, movement_type, reference_type, reference_name,
            gold_item, carat, actual_weight, equivalent_21_change,
            balance_after, source_warehouse, target_warehouse, notes
        FROM `tabGold Customer Ledger`
        WHERE {conditions}
        ORDER BY date ASC, creation ASC
    """, values, as_dict=True)

    return columns, data

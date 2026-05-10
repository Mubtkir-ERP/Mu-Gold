import frappe
from frappe import _

def execute(filters=None):
    filters = filters or {}
    columns = [
        {"fieldname": "carat",     "label": _("Carat"),              "fieldtype": "Data",  "width": 80},
        {"fieldname": "item_code", "label": _("Item"),               "fieldtype": "Link",  "options": "Item", "width": 180},
        {"fieldname": "warehouse", "label": _("Warehouse"),          "fieldtype": "Link",  "options": "Warehouse", "width": 220},
        {"fieldname": "actual_qty","label": _("Actual Qty (Grams)"), "fieldtype": "Float", "precision": 6, "width": 150},
    ]

    conditions = "item.item_group = 'ذهب'"
    params = {}
    if filters.get("company"):
        abbr = frappe.get_cached_value("Company", filters["company"], "abbr")
        conditions += " AND bin.warehouse LIKE %(wh_suffix)s"
        params["wh_suffix"] = f"% - {abbr}"

    data = frappe.db.sql(f"""
        SELECT
            REGEXP_SUBSTR(bin.item_code, '[0-9]+') AS carat,
            bin.item_code   AS item_code,
            bin.warehouse   AS warehouse,
            bin.actual_qty  AS actual_qty
        FROM `tabBin` bin
        JOIN `tabItem` item ON bin.item_code = item.name
        WHERE {conditions} AND bin.actual_qty != 0
        ORDER BY carat ASC, bin.warehouse ASC
    """, params, as_dict=True)

    return columns, data

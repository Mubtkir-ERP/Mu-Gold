import frappe
from frappe.utils import flt
import re


def validate(doc, method):
    """
    Intercept Stock Entry before save/submit.
    Enforces the Multi-UOM design pattern for all manual and system gold entries:
    - Standardizes the item code to the unified base item ('ذهب كسر').
    - Sets the row UOM to the specific secondary carat UOM ('جرام-24', 'جرام-18', etc.).
    - Populates the corresponding mathematical conversion factor natively.
    - Allows ERPNext core inventory engine to post weighted base units automatically.
    """
    std_item = "ذهب كسر"
    has_std_item = frappe.db.exists("Item", std_item)

    factors = {"24": 1.142857, "22": 1.047619, "21": 1.0, "18": 0.857143}

    for item in doc.get("items") or []:
        if not item.item_code:
            continue

        is_gold = False
        if "ذهب" in str(item.item_code) or "Gold" in str(item.item_code):
            is_gold = True
        else:
            item_group = frappe.db.get_value("Item", item.item_code, "item_group")
            if item_group and ("ذهب" in item_group or "Gold" in item_group):
                is_gold = True

        if is_gold:
            # Determine original carat string
            carat_str = "21"
            match = re.search(r'\b(24|22|21|18)\b', str(item.item_code))
            if match:
                carat_str = match.group(1)
            else:
                item_name = frappe.db.get_value("Item", item.item_code, "item_name") or ""
                match2 = re.search(r'\b(24|22|21|18)\b', str(item_name))
                if match2:
                    carat_str = match2.group(1)
                else:
                    if getattr(item, "uom", "") and "جرام-" in str(item.uom):
                        carat_str = str(item.uom).split("-")[-1]

            uom_name = f"جرام-{carat_str}"
            factor = factors.get(carat_str, 1.0)

            if has_std_item:
                item.item_code = std_item
                item.item_name = std_item
                item.description = std_item

            item.uom = uom_name
            item.conversion_factor = factor
            item.stock_uom = "جرام-21"
            
            # Recalculate transfer_qty natively if supported
            if hasattr(item, "transfer_qty") and item.transfer_qty is not None:
                item.transfer_qty = flt(item.qty) * factor

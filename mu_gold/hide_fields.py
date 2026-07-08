import frappe

def execute():
    fields_to_keep = [
        # Main
        "customer_section",
        "title",
        "naming_series",
        "customer",
        "customer_name",
        "column_break1",
        "posting_date",
        "posting_time",
        "set_posting_time",
        "due_date",
        "update_stock",
        
        # Items and Item Totals
        "items_section",
        "items",
        "section_break_30",
        "total_qty",
        "total_net_weight",
        "column_break_32",
        "base_total",
        "base_net_total",
        "column_break_52",
        "total",
        "net_total",
        
        # Totals
        "totals",
        "base_grand_total",
        "base_rounding_adjustment",
        "base_rounded_total",
        "base_in_words",
        "column_break5",
        "grand_total",
        "rounding_adjustment",
        "use_company_roundoff_cost_center",
        "rounded_total",
        "in_words",
        "total_advance",
        "outstanding_amount",
        "disable_rounded_total",
        
        # Taxes
        "taxes_section",
        "tax_category",
        "taxes_and_charges",
        "column_break_38",
        "shipping_rule",
        "column_break_55",
        "incoterm",
        "named_place",
        "section_break_40",
        "taxes",
        "section_break_43",
        "base_total_taxes_and_charges",
        "column_break_47",
        "total_taxes_and_charges",
        
        # Discount
        "section_break_49",
        "apply_discount_on",
        "base_discount_amount",
        "is_cash_or_non_trade_discount",
        "additional_discount_account",
        "column_break_51",
        "additional_discount_percentage",
        "discount_amount",
        
        # Address & Contact
        "contact_and_address_tab",
        "address_and_contact",
        "customer_address",
        "address_display",
        "col_break4",
        "contact_person",
        "contact_display",
        "contact_mobile",
        
        # Connections
        "connections_tab"
    ]

    gold_custom_fields_to_keep = [
        "is_gold_invoice",
        "gold_section",
        "gold_item",
        "gold_carat",
        "gold_weight",
        "equivalent_21",
        "gold_col_break",
        "price_per_gram",
        "total_workmanship",
        "source_warehouse",
        "target_warehouse",
        "gold_status_section",
        "gold_movement_created",
        "gold_movement_status",
        "gold_col_break_2",
        "stock_entry_ref",
        "journal_entry_ref"
    ]

    meta = frappe.get_meta("Sales Invoice")
    
    # Hide fields
    for d in meta.fields:
        if d.fieldname not in fields_to_keep and d.fieldname not in gold_custom_fields_to_keep:
            # Create property setter to hide
            if not d.hidden:
                frappe.make_property_setter({
                    "doctype": "Sales Invoice",
                    "doctype_or_field": "DocField",
                    "fieldname": d.fieldname,
                    "property": "hidden",
                    "value": 1,
                    "property_type": "Check"
                }, validate_fields_for_doctype=False)
        else:
            # Ensure it's visible (remove hidden property setter if any)
            if d.fieldname not in ["title"]: # title is standard hidden
                frappe.db.delete("Property Setter", {
                    "doc_type": "Sales Invoice",
                    "field_name": d.fieldname,
                    "property": "hidden"
                })

    # Discount right after Totals
    # We move section_break_49 (Discount) to be after disable_rounded_total
    # To move the whole section, we need to move its fields sequentially if they aren't already sequential.
    # Actually, Discount is natively after Totals, so we don't strictly need to move it, but let's keep the logic if needed.
    
    # We will use the 'field_order' property on the DocType to guarantee the reordering.
    # The user wants Taxes to be below Totals and Discount on the main page.
    import json
    
    field_order = [d.fieldname for d in meta.fields]
    
    taxes_fields = [
        "taxes_section",
        "tax_category",
        "taxes_and_charges",
        "column_break_38",
        "shipping_rule",
        "incoterm",
        "named_place",
        "taxes",
        "column_break_47",
        "total_taxes_and_charges"
    ]
    
    # Remove taxes fields from current order
    for tf in taxes_fields:
        if tf in field_order:
            field_order.remove(tf)
            
    # Insert them right before contact_and_address_tab to be at the very bottom of the main tab
    if "contact_and_address_tab" in field_order:
        idx = field_order.index("contact_and_address_tab")
        for i, tf in enumerate(taxes_fields):
            field_order.insert(idx + i, tf)
    else:
        for tf in taxes_fields:
            field_order.append(tf)
            
    # Set the field_order property setter for the DocType
    frappe.make_property_setter({
        "doctype": "Sales Invoice",
        "doctype_or_field": "DocType",
        "fieldname": "Sales Invoice", # required by Frappe Property Setter for DocType properties
        "property": "field_order",
        "value": json.dumps(field_order),
        "property_type": "Data"
    }, validate_fields_for_doctype=False)

    # Move update_stock right below due_date to fit in main section
    # Since we redefine field_order above, we should also manually adjust update_stock in the field_order array!
    if "update_stock" in field_order:
        field_order.remove("update_stock")
        if "due_date" in field_order:
            due_date_idx = field_order.index("due_date")
            field_order.insert(due_date_idx + 1, "update_stock")
            
        frappe.make_property_setter({
            "doctype": "Sales Invoice",
            "doctype_or_field": "DocType",
            "fieldname": "Sales Invoice",
            "property": "field_order",
            "value": json.dumps(field_order),
            "property_type": "Data"
        }, validate_fields_for_doctype=False)

    # Hide custom gold_item_description
    frappe.db.set_value("Custom Field", "Sales Invoice-gold_item_description", "hidden", 1)

    # Clean up any previously created insert_after for customer_group
    frappe.db.delete("Property Setter", {
        "doc_type": "Sales Invoice",
        "field_name": "customer_group",
        "property": "insert_after"
    })

    frappe.db.commit()
    print("Successfully configured Sales Invoice layout.")

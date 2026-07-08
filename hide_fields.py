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
                frappe.make_property_setter(
                    doctype='Sales Invoice',
                    fieldname=d.fieldname,
                    property='hidden',
                    value=1,
                    property_type='Check',
                    doctype_or_field='DocField'
                )
        else:
            # Ensure it's visible (remove hidden property setter if any)
            if d.fieldname not in ["title"]: # title is standard hidden
                frappe.db.delete("Property Setter", {
                    "doc_type": "Sales Invoice",
                    "field_name": d.fieldname,
                    "property": "hidden"
                })

    # To satisfy "المجموعات ارفعها فوق والضريبه والخصم تحت الاجماليات"
    # We move Taxes and Discount under Totals. 
    # Taxes moved right after the end of Totals section:
    frappe.make_property_setter(
        doctype='Sales Invoice',
        fieldname='taxes_section',
        property='insert_after',
        value='disable_rounded_total',
        property_type='Data',
        doctype_or_field='DocField'
    )

    # Discount is natively after Totals, but let's make sure it's after Taxes:
    frappe.make_property_setter(
        doctype='Sales Invoice',
        fieldname='section_break_49',
        property='insert_after',
        value='total_taxes_and_charges',
        property_type='Data',
        doctype_or_field='DocField'
    )
    
    # Hide custom gold_item_description
    frappe.db.set_value("Custom Field", "Sales Invoice-gold_item_description", "hidden", 1)

    # Move update_stock right below due_date to fit in main section
    frappe.make_property_setter(
        doctype='Sales Invoice',
        fieldname='update_stock',
        property='insert_after',
        value='due_date',
        property_type='Data',
        doctype_or_field='DocField'
    )

    # Clean up any previously created insert_after for customer_group
    frappe.db.delete("Property Setter", {
        "doc_type": "Sales Invoice",
        "field_name": "customer_group",
        "property": "insert_after"
    })

    frappe.db.commit()
    print("Successfully configured Sales Invoice layout.")

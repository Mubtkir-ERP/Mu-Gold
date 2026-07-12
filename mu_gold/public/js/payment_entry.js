frappe.ui.form.on('Payment Entry', {
    setup: function(frm) {
        // Prevent other scripts from unhiding these fields
        let fields_to_force_hide = [
            "is_advance_payment",
            "is_advance_payment_depends_on_entry",
            "section_break_34", 
            "total_allocated_amount",
            "base_total_allocated_amount",
            "column_break_36",
            "unallocated_amount",
            "difference_amount",
            "write_off_difference_amount",
            "unallocated_tax",
            "allocated_tax",
            "accounting_dimensions_section",
            "project",
            "dimension_col_break",
            "cost_center",
            "reference_date"
        ];
        
        let original_set_df_property = frm.set_df_property;
        frm.set_df_property = function(fieldname, property, value) {
            if (property === 'hidden' && value === 0 && fields_to_force_hide.includes(fieldname)) {
                // Deny unhiding
                return;
            }
            return original_set_df_property.apply(this, arguments);
        };
    },
    refresh: function(frm) {
        if (!frm.doc.reference_date && frm.doc.posting_date) {
            frm.set_value("reference_date", frm.doc.posting_date);
        }
    },
    posting_date: function(frm) {
        if (frm.doc.posting_date) {
            frm.set_value("reference_date", frm.doc.posting_date);
        }
    },
    validate: function(frm) {
        if (!frm.doc.reference_date && frm.doc.posting_date) {
            frm.doc.reference_date = frm.doc.posting_date;
        }
    }
});

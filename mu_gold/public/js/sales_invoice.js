frappe.ui.form.on('Sales Invoice', {
    refresh: function(frm) {
        setup_gold_invoice_behavior(frm);
    },
    is_gold_invoice: function(frm) {
        setup_gold_invoice_behavior(frm);
        if (frm.doc.is_gold_invoice) {
            fetch_default_gold_metadata(frm);
        }
    },
    gold_item: function(frm) {
        update_live_shadow_row(frm);
    },
    gold_carat: function(frm) {
        update_live_shadow_row(frm);
    },
    gold_weight: function(frm) {
        update_live_shadow_row(frm);
        // Calculate equivalent 21k weight client-side for immediate user feedback
        if (frm.doc.gold_weight && frm.doc.gold_carat) {
            let carat_val = parseFloat(frm.doc.gold_carat.replace("جرام-", "")) || 21.0;
            frm.set_value("equivalent_21", flt(frm.doc.gold_weight * carat_val / 21.0, 6));
        }
    },
    price_per_gram: function(frm) {
        update_live_shadow_row(frm);
        if (frm.doc.gold_weight && frm.doc.price_per_gram) {
            frm.set_value("total_workmanship", flt(frm.doc.gold_weight * frm.doc.price_per_gram, 2));
        }
    }
});

function setup_gold_invoice_behavior(frm) {
    if (frm.doc.is_gold_invoice) {
        // Filter gold_carat link field to show only Gold UOMs
        frm.set_query("gold_carat", function() {
            return {
                filters: {
                    "is_gold_uom": 1
                }
            };
        });

        // Filter gold_item to show gold items or default items
        frm.set_query("gold_item", function() {
            return {
                filters: {
                    "is_stock_item": 1
                }
            };
        });

        // Make warehouses read-only if populated automatically
        frm.set_df_property("source_warehouse", "read_only", 1);
        frm.set_df_property("target_warehouse", "read_only", 1);
        
        // Hide the items table to prevent manual tampering for gold invoices
        frm.set_df_property("items", "hidden", 1);
        
        // Fetch if not set yet
        if (!frm.doc.gold_item || !frm.doc.source_warehouse) {
            fetch_default_gold_metadata(frm);
        }
    } else {
        frm.set_df_property("source_warehouse", "read_only", 0);
        frm.set_df_property("target_warehouse", "read_only", 0);
        
        // Show the items table for normal invoices
        frm.set_df_property("items", "hidden", 0);
    }
}

function fetch_default_gold_metadata(frm) {
    frappe.db.get_value("Item", {"is_default_gold_item": 1}, 
        ["name", "default_source_warehouse", "default_target_warehouse"])
    .then(r => {
        let values = r.message;
        if (values && values.name) {
            let updates = {};
            if (!frm.doc.gold_item) updates["gold_item"] = values.name;
            if (values.default_source_warehouse) updates["source_warehouse"] = values.default_source_warehouse;
            if (values.default_target_warehouse) updates["target_warehouse"] = values.default_target_warehouse;
            
            if (Object.keys(updates).length > 0) {
                frm.set_value(updates);
            }
        }
    });
}

function update_live_shadow_row(frm) {
    if (!frm.doc.is_gold_invoice) return;
    
    // Ensure we have at least one item row to act as the shadow
    let row = null;
    if (!frm.doc.items || frm.doc.items.length === 0) {
        row = frm.add_child("items");
    } else {
        row = frm.doc.items[0];
    }
    
    let updated = false;
    let item_val = frm.doc.gold_item || "ذهب كسر";
    if (row.item_code !== item_val) {
        row.item_code = item_val;
        row.item_name = item_val; // Initial safe fallback to satisfy immediate grid constraints
        row.description = item_val;
        updated = true;
    }
    
    if (frm.doc.gold_weight && row.qty !== frm.doc.gold_weight) {
        row.qty = frm.doc.gold_weight;
        updated = true;
        // Native core invocation to recalculate row totals and stock quantities standardly
        setTimeout(() => frm.script_manager.trigger("qty", row.doctype, row.name), 50);
    }
    
    if (frm.doc.gold_carat && row.uom !== frm.doc.gold_carat) {
        row.uom = frm.doc.gold_carat;
        updated = true;
        // Native core invocation to trigger multi-uom conversion factor mapping standardly
        setTimeout(() => frm.script_manager.trigger("uom", row.doctype, row.name), 50);
    }
    
    if (frm.doc.price_per_gram !== undefined && row.rate !== frm.doc.price_per_gram) {
        row.rate = frm.doc.price_per_gram;
        updated = true;
    }
    
    // Asynchronously fetch permitted metadata (item_name, description) to satisfy immediate grid constraints
    if (!row.item_name || row.item_name === item_val || !row.income_account) {
        frappe.db.get_value("Item", item_val, ["item_name", "description"])
        .then(r => {
            let item_data = r.message;
            if (item_data) {
                let row_needs_refresh = false;
                if (item_data.item_name && row.item_name !== item_data.item_name) {
                    row.item_name = item_data.item_name;
                    row_needs_refresh = true;
                }
                if (item_data.description && row.description !== item_data.description) {
                    row.description = item_data.description;
                    row_needs_refresh = true;
                }
                
                // Resolve Income Account securely from Company Default Income Account to bypass Item child table restrictions
                if (!row.income_account && frm.doc.company) {
                    frappe.db.get_value("Company", frm.doc.company, "default_income_account")
                    .then(cr => {
                        if (cr && cr.message && cr.message.default_income_account) {
                            row.income_account = cr.message.default_income_account;
                            frm.refresh_field("items");
                        }
                    });
                } else if (row_needs_refresh) {
                    frm.refresh_field("items");
                }
            }
        });
    }

    if (updated) {
        frm.refresh_field("items");
    }
}

frappe.ui.form.on('Purchase Invoice', {
    refresh: function(frm) {
        setup_gold_invoice_behavior(frm);
    },
    is_gold_invoice: function(frm) {
        setup_gold_invoice_behavior(frm);
        if (frm.doc.is_gold_invoice && frm.doc.supplier && !frm.doc.gold_item) {
            fetch_default_gold_metadata(frm);
        }
    },
    supplier: function(frm) {
        if (frm.doc.is_gold_invoice && frm.doc.supplier && !frm.doc.gold_item) {
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

        // Hide the items table to prevent manual tampering for gold invoices
        frm.set_df_property("items", "hidden", 1);

    } else {
        // Show the items table for normal invoices
        frm.set_df_property("items", "hidden", 0);
    }
}

function fetch_default_gold_metadata(frm) {
    frappe.db.get_value("Item", {"is_default_gold_item": 1},
        ["name"])
    .then(r => {
        let values = r.message;
        if (values && values.name) {
            let updates = {};
            if (!frm.doc.gold_item) updates["gold_item"] = values.name;

            if (Object.keys(updates).length > 0) {
                frm.set_value(updates);
            }
        }
    });
}

function update_live_shadow_row(frm) {
    if (!frm.doc.is_gold_invoice) return;

    // Ensure we have at least one item row
    let row = null;
    if (!frm.doc.items || frm.doc.items.length === 0) {
        row = frm.add_child("items");
        frm.refresh_field("items");
    } else {
        row = frm.doc.items[0];
    }

    let item_val = frm.doc.gold_item || "ذهب كسر";

    // Use frappe.model.set_value for every field so Frappe's native event chain
    // fires — this is exactly what happens when the user picks values manually.
    // This ensures conversion_factor is fetched correctly from the Item master.

    // Step 1: item_code — triggers item defaults fetch (stock_uom, accounts, etc.)
    if (row.item_code !== item_val) {
        frappe.model.set_value(row.doctype, row.name, "item_code", item_val);
    }

    // Step 2: UOM — triggers conversion_factor fetch from Item master automatically
    //         (same behavior as when user manually selects UOM from the child table)
    if (frm.doc.gold_carat && row.uom !== frm.doc.gold_carat) {
        frappe.model.set_value(row.doctype, row.name, "uom", frm.doc.gold_carat);
    }

    // Step 3: qty — triggers stock_qty recalculation
    if (frm.doc.gold_weight && row.qty !== frm.doc.gold_weight) {
        frappe.model.set_value(row.doctype, row.name, "qty", frm.doc.gold_weight);
    }

    // Step 4: rate — enforce price_per_gram (override any pricing rule)
    if (frm.doc.price_per_gram !== undefined && row.rate !== frm.doc.price_per_gram) {
        frappe.model.set_value(row.doctype, row.name, "rate", frm.doc.price_per_gram);
    }
}

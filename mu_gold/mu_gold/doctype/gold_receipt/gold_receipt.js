frappe.ui.form.on("Gold Receipt", {
    onload: function(frm) {
        if (frm.is_new()) {
            frm.set_value("date", frappe.datetime.get_today());
            fetch_default_receipt_metadata(frm);
        }
    },
    refresh: function(frm) {
        // Filter carat to show only gold UOMs
        frm.set_query("carat", function() {
            return {
                filters: {
                    "is_gold_uom": 1
                }
            };
        });

        // Filter gold_item to show only stock items
        frm.set_query("gold_item", function() {
            return {
                filters: {
                    "is_stock_item": 1
                }
            };
        });

        // Make warehouses read-only to ensure strict vault consistency
        frm.set_df_property("source_warehouse", "read_only", 1);
        frm.set_df_property("target_warehouse", "read_only", 1);

        if (frm.is_new() && (!frm.doc.gold_item || !frm.doc.source_warehouse)) {
            fetch_default_receipt_metadata(frm);
        }
    },
    weight: function(frm) {
        calculate_equivalent_21(frm);
    },
    carat: function(frm) {
        calculate_equivalent_21(frm);
    }
});

function fetch_default_receipt_metadata(frm) {
    frappe.db.get_value("Item", {"is_default_gold_item": 1}, 
        ["name", "default_source_warehouse", "default_target_warehouse"])
    .then(r => {
        let values = r.message;
        if (values && values.name) {
            let updates = {};
            if (!frm.doc.gold_item) updates["gold_item"] = values.name;
            // For Gold Receipt, gold returns FROM Custodial Vault (source) TO Internal Shop Vault (target)
            if (values.default_target_warehouse && !frm.doc.source_warehouse) {
                updates["source_warehouse"] = values.default_target_warehouse;
            }
            if (values.default_source_warehouse && !frm.doc.target_warehouse) {
                updates["target_warehouse"] = values.default_source_warehouse;
            }
            if (Object.keys(updates).length > 0) {
                frm.set_value(updates);
            }
        }
    });
}

function calculate_equivalent_21(frm) {
    if (frm.doc.weight && frm.doc.carat) {
        let carat_val = parseFloat(frm.doc.carat.replace("جرام-", "")) || 21.0;
        frm.set_value("equivalent_21", flt(frm.doc.weight * carat_val / 21.0, 6));
    }
}

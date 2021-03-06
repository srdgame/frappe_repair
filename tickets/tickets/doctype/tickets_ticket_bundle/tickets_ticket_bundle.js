// Copyright (c) 2017, Dirk Chang and contributors
// For license information, please see license.txt

frappe.ui.form.on('Tickets Ticket Bundle', {
	setup: function (frm) {
		frm.fields_dict['tickets'].grid.get_field("ticket").get_query = function(doc) {
			return {
				searchfield:"ticket_name",
				filters: {
					"docstatus": 1,
					"assigned_to_user": null,
					"status": "New",
					"task_type": doc.tickets_type
				}
			}
		}
	},
	refresh: function(frm) {
		frm.clear_custom_buttons();
		if(frm.doc.docstatus == 1 && !frm.doc.assigned_to_user) {
			frm.add_custom_button(__("Get It"), function() {
				frm.events.bundle_event(frm, "bundle_get");
			}).removeClass("btn-default").addClass("btn-primary");
		}
		if(frm.doc.docstatus == 1 && frm.doc.assigned_to_user==user) {
			frm.add_custom_button(__("Fixed"), function() {
				frm.events.bundle_event(frm, "bundle_fixed");
			}).removeClass("btn-default").addClass("btn-success");
		}
	},
	bundle_event: function(frm, event) {
		return frappe.call({
			doc: frm.doc,
			method: event,
			freeze: true,
			callback: function(r) {
				if(!r.exc)
					frm.refresh_fields();
					frm.events.refresh(frm);
			}
		});
	}
});

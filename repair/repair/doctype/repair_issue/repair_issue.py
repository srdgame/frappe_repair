# -*- coding: utf-8 -*-
# Copyright (c) 2015, Dirk Chang and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import json
from frappe.model.document import Document
from frappe import throw, _
from frappe.utils.data import format_datetime
from repair.repair.doctype.repair_site.repair_site import list_sites



class RepairIssue(Document):

	def on_submit(self):
		if self.wechat_notify == 1:
			frappe.enqueue('repair.repair.doctype.repair_issue.repair_issue.wechat_notify_by_issue_name',
							issue_name = self.name, issue_doc=self)

	def has_website_permission(self, ptype, verbose=False):
		user = frappe.session.user
		if self.fixed_by == user:
			return True

		teams = [d[0] for d in frappe.db.get_values('Repair SiteTeam', {"parent": self.site}, "team")]

		for team in teams:
			if frappe.get_value('Repair TeamUser', {"parent": team, "user": user}):
				return True

		return False

	def wechat_tmsg_data(self):
		return {
			"first": {
				"value": _("New Issue Created"),
				"color": "red"
			},
			"keyword1": {
				"value": self.name,  # 编号
				"color": "blue"
			},
			"keyword2": {
				"value": self.issue_name,  # 标题
				"color": "blue"
			},
			"keyword3": {
				"value": format_datetime(self.modified),  # 时间
				"color": "green",
			},
			"remark": {
				"value": _("Site: {0}\nPrioirty: {1}\nInfo: {2}").format(self.site, self.total_cost, self.issue_desc)
			}
		}

	def wechat_tmsg_url(self):
		return "/update-repair-issue?name=" + self.name

	def update_cost(self):
		tickets = self.get("tickets")
		self.total_cost = 0
		for ticket in tickets:
			self.total_cost += frappe.get_value("Repair Ticket", ticket.ticket, "cost")
		self.save()

	def append_tickets(self, *tickets):
		if self.docstatus != 1:
			throw(_("Cannot append tickets on un-submitted issue"))
			
		current_tickets = [d.ticket for d in self.get("tickets")]
		for ticket in tickets:
			if ticket.name in current_tickets:
				continue
			self.append("tickets", {"ticket": ticket.name})

		self.update_cost()

	def remove_tickets(self, *tickets):
		if self.docstatus != 1:
			throw(_("Cannot append tickets on un-submitted issue"))

		existing_tickets = dict((d.ticket, d) for d in self.get("tickets"))
		for ticket in tickets:
			if ticket.name in existing_tickets:
				self.get("tickets").remove(existing_tickets[ticket.name])

		self.update_cost()


def get_issue_list(doctype, txt, filters, limit_start, limit_page_length=20, order_by="modified desc"):
	user_groups='"' + '", "'.join(list_user_groups(frappe.session.user)) + '"'
	return frappe.db.sql('''select distinct issue.*
		from `tabRepair Issue` issue, `tabRepair SiteTeam` site_team
		where issue.docstatus != 2
			and issue.site = site_team.parent
			and site_team.team in %(groups)s)
			order by issue.{0}
			limit {1}, {2}
		'''.format(order_by, limit_start, limit_page_length),
			{'groups':user_groups},
			as_dict=True,
			update={'doctype':'Repair Issue'})


def get_list_context(context=None):
	return {
		"show_sidebar": True,
		"show_search": True,
		"no_breadcrumbs": True,
		"title": _("Repair Issues"),
		"get_list": get_issue_list,
		"row_template": "templates/generators/repair_issue_row.html",
	}


def get_permission_query_conditions(user):
	if 'Repair Manager' in frappe.get_roles(user):
		return ""

	sites = list_sites(user)

	return """(`tabRepair Issue`.site in ({sites}))""".format(
		sites='"' + '", "'.join(sites) + '"')


def wechat_notify_by_issue_name(issue_name, issue_doc=None):
	issue_doc = issue_doc or frappe.get_doc("Repair Issue", issue_name)

	user_list = {}
	# Get all teams for that site
	for st in frappe.db.get_values("Repair SiteTeam", {"parent": issue_doc.site}, "team"):
		ent = frappe.db.get_value("Repair Team", st[0], "enterprise")
		app = frappe.db.get_value("Repair Enterprise", ent, "wechat_app")
		if not app:
			app = frappe.db.get_single_value("Repair Settings", "default_wechat_app")
		if app:
			if not user_list.has_key(app):
				user_list[app] = []
			for d in frappe.db.get_values("Repair TeamUser", {"parent": st[0]}, "user"):
				user_list[app].append(d[0])
			"""
			frappe.sendmail(recipients=email_account.get_unreplied_notification_emails(),
				content=comm.content, subject=comm.subject, doctype= comm.reference_doctype,
				name=comm.reference_name)
			"""
	for app in user_list:
		#print("Send wechat notify : {0} to users {1} via app {2}".format(issue_doc.as_json(), user_list[app], app))
		from wechat.api import send_doc
		send_doc(app, 'Repair Issue', issue_doc.name, user_list[app])


@frappe.whitelist()
def list_issue_map():
	sites = list_sites(frappe.session.user)
	issues = frappe.get_all('Repair Issue', filters={"docstatus": ["in",[1, 2]], "site": ["in", sites]},
							fields=["name", "issue_name", "site", "priority", "total_cost", "status"])

	for issue in issues:
		issue.longitude = frappe.get_value('Repair Site', issue.site, "longitude") or '116.3252'
		issue.latitude = frappe.get_value('Repair Site', issue.site, "latitude") or '40.045103'
	return issues

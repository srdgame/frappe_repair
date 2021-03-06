# -*- coding: utf-8 -*-
# Copyright (c) 2017, Dirk Chang and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class TicketsRegion(Document):
	def validate(self):
		self.region_name_text = frappe.get_value("Region", self.region, "region_name")


def list_admin_regions(user, check_enable=True, region=None):
	from cloud.cloud.doctype.cloud_project.cloud_project import list_user_projects
	projects = list_user_projects(user, check_enable=check_enable)

	if len(projects) == 0:
		return []
	filters = {"project": ["in", projects]}
	if check_enable:
		filters["enabled"] = 1
	if region:
		filters["region"] = region
	return [d[0] for d in frappe.db.get_values("Tickets Region", filters=filters)]


def list_user_regions(user=None, type=None):
	from cloud.cloud.doctype.cloud_company_group.cloud_company_group import list_user_groups
	teams = list_user_groups(user)

	regions = []
	for team in teams:
		filters = {'team': team.name}
		if type:
			filters['type'] = type
		for d in frappe.db.get_values('Tickets RegionTeam', filters, "parent"):
			regions.append(frappe.get_value('Tickets Region', d[0], 'region'))

	return regions


def get_permission_query_conditions(user):
	if 'Tickets Manager' in frappe.get_roles(user):
		return ""

	from cloud.cloud.doctype.cloud_project.cloud_project import list_user_projects
	return """(`tabTickets Region`.project in ({projects}))""".format(
		projects='"' + '", "'.join(list_user_projects(user)) + '"')


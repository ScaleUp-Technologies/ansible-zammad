#!/usr/bin/python

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: zammad_create_ticket

short_description: Creates a zammad ticket via the API

version_added: "1.0.0"

description: This module creates a zammad ticket using the API with user credentials and ticket details passed as parameters.

options:
	title:
		description: The title of the ticket.
		required: true
		type: str
	group:
		description: The group handling the ticket.
		required: true
		type: str
	customer:
		description: The email address of the customer for the ticket.
		required: true
		type: str
	subject:
		description: The subject for the ticket's article.
		required: true
		type: str
	body:
		description: The body content for the ticket's article.
		required: true
		type: str
	internal:
		description: Whether the article is internal or not.
		required: false 
		type: bool
		default: False
'''

EXAMPLES = r'''
- name: Create a ticket
	scaleuptechnologies.utils.zammad_create_ticket:
		title: "Deleted the internet!"
		group: "Operations"
		customer: "example@domain.com"
		subject: "Internet outage"
		body: "The internet is not working."
		internal: false
'''

RETURN = r'''
ticket_id:
	description: The ID of the created support ticket.
	type: str
	returned: always
	sample: "12345"
status_code:
	description: The status code returned by the API.
	type: int
	returned: always
	sample: 200
'''

from ansible.module_utils.basic import AnsibleModule
import json
import requests

def create_ticket(fqdn, endpoint, apiUser, apiSecret, title, group, customer, subject, body, internal):
	headers = {
		"Content-type": "application/json"
	}
	data = {
		"title": title,
		"group": group,
		"customer": customer,
		"article": {
			"subject": subject,
			"body": body,
			"type": "note",
			"internal": str(internal).lower()
		}
	}

	try:
		response = requests.post(f"{fqdn}{endpoint}", data=json.dumps(data), headers=headers, auth=(apiUser, apiSecret))
		response.raise_for_status()
		return response.json(), response.status_code
	except requests.exceptions.RequestException as e:
		raise ValueError(f"API request failed: {e}")

#def update_ticket(fqdn, endpoint, apiUser, apiSecret, ticketID, title, group, state, priority, subject, body, internal):
#	headers = {
#		"Content-type": "application/json"
#	}
#	data = {
#		"title": title,
#		"group": group,
#		"state": state,
#		"priority": priority,
#		"article": {
#			"subject": subject,
#			"body": body,
#			"internal": str(internal).lower()
#		}
#	}
#
#	try:
#		response = requests.put(f"{fqdn}{endpoint}/{ticketID}", data=json.dumps(data), headers=headers, auth=(apiUser, apiSecret))
#		response.raise_for_status()
#		return response.json(), response.status_code
#	except requests.exceptions.RequestException as e:
#		raise ValueError(f"API request failed: {e}")
#
#def close_ticket(fqdn, endpoint, apiUser, apiSecret, ticketID, ticketState):
#	headers = {
#		"Content-type": "application/json"
#	}
#	data = {
#		"state": ticketState
#	}
#
#	try:
#		response = requests.put(f"{fqdn}{endpoint}/{ticketID}", data=json.dumps(data), headers=headers, auth=(apiUser, apiSecret))
#		response.raise_for_status()
#		return response.json(), response.status_code
#	except requests.exceptions.RequestException as e:
#		raise ValueError(f"API request failed: {e}")

def run_module():
	module_args = dict(
		#state=dict(type="str", required=False),
		#ticketState=dict(type="str", required=False),
		#ticketID=dict(type="str", required=False),
		apiUser=dict(type="str", required=True),
		apiSecret=dict(type="str", required=True),
		fqdn=dict(type="str", required=True),
		endpoint=dict(type="str", required=True),
		title=dict(type="str", required=True),
		group=dict(type="str", required=True),
		customer=dict(type="str", required=True),
		subject=dict(type="str", required=True),
		body=dict(type="str", required=True),
		internal=dict(type="bool", required=False, default=False)
	)

	result = dict(
		changed=False,
		ticket_id="",
		status_code=0,
		message=""
	)

	module = AnsibleModule(
		argument_spec=module_args,
		supports_check_mode=True
	)

	if module.check_mode:
		module.exit_json(**result)

	try:
		ticket_data, status_code = create_ticket(
			module.params["fqdn"],
			module.params["endpoint"],
			module.params["apiUser"],
			module.params["apiSecret"],
			module.params["title"],
			module.params["group"],
			module.params["customer"],
			module.params["subject"],
			module.params["body"],
			module.params["internal"]
		)
		result["changed"] = True
		result["ticket_id"] = ticket_data.get("id", "N/A")
		result["status_code"] = status_code
		result["message"] = "Ticket created successfully."
		module.exit_json(**result)
	except ValueError as e:
		module.fail_json(msg=str(e), **result)

def main():
	run_module()

if __name__ == "__main__":
	main()

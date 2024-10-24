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

def make_request(method, fqdn, endpoint, api_user, api_secret, data, ticket_id = ""):
    headers = {"Content-type": "application/json"}
    url = f"{fqdn}{endpoint}" + (f"/{ticket_id}")
    try:
        response = requests.request(method, url, data=json.dumps(data), headers=headers, auth=(api_user, api_secret))
        response.raise_for_status()
        return response.json(), response.status_code
    except requests.exceptions.RequestException as e:
        raise ValueError(f"API request failed: {e}")

def create_ticket(fqdn, endpoint, api_user, api_secret, customer, title, group, subject, body, internal, ticket_state, priority):
	data = {
		"title": title,
		"group": group,
		"state": ticket_state,
		"customer": customer,
		"priority": priority,
		"article": {
			"subject": subject,
			"body": body,
			"type": "note",
			"internal": str(internal).lower()
		}
	}
	return make_request("POST", fqdn, endpoint, api_user, api_secret, data)

def update_ticket(fqdn, endpoint, api_user, api_secret, ticket_id, customer, title, group, subject, body, internal, ticket_state, priority):
	data = {
		"title": title,
		"group": group,
		"state": ticket_state,
		"priority": priority,
		"article": {
			"subject": subject,
			"body": body,
			"internal": str(internal).lower()
		}
	}
	return make_request("PUT", fqdn, endpoint, api_user, api_secret, data, ticket_id)

def close_ticket(fqdn, endpoint, api_user, api_secret, ticket_id):
	data = {"state": "closed"}
	return make_request("PUT", fqdn, endpoint, api_user, api_secret, data, ticket_id)

def validate_params(module, required_params):
	if not all(module.params[param] for param in required_params):
		module.fail_json(msg = "Missing required paramters: " + ", ".join(required_params))

def run_module():
	module_args = dict(
		state=dict(type="str", required=True, choices=("present", "absent")),
		fqdn=dict(type="str", required=True),
		endpoint=dict(type="str", required=True),
		api_user=dict(type="str", required=True),
		api_secret=dict(type="str", required=True),
		ticket_id=dict(type="str", required=False),
		customer=dict(type="str", required=False),
		title=dict(type="str", required=False),
		group=dict(type="str", required=False),
		subject=dict(type="str", required=False),
		body=dict(type="str", required=False,),
		internal=dict(type="bool", required=False, default="false"),
		ticket_state=dict(type="str", required=False),
		priority=dict(type="str", required=False)
	)

	result = dict(changed = False, ticket_id = "", status_code = 0, message = "")
	module = AnsibleModule(argument_spec = module_args, supports_check_mode = True)

	if module.check_mode:
		module.exit_json(**result)

	try:
		state = module.params["state"]
		if state == "present" and module.params["ticket_id"]:
			validate_params(
				module,
				[
					"ticket_id",
					"customer",
					"title",
					"group",
					"subject",
					"body",
					"ticket_state",
					"priority"
				]
			)
			ticket_data, status_code = update_ticket(
				module.params["fqdn"],
				module.params["endpoint"],
				module.params["api_user"],
				module.params["api_secret"],
				module.params["ticket_id"],
				module.params["customer"],
				module.params["title"],
				module.params["group"],
				module.params["subject"],
				module.params["body"],
				module.params["internal"],
				module.params["ticket_state"],
				module.params["priority"]
			)
			result.update({
				"changed": True,
				"ticket_id": module.params["ticket_id"],
				"status_code": status_code,
				"message": "Ticket updated successfully."
			})

		elif state == "present":
			validate_params(
				module,
				[
					"customer",
					"title",
					"group",
					"subject",
					"body",
					"ticket_state",
					"priority"
				]
			)
			ticket_data, status_code = create_ticket(
				module.params["fqdn"],
				module.params["endpoint"],
				module.params["api_user"],
				module.params["api_secret"],
				module.params["customer"],
				module.params["title"],
				module.params["group"],
				module.params["subject"],
				module.params["body"],
				module.params["internal"],
				module.params["ticket_state"],
				module.params["priority"]
			)
			result.update({
				"changed": True,
				"ticket_id": ticket_data.get("id", "N/A"),
				"status_code": status_code,
				"message": "Ticket created successfully."
			})

		elif state == "absent":
			validate_params(module, ["ticket_id"])
			ticket_data, status_code = close_ticket(
				module.params["fqdn"],
				module.params["endpoint"],
				module.params["api_user"],
				module.params["api_secret"],
				module.params["ticket_id"]
			)
			result.update({
				"changed": True,
				"ticket_id": module.params["ticket_id"],
				"status_code": status_code,
				"message": "Ticket closed successfully."
			})

		module.exit_json(**result)

	except ValueError as e:
		module.fail_json(msg=str(e), **result)

def main():
	run_module()

if __name__ == "__main__":
	main()

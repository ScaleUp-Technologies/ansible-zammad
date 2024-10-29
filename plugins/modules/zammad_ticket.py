#!/usr/bin/python

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
author:
- Melvin Ziemann (@cloucs), ScaleUp Technologies GmbH & Co. KG

module: zammad_ticket

short_description: Create, update, close a Zammad ticket via the API

version_added: "1.0.0"

description: |
  This module creates, updates, or closes a Zammad ticket using the API.
  User credentials and ticket details are passed as parameters. This module can handle
  ticket creation and updates based on the specified state. It also allows for the
  closure of existing tickets.

options:
  zammad_url:
    description: The fully qualified domain name of the Zammad instance.
    required: true
    type: str
  api_user:
    description: The username for authenticating with the Zammad API.
    required: true
    type: str
  api_secret:
    description: The password or API key for authenticating with the Zammad API.
    required: true
    type: str
  state:
    description: The desired state of the ticket. Use 'present' to create or update a ticket, and 'absent' to close a ticket.
    required: true
    type: str
    choices: ["present", "absent"]
  ticket_id:
    description: The unique identifier of the ticket to update or close. Required if state is 'absent' or when updating a ticket.
    required: false
    type: int
  customer:
    description: The email address of the customer for the ticket.
    required: true
    type: str
  title:
    description: The title of the ticket.
    required: true
    type: str
  group:
    description: The group handling the ticket.
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
    description: Indicates whether the article is internal. Defaults to false.
    required: false
    type: bool
    default: false
  ticket_state:
    description: The state of the ticket (e.g., open, pending, etc.).
    required: true
    type: str
  priority:
    description: The priority of the ticket (e.g., low, normal, high).
    required: true
	type: str

examples:
  - name: Create a new ticket
    zammad_ticket:
	  zammad_url: "https://zammad.example.com"
      api_user: "api_user"
      api_secret: "api_secret"
      state: "present"
      title: "Internet Outage"
      group: "Support"
      customer: "customer@example.com"
      subject: "Internet is down"
      body: "The internet is not working since this morning."
      internal: false
      ticket_state: "open"
      priority: "high"

  - name: Update an existing ticket
    zammad_ticket:
	  zammad_url: "https://zammad.example.com"
      api_user: "api_user"
      api_secret: "api_secret"
      state: "present"
      ticket_id: "12345"
      title: "Internet Outage - Follow Up"
      group: "Support"
      customer: "customer@example.com"
      subject: "Update on internet issue"
      body: "The internet issue is being worked on."
      internal: true
      ticket_state: "pending"
      priority: "normal"

  - name: Close a ticket
    zammad_ticket:
      zammad_url: "https://zammad.example.com"
      api_user: "api_user"
      api_secret: "api_secret"
      state: "absent"
      ticket_id: "12345"

return:
  ticket_id:
    description: The ID of the created or updated support ticket.
    type: str
    returned: always
    sample: "12345"
  status_code:
    description: The status code returned by the Zammad API.
    type: int
    returned: always
    sample: 200
  message:
    description: A message indicating the result of the operation (success or failure).
    type: str
    returned: always
    sample: "Ticket created successfully."
'''

from ansible.module_utils.basic import AnsibleModule
import json
import requests

def make_request(method, zammad_url, api_user, api_secret, data, ticket_id = None, endpoint = None):
    headers = {"Content-type": "application/json"}
    url = f"{zammad_url}/api/v1/tickets/{ticket_id}" if ticket_id else f"{zammad_url}/api/v1/{endpoint or 'tickets/'}"
    try:
        response = requests.request(method, url, data=json.dumps(data), headers=headers, auth=(api_user, api_secret))
        response.raise_for_status()
        return response.json(), response.status_code
    except requests.exceptions.RequestException as e:
        raise ValueError(f"API request failed: {e}")

def create_ticket(zammad_url, api_user, api_secret, customer, title, group, subject, body, internal, ticket_state, priority):
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
	return make_request("POST", zammad_url, api_user, api_secret, data)

def update_ticket(zammad_url, api_user, api_secret, ticket_id, customer, title, group, subject, body, internal, ticket_state, priority):
	article = {}

	if body: 
		article = {
			"subject": subject,
			"body": body,
			"internal": str(internal).lower()
		}

	data = {
		"article": article,
		**{key: value for key, value in {
			"title": title,
			"group": group,
			"ticket_state": ticket_state,
			"priority": priority
		}.items() if value is not None}
	}
	return make_request("PUT", zammad_url, api_user, api_secret, data, ticket_id)

def close_ticket(zammad_url, api_user, api_secret, ticket_id):
	data = {"state": "closed"}
	return make_request("PUT", zammad_url, api_user, api_secret, data, ticket_id)

def get_ticket(zammad_url, api_user, api_secret, ticket_id):
	return make_request("GET", zammad_url, api_user, api_secret, {}, ticket_id)

def get_customers(zammad_url, api_user, api_secret):
	return make_request("GET", zammad_url, api_user, api_secret, {}, endpoint = "users")

def get_customer_name(ticket_data, customers):
	customer_id = ticket_data.get("customer_id")
	for customer in customers:
		if customer["id"] == customer_id:
			return customer["firstname"] + " " + customer["lastname"]

def get_groups(zammad_url, api_user, api_secret):
	return make_request("GET", zammad_url, api_user, api_secret, {}, endpoint = "groups")

def get_group_name(ticket_data, groups):
	group_id = ticket_data.get("group_id")
	for group in groups:
		if group["id"] == group_id:
			return group["name"]

def get_ticket_states(zammad_url, api_user, api_secret):
	return make_request("GET", zammad_url, api_user, api_secret, {}, endpoint = "ticket_states")

def	get_ticket_state_name(ticket_data, ticket_states):
	ticket_state_id = ticket_data.get("state_id")
	for ticket_state in ticket_states:
		if ticket_state["id"] == ticket_state_id:
			return ticket_state["name"]

def get_priorities(zammad_url, api_user, api_secret):
	return make_request("GET", zammad_url, api_user, api_secret, {}, endpoint = "ticket_priorities")

def get_priority_name(ticket_data, priorities):
	priority_id = ticket_data.get("priority_id")
	for priority in priorities:
		if priority["id"] == priority_id:
			return priority["name"]

def get_ticket_articles(zammad_url, api_user, api_secret, ticket_id):
	return make_request("GET", zammad_url, api_user, api_secret, {}, endpoint = f"ticket_articles/by_ticket/{ticket_id}")

def get_last_article_data(ticket_articles, article_object):
	return ticket_articles[-1][f"{article_object}"]

def validate_params(module, required_params):
	if not all(module.params[param] for param in required_params):
		module.fail_json(msg = "Missing required paramters: " + ", ".join(required_params))

def has_changes(current_ticket_data, ticket_data):
	for key, value in ticket_data.items():
		if value is not None:
			if current_ticket_data.get(key) != value:
				return True
	return False

def run_module():
	module_args = dict(
		state=dict(type="str", required=True, choices=("present", "absent")),
		zammad_url=dict(type="str", required=True),
		api_user=dict(type="str", required=True),
		api_secret=dict(type="str", required=True),
		ticket_id=dict(type="int", required=False),
		customer=dict(type="str", required=False, default = None),
		title=dict(type="str", required=False, default = None),
		group=dict(type="str", required=False, default = None),
		subject=dict(type="str", required=False, default = None),
		body=dict(type="str", required=False, default = None),
		internal=dict(type="bool", required=False, default = "false"),
		ticket_state=dict(type="str", required=False, default = None),
		priority=dict(type="str", required=False, default = None)
	)

	result = dict(changed = False, ticket_id = None, status_code = 0, message = "")
	module = AnsibleModule(argument_spec = module_args, supports_check_mode = True)

	if module.check_mode:
		module.exit_json(**result)

	try:
		customers, status_code = get_customers(
			module.params["zammad_url"],
			module.params["api_user"],
			module.params["api_secret"]
		)

		groups, status_code = get_groups(
			module.params["zammad_url"],
			module.params["api_user"],
			module.params["api_secret"]
		)

		ticket_states, status_code = get_ticket_states(
			module.params["zammad_url"],
			module.params["api_user"],
			module.params["api_secret"]
		)

		priorities, status_code = get_priorities(
			module.params["zammad_url"],
			module.params["api_user"],
			module.params["api_secret"]
		)

		state = module.params["state"]
		if state == "present" and module.params["ticket_id"]:
			validate_params(module, ["ticket_id"])

			ticket_data, status_code = get_ticket(
				module.params["zammad_url"],
				module.params["api_user"],
				module.params["api_secret"],
				module.params["ticket_id"]
			)

			ticket_articles, status_code = get_ticket_articles(
				module.params["zammad_url"],
				module.params["api_user"],
				module.params["api_secret"],
				module.params["ticket_id"]
			)

			current_ticket_data = {
				"customer": get_customer_name(ticket_data, customers),
				"title": ticket_data["title"],
				"group": get_group_name(ticket_data, groups),
				"subject": get_last_article_data(ticket_articles, "subject"),
				"body": get_last_article_data(ticket_articles, "body"),
				"internal": str(get_last_article_data(ticket_articles, "internal")).lower(),
				"ticket_state": get_ticket_state_name(ticket_data, ticket_states),
				"priority": get_priority_name(ticket_data, priorities)
			}

			ticket_data = {
				"customer": module.params["customer"],
				"title": module.params["title"],
				"group": module.params["group"],
				"subject": module.params["subject"],
				"body": module.params["body"],
				"internal": str(module.params["internal"]).lower(),
				"ticket_state": module.params["ticket_state"],
				"priority": module.params["priority"]
			}

			if has_changes(current_ticket_data, ticket_data):
				ticket_data, status_code = update_ticket(
					module.params["zammad_url"],
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
			else:
				result.update({
					"changed": False,
					"ticket_id": module.params["ticket_id"],
					"message": "No changes required."
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
				module.params["zammad_url"],
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
			ticket_data, status_code = get_ticket(
				module.params["zammad_url"],
				module.params["api_user"],
				module.params["api_secret"],
				module.params["ticket_id"]
			)

			current_ticket_data = {
				"ticket_state": get_ticket_state_name(ticket_data, ticket_states),
			}

			ticket_data = {
				"ticket_state": module.params["ticket_state"],
			}

			if has_changes(current_ticket_data, ticket_data):
				validate_params(module, ["ticket_id"])
				ticket_data, status_code = close_ticket(
					module.params["zammad_url"],
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
			else:
				result.update({
					"changed": False,
					"ticket_id": module.params["ticket_id"],
					"message": "Ticket is already closed."
				})

		module.exit_json(**result)

	except ValueError as e:
		module.fail_json(msg=str(e), **result)

def main():
	run_module()

if __name__ == "__main__":
	main()

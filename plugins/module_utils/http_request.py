#!/usr/bin/python

# Copyright: (c) 2024, Melvin Ziemann <ziemann.melvin@gmail.com>
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
from ansible.module_utils.urls import fetch_url
import json
import base64


__metaclass__ = type


def make_request(module, method, zammad_url, api_user, api_secret, data, ticket_id=None, endpoint=None):
    headers = {"Content-type": "application/json"}
    auth = f"{api_user}:{api_secret}"
    encoded_auth = base64.b64encode(auth.encode("utf-8")).decode("utf-8")
    headers["Authorization"] = f"Basic {encoded_auth}"
    url = f"{zammad_url}/api/v1/tickets/{ticket_id}" if ticket_id else f"{zammad_url}/api/v1/{endpoint or 'tickets/'}"
    data_json = json.dumps(data) if data else None
    response, info = fetch_url(
        module,
        url,
        method=method,
        data=data_json,
        headers=headers
    )
    if info["status"] >= 400:
        module.fail_json(msg=f"API request failed: {info['msg']}", status_code=info["status"])
    try:
        result = json.load(response)
    except json.JSONDecodeError:
        module.fail_json(msg="Failed to parse JSON response")
    return result, info["status"]

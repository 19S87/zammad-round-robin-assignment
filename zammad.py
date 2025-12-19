import os
import requests

ZAMMAD_URL = os.getenv("ZAMMAD_URL")
ZAMMAD_TOKEN = os.getenv("ZAMMAD_API_TOKEN")

HEADERS = {
    "Authorization": f"Token token={ZAMMAD_TOKEN}",
    "Content-Type": "application/json",
}


def get_group_agents(group_id: int):
    """
    Return ONLY assignable agents for a group.
    Matches Zammad UI assignment behavior.
    """

    # 1️⃣ Fetch group with members
    group_resp = requests.get(
        f"{ZAMMAD_URL}/api/v1/groups/{group_id}",
        headers=HEADERS,
        timeout=10,
    )
    group_resp.raise_for_status()
    group = group_resp.json()

    user_ids = set(group.get("user_ids", []))
    if not user_ids:
        return []

    # 2️⃣ Fetch ONLY agents
    users_resp = requests.get(
        f"{ZAMMAD_URL}/api/v1/users",
        headers=HEADERS,
        params={"role_ids": "agent", "active": True},
        timeout=10,
    )
    users_resp.raise_for_status()

    users = users_resp.json()

    assignable_agents = [
        u for u in users
        if u["id"] in user_ids
    ]

    return assignable_agents


def assign_ticket(ticket_id: int, owner_id: int):
    """
    Explicit owner assignment.
    """
    resp = requests.put(
        f"{ZAMMAD_URL}/api/v1/tickets/{ticket_id}",
        headers=HEADERS,
        json={"owner_id": owner_id},
        timeout=10,
    )
    resp.raise_for_status()


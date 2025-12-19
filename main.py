from fastapi import FastAPI, Request, HTTPException
import hmac
import hashlib
import os
import time
import requests

from zammad import get_group_agents, assign_ticket
from db import init_db, get_last_user, set_last_user

app = FastAPI()
init_db()

MAX_RETRIES = 5
RETRY_DELAY = 2  # seconds

ZAMMAD_URL = os.getenv("ZAMMAD_URL")
ZAMMAD_TOKEN = os.getenv("ZAMMAD_API_TOKEN")

HEADERS = {
    "Authorization": f"Token token={ZAMMAD_TOKEN}",
    "Content-Type": "application/json",
}


async def verify_hmac(request: Request) -> bool:
    """
    Verify SHA1 HMAC signature from Zammad trigger.
    Header format: X-Hub-Signature: sha1=<hex>
    """
    signature_header = request.headers.get("X-Hub-Signature")
    if not signature_header:
        return False

    if signature_header.startswith("sha1="):
        signature_header = signature_header[5:]

    body = await request.body()

    secret = os.getenv("HMAC_SECRET")
    if not secret:
        raise HTTPException(
            status_code=500,
            detail="Server misconfiguration: HMAC_SECRET not set"
        )

    computed = hmac.new(secret.encode(), body, hashlib.sha1).hexdigest()
    return hmac.compare_digest(computed, signature_header)


@app.post("/assignment")
async def assign(request: Request):
    # 1️⃣ Verify webhook signature
    if not await verify_hmac(request):
        raise HTTPException(status_code=401, detail="Invalid signature")

    # 2️⃣ Parse payload
    try:
        data = await request.json()
        ticket_id = data.get("ticket_id")
        group_id = data.get("group_id")
        if not ticket_id or not group_id:
            raise ValueError
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Invalid JSON body. Required: ticket_id, group_id"
        )

    # 3️⃣ Fetch active agents in the group
    agents = get_group_agents(group_id)
    if not agents:
        raise HTTPException(
            status_code=400,
            detail="No active agents found for group"
        )

    # 4️⃣ Stable ordering for round-robin
    agents = sorted(agents, key=lambda a: a["id"])
    agent_ids = [a["id"] for a in agents]

    # 5️⃣ Determine next agent based on last assignment
    last_user = get_last_user(group_id)
    if last_user in agent_ids:
        next_index = (agent_ids.index(last_user) + 1) % len(agent_ids)
    else:
        next_index = 0
    next_agent_id = agent_ids[next_index]

    # 6️⃣ Attempt assignment with verification
    assigned = False
    attempt_agents = agent_ids.copy()  # preserve valid agent IDs
    for attempt in range(len(attempt_agents)):
        current_agent_id = attempt_agents[(next_index + attempt) % len(attempt_agents)]
        for retry in range(1, MAX_RETRIES + 1):
            try:
                assign_ticket(ticket_id, current_agent_id)

                # Verify ticket ownership
                resp = requests.get(f"{ZAMMAD_URL}/api/v1/tickets/{ticket_id}",
                                    headers=HEADERS, timeout=5)
                ticket = resp.json()
                if ticket.get("owner_id") == current_agent_id:
                    assigned = True
                    set_last_user(group_id, current_agent_id)
                    next_agent_id = current_agent_id
                    break
                else:
                    continue
            except Exception as e:
                if retry < MAX_RETRIES:
                    time.sleep(RETRY_DELAY)
                else:
                    continue
        if assigned:
            break

    # 7️⃣ Fallback to first agent if all else fails
    if not assigned and agent_ids:
        fallback_agent_id = agent_ids[0]
        try:
            assign_ticket(ticket_id, fallback_agent_id)
            set_last_user(group_id, fallback_agent_id)
            assigned = True
            next_agent_id = fallback_agent_id
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Ticket could not be assigned even to first agent: {e}"
            )

    if not assigned:
        raise HTTPException(
            status_code=500,
            detail="Ticket assignment failed for all agents"
        )

    # 8️⃣ Success response
    assigned_agent = next(a for a in agents if a["id"] == next_agent_id)
    assigned_name = (
        f"{assigned_agent.get('firstname', '')} {assigned_agent.get('lastname', '')}".strip()
        or assigned_agent.get("login")
    )

    return {
        "ticket_id": ticket_id,
        "group_id": group_id,
        "owner_id": next_agent_id,
        "assigned_to": assigned_name
    }


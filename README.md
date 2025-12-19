
## Zammad Round-Robin Auto Assignment

# Overview
Zammad does not provide true round-robin ticket assignment out of the box for groups.
This project implements a stateless, webhook-driven round-robin assignment service that:
Assigns tickets evenly across eligible group agents
Persists state in Redis
Respects Zammad permission and ownership rules
Works with nested groups
Is container-ready and production safe
This solution integrates cleanly using Zammad Triggers + Webhooks and does not modify Zammad core code.

# Features
    •  True round-robin per group
    •  Skips inactive / non-assignable users
    •  Redis-backed cursor (crash-safe)
    •  HMAC webhook verification
    •  Docker-first deployment
    •  Works with Zammad Community & Enterprise

# Prerequisites
    1. Zammad (Docker-based setup recommended)
    2. Redis (already included with Zammad)
    3. Docker & Docker Compose
    4. Zammad Admin or Agent API Token

## Setup & Installation

# 1. Upload the Code
Clone or upload this repository into your Zammad deployment directory:
git clone https://github.com/19S87/zammad-round-robin-assignment.git

# 2. Configure Environment Variables
Edit your .env file and add the following:

ZAMMAD_URL=               # https://your-zammad-domain
ZAMMAD_API_TOKEN=         # Zammad Admin or Agent API token
REDIS_HOST=zammad-redis   # Redis container name
REDIS_PORT=6379           # Redis port
HMAC_SECRET=              # Shared secret for webhook validation

Notes
    • API token must belong to a user with ticket.owner update permission
    • HMAC_SECRET must match the value configured in Zammad Webhook

# 3. Add Assignment Service to Docker Compose
Edit your scenarios/add-assignment.yml (or equivalent):

---
Service: 
  assignment:
    build:
      context: ./assignment
      dockerfile: Dockerfile
    container_name: zammad-rr-assignment
    env_file:
      - .env
    ports:
      - "8001:8001"
    depends_on:
      - zammad-redis
    volumes:
      - ./assignment/data:/data

# 4. Start the Service
docker compose -f docker-compose.yml -f scenarios/add-assignment.yml up -d

# 5. Create Webhook

Navigate to:

Admin → Settings → Webhooks

Create a new webhook:

Field	        Value
Name	        Round Robin Assignment
Endpoint	    https://<your-domain>/assignment
Method	        POST
Secret	        HMAC_SECRET
CUSTOM PAYLOAD  Yes

PAYLOAD:         
{
  "ticket_id": "#{ticket.id}",
  "group_id": "#{ticket.group_id}"
}

# 6. Create Trigger

Navigate to:
Admin → Manage → Triggers

Example trigger:

CONDITIONS
State is:   new
Action:     Ticket created
Owner is:   not set
Group is:   <target group>

EXECUTE
Webhook → Round Robin Assignment

## This project:

- Does not override Zammad core behavior
- Aligns with Zammad permission model
- Is safe for upgrades
- Encourages modular extensibility
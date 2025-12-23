# Zammad Round-Robin Auto Assignment

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)

A stateless, webhook-driven round-robin assignment service for Zammad that assigns tickets evenly across eligible group agents using Redis for cursor persistence. Designed to integrate with Zammad Triggers + Webhooks without modifying Zammad core.

Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
  - [Clone](#clone)
  - [Configure environment variables](#configure-environment-variables)
  - [Add to Docker Compose](#add-to-docker-compose)
  - [Start the service](#start-the-service)
- [Zammad Integration](#zammad-integration)
  - [Create Webhook](#create-webhook)
  - [Create Trigger](#create-trigger)
- [Behavior & Security](#behavior--security)
- [Data & Persistence](#data--persistence)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

Zammad does not provide true round-robin ticket assignment for groups by default. This project implements a lightweight service that:

- Assigns tickets evenly across eligible agents in a group (round-robin)
- Persists a cursor per group in Redis for crash-safe operation
- Respects Zammad permissions and ownership rules
- Works with nested groups
- Is container-first and production-ready

This service integrates with Zammad using a webhook (no core changes required).

## Features

- True per-group round-robin
- Skips inactive or non-assignable users
- Redis-backed cursor for durability
- HMAC webhook verification for authenticity
- Simple Docker deployment
- Supports Zammad Community & Enterprise

## Prerequisites

- Zammad (Docker-based setup recommended)
- Redis (Zammad usually provides one)
- Docker & Docker Compose
- Zammad Admin or Agent API token (must have permission to update ticket.owner)

## Quick Start

### Clone

Clone the repository into your Zammad deployment directory (or wherever you manage additional services):

```bash
git clone https://github.com/19S87/zammad-round-robin-assignment.git
cd zammad-round-robin-assignment/assignment
```

### Configure environment variables

Create or edit a `.env` file and set the following variables:

```
ZAMMAD_URL=https://your-zammad-domain
ZAMMAD_API_TOKEN=your_api_token_here
REDIS_HOST=zammad-redis
REDIS_PORT=6379
HMAC_SECRET=your_hmac_secret_here
```

Notes:
- The API token must belong to a user with permission to update ticket owners.
- `HMAC_SECRET` must match the secret configured in the Zammad webhook.

### Add to Docker Compose

Add the service to your Docker Compose override (example `scenarios/add-assignment.yml`):

```yaml
version: '3.8'
services:
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
```

### Start the service

```bash
docker compose -f docker-compose.yml -f scenarios/add-assignment.yml up -d
```

## Zammad Integration

### Create Webhook

In the Zammad Admin UI, navigate to:

Admin → Settings → Webhooks

Create a new webhook with these example values:

- Name: Round Robin Assignment
- Endpoint: https://(your-domain)/assignment
- Method: POST
- Secret: (set to your HMAC_SECRET)
- CUSTOM PAYLOAD: Yes

Payload example:

```json
{
  "ticket_id": "#{ticket.id}",
  "group_id": "#{ticket.group_id}"
}
```

The service verifies the HMAC signature of incoming requests using the configured `HMAC_SECRET`.

### Create Trigger

In Zammad, create a Trigger to call the webhook when a ticket should be auto-assigned. Example trigger:

Conditions
- State is: new
- Owner is: not set
- <Group is: <target group>>

Execute
- Webhook → Round Robin Assignment

This will call the assignment service which will pick the next eligible agent and update the ticket owner via the Zammad API.

## Behavior & Security

- The service skips users who are inactive or who cannot be assigned tickets.
- It uses an API token to perform owner updates; ensure the token user has the appropriate permissions.
- Webhook requests are validated using HMAC to prevent unauthorized calls.
- All state (the round-robin cursors) are stored in Redis so the service is stateless and horizontally scalable.

## Data & Persistence

Persistent data is minimal: a Redis-backed cursor per group stored under the service Redis namespace. The local `./assignment/data` volume is used only for local state/diagnostics if configured.

## Troubleshooting

- 401 from Zammad API: verify `ZAMMAD_API_TOKEN` and the token user's permissions.
- HMAC validation failures: ensure the webhook secret in Zammad matches `HMAC_SECRET`.
- No eligible agents found: check group membership and user active/assignable status.
- Redis errors: ensure `REDIS_HOST`/`REDIS_PORT` are reachable from the assignment container.

Logs: check container logs for details:

```bash
docker logs -f zammad-rr-assignment
```

## Contributing

Contributions, issues, and feature requests are welcome. Please open an issue or submit a pull request.

## License

This project is licensed under the GNU Affero General Public License v3.0 (AGPL-3.0). See the `LICENSE` file for details or https://www.gnu.org/licenses/agpl-3.0 for the full text.


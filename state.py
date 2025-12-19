import os
import redis

r = redis.Redis(
    host=os.getenv("REDIS_HOST"),
    port=int(os.getenv("REDIS_PORT")),
    decode_responses=True
)

def get_last_agent(group_id):
    return r.get(f"rr:last:{group_id}")

def set_last_agent(group_id, agent_id):
    r.set(f"rr:last:{group_id}", agent_id)



from state import get_last_agent, set_last_agent

def pick_agent(group_id, agents):
    agents = sorted(agents, key=lambda x: x["id"])
    last_id = get_last_agent(group_id)

    # Find next agent
    if last_id:
        for agent in agents:
            if agent["id"] > int(last_id):
                set_last_agent(group_id, agent["id"])
                return agent

    # Wrap around
    chosen = agents[0]
    set_last_agent(group_id, chosen["id"])
    return chosen


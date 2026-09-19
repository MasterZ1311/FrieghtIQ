import urllib.request
import json
import time

req_data = {
    "message": "Analyze 75,000 MT coal from Newcastle to Paradip within 30 days and tell me the chartering situation.",
    "origin_port_id": "PORT-AU-NEW",
    "destination_port_id": "PORT-IN-PAR",
    "cargo_type": "Coal",
    "quantity_mt": 75000.0,
    "stream": True
}

req = urllib.request.Request(
    "http://127.0.0.1:8000/api/v1/copilot/chat",
    data=json.dumps(req_data).encode("utf-8"),
    headers={"Content-Type": "application/json"}
)

print("Connecting to SSE stream...")
event_count = 0
with urllib.request.urlopen(req, timeout=60) as resp:
    for line in resp:
        line_str = line.decode("utf-8").strip()
        if line_str.startswith("data:"):
            data_json = line_str[5:].strip()
            event = json.loads(data_json)
            event_count += 1
            evt_type = event.get("type")
            if evt_type == "init":
                print(f"[{event_count}] Init: {event.get('label')} (Session: {event.get('session_id')})")
            elif evt_type == "planning":
                print(f"[{event_count}] Planning: {event.get('label')}")
            elif evt_type == "plan_ready":
                print(f"[{event_count}] Plan Ready: {len(event.get('steps', []))} tools planned")
            elif evt_type == "tool_start":
                print(f"[{event_count}] -> Starting tool [{event.get('step_index')}/{event.get('total_steps')}]: {event.get('tool')}")
            elif evt_type == "tool_complete":
                print(f"[{event_count}] <- Completed tool: {event.get('tool')} ({event.get('status')}) in {event.get('time_ms')} ms [Data: {event.get('data_status')}]")
            elif evt_type == "validating":
                print(f"[{event_count}] Validating: {event.get('label')}")
            elif evt_type == "synthesis":
                print(f"[{event_count}] Synthesis: {event.get('label')}")
            elif "message" in event:
                msg = event.get("message", {})
                sr = msg.get("structured_response", {})
                print(f"[{event_count}] FINAL ASSESSMENT RECEIVED: {sr.get('summary')[:80]}...")
            else:
                print(f"[{event_count}] Event: {evt_type or list(event.keys())}")

print(f"\nTotal SSE events received: {event_count}")

import urllib.request
import json

req_data = {
    "message": "Analyze 75,000 MT coal from Newcastle to Paradip within 30 days and tell me the chartering situation.",
    "origin_port_id": "PORT-AU-NEW",
    "destination_port_id": "PORT-IN-PAR",
    "cargo_type": "Coal",
    "quantity_mt": 75000.0,
    "stream": False
}

req = urllib.request.Request(
    "http://127.0.0.1:8000/api/v1/copilot/chat",
    data=json.dumps(req_data).encode("utf-8"),
    headers={"Content-Type": "application/json"}
)

with urllib.request.urlopen(req, timeout=40) as resp:
    res = json.loads(resp.read().decode("utf-8"))
    sr = res.get("structured_response", {})
    print("=== STRUCTURED COPILOT ASSESSMENT ===\n")
    print("SUMMARY:\n", sr.get("summary"))
    print("\nFINDINGS:")
    for f in sr.get("findings", []):
        print(" -", f)
    print("\nDECISION CONTEXT:")
    print(json.dumps(sr.get("decision_context", {}), indent=2))
    print("\nECONOMICS:")
    print(json.dumps(sr.get("economics", {}), indent=2))
    print("\nASSUMPTIONS:")
    for a in sr.get("assumptions", []):
        print(" -", a)
    print("\nUNCERTAINTIES:")
    for u in sr.get("uncertainties", []):
        print(" -", u)
    print("\nEVIDENCE:")
    for e in sr.get("evidence", []):
        print(" -", e)
    print("\nDATA QUALITY SCORECARD:")
    print(json.dumps(sr.get("data_quality", {}), indent=2))
    print("\nRECOMMENDED ACTIONS / DEEP LINKS:")
    for a in sr.get("actions", []):
        print(f" - {a.get('label')}: {a.get('action_url')} ({a.get('description')})")

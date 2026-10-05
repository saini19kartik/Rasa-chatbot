import requests
import json
import uuid

RASA_URL = "http://localhost:5005/webhooks/rest/webhook"

def send_msg(user_id, text):
    payload = {"sender": user_id, "message": text}
    r = requests.post(RASA_URL, json=payload)
    if r.status_code == 200:
        return r.json()
    return []

print("=== HANDOVER WITH FILLED SLOTS TEST ===")
sid = f"test_user_slots_{uuid.uuid4().hex[:6]}"
send_msg(sid, "I want to plan a trip")
send_msg(sid, "London")
send_msg(sid, "Paris")
send_msg(sid, "10 October to 15 October")
send_msg(sid, "800 euros")
send_msg(sid, "high")
send_msg(sid, "rail")
resp = send_msg(sid, "I want to speak to a human")
for msg in resp:
    print("Bot reply:", msg.get("text"))

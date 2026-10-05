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

print("=== TEST 2: AMADEUS / ACCOMMODATION TEST ===")
sid2 = f"test_user_amadeus_{uuid.uuid4().hex[:6]}"
resp2 = send_msg(sid2, "recommend an eco friendly hotel")
print(f"User: recommend an eco friendly hotel")
for msg in resp2:
    print("Bot:", msg.get("text"))

print("\n=== TEST 3: TRANSPORT RECOMMENDATION TEST ===")
sid3 = f"test_user_transport_{uuid.uuid4().hex[:6]}"
resp3 = send_msg(sid3, "recommend sustainable transport")
print(f"User: recommend sustainable transport")
for msg in resp3:
    print("Bot:", msg.get("text"))

print("\n=== TEST 4: ACTIVITY RECOMMENDATION TEST (Paris) ===")
sid4 = f"test_user_activity_{uuid.uuid4().hex[:6]}"
resp4 = send_msg(sid4, "recommend sustainable activities")
print(f"User: recommend sustainable activities")
for msg in resp4:
    print("Bot:", msg.get("text"))

print("\n=== TEST 5: HUMAN HANDOVER TEST ===")
sid5 = f"test_user_handover_{uuid.uuid4().hex[:6]}"
send_msg(sid5, "London")
send_msg(sid5, "Paris")
send_msg(sid5, "10 October to 15 October")
send_msg(sid5, "800 euros")
send_msg(sid5, "high")
send_msg(sid5, "rail")
resp5 = send_msg(sid5, "I want to speak to a human")
print(f"User: I want to speak to a human")
for msg in resp5:
    print("Bot:", msg.get("text"))
    if "custom" in msg:
        print("Custom payload:", json.dumps(msg["custom"], indent=2))

print("\n=== TEST 6: TWO-STAGE FALLBACK TEST ===")
sid6 = f"test_user_fallback_{uuid.uuid4().hex[:6]}"
resp6_1 = send_msg(sid6, "qwerty zxcvbn poiuy")
print("User Stage 1 input: qwerty zxcvbn poiuy")
for msg in resp6_1:
    print("Bot Stage 1 reply:", msg.get("text"))
    if "buttons" in msg:
        print("Stage 1 Buttons:", [b.get("title") for b in msg["buttons"]])

resp6_2 = send_msg(sid6, "another gibberish msg")
print("User Stage 2 input: another gibberish msg")
for msg in resp6_2:
    print("Bot Stage 2 reply:", msg.get("text"))
    if "custom" in msg:
        print("Stage 2 Custom Handover Payload:", json.dumps(msg["custom"], indent=2))

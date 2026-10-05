"""
EcoTravel Advisor – Docker Stack Automated Verification
========================================================
MSc Assignment Stage 4: Docker Runtime Verification

Tests containerised services:
1. Rasa REST Endpoint on http://127.0.0.1:5005
2. Inter-container communication (Rasa -> Actions container)
3. Custom Action execution
4. Form flow execution
5. Nginx Frontend HTTP GET on http://127.0.0.1:8080
"""

import requests
import sys
import uuid

RASA_URL = "http://127.0.0.1:5005/webhooks/rest/webhook"
FRONTEND_URL = "http://127.0.0.1:8080/"

def send_msg(sender_id, text):
    resp = requests.post(RASA_URL, json={"sender": sender_id, "message": text}, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    texts = [m.get("text", "") for m in data if m.get("text")]
    buttons = [b for m in data for b in m.get("buttons", [])]
    return texts, buttons

def test_docker_stack():
    print("==================================================")
    print("  ECOTRAVEL ADVISOR – DOCKER STACK VERIFICATION")
    print("==================================================")

    # 1. Frontend HTTP check
    print("\n[1/5] Testing Frontend (Nginx) on port 8080...")
    f_resp = requests.get(FRONTEND_URL, timeout=5)
    print(f"  HTTP Status: {f_resp.status_code}")
    assert f_resp.status_code == 200, f"Frontend returned {f_resp.status_code}"
    assert "<title>" in f_resp.text.lower() or "ecotravel" in f_resp.text.lower(), "Frontend HTML invalid"
    print("  ✓ Frontend HTTP check PASSED")

    # 2. Rasa REST Greeting
    print("\n[2/5] Testing Rasa REST Webhook (Greeting)...")
    sender = f"docker_test_{uuid.uuid4().hex[:8]}"
    texts, _ = send_msg(sender, "hello")
    print(f"  Bot Response: {texts}")
    assert len(texts) > 0, "No bot response received for greeting"
    print("  ✓ Rasa REST Greeting PASSED")

    # 3. Custom Action via Docker inter-container network
    print("\n[3/5] Testing Custom Action via Docker Inter-container Communication...")
    sender_action = f"docker_action_{uuid.uuid4().hex[:8]}"
    texts_act, _ = send_msg(sender_action, "recommend carbon offset programmes")
    print(f"  Action Response Preview: {texts_act[0][:120]}..." if texts_act else "No response")
    assert len(texts_act) > 0 and "Carbon Offset" in texts_act[0], "Custom action failed"
    print("  ✓ Custom Action (Rasa -> Actions container) PASSED")

    # 4. Sustainable Activities Custom Action
    print("\n[4/5] Testing Sustainable Activities Custom Action...")
    sender_act2 = f"docker_act2_{uuid.uuid4().hex[:8]}"
    texts_act2, _ = send_msg(sender_act2, "recommend sustainable activities")
    print(f"  Activities Response Preview: {texts_act2[0][:120]}..." if texts_act2 else "No response")
    assert len(texts_act2) > 0 and "Sustainable" in texts_act2[0], "Activities action failed"
    print("  ✓ Sustainable Activities Custom Action PASSED")

    # 5. Form Flow Execution
    print("\n[5/5] Testing Trip Planning Form Flow in Docker...")
    sender_form = f"docker_form_{uuid.uuid4().hex[:8]}"
    
    t1, _ = send_msg(sender_form, "/plan_trip")
    print(f"  Form Step 1 (/plan_trip): {t1[0][:80]}...")
    
    t2, _ = send_msg(sender_form, "Paris")
    print(f"  Form Step 2 (Paris): {t2[0][:80]}...")
    
    t3, _ = send_msg(sender_form, "10 October to 15 October")
    print(f"  Form Step 3 (Dates): {t3[0][:80]}...")

    t4, _ = send_msg(sender_form, "800 euros")
    print(f"  Form Step 4 (Budget): {t4[0][:80]}...")

    t5, _ = send_msg(sender_form, "high")
    print(f"  Form Step 5 (Sustainability): {' | '.join([m[:60] for m in t5])}")

    assert len(t5) > 0, "Form completion returned no messages"
    print("  ✓ Form Flow Execution PASSED")

    print("\n==================================================")
    print("  ALL DOCKER RUNTIME VERIFICATION TESTS PASSED!  ")
    print("==================================================")

if __name__ == "__main__":
    try:
        test_docker_stack()
    except Exception as e:
        print(f"\nERROR: {e}")
        sys.exit(1)

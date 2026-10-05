"""
EcoTravel Advisor – Hugging Face Single-Container Local Verification
====================================================================
MSc Assignment Stage 5: Hugging Face Spaces Deployment

Tests single-container runtime on public port 7860:
1. Nginx static frontend on http://127.0.0.1:7860/
2. Nginx reverse proxy to Rasa REST webhook on http://127.0.0.1:7860/webhooks/rest/webhook
3. Inter-process custom action routing (Nginx 7860 -> Rasa 5005 -> Action Server 5055)
4. Trip planning form execution
"""

import requests
import sys
import uuid

HF_PORT_7860_URL = "http://127.0.0.1:7860/webhooks/rest/webhook"
FRONTEND_URL = "http://127.0.0.1:7860/"

def send_msg(sender_id, text):
    resp = requests.post(HF_PORT_7860_URL, json={"sender": sender_id, "message": text}, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    texts = [m.get("text", "") for m in data if m.get("text")]
    return texts

def test_hf_container():
    print("==================================================")
    print("  ECOTRAVEL ADVISOR – HF SINGLE CONTAINER TEST")
    print("==================================================")

    # 1. Nginx static frontend HTTP check
    print("\n[1/5] Testing Nginx Frontend on Port 7860...")
    f_resp = requests.get(FRONTEND_URL, timeout=5)
    print(f"  HTTP Status: {f_resp.status_code}")
    assert f_resp.status_code == 200, f"Frontend returned {f_resp.status_code}"
    print("  ✓ Port 7860 Nginx Frontend HTTP check PASSED")

    # 2. Rasa REST Greeting via Nginx Proxy
    print("\n[2/5] Testing Nginx Proxy -> Rasa REST Webhook (Greeting)...")
    sender = f"hf_test_{uuid.uuid4().hex[:8]}"
    texts = send_msg(sender, "hello")
    print(f"  Bot Response: {texts}")
    assert len(texts) > 0, "No bot response received for greeting"
    print("  ✓ Port 7860 Nginx Proxy -> Rasa Greeting PASSED")

    # 3. Custom Action via Single-Container Loopback (Nginx -> Rasa -> Action Server)
    print("\n[3/5] Testing Custom Action (Carbon Offset Guidance)...")
    sender_action = f"hf_action_{uuid.uuid4().hex[:8]}"
    texts_act = send_msg(sender_action, "recommend carbon offset programmes")
    print(f"  Action Response Preview: {texts_act[0][:120]}..." if texts_act else "No response")
    assert len(texts_act) > 0 and "Carbon Offset" in texts_act[0], "Custom action failed"
    print("  ✓ Single-Container Custom Action PASSED")

    # 4. Sustainable Activities Custom Action
    print("\n[4/5] Testing Custom Action (Sustainable Activities)...")
    sender_act2 = f"hf_act2_{uuid.uuid4().hex[:8]}"
    texts_act2 = send_msg(sender_act2, "recommend sustainable activities")
    print(f"  Activities Response Preview: {texts_act2[0][:120]}..." if texts_act2 else "No response")
    assert len(texts_act2) > 0 and "Sustainable" in texts_act2[0], "Activities action failed"
    print("  ✓ Sustainable Activities Custom Action PASSED")

    # 5. Form Flow Execution
    print("\n[5/5] Testing Trip Planning Form Flow via Port 7860...")
    sender_form = f"hf_form_{uuid.uuid4().hex[:8]}"
    
    t1 = send_msg(sender_form, "/plan_trip")
    print(f"  Form Step 1 (/plan_trip): {t1[0][:80]}...")
    
    t2 = send_msg(sender_form, "Paris")
    print(f"  Form Step 2 (Paris): {t2[0][:80]}...")
    
    t3 = send_msg(sender_form, "10 October to 15 October")
    print(f"  Form Step 3 (Dates): {t3[0][:80]}...")

    t4 = send_msg(sender_form, "800 euros")
    print(f"  Form Step 4 (Budget): {t4[0][:80]}...")

    t5 = send_msg(sender_form, "high")
    print(f"  Form Step 5 (Sustainability): {' | '.join([m[:60] for m in t5])}")

    assert len(t5) > 0, "Form completion returned no messages"
    print("  ✓ Form Flow Execution PASSED")

    print("\n==================================================")
    print("  ALL HF CONTAINER LOCAL VERIFICATION TESTS PASSED! ")
    print("==================================================")

if __name__ == "__main__":
    try:
        test_hf_container()
    except Exception as e:
        print(f"\nERROR: {e}")
        sys.exit(1)

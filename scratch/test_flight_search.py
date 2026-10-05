"""
Test script for Stage 1: Amadeus Flight Search
Executes ActionSearchFlights directly via python with simulated Rasa tracker.
Records exact OAuth status, HTTP outcome, and chatbot output without exposing secrets.
"""

from dotenv import load_dotenv
import os

load_dotenv()

# Credential availability check
climatiq_key = bool(os.getenv("CLIMATIQ_API_KEY"))
amadeus_key = bool(os.getenv("AMADEUS_API_KEY"))
amadeus_secret = bool(os.getenv("AMADEUS_API_SECRET"))

print("=== CREDENTIAL AVAILABILITY CHECK ===")
print(f"CLIMATIQ_API_KEY loaded: {climatiq_key}")
print(f"AMADEUS_API_KEY loaded: {amadeus_key}")
print(f"AMADEUS_API_SECRET loaded: {amadeus_secret}")

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from actions.actions import ActionSearchFlights, get_amadeus_token, search_amadeus_flights

print("\n=== STAGE 1: AMADEUS OAUTH & FLIGHT SEARCH API TEST ===")
token = get_amadeus_token()
print(f"OAuth Succeeded: {bool(token)}")

data, err_msg, status_code = search_amadeus_flights("LON", "PAR", "2026-10-15", token or "dummy_token")
print(f"Amadeus Flight API Endpoint: https://test.api.amadeus.com/v2/shopping/flight-offers")
print(f"HTTP Status Code: {status_code}")
print(f"Error Message: {err_msg}")
print(f"Number of Live Flight Results: {len(data)}")

# Now test the custom action execution with simulated tracker
class DummyTracker:
    def get_slot(self, slot_name):
        slots = {
            "origin": "London",
            "destination": "Paris",
            "travel_dates": "10 October to 15 October"
        }
        return slots.get(slot_name)

class DummyDispatcher:
    def __init__(self):
        self.messages = []
    def utter_message(self, text=None, **kwargs):
        if text:
            self.messages.append(text)

dispatcher = DummyDispatcher()
tracker = DummyTracker()
action = ActionSearchFlights()
action.run(dispatcher, tracker, {})

print("\n=== CHATBOT FLIGHT-SEARCH RESPONSE ===")
for msg in dispatcher.messages:
    print(msg)

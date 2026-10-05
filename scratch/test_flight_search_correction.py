import os
import sys
import asyncio
from dotenv import load_dotenv

load_dotenv()

# Add project root to sys.path
sys.path.insert(0, os.path.abspath("."))

from rasa_sdk import Tracker
from rasa_sdk.executor import CollectingDispatcher
from actions.actions import ActionSearchFlights

async def test_flight_action():
    action = ActionSearchFlights()
    dispatcher = CollectingDispatcher()
    tracker = Tracker(
        sender_id="test_user",
        slots={
            "origin": "London",
            "destination": "Paris",
            "travel_dates": "10 October to 15 October"
        },
        latest_message={"text": "recommend flights"},
        events=[],
        paused=False,
        followup_action=None,
        active_loop={},
        latest_action_name=None,
    )
    domain = {}
    
    events = action.run(dispatcher, tracker, domain)
    print("=== DISPATCHER MESSAGES ===")
    for msg in dispatcher.messages:
        print(msg.get("text"))

if __name__ == "__main__":
    asyncio.run(test_flight_action())

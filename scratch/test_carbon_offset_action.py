import os
import sys
import asyncio
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.abspath("."))

from rasa_sdk import Tracker
from rasa_sdk.executor import CollectingDispatcher
from actions.actions import ActionRecommendCarbonOffsets

async def test_carbon_offset():
    action = ActionRecommendCarbonOffsets()
    dispatcher = CollectingDispatcher()
    tracker = Tracker(
        sender_id="test_user",
        slots={},
        latest_message={"text": "recommend carbon offset programmes"},
        events=[],
        paused=False,
        followup_action=None,
        active_loop={},
        latest_action_name=None,
    )
    domain = {}
    
    events = action.run(dispatcher, tracker, domain)
    for msg in dispatcher.messages:
        print(msg.get("text"))

if __name__ == "__main__":
    asyncio.run(test_carbon_offset())

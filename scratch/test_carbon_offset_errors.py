import os
import sys
import asyncio
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.abspath("."))

from rasa_sdk import Tracker
from rasa_sdk.executor import CollectingDispatcher
from actions.actions import ActionRecommendCarbonOffsets

async def test_error_handling():
    action = ActionRecommendCarbonOffsets()
    
    # Save original load_json_file
    import actions.actions as act_module
    orig_load = act_module.load_json_file

    print("=== TEST 1: Missing JSON ===")
    act_module.load_json_file = lambda path: None
    disp1 = CollectingDispatcher()
    action.run(disp1, Tracker("u1", {}, {"text": "hi"}, [], False, None, {}, None), {})
    print("Output:", disp1.messages[0].get("text"))

    print("\n=== TEST 2: Malformed/Invalid Type JSON ===")
    act_module.load_json_file = lambda path: "Not a list"
    disp2 = CollectingDispatcher()
    action.run(disp2, Tracker("u1", {}, {"text": "hi"}, [], False, None, {}, None), {})
    print("Output:", disp2.messages[0].get("text"))

    print("\n=== TEST 3: Empty List ===")
    act_module.load_json_file = lambda path: []
    disp3 = CollectingDispatcher()
    action.run(disp3, Tracker("u1", {}, {"text": "hi"}, [], False, None, {}, None), {})
    print("Output:", disp3.messages[0].get("text"))

    # Restore original function
    act_module.load_json_file = orig_load
    print("\nError handling test completed successfully & restored original loader.")

if __name__ == "__main__":
    asyncio.run(test_error_handling())

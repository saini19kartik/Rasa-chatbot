import os
import sys
import asyncio
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.abspath("."))

from rasa_sdk import Tracker
from rasa_sdk.executor import CollectingDispatcher
from actions.actions import ActionSearchFlights, parse_departure_date, resolve_iata_code

def test_helpers():
    print("=== TESTING HELPERS ===")
    print("1. Date '10 October to 15 October':", parse_departure_date("10 October to 15 October"))
    print("2. Date '2026-12-01':", parse_departure_date("2026-12-01"))
    print("3. Invalid date 'invalid':", parse_departure_date("invalid"))
    print("4. City 'London':", resolve_iata_code("London"))
    print("5. City 'PAR':", resolve_iata_code("PAR"))
    print("6. Unsupported city 'Atlantis':", resolve_iata_code("Atlantis"))

if __name__ == "__main__":
    test_helpers()

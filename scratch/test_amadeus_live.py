from dotenv import load_dotenv
import os
import requests

load_dotenv()

key = os.getenv('AMADEUS_API_KEY')
secret = os.getenv('AMADEUS_API_SECRET')

print("=== AMADEUS LIVE API TEST ===")
print("Credentials check:")
print("AMADEUS_API_KEY loaded:", bool(key))
print("AMADEUS_API_SECRET loaded:", bool(secret))

token_url = "https://test.api.amadeus.com/v1/security/oauth2/token"
payload = {
    "grant_type": "client_credentials",
    "client_id": key,
    "client_secret": secret
}

r_token = requests.post(token_url, data=payload, headers={"Content-Type": "application/x-www-form-urlencoded"})
print("\n1. OAuth Token Request:")
print("Endpoint:", token_url)
print("HTTP Status:", r_token.status_code)
oauth_succeeded = r_token.status_code == 200
print("OAuth Succeeded:", oauth_succeeded)

if oauth_succeeded:
    token_data = r_token.json()
    access_token = token_data.get("access_token")
    
    # Test hotel by city search (e.g., LON for London or PAR for Paris)
    hotel_url = "https://test.api.amadeus.com/v1/reference-data/locations/hotels/by-city"
    params = {"cityCode": "PAR"}
    headers = {"Authorization": f"Bearer {access_token}"}
    
    r_hotel = requests.get(hotel_url, params=params, headers=headers)
    print("\n2. Hotel Search Request:")
    print("Endpoint:", hotel_url)
    print("HTTP Status:", r_hotel.status_code)
    
    if r_hotel.status_code == 200:
        data = r_hotel.json().get("data", [])
        print("Hotel Data Returned:", len(data) > 0)
        print("Number of Results:", len(data))
    else:
        print("Hotel Data Returned: False")
        print("Response Body:", r_hotel.text[:200])
else:
    print("OAuth error body:", r_token.text[:200])

#!/usr/bin/env python3
import requests
import json
from datetime import datetime

def make_camping_request():
    """
    Make a POST request to BC Parks camping reservation system API to check availability
    """
    # The correct URL for BC Parks camping availability API
    base_url = "https://camping.bcparks.ca/api/availability/cards"
    
    # Current timestamp for the seed parameter
    current_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    
    # Data for the POST request
    params = {
        "resourceId": "",
        "bookingCategoryId": 0,
        "resourceLocationId": -2147483647,
        "equipmentCategoryId": -32768,
        "subEquipmentCategoryId": -32768,
        "numEquipment": "",
        "startDate": "2025-09-01",
        "endDate": "2025-10-01",
        "nights": 1,
        "filterData": [],  # Using proper JSON array instead of string
        "boatLength": 0,
        "boatDraft": 0,
        "boatWidth": 0,
        "peopleCapacityCategoryCounts": [],  # Using proper JSON array instead of string
        "preferWeekends": False,  # Using proper JSON boolean instead of string
        "seed": current_time
    }
    
    # Set up headers to mimic a browser
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'Connection': 'keep-alive',
        'Referer': 'https://camping.bcparks.ca/',
        'Origin': 'https://camping.bcparks.ca',
        'Cache-Control': 'no-cache',
        'Content-Type': 'application/json',
    }
    
    print(f"Making POST request to BC Parks camping reservation system API...")
    print(f"URL: {base_url}")
    print(f"Parameters: {json.dumps(params, indent=2)}")
    
    # Make the POST request with empty data but parameters in URL
    response = requests.post(base_url, params=params, data="[]", headers=headers)
    
    # Check if the request was successful
    if response.status_code == 200:
        print(f"\nRequest successful! Status code: {response.status_code}")
        
        # Try to parse the response as JSON
        try:
            json_response = response.json()
            
            # Save the JSON response to a file
            with open("camping_response.json", "w", encoding="utf-8") as f:
                json.dump(json_response, f, indent=2)
                print("\nFull JSON response saved to camping_response.json")
            
            # Process the response to find available spots
            print("\n=== AVAILABLE CAMPING SPOTS ===")
            available_count = 0
            
            if "availabilityCards" in json_response:
                for card in json_response["availabilityCards"]:
                    resource_id = card.get("resourceId")
                    date_ranges = card.get("dateRanges", [])
                    
                    # Check if there are available dates
                    if date_ranges:
                        available_count += 1
                        print(f"\nResource ID: {resource_id}")
                        print("Available dates:")
                        for date_range in date_ranges:
                            start = date_range.get("start", "Unknown")
                            end = date_range.get("end", "Unknown")
                            print(f"  - From {start} to {end}")
            
            if available_count == 0:
                print("No available camping spots found for the specified dates.")
            else:
                print(f"\nTotal available resources: {available_count}")
                
        except json.JSONDecodeError:
            print("\nResponse is not valid JSON. Treating as HTML/text.")
            # Print a snippet of the response content
            content_preview = response.text[:500] + "..." if len(response.text) > 500 else response.text
            print(f"\nResponse content preview (first 500 chars):\n{content_preview}")
            
            # Save the full response to a file
            with open("camping_response.html", "w", encoding="utf-8") as f:
                f.write(response.text)
                print("\nFull response saved to camping_response.html")
    else:
        print(f"\nRequest failed with status code: {response.status_code}")
        print(f"Response content: {response.text}")

if __name__ == "__main__":
    make_camping_request()
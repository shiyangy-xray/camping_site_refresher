#!/usr/bin/env python3
import requests
import json
import os
import boto3
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timedelta, date

# === Config ===
RESOURCE_LOCATIONS = {
    "Golden Ears": -2147483606,
    "Alice Lake": -2147483647,
    "Porteau Cove": -2147483550,
    "Cultus Lake": -2147483623,
    "Silver Lake": -2147483535
}

DATE_RANGES = [
    ("2025-07-01", "2025-08-01"),
    ("2025-08-01", "2025-09-01"),
]

INTERVAL_SECONDS = 5

# === Email Notification ===
def send_email_notification(available_resources, recipient_email, profile_name="default", region="us-west-2"):
    if not available_resources:
        print("No available resources to notify about.")
        return False

    sender_email = "kjoshy12@gmail.com"

    email_body = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; }}
            .resource {{ margin-bottom: 20px; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }}
            .dates {{ margin-left: 20px; }}
            h2 {{ color: #2c6e49; }}
            .header {{ background-color: #2c6e49; color: white; padding: 10px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>BC Parks Camping Availability Alert</h1>
        </div>
        <p>Good news! We found {len(available_resources)} available camping spots:</p>
    """

    for resource in available_resources:
        location_name = resource.get("locationName", "Unknown Location")
        resource_id = resource.get("resourceId")
        date_ranges = resource.get("dateRanges", [])
        
        email_body += f"""
        <div class="resource">
            <h2>{location_name} (Resource ID: {resource_id})</h2>
            <p>Available dates:</p>
            <ul class="dates">
        """
        for date_range in date_ranges:
            start = date_range.get("start", "Unknown")
            end = date_range.get("end", "Unknown")
            email_body += f"<li>From {start} to {end}</li>"

        email_body += """
            </ul>
            <p><a href="https://camping.bcparks.ca/">Book Now</a></p>
        </div>
        """

    email_body += """
        <p>This is an automated notification. Please book quickly as spots may fill up fast!</p>
    </body>
    </html>
    """

    try:
        session = boto3.Session(profile_name=profile_name, region_name=region)
        ses = session.client('ses')

        ses.send_email(
            Source=sender_email,
            Destination={"ToAddresses": [recipient_email]},
            Message={
                "Subject": {"Data": f"BC Parks Camping Alert: {len(available_resources)} spots available!"},
                "Body": {
                    "Text": {"Data": "Camping spots available. Check your inbox for full details."},
                    "Html": {"Data": email_body}
                }
            }
        )
        print(f"\nEmail notification sent successfully to {recipient_email}")
        return True
    except Exception as e:
        print(f"\nFailed to send email notification: {str(e)}")
        return False

# === Parse JSON ===
def parse_camping_response(json_response, location_name):
    available_resources = []
    for card in json_response.get("availabilityCards", []):
        resource_id = card.get("resourceId")
        date_ranges = card.get("dateRanges", [])
        if date_ranges:
            available_resources.append({
                "locationName": location_name,
                "resourceId": resource_id,
                "dateRanges": date_ranges
            })
    return available_resources

# === Request Function ===
def make_camping_request(location_id, location_name, start_date, end_date):
    base_url = "https://camping.bcparks.ca/api/availability/cards"
    current_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

    params = {
        "resourceId": "",
        "bookingCategoryId": 0,
        "resourceLocationId": location_id,
        "equipmentCategoryId": -32768,
        "subEquipmentCategoryId": -32768,
        "numEquipment": "",
        "startDate": start_date,
        "endDate": end_date,
        "nights": 1,
        "filterData": "[]",
        "boatLength": 0,
        "boatDraft": 0,
        "boatWidth": 0,
        "peopleCapacityCategoryCounts": "[]",
        "preferWeekends": "true",
        "seed": current_time
    }

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'Referer': 'https://camping.bcparks.ca/',
        'Origin': 'https://camping.bcparks.ca',
        'Cache-Control': 'no-cache',
        'Content-Type': 'application/json',
    }

    print(f"\nChecking {location_name} from {start_date} to {end_date}...")

    try:
        response = requests.post(base_url, params=params, data="[]", headers=headers)

        if response.status_code == 200:
            print("✅ 200 OK")
            return parse_camping_response(response.json(), location_name)
        else:
            print(f"❌ Request failed with status code: {response.status_code}")
            print("--- Request Debug Info ---")
            print(f"URL: {response.url}")
            print(f"Headers: {json.dumps(headers, indent=2)}")
            print(f"Params: {json.dumps(params, indent=2)}")
            print(f"Payload: []")
            print(f"Response Text: {response.text[:1000]}")
            return []
    except Exception as e:
        print(f"💥 Exception occurred while checking {location_name}: {e}")
        return []

# === Main Function ===
def main():
    all_available_resources = []
    today = date.today()

    for original_start, original_end in DATE_RANGES:
        start_dt = datetime.strptime(original_start, "%Y-%m-%d").date()
        end_dt = datetime.strptime(original_end, "%Y-%m-%d").date()

        # Skip range if it's completely in the past
        if end_dt < today:
            print(f"⏩ Skipping range {original_start} to {original_end} (already in the past)")
            continue

        # Adjust start date if it's in the past
        effective_start = max(start_dt, today)
        effective_start_str = effective_start.strftime("%Y-%m-%d")
        end_str = end_dt.strftime("%Y-%m-%d")

        print(f"\n📅 Checking range {effective_start_str} to {end_str}")

        for location_name, location_id in RESOURCE_LOCATIONS.items():
            found = make_camping_request(location_id, location_name, effective_start_str, end_str)
            all_available_resources.extend(found)
            time.sleep(INTERVAL_SECONDS)

    if all_available_resources:
        recipient_email = os.environ.get("NOTIFICATION_EMAIL", "kjoshy12@gmail.com")
        send_email_notification(all_available_resources, recipient_email)
    else:
        print("\nNo availability found for any date or location.")


if __name__ == "__main__":
    main()

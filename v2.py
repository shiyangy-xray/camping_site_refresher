#!/usr/bin/env python3
import requests
import json
import smtplib
import os
import boto3
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

def send_email_notification(available_resources, recipient_email, profile_name="default", region="us-west-2"):
    """
    Send an email notification using AWS SES when available camping resources are found.

    Args:
        available_resources (list): List of available resources with their date ranges
        recipient_email (str): Email address to send the notification to
        profile_name (str): AWS CLI profile name (configured via ADA)
        region (str): AWS region where SES is enabled

    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    if not available_resources:
        print("No available resources to notify about.")
        return False

    sender_email = "kjoshy12@gmail.com"  # Must be verified in Amazon SES

    # Build HTML email body
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
        resource_id = resource.get("resourceId")
        date_ranges = resource.get("dateRanges", [])
        
        email_body += f"""
        <div class="resource">
            <h2>Resource ID: {resource_id}</h2>
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

    # Use ADA-managed profile
    try:
        session = boto3.Session(profile_name=profile_name, region_name=region)
        ses = session.client('ses')

        response = ses.send_email(
            Source=sender_email,
            Destination={"ToAddresses": [recipient_email]},
            Message={
                "Subject": {"Data": f"BC Parks Camping Alert: {len(available_resources)} spots available!"},
                "Body": {"Html": {"Data": email_body}}
            }
        )

        print(f"\nEmail notification sent successfully to {recipient_email}")
        return True
    except Exception as e:
        print(f"\nFailed to send email notification: {str(e)}")
        print("Make sure:")
        print("  - ADA is refreshing your credentials (e.g., via `ada run` or `ada credential-process`)")
        print("  - Your sender email is verified in SES")
        print("  - SES is out of the sandbox or recipient is verified")
        return False

def parse_camping_response(json_response):
    """
    Parse the camping API response and extract available spots
    
    Args:
        json_response (dict): The JSON response from the API
        
    Returns:
        list: List of available resources with their date ranges
    """
    print("\n=== AVAILABLE CAMPING SPOTS ===")
    available_resources = []
    available_count = 0
    
    if "availabilityCards" in json_response:
        for card in json_response["availabilityCards"]:
            resource_id = card.get("resourceId")
            date_ranges = card.get("dateRanges", [])
            
            # Check if there are available dates
            if date_ranges:
                available_count += 1
                resource_info = {
                    "resourceId": resource_id,
                    "dateRanges": date_ranges
                }
                available_resources.append(resource_info)
                
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
    
    return available_resources

def make_camping_request():
    """
    Make a POST request to BC Parks camping reservation system API to check availability
    with parameters in the URL
    """
    # Base URL for BC Parks camping availability API
    base_url = "https://camping.bcparks.ca/api/availability/cards"
    
    # Current timestamp for the seed parameter
    current_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    
    # Parameters for the URL query string
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
        "filterData": "[]",
        "boatLength": 0,
        "boatDraft": 0,
        "boatWidth": 0,
        "peopleCapacityCategoryCounts": "[]",
        "preferWeekends": "true",
        "seed": current_time
    }
    
    # Set up headers to mimic a browser
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
            
            # Parse the response to find available spots
            available_resources = parse_camping_response(json_response)
            return available_resources
                
        except json.JSONDecodeError:
            print("\nResponse is not valid JSON. Treating as HTML/text.")
            # Print a snippet of the response content
            content_preview = response.text[:500] + "..." if len(response.text) > 500 else response.text
            print(f"\nResponse content preview (first 500 chars):\n{content_preview}")
            
            # Save the full response to a file
            with open("camping_response.html", "w", encoding="utf-8") as f:
                f.write(response.text)
                print("\nFull response saved to camping_response.html")
            return None
    else:
        print(f"\nRequest failed with status code: {response.status_code}")
        print(f"Response content: {response.text}")
        return None

if __name__ == "__main__":
    # Make the request and get available resources
    available_resources = make_camping_request()
    
    # If resources are available, send an email notification
    if available_resources:
        print(f"\nFound {len(available_resources)} available camping resources.")
        
        # You can set a recipient email here or pass it as a command line argument
        recipient_email = os.environ.get("NOTIFICATION_EMAIL", "kjoshy12@gmail.com")
        
        # Uncomment the line below to enable email notifications
        send_email_notification(available_resources, recipient_email)
        
        print("\nTo enable email notifications:")
        print("1. Set the NOTIFICATION_EMAIL environment variable")
        print("2. Set EMAIL_USER and EMAIL_PASSWORD environment variables")
        print("3. Uncomment the send_email_notification line in the script")
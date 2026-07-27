import requests
import json
import random
import time
import os

# --- Configuration ---
ACCOUNTS_FILE = 'accounts.json'

# List of mobile User-Agents to rotate
USER_AGENTS = [
    'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Mobile Safari/537.36',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36',
    'Mozilla/5.0 (iPad; CPU OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/104.0.5112.99 Mobile/15E148 Safari/604.1',
]

# --- Functions ---
def load_accounts(filename=ACCOUNTS_FILE):
    """Loads account data (cookies and identifiers) from a JSON file."""
    if not os.path.exists(filename):
        # Create a template if the file doesn't exist
        template = {
            "account1": {
                "identifier": "example1@email.com",
                "cookies": {"c_user": "val1", "xs": "val2"}
            },
            "account2": {
                "identifier": "example2@email.com",
                "cookies": {"c_user": "val3", "xs": "val4"}
            }
        }
        with open(filename, 'w') as f:
            json.dump(template, f, indent=4)
        print(f"Created template {filename}. Please add your account details there.")
        return {}
    
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        print(f"Error: {filename} is not a valid JSON file.")
        return {}

def get_session(cookies: dict):
    """Creates a requests session with provided cookies and a random User-Agent."""
    session = requests.Session()
    for k, v in cookies.items():
        session.cookies.set(k, v)
    session.headers.update({
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    })
    return session

def attempt_otp_request(session: requests.Session, account_identifier: str):
    """Placeholder for attempting an OTP request."""
    print(f"Attempting OTP request for: {account_identifier} with User-Agent: {session.headers['User-Agent']}")
    
    otp_request_url = "https://m.facebook.com/login/identify/"
    
    try:
        response = session.get(otp_request_url, params={'q': account_identifier}, allow_redirects=True)
        print(f"Response Status Code: {response.status_code}")
        
        if "code_sent" in response.text.lower():
            print("OTP request might have been initiated.")
            return True
        else:
            print("OTP request failed or endpoint is incorrect.")
            return False
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return False

# --- Main execution ---
if __name__ == "__main__":
    print("Starting Facebook Multi-Account OTP Tool")
    
    accounts = load_accounts()
    if not accounts:
        print("No accounts found. Please configure accounts.json.")
    else:
        for account_name, data in accounts.items():
            print(f"\n--- Processing Account: {account_name} ---")
            identifier = data.get('identifier')
            cookies = data.get('cookies')
            
            if not identifier or not cookies:
                print(f"Skipping {account_name}: Missing identifier or cookies.")
                continue

            session = get_session(cookies)
            success = attempt_otp_request(session, identifier)
            
            if success:
                print(f"OTP request attempt for {account_name} successful.")
            else:
                print(f"OTP request attempt for {account_name} failed.")
            
            # Wait between accounts to avoid detection
            delay = random.uniform(10, 20)
            print(f"Waiting {delay:.2f} seconds before next account...")
            time.sleep(delay)

    print("\nAll accounts processed.")

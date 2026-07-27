import os
import json
import time
import random
import sys
from core.session_builder import create_http_session, build_request_context, setup_session_cookies
from core.proxy_manager import format_proxy_for_requests
from ui.colors import GREEN, RED, WHITE, YELLOW, CYAN, EKL, LINE
from ui.logo import logo
from core.counter import Counter

# --- Configuration ---
ACCOUNTS_FILE = 'accounts.json'

def load_accounts(filename=ACCOUNTS_FILE):
    """Loads account data (cookies and identifiers) from a JSON file."""
    if not os.path.exists(filename):
        template = {
            "account1": {
                "identifier": "example1@email.com",
                "cookies": {"c_user": "val1", "xs": "val2"}
            }
        }
        with open(filename, 'w') as f:
            json.dump(template, f, indent=4)
        return {}
    
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}

def attempt_otp_request(session, account_identifier, server="m.facebook.com", ctx=None):
    """Attempts an OTP request using the upgraded session and context."""
    otp_request_url = f"https://{server}/login/identify/"
    headers = ctx["base_headers"] if ctx else {}
    
    try:
        response = session.get(otp_request_url, params={'q': account_identifier}, headers=headers, allow_redirects=True)
        
        if response.status_code == 200:
            if "code_sent" in response.text.lower() or "checkpoint" in response.text.lower():
                return True, "OTP request initiated or Checkpoint triggered."
            else:
                return False, "Endpoint reached but OTP not confirmed."
        else:
            return False, f"HTTP Error: {response.status_code}"
    except Exception as e:
        return False, str(e)

def main():
    logo()
    print(f" {GREEN}[{RED}●{GREEN}] {WHITE}Upgraded FB OTP Tool with TLS Fingerprinting")
    print(f"{LINE}")
    
    accounts = load_accounts()
    if not accounts:
        print(f" {RED}[!] No accounts found in {ACCOUNTS_FILE}")
        return

    counter = Counter()
    device_type = "Android" # Default upgraded device
    browser_type = "Default"
    server = "m.facebook.com"
    locale = "en_US"

    for account_name, data in accounts.items():
        print(f" {CYAN}[*] Processing: {account_name}")
        identifier = data.get('identifier')
        cookies_data = data.get('cookies')
        
        if not identifier or not cookies_data:
            print(f" {YELLOW}[!] Skipping: Missing identifier or cookies.")
            continue

        try:
            # Create session with TLS fingerprinting (curl_cffi)
            session = create_http_session(device_type)
            setup_session_cookies(session, device_type)
            
            # Load account cookies into session
            for k, v in cookies_data.items():
                session.cookies.set(k, v)
            
            ctx = build_request_context(device_type, browser_type, locale)
            
            success, message = attempt_otp_request(session, identifier, server, ctx)
            
            if success:
                counter.update("success", number=identifier, message=message, color=GREEN)
            else:
                counter.update("failed", number=identifier, message=message, color=YELLOW)
                
        except Exception as e:
            counter.update("error", number=identifier, message=str(e), color=RED)

        # Random delay to mimic human behavior
        delay = random.uniform(5, 10)
        time.sleep(delay)

    print(f"{LINE}")
    s = counter.summary()
    print(f" {GREEN}[{RED}●{GREEN}] {WHITE}Total: {s['checked']} | Success: {s['success']} | Failed: {s['failed']} | Error: {s['error']}")
    print(f"{LINE}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n {RED}[!] Cancelled by user.")
        sys.exit(0)

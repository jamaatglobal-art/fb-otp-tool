import os
import json
import time
import random
import sys
import re
from core.session_builder import create_http_session, build_request_context, setup_session_cookies
from core.proxy_manager import format_proxy_for_requests
from ui.colors import GREEN, RED, WHITE, YELLOW, CYAN, EKL, LINE, ORANGE
from ui.logo import logo
from core.counter import Counter

# --- Configuration ---
ACCOUNTS_FILE = 'accounts.json'

def load_accounts(filename=ACCOUNTS_FILE):
    """Loads account data (cookies and identifiers) from a JSON file."""
    if not os.path.exists(filename):
        return {}
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}

def _search(pattern, text):
    m = re.search(pattern, text)
    return m.group(1) if m else None

def attempt_otp_request(session, account_identifier, server="m.facebook.com", ctx=None):
    """
    Attempts an OTP request using advanced detection.
    Steps:
    1. Visit /login/identify to get tokens.
    2. Submit the identifier to find the account.
    3. Select the SMS/Email OTP method.
    4. Verify if the code was actually sent.
    """
    headers = ctx["base_headers"] if ctx else {}
    
    try:
        # Step 1: Initial identify page to get tokens (LSD, jazoest)
        identify_url = f"https://{server}/login/identify/?ctx=recover"
        res1 = session.get(identify_url, headers=headers)
        lsd = _search(r'name="lsd" value="([^"]+)"', res1.text)
        jazoest = _search(r'name="jazoest" value="([^"]+)"', res1.text)
        
        if not lsd:
            return False, "Failed to fetch security tokens (LSD missing)."

        # Step 2: Search for the account
        search_url = f"https://{server}/login/identify/?ctx=recover&search_attempts=1"
        data = {
            'lsd': lsd,
            'jazoest': jazoest,
            'email': account_identifier,
            'did_submit': 'Search'
        }
        res2 = session.post(search_url, data=data, headers=headers, allow_redirects=True)
        
        if "identify_search_error" in res2.text:
            return False, "Account not found or Search Limit reached."

        # Step 3: Check if we are on the 'select method' page
        # Usually it redirects to /recover/initiate/
        if "/recover/initiate/" not in res2.url and "recover" not in res2.text:
             return False, "Could not reach recovery initiation page."

        # Extract recovery tokens
        lsd = _search(r'name="lsd" value="([^"]+)"', res2.text) or lsd
        jazoest = _search(r'name="jazoest" value="([^"]+)"', res2.text) or jazoest
        
        # Step 4: Request the code (Trigger OTP)
        # We need to find the 'recover_method' value (e.g., send_email, send_sms)
        # For simplicity, we try to trigger the first available method
        recover_method = _search(r'name="recover_method" value="([^"]+)"', res2.text)
        if not recover_method:
            return False, "No recovery method (SMS/Email) found for this account."

        initiate_url = f"https://{server}/recover/initiate/"
        data = {
            'lsd': lsd,
            'jazoest': jazoest,
            'recover_method': recover_method,
            'reset_action': 'Send Code'
        }
        
        res3 = session.post(initiate_url, data=data, headers=headers, allow_redirects=True)
        
        # Step 5: Verify Success
        # Look for the 'enter_code' input or confirmation message
        if "n" in res3.url and ("confirm" in res3.text.lower() or "code" in res3.text.lower()):
            return True, f"OTP Sent via {recover_method}!"
        elif "checkpoint" in res3.text.lower():
            return False, "Account Checkpoint (Security Blocked)."
        elif "try again later" in res3.text.lower():
            return False, "Rate Limited: Try again later."
        else:
            return False, "Request submitted but confirmation not found."

    except Exception as e:
        return False, f"Exception: {str(e)[:50]}"

def main():
    logo()
    print(f" {GREEN}[{RED}●{GREEN}] {WHITE}Facebook OTP Tool - Precise Mode (2026)")
    print(f" {GREEN}[{RED}●{GREEN}] {WHITE}Analyzing and Sending OTP...")
    print(f"{LINE}")
    
    accounts = load_accounts()
    if not accounts:
        print(f" {RED}[!] No accounts found in {ACCOUNTS_FILE}")
        print(f" {YELLOW}[*] Run the registration tool first to generate accounts.")
        return

    counter = Counter()
    device_type = "Android"
    browser_type = "Default"
    server = "m.facebook.com"
    locale = "en_US"

    for account_name, data in accounts.items():
        identifier = data.get('identifier')
        cookies_data = data.get('cookies')
        
        if not identifier or not cookies_data:
            continue

        print(f" {CYAN}[*] Target: {identifier}")
        
        try:
            session = create_http_session(device_type)
            setup_session_cookies(session, device_type)
            
            # Load account cookies
            for k, v in cookies_data.items():
                session.cookies.set(k, v)
            
            ctx = build_request_context(device_type, browser_type, locale)
            
            success, message = attempt_otp_request(session, identifier, server, ctx)
            
            if success:
                counter.update("success", number=identifier, message=message, color=GREEN)
            else:
                # Color code errors based on message
                color = RED if "Failed" in message or "Exception" in message else YELLOW
                counter.update("failed", number=identifier, message=message, color=color)
                
        except Exception as e:
            counter.update("error", number=identifier, message=str(e)[:50], color=RED)

        # Safety delay
        time.sleep(random.uniform(3, 7))

    print(f"\n{LINE}")
    s = counter.summary()
    print(f" {GREEN}[{RED}●{GREEN}] {WHITE}Total: {s['checked']} | {GREEN}Sent: {s['success']} | {RED}Failed/Blocked: {s['failed']}")
    print(f"{LINE}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n {RED}[!] Cancelled.")
        sys.exit(0)

import os
import json
import time
import random
import sys
import re
from core.session_builder import create_http_session, build_request_context, setup_session_cookies
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
            data = json.load(f)
            # Filter out demo accounts
            return {k: v for k, v in data.items() if "example" not in v.get('identifier', '') and "017XXXXXXXX" not in v.get('identifier', '')}
    except json.JSONDecodeError:
        return {}

def _search(pattern, text):
    m = re.search(pattern, text)
    return m.group(1) if m else None

def attempt_otp_resend(session, account_identifier, server="m.facebook.com", ctx=None):
    """
    Attempts to resend OTP using the session and cookies.
    This mimics the behavior of clicking 'Resend Code' on the verification page.
    """
    headers = ctx["base_headers"] if ctx else {}
    headers.update({
        'Referer': f"https://{server}/confirmemail.php",
        'X-Requested-With': 'XMLHttpRequest'
    })
    
    try:
        # Step 1: Visit confirm page to see current state and get tokens
        confirm_url = f"https://{server}/confirmemail.php"
        res1 = session.get(confirm_url, headers=headers)
        
        # Check if we are already logged in but need confirmation
        if "confirm" not in res1.url and "checkpoint" not in res1.text:
            # If not on confirm page, try to reach it via recover
            identify_url = f"https://{server}/login/identify/?ctx=recover"
            res1 = session.get(identify_url, headers=headers)

        lsd = _search(r'name="lsd" value="([^"]+)"', res1.text)
        jazoest = _search(r'name="jazoest" value="([^"]+)"', res1.text)
        
        if not lsd:
            return False, "Security Token (LSD) Missing. Session might be expired."

        # Step 2: Search/Identify the account if needed
        # (This part uses the same logic as the registration tool's search)
        search_url = f"https://{server}/login/identify/?ctx=recover&search_attempts=1"
        data = {
            'lsd': lsd,
            'jazoest': jazoest,
            'email': account_identifier,
            'did_submit': 'Search'
        }
        res2 = session.post(search_url, data=data, headers=headers, allow_redirects=True)
        
        # Step 3: Trigger Resend / Send Code
        # We look for the 'resend' or 'send_code' action
        lsd = _search(r'name="lsd" value="([^"]+)"', res2.text) or lsd
        
        # Current Facebook OTP Resend Endpoint (2026)
        # It often uses /recover/initiate/ or /confirmemail.php with specific params
        resend_url = f"https://{server}/recover/initiate/"
        
        # Find available recovery method
        recover_method = _search(r'name="recover_method" value="([^"]+)"', res2.text)
        if not recover_method:
             # Try alternative: confirmemail.php resend
             resend_url = f"https://{server}/confirmemail.php?next=https%3A%2F%2F{server}%2F&rd"
             data = {
                 'lsd': lsd,
                 'jazoest': jazoest,
                 'resend': '1'
             }
        else:
            data = {
                'lsd': lsd,
                'jazoest': jazoest,
                'recover_method': recover_method,
                'reset_action': 'Send Code'
            }

        res3 = session.post(resend_url, data=data, headers=headers, allow_redirects=True)
        
        # Step 4: Final Verification
        if "code" in res3.text.lower() or "sent" in res3.text.lower() or "/recover/code/" in res3.url:
            return True, f"OTP Sent Successfully! (Method: {recover_method if 'recover_method' in locals() else 'Direct'})"
        elif "checkpoint" in res3.text.lower():
            return False, "Account Checkpoint triggered."
        elif "try again later" in res3.text.lower():
            return False, "Rate Limited by Facebook."
        else:
            return False, "Request failed to trigger OTP."

    except Exception as e:
        return False, f"Exception: {str(e)[:40]}"

def main():
    logo()
    print(f" {GREEN}[●] {WHITE}Facebook OTP Resend Tool - Session Based")
    print(f" {GREEN}[●] {WHITE}Using cookies from successful registrations...")
    print(f"{LINE}")
    
    accounts = load_accounts()
    if not accounts:
        print(f" {RED}[!] No valid accounts found. Please run registration first.")
        return

    counter = Counter()
    device_type = "Android"
    server = "m.facebook.com"
    locale = "en_US"

    # Process accounts
    for account_name, data in accounts.items():
        identifier = data.get('identifier')
        cookies_data = data.get('cookies')
        
        print(f" {CYAN}[*] Processing Account: {identifier}")
        
        try:
            session = create_http_session(device_type)
            setup_session_cookies(session, device_type)
            
            # Load account cookies
            for k, v in cookies_data.items():
                session.cookies.set(k, v)
            
            ctx = build_request_context(device_type, "Default", locale)
            
            success, message = attempt_otp_resend(session, identifier, server, ctx)
            
            if success:
                counter.update("success", number=identifier, message=message, color=GREEN)
            else:
                counter.update("failed", number=identifier, message=message, color=YELLOW)
                
        except Exception as e:
            counter.update("error", number=identifier, message=str(e)[:40], color=RED)

        # Human-like delay
        time.sleep(random.uniform(5, 10))

    print(f"\n{LINE}")
    s = counter.summary()
    print(f" {GREEN}[●] {WHITE}Total: {s['checked']} | {GREEN}Success: {s['success']} | {RED}Failed: {s['failed']}")
    print(f"{LINE}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n {RED}[!] Stopped.")
        sys.exit(0)

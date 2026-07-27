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
    """
    headers = ctx["base_headers"] if ctx else {}
    headers.update({
        'Referer': f"https://{server}/confirmemail.php",
        'X-Requested-With': 'XMLHttpRequest',
        'Accept': '*/*'
    })
    
    try:
        # Step 1: Visit confirm page to get tokens
        confirm_url = f"https://{server}/confirmemail.php"
        res1 = session.get(confirm_url, headers=headers)
        
        # Enhanced Token Extraction (JSON structure detection)
        lsd = _search(r'\"LSD\",\[\],\{\"token\":\"([^\"]+)\"', res1.text) or _search(r'name=\"lsd\" value=\"([^\"]+)\"', res1.text)
        jazoest = _search(r'\"jazoest\":\"([^\"]+)\"', res1.text) or _search(r'name=\"jazoest\" value=\"([^\"]+)\"', res1.text) or "21049"
        
        if not lsd:
            # Fallback search
            lsd = _search(r'lsd=([^&\" ]+)', res1.text)
            
        if not lsd:
            return False, "Security Token (LSD) Missing. Session might be restricted."

        # Step 2: Trigger Resend
        # We use the direct resend endpoint found during analysis
        resend_url = f"https://{server}/confirmemail.php?next=https%3A%2F%2F{server}%2F&rd"
        data = {
            'lsd': lsd,
            'jazoest': jazoest,
            'resend': '1'
        }

        res2 = session.post(resend_url, data=data, headers=headers, allow_redirects=True)
        
        # Step 3: Verify Success
        # Look for confirmation in the response
        if res2.status_code == 200:
            if any(x in res2.text.lower() for x in ["code", "sent", "envoyé", "confirm"]):
                return True, "OTP Resend Request Triggered!"
            elif "checkpoint" in res2.text.lower():
                return False, "Account Checkpoint (Security Blocked)."
            else:
                return False, "Request submitted but state unchanged."
        else:
            return False, f"Failed with HTTP {res2.status_code}"

    except Exception as e:
        return False, f"Error: {str(e)[:40]}"

def main():
    logo()
    print(f" {GREEN}[●] {WHITE}Facebook OTP Resend Tool - Session Based (v2)")
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

    for account_name, data in accounts.items():
        identifier = data.get('identifier')
        cookies_data = data.get('cookies')
        
        print(f" {CYAN}[*] Processing Account: {identifier}")
        
        try:
            session = create_http_session(device_type)
            setup_session_cookies(session, device_type)
            
            # Load account cookies
            for k, v in cookies_data.items():
                session.cookies.set(k, v, domain=".facebook.com")
            
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

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
    Attempts to resend OTP using synchronized session and advanced error detection.
    """
    headers = ctx["base_headers"] if ctx else {}
    headers.update({
        'Referer': f"https://{server}/confirmemail.php",
        'X-Requested-With': 'XMLHttpRequest',
        'Accept': '*/*'
    })
    
    try:
        # Step 1: Visit confirm page to get fresh tokens
        confirm_url = f"https://{server}/confirmemail.php"
        res1 = session.get(confirm_url, headers=headers)
        
        # Enhanced Token Extraction from JSON structure
        lsd = _search(r'\"LSD\",\[\],\{\"token\":\"([^\"]+)\"', res1.text) or _search(r'name=\"lsd\" value=\"([^\"]+)\"', res1.text)
        jazoest = _search(r'\"jazoest\":\"([^\"]+)\"', res1.text) or _search(r'name=\"jazoest\" value=\"([^\"]+)\"', res1.text) or "21049"
        
        if not lsd:
            return False, "Security Token (LSD) Missing. Device or Proxy might be blocked."

        # Step 2: Trigger Resend Request
        resend_url = f"https://{server}/confirmemail.php?next=https%3A%2F%2F{server}%2F&rd"
        data = {
            'lsd': lsd,
            'jazoest': jazoest,
            'resend': '1'
        }

        res2 = session.post(resend_url, data=data, headers=headers, allow_redirects=True)
        
        # Step 3: Advanced Success/Failure Detection
        body = res2.text.lower()
        
        # Check for Silent Failures (Common in 2026)
        if "erreur" in body or "error" in body or "title>erreur" in body:
            return False, "Silent Failure: Facebook rejected the request (Device/IP mismatch)."
        
        if "checkpoint" in body:
            return False, "Account Checkpoint: Security block triggered."
        
        if "try again later" in body or "réessayez plus tard" in body:
            return False, "Rate Limited: Too many requests from this IP."

        # Check for Success Indicators
        if any(x in body for x in ["code", "sent", "envoyé", "confirm", "vérification"]):
            # Double check if we are on the code entry page
            if "/recover/code/" in res2.url or "n=" in res2.url or "code" in body:
                return True, "OTP Sent Successfully! (Confirmed by response body)"
        
        return False, "Request submitted but no confirmation detected."

    except Exception as e:
        return False, f"Exception: {str(e)[:40]}"

def main():
    logo()
    print(f" {GREEN}[●] {WHITE}Facebook OTP Tool - Precise Sync Mode (2026)")
    print(f" {GREEN}[●] {WHITE}Synchronizing with Registration Device Config...")
    print(f"{LINE}")
    
    accounts = load_accounts()
    if not accounts:
        print(f" {RED}[!] No valid accounts found. Please run registration first.")
        return

    counter = Counter()
    
    # Process accounts (Newest first)
    account_items = list(accounts.items())
    account_items.reverse()

    for account_name, data in account_items:
        identifier = data.get('identifier')
        cookies_data = data.get('cookies')
        config = data.get('config', {}) # Load saved config from registration
        
        # Sync with registration config or use defaults
        device_type = config.get('device_type', 'Android')
        browser_type = config.get('browser_type', 'Default')
        server = config.get('server', 'm.facebook.com')
        locale = config.get('locale', 'en_US')

        print(f" {CYAN}[*] Target: {identifier} | Device: {device_type} | Server: {server}")
        
        try:
            # Create session with SAME device type as registration
            session = create_http_session(device_type)
            setup_session_cookies(session, device_type)
            
            # Load account cookies
            for k, v in cookies_data.items():
                session.cookies.set(k, v, domain=".facebook.com")
            
            ctx = build_request_context(device_type, browser_type, locale)
            
            success, message = attempt_otp_resend(session, identifier, server, ctx)
            
            if success:
                counter.update("success", number=identifier, message=message, color=GREEN)
            else:
                color = RED if "Failure" in message or "Exception" in message else YELLOW
                counter.update("failed", number=identifier, message=message, color=color)
                
        except Exception as e:
            counter.update("error", number=identifier, message=str(e)[:40], color=RED)

        # Random human-like delay
        time.sleep(random.uniform(6, 12))

    print(f"\n{LINE}")
    s = counter.summary()
    print(f" {GREEN}[●] {WHITE}Total: {s['checked']} | {GREEN}Sent: {s['success']} | {RED}Failed: {s['failed']}")
    print(f"{LINE}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n {RED}[!] Stopped.")
        sys.exit(0)

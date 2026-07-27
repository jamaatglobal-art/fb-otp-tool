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
    Attempts an OTP request using advanced detection and fallback endpoints.
    """
    headers = ctx["base_headers"] if ctx else {}
    # Ensure Referer is set to avoid some security checks
    headers['Referer'] = f"https://{server}/"
    
    try:
        # Step 1: Visit initial page to get session tokens
        # We try a few different endpoints if one fails
        endpoints = [
            f"https://{server}/login/identify/?ctx=recover",
            f"https://{server}/recover/initiate/",
            f"https://{server}/login/device-based/password/reset/"
        ]
        
        res1 = None
        for url in endpoints:
            try:
                res1 = session.get(url, headers=headers, timeout=10)
                if 'name="lsd"' in res1.text:
                    break
            except:
                continue
        
        if not res1 or 'name="lsd"' not in res1.text:
            return False, "Failed to fetch security tokens (LSD missing)."

        lsd = _search(r'name="lsd" value="([^"]+)"', res1.text)
        jazoest = _search(r'name="jazoest" value="([^"]+)"', res1.text)
        
        # Step 2: Search for the account
        # Use mbasic for better reliability in scraping if m.facebook fails
        search_url = f"https://{server}/login/identify/?ctx=recover&search_attempts=1"
        data = {
            'lsd': lsd,
            'jazoest': jazoest,
            'email': account_identifier,
            'did_submit': 'Search'
        }
        
        # Update headers for POST
        post_headers = headers.copy()
        post_headers['Content-Type'] = 'application/x-www-form-urlencoded'
        
        res2 = session.post(search_url, data=data, headers=post_headers, allow_redirects=True)
        
        if "identify_search_error" in res2.text or "Account not found" in res2.text:
            return False, "Account not found or Search Limit reached."

        # Step 3: Extract recovery method
        # Look for SMS or Email recovery options
        # Pattern for recover_method usually looks like "send_email", "send_sms", "send_whatsapp"
        methods = re.findall(r'name="recover_method" value="([^"]+)"', res2.text)
        
        if not methods:
            # Fallback: Check if we are already on a page that says "We sent a code"
            if "code" in res2.text.lower() and "sent" in res2.text.lower():
                return True, "OTP already sent (Detected in response)."
            return False, "No recovery method (SMS/Email) found. Account might be locked."

        # Try the first available method (usually SMS or Email)
        recover_method = methods[0]
        
        # Get new tokens from the current page
        lsd = _search(r'name="lsd" value="([^"]+)"', res2.text) or lsd
        jazoest = _search(r'name="jazoest" value="([^"]+)"', res2.text) or jazoest
        
        # Step 4: Final Trigger
        initiate_url = f"https://{server}/recover/initiate/"
        data = {
            'lsd': lsd,
            'jazoest': jazoest,
            'recover_method': recover_method,
            'reset_action': 'Send Code'
        }
        
        res3 = session.post(initiate_url, data=data, headers=post_headers, allow_redirects=True)
        
        # Step 5: Verify
        if res3.status_code == 200:
            if any(x in res3.text.lower() for x in ["enter code", "confirm your account", "we sent a code"]):
                return True, f"OTP Sent successfully via {recover_method}!"
            elif "checkpoint" in res3.text.lower():
                return False, "Account Checkpoint (Security Blocked)."
            elif "try again later" in res3.text.lower():
                return False, "Rate Limited: Try again later."
            else:
                # Sometimes it sends but the text is different
                if "/recover/code/" in res3.url:
                    return True, f"OTP Sent (Redirected to code entry)."
                return False, "Sent but confirmation not detected."
        else:
            return False, f"Final Request Failed (HTTP {res3.status_code})"

    except Exception as e:
        return False, f"Error: {str(e)[:40]}"

def main():
    logo()
    print(f" {GREEN}[●] {WHITE}Facebook OTP Tool - Precise Mode (2026)")
    print(f" {GREEN}[●] {WHITE}Analyzing and Sending OTP...")
    print(f"{LINE}")
    
    accounts = load_accounts()
    if not accounts:
        print(f" {RED}[!] No accounts found in {ACCOUNTS_FILE}")
        return

    counter = Counter()
    device_type = "Android"
    browser_type = "Default"
    server = "m.facebook.com"
    locale = "en_US"

    # Process accounts in reverse order (newest first)
    account_items = list(accounts.items())
    account_items.reverse()

    for account_name, data in account_items:
        identifier = data.get('identifier')
        cookies_data = data.get('cookies')
        
        if not identifier or not cookies_data:
            continue

        print(f" {CYAN}[*] Target: {identifier}")
        
        try:
            # Use curl_cffi for real TLS fingerprinting
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
                color = RED if "LSD" in message or "Error" in message else YELLOW
                counter.update("failed", number=identifier, message=message, color=color)
                
        except Exception as e:
            counter.update("error", number=identifier, message=str(e)[:40], color=RED)

        # Random human-like delay
        time.sleep(random.uniform(4, 8))

    print(f"\n{LINE}")
    s = counter.summary()
    print(f" {GREEN}[●] {WHITE}Total: {s['checked']} | {GREEN}Sent: {s['success']} | {RED}Failed: {s['failed']}")
    print(f"{LINE}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n {RED}[!] Cancelled.")
        sys.exit(0)

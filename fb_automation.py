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
            return {k: v for k, v in data.items() if "example" not in v.get('identifier', '') and "017XXXXXXXX" not in v.get('identifier', '')}
    except json.JSONDecodeError:
        return {}

def _search(pattern, text):
    m = re.search(pattern, text)
    return m.group(1) if m else None

def attempt_otp_resend(session, account_identifier, server="m.facebook.com", ctx=None, resend_count=1):
    """
    Attempts to resend OTP using synchronized session, proxy, and advanced detection.
    """
    headers = ctx["base_headers"] if ctx else {}
    headers.update({
        'Referer': f"https://{server}/confirmemail.php",
        'X-Requested-With': 'XMLHttpRequest',
        'Accept': '*/*',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Dest': 'empty'
    })
    
    success_count = 0
    
    try:
        for i in range(resend_count):
            if i > 0:
                # Human Behavior: Wait between resends
                time.sleep(random.uniform(3, 7))
            
            # Step 1: Visit confirm page (Human Behavior: visit main page/confirm page first)
            confirm_url = f"https://{server}/confirmemail.php"
            res1 = session.get(confirm_url, headers=headers)
            
            # Dynamic Token Parsing (Enhanced Regex + JSON fallback)
            lsd = _search(r'\"LSD\",\[\],\{\"token\":\"([^\"]+)\"', res1.text) or \
                  _search(r'name=\"lsd\" value=\"([^\"]+)\"', res1.text) or \
                  _search(r'\"lsd\":\"([^\"]+)\"', res1.text)
                  
            jazoest = _search(r'\"jazoest\":\"([^\"]+)\"', res1.text) or \
                      _search(r'name=\"jazoest\" value=\"([^\"]+)\"', res1.text) or \
                      _search(r'jazoest=([0-9]+)', res1.text) or "21049"
            
            if not lsd:
                if i == 0: return False, "Security Token (LSD) Missing. Device or IP mismatch."
                else: break

            # Human Behavior: Wait before clicking resend
            time.sleep(random.uniform(2, 4))

            # Step 2: Trigger Resend (Using updated endpoints)
            # Some accounts use /recover/initiate for resend in newer updates
            resend_url = f"https://{server}/confirmemail.php?next=https%3A%2F%2F{server}%2F&rd"
            data = {
                'lsd': lsd,
                'jazoest': jazoest,
                'resend': '1'
            }

            res2 = session.post(resend_url, data=data, headers=headers, allow_redirects=True)
            
            # Step 3: Success/Failure Detection
            body = res2.text.lower()
            
            if "erreur" in body or "error" in body or "title>erreur" in body:
                if i == 0: return False, "Facebook rejected the request (Silent Failure)."
                else: break
            
            if "checkpoint" in body:
                if i == 0: return False, "Account Checkpoint: Security block."
                else: break
            
            if "try again later" in body or "réessayez plus tard" in body:
                if i == 0: return False, "Rate Limited: Try another IP."
                else: break

            if any(x in body for x in ["code", "sent", "envoyé", "confirm", "vérification"]) or "/recover/code/" in res2.url:
                success_count += 1
            else:
                if i == 0: return False, "Sent but confirmation not detected."
                else: break
        
        if success_count > 0:
            return True, f"OTP Sent Successfully {success_count} times!"
        return False, "Failed to send OTP."

    except Exception as e:
        return False, f"Exception: {str(e)[:40]}"

def main():
    logo()
    print(f" {GREEN}[●] {WHITE}Facebook OTP Tool - Perfect Sync Mode (2026)")
    print(f" {GREEN}[●] {WHITE}Syncing Proxy, Device & Headers...")
    print(f"{LINE}")
    
    accounts = load_accounts()
    if not accounts:
        print(f" {RED}[!] No valid accounts found. Please run registration first.")
        return

    counter = Counter()
    account_items = list(accounts.items())
    account_items.reverse()

    # Ask user for resend count
    try:
        resend_input = input(f" {GREEN}[●] {WHITE}How many OTP resends per account? (Default 1): ").strip()
        resend_count = int(resend_input) if resend_input.isdigit() else 1
    except Exception:
        resend_count = 1

    for account_name, data in account_items:
        identifier = data.get('identifier')
        cookies_data = data.get('cookies')
        config = data.get('config', {})
        
        device_type = config.get('device_type', 'Android')
        browser_type = config.get('browser_type', 'Default')
        server = config.get('server', 'm.facebook.com')
        locale = config.get('locale', 'en_US')
        proxy_data = config.get('proxy_data', None) # Load saved proxy

        print(f" {CYAN}[*] Target: {identifier} | Device: {device_type}")
        
        try:
            # Sync Proxy
            proxy_dict = format_proxy_for_requests(proxy_data) if proxy_data else None
            if proxy_dict:
                print(f" {YELLOW}[*] Using Sync Proxy: {proxy_data.get('proxy', '...')}")
            
        # Create session with SAME device and proxy
        session = create_http_session(device_type, proxy_dict)
        
        # Load persisted screen metrics
        screen_res = config.get('screen_res', '720x1280')
        session.cookies.update({"m_pixel_ratio": "1", "wd": screen_res})
        
        for k, v in cookies_data.items():
            session.cookies.set(k, v, domain=".facebook.com")
        
        # Use persisted headers for Full Header Mirroring
        persisted_headers = config.get('headers')
        if persisted_headers:
            ctx = {"base_headers": persisted_headers}
        else:
            ctx = build_request_context(device_type, browser_type, locale)
        
            success, message = attempt_otp_resend(session, identifier, server, ctx, resend_count)
            
            if success:
                counter.update("success", number=identifier, message=message, color=GREEN)
            else:
                counter.update("failed", number=identifier, message=message, color=RED if "Failure" in message else YELLOW)
                
        except Exception as e:
            counter.update("error", number=identifier, message=str(e)[:40], color=RED)

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

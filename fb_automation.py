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
    Attempts to resend OTP using synchronized session, mirroring registration methods.
    """
    base_headers = ctx["base_headers"] if ctx else {}
    
    success_count = 0
    
    try:
        for i in range(resend_count):
            if i > 0:
                time.sleep(random.uniform(5, 10))
            
            # Step 1: Visit confirm page to get fresh tokens (with retry for Proxy CONN errors)
            confirm_url = f"https://{server}/confirmemail.php"
            res1 = None
            for retry in range(3):
                try:
                    res1 = session.get(confirm_url, headers=base_headers, timeout=30)
                    break
                except Exception as e:
                    if "curl: (56)" in str(e) and retry < 2:
                        time.sleep(2)
                        continue
                    raise e
            
            html = res1.text
            
            # Mirror Registration: Extract all dynamic tokens (Enhanced for OTP page)
            lsd = _search(r'name="lsd" value="([^"]+)"', html) or \
                  _search(r'"lsd":"([^"]+)"', html) or \
                  _search(r'\["LSD",\[\],\{"token":"([^"]+)"\}', html) or \
                  _search(r'LSD.*?token":"([^"]+)"', html)
                  
            jazoest = _search(r'name="jazoest" value="([^"]+)"', html) or \
                      _search(r'"jazoest":"([^"]+)"', html) or \
                      _search(r'jazoest=([0-9]+)', html) or "21049"
                      
            fb_dtsg = _search(r'name="fb_dtsg" value="([^"]+)"', html) or \
                      _search(r'"dtsg"\s*:\s*\{\s*"token"\s*:\s*"([^"]+)"', html) or \
                      _search(r'"fb_dtsg":"([^"]+)"', html)
                      
            encrypted_token = _search(r'"encrypted"\s*:\s*"([^"]+)"', html) or \
                               _search(r'name="encrypted" value="([^"]+)"', html)
            
            if not lsd or not fb_dtsg:
                # If LSD is missing but we have DTSG, try to fallback to cookies if possible or report clearly
                return False, f"Token Missing (LSD: {'OK' if lsd else 'NO'}, DTSG: {'OK' if fb_dtsg else 'NO'})"

            # Mirror Registration: Setup AJAX/JSONStream headers
            post_headers = dict(base_headers)
            post_headers.update({
                'accept': '*/*',
                'content-type': 'application/x-www-form-urlencoded',
                'origin': f'https://{server}',
                'referer': confirm_url,
                'x-fb-lsd': lsd,
                'x-requested-with': 'XMLHttpRequest',
                'x-response-format': 'JSONStream',
            })
            post_headers.pop('upgrade-insecure-requests', None)
            
            # Mirror Registration: Setup data with dynamic parameters
            data = {
                'lsd': lsd,
                'jazoest': jazoest,
                'fb_dtsg': fb_dtsg,
                'contact': account_identifier,
                'resend': '1',
                '__user': session.cookies.get("c_user", "0"),
                '__a': encrypted_token if encrypted_token else "",
                '__req': 'r',
                '__fmt': '1',
            }

            # Step 2: POST resend with mirrored registration logic
            resend_url = f"https://{server}/confirmemail.php?next=https%3A%2F%2F{server}%2F&rd"
            res2 = session.post(resend_url, data=data, headers=post_headers, allow_redirects=True)
            
            # Step 3: Advanced Detection & Error Reporting
            body = res2.text
            body_lower = body.lower()
            
            # If it's a JSONStream response, try to parse the actual error
            error_msg = None
            if "for (;;);" in body:
                try:
                    clean_json = body.split("for (;;);")[1]
                    json_data = json.loads(clean_json)
                    # Extract error from Facebook JSON response
                    if "error" in json_data:
                        error_msg = json_data.get("errorDescription") or json_data.get("errorMessage") or str(json_data["error"])
                    elif "payload" in json_data and "error" in str(json_data["payload"]):
                        error_msg = "Facebook Payload Error"
                except:
                    pass

            if error_msg:
                return False, f"FB Error: {error_msg}"
            
            if "checkpoint" in body_lower:
                return False, "Checkpoint: Security Block"
            
            if "try again later" in body_lower or "réessayez plus tard" in body_lower:
                return False, "Rate Limited (Spam Block)"

            if any(x in body_lower for x in ["code", "sent", "envoyé", "confirm", "vérification"]) or "/recover/code/" in res2.url:
                success_count += 1
            else:
                # Fallback to general error if no success indicator
                snippet = body.replace('\n', ' ')[:100]
                return False, f"Rejected: {snippet}..."
        
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
            # proxy_data already contains the structured proxy info
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

import time
import itertools
import os
import random
from concurrent.futures import ThreadPoolExecutor
import requests
from urllib.parse import urlparse, quote
from ui.colors import GREEN, RED, WHITE, EKL, YELLOW
from core.settings_manager import load_settings
from core.locale_data import get_locale, get_timezone, get_language

FALLBACK_IP_INFO = {"country": "United States", "countryCode": "US", "timezone": "America/New_York"}
PROXIES_FILE = "proxies.txt"

# Parse proxy string into structured dict (supports ip:port, ip:port:user:pass)
def parse_proxy(proxy_str):
    proxy_str = proxy_str.strip()
    if not proxy_str:
        return None
        
    parts = proxy_str.split(":")
    if len(parts) == 2:
        ip, port = parts
        return {"http": f"http://{ip}:{port}", "https": f"http://{ip}:{port}", "username": None, "password": None}
    elif len(parts) >= 4:
        ip, port, user = parts[0], parts[1], parts[2]
        password = ":".join(parts[3:])
        return {"http": f"http://{ip}:{port}", "https": f"http://{ip}:{port}", "username": user, "password": password}
    return None

# Fetch geolocation info for a proxy
def get_ip_info(proxies=None, retries=1):
    for attempt in range(retries + 1):
        try:
            r = requests.get("http://ip-api.com/json/", proxies=proxies, timeout=10)
            if r.status_code == 200:
                data = r.json()
                return {
                    "country": data.get("country", "Unknown"),
                    "countryCode": data.get("countryCode", "US"),
                    "timezone": data.get("timezone", "Unknown")
                }
        except Exception:
            pass
        if attempt < retries:
            time.sleep(1)
    return None

# Build proxy data with locale and targeting
def build_proxy_data(proxy_dict, country_target=None):
    req_proxies = format_proxy_for_requests({"proxy": proxy_dict})
    
    # Apply targeting if it's a dynamic residential proxy
    # Based on the user's example: Change6.owlproxy.com:7778:USER_custom_zone_CF_country_cf_sid_08672854_time_15:PASS
    if proxy_dict.get("username") and country_target:
        user = proxy_dict["username"]
        # Replace country target in username if present, or append it
        # This is a heuristic based on the user's provided format
        if "_country_" in user:
            parts = user.split("_country_")
            prefix = parts[0]
            suffix = "_".join(parts[1].split("_")[1:]) # skip the old country code
            new_user = f"{prefix}_country_{country_target.lower()}_{suffix}"
            proxy_dict["username"] = new_user
        
        # Refresh req_proxies with new username
        req_proxies = format_proxy_for_requests({"proxy": proxy_dict})

    info = get_ip_info(req_proxies)
    if info is None:
        info = FALLBACK_IP_INFO
        
    cc = info["countryCode"]
    return {
        "proxy": proxy_dict,
        "country": info["country"],
        "country_code": cc,
        "locale": get_locale(cc),
        "timezone": get_timezone(cc),
        "language": get_language(cc),
        "ip_timezone": info["timezone"]
    }

# Load proxies from proxies.txt
def load_proxies_from_file():
    if not os.path.exists(PROXIES_FILE):
        return []
    with open(PROXIES_FILE, "r") as f:
        lines = f.readlines()
    
    proxies = []
    for line in lines:
        parsed = parse_proxy(line)
        if parsed:
            proxies.append(parsed)
    return proxies

# Main proxy handler for registration
def get_proxy_list(config_state=None, render_callback=None):
    proxies_from_file = load_proxies_from_file()
    
    if not proxies_from_file:
        print(f" {YELLOW}[!] {PROXIES_FILE} not found or empty. Using Direct IP.")
        if config_state is not None:
            config_state["proxy"] = "Direct (No File)"
        return []

    # Ask if user wants to use proxy
    if render_callback:
        render_callback()
    
    choice = input(f" {GREEN}[{RED}●{GREEN}] Use Proxy from {PROXIES_FILE}? (y/n): {EKL} ").strip().lower()
    
    if choice != 'y':
        if config_state is not None:
            config_state["proxy"] = "Direct (User Skipped)"
        return []

    if config_state is not None:
        config_state["proxy"] = f"Loaded {len(proxies_from_file)} from file"
    
    return proxies_from_file

# Format proxy for requests
def format_proxy_for_requests(proxy_data):
    if not proxy_data or not proxy_data.get("proxy"):
        return None
    
    p = proxy_data["proxy"]
    user = p.get("username")
    password = p.get("password")
    url = p.get("http")
    
    if user and password:
        parsed = urlparse(url)
        auth_url = f"{parsed.scheme}://{quote(user)}:{quote(password)}@{parsed.netloc}"
        return {"http": auth_url, "https": auth_url}
    return {"http": url, "https": url}

# Function to get sticky session IP for a thread
def get_sticky_proxy(base_proxy, country_code, thread_id):
    """
    Customizes a dynamic proxy for a specific thread/session.
    Adds state target and unique session ID.
    """
    proxy = base_proxy.copy()
    user = proxy.get("username")
    if not user:
        return proxy
        
    # Example: BUm5A89KAN40_custom_zone_CF_country_cf_sid_08672854_time_15
    # We will inject/update country and session ID
    
    # 1. Ensure country is correct
    if "_country_" in user:
        parts = user.split("_country_")
        prefix = parts[0]
        rest = "_".join(parts[1].split("_")[1:])
        user = f"{prefix}_country_{country_code.lower()}_{rest}"
    
    # 2. Inject/Update Session ID (sid) for stickiness
    session_id = f"{int(time.time())}{thread_id}{random.randint(100, 999)}"
    if "_sid_" in user:
        parts = user.split("_sid_")
        prefix = parts[0]
        rest = "_".join(parts[1].split("_")[1:])
        user = f"{prefix}_sid_{session_id}_{rest}"
    else:
        user = f"{user}_sid_{session_id}"
        
    proxy["username"] = user
    return proxy

def get_no_proxy_data():
    info = get_ip_info(None)
    if info is None:
        info = FALLBACK_IP_INFO
    cc = info["countryCode"]
    return {
        "proxy": None,
        "country": info["country"],
        "country_code": cc,
        "locale": get_locale(cc),
        "timezone": get_timezone(cc),
        "language": get_language(cc),
        "ip_timezone": info["timezone"]
    }

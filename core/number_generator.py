import requests
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from ui.colors import GREEN, RED, WHITE, YELLOW, CYAN, MAGENTA, RESET, LINE

# --- CONFIGURATION ---
BASE_URL = "https://api.zenexnetwork.com"
API_KEY = "ZNX_V48FVLSI120KMM2WW09V5726"

HEADERS = {
    "mapikey": API_KEY,
    "Content-Type": "application/json"
}

def get_number(range_prefix, silent=True):
    url = f"{BASE_URL}/v1/getnum"
    payload = {
        "range": range_prefix,
        "is_national": False,
        "remove_plus": False
    }
    try:
        response = requests.post(url, headers=HEADERS, json=payload, timeout=10)
        if response.status_code == 200:
            res_data = response.json()
            if res_data.get("meta", {}).get("status") == "success":
                return res_data.get("data", {})
    except Exception:
        pass
    return None

def run_multi_range_allocator():
    print(f"\n{LINE}")
    print(f" {YELLOW}[●] {WHITE}Multi-Range Bulk Allocator (Zenex API)")
    print(f"{LINE}")
    
    raw_prefixes = input(f" {YELLOW}[?] Enter Ranges/Prefixes (Comma separated, e.g., 447384XXX): {RESET}").strip()
    if not raw_prefixes:
        print(f" {RED}[⚠️] Ranges cannot be empty!{RESET}")
        return False

    prefixes = [p.strip() for p in raw_prefixes.split(",") if p.strip()]

    count_input = input(f" {YELLOW}[?] Total How Many Numbers Do You Want? (e.g., 100): {RESET}").strip()
    try:
        total_count = int(count_input)
    except ValueError:
        print(f" {RED}[⚠️] Invalid number amount!{RESET}")
        return False

    thread_input = input(f" {YELLOW}[?] Enter Thread Count (Recommended: 10-30): {RESET}").strip()
    try:
        threads = int(thread_input)
    except ValueError:
        threads = 15

    print(f"\n {CYAN}[⏳] Allocating {total_count} numbers using {threads} threads...{RESET}")
    allocated_numbers = []
    completed = 0

    with ThreadPoolExecutor(max_workers=threads) as executor:
        futures = []
        for i in range(total_count):
            current_prefix = prefixes[i % len(prefixes)]
            futures.append(executor.submit(get_number, current_prefix, silent=True))
        
        for future in as_completed(futures):
            completed += 1
            sys.stdout.write(f"\r {WHITE}[⏳] Progress: {completed}/{total_count} processed...{RESET}")
            sys.stdout.flush()
            
            try:
                num_info = future.result()
                if num_info and num_info.get('full_number'):
                    allocated_numbers.append(num_info.get('full_number'))
            except Exception:
                pass

    print("\n")
    if allocated_numbers:
        print(f" {GREEN}[✅] Successfully Allocated {len(allocated_numbers)} Numbers.{RESET}")
        
        # Save to Number_List.txt
        with open("Number_List.txt", "w") as f:
            for num in allocated_numbers:
                f.write(f"{num}\n")
        
        print(f" {GREEN}[✅] Numbers saved to Number_List.txt automatically.{RESET}")
        time.sleep(2)
        return True
    else:
        print(f" {RED}[❌] No numbers could be allocated.{RESET}")
        return False

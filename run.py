import os
import sys
import time
from ui.logo import logo
from ui.colors import GREEN, RED, WHITE, YELLOW, CYAN, LINE

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def main():
    while True:
        clear()
        logo()
        print(f" {GREEN}[*] {WHITE}Welcome to FB Automation Suite (Upgraded)")
        print(f" {GREEN}[1] {WHITE}Start Registration -> Auto-Save Cookies -> Run OTP Tool")
        print(f" {GREEN}[2] {WHITE}Run OTP Tool Only (Using saved accounts.json)")
        print(f" {GREEN}[0] {WHITE}Exit")
        print(f"{LINE}")
        
        choice = input(f" {CYAN}Select Option: {WHITE}")
        
        if choice == '1':
            clear()
            logo()
            print(f"\n {YELLOW}[*] Phase 1: Starting Facebook Account Registration...")
            print(f" {WHITE}After finishing, cookies will be saved automatically to accounts.json.")
            print(f"{LINE}\n")
            time.sleep(2)
            
            # Run the registration tool
            # Assuming main.py is the entry point for registration
            os.system('python3 main.py')
            
            print(f"\n\n{LINE}")
            print(f" {GREEN}[✔] Registration Session Finished.")
            print(f" {GREEN}[✔] Cookies saved to accounts.json automatically.")
            print(f"{LINE}")
            
            print(f"\n {YELLOW}[*] Phase 2: Auto-starting OTP Tool...")
            time.sleep(1)
            os.system('python3 fb_automation.py')
            input(f"\n {WHITE}Process completed. Press Enter to return to menu...")
            
        elif choice == '2':
            clear()
            logo()
            print(f"\n {YELLOW}[*] Starting OTP Tool only...")
            time.sleep(1)
            os.system('python3 fb_automation.py')
            input(f"\n {WHITE}Press Enter to return to menu...")
            
        elif choice == '0':
            print(f" {RED}Exiting...")
            break
        else:
            print(f" {RED}Invalid Choice!")
            time.sleep(1)

if __name__ == "__main__":
    # Ensure dependencies are checked
    try:
        import curl_cffi
        import faker
    except ImportError:
        print(f" {YELLOW}[!] Installing missing dependencies...")
        os.system('pip install curl_cffi faker requests')
    
    # Ensure we are in the right directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    main()

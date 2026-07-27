import os
import sys
import time
from ui.logo import logo
from ui.colors import GREEN, RED, WHITE, YELLOW, CYAN, LINE

def main():
    while True:
        logo()
        print(f" {GREEN}[1] {WHITE}Run Facebook Account Registration")
        print(f" {GREEN}[2] {WHITE}Run Facebook OTP Tool (Send Codes)")
        print(f" {GREEN}[0] {WHITE}Exit")
        print(f"{LINE}")
        
        choice = input(f" {CYAN}Select Option: {WHITE}")
        
        if choice == '1':
            print(f"\n {YELLOW}[*] Starting Registration Tool...")
            time.sleep(1)
            os.system('python3 main.py')
        elif choice == '2':
            print(f"\n {YELLOW}[*] Starting OTP Tool...")
            time.sleep(1)
            os.system('python3 fb_automation.py')
        elif choice == '0':
            print(f" {RED}Exiting...")
            break
        else:
            print(f" {RED}Invalid Choice!")
            time.sleep(1)

if __name__ == "__main__":
    # Ensure we are in the right directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Check for main.py (from registration repo)
    if not os.path.exists('main.py'):
        # Copy main.py if it's missing but we have the repo
        if os.path.exists('../facebook-account-registration/main.py'):
            os.system('cp ../facebook-account-registration/main.py .')
    
    main()

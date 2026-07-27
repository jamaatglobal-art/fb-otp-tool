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
            
            print(f" {CYAN}[1] {WHITE}Generate Numbers using Zenex API")
            print(f" {CYAN}[2] {WHITE}Use Existing Number_List.txt")
            print(f"{LINE}")
            sub_choice = input(f" {CYAN}Select Option: {WHITE}")
            
            if sub_choice == '1':
                # Phase 0: Number Generation
                from core.number_generator import run_multi_range_allocator
                success = run_multi_range_allocator()
                if not success:
                    input(f"\n {RED}[!] Number generation failed or skipped. Press Enter to return...")
                    continue
            elif sub_choice == '2':
                if not os.path.exists("Number_List.txt") or os.stat("Number_List.txt").st_size == 0:
                    print(f"\n {RED}[!] Number_List.txt is empty or missing! Please add numbers first.")
                    input(f"\n {WHITE}Press Enter to return...")
                    continue
                print(f"\n {GREEN}[✅] Using existing Number_List.txt")
            else:
                print(f"\n {RED}[!] Invalid Choice!")
                input(f"\n {WHITE}Press Enter to return...")
                continue
            
            print(f"\n {YELLOW}[*] Phase 1: Starting Facebook Account Registration...")
            print(f" {WHITE}After finishing, cookies will be saved automatically to accounts.json.")
            print(f"{LINE}\n")
            time.sleep(2)
            
            # Run the registration tool
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

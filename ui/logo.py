import os
import platform
from ui.colors import GREEN, CYAN, RED, ORANGE, LINE

VERSION = "1.0.0"


# Clear terminal screen (cross-platform)
def clear():
    if platform.system() == "Windows":
        os.system("cls")
    else:
        os.system("clear")


# Display the tool banner with ASCII art logo and info
def logo():
    clear()
    print(f"""{GREEN}
  ██╗  ██╗ █████╗ ██████╗  ██████╗ ██╗    ██╗ ██████╗ 
  ██║ ██╔╝██╔══██╗██╔══██╗██╔═══██╗██║    ██║██╔════╝ 
  █████╔╝ ███████║██████╔╝██║   ██║██║ █╗ ██║██║  ███╗
  ██╔═██╗ ██╔══██║██╔══██╗██║   ██║██║███╗██║██║   ██║
  ██║  ██╗██║  ██║██║  ██║╚██████╔╝╚███╔███╔╝╚██████╔╝
  ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝  ╚══╝╚══╝  ╚═════╝ {ORANGE}V-{VERSION}
{LINE}
 {GREEN}[{RED}●{GREEN}] TOOL OWNER   {CYAN}:{GREEN} @kabbopro
 {GREEN}[{RED}●{GREEN}] TOOL         {CYAN}:{GREEN} KABBO-PRO AUTO CREATE
 {GREEN}[{RED}●{GREEN}] TOOL STATUS  {CYAN}:{GREEN} PAID
{LINE}""")

# Facebook OTP Automation Tool

This is a Python-based tool designed for Termux to automate Facebook OTP requests using cookies and device rotation.

## Features
- **Cookie Management:** Uses browser cookies for session persistence.
- **Device Rotation:** Randomizes User-Agents and device profiles to mimic real mobile devices.
- **Termux Optimized:** Lightweight and easy to run on Android via Termux.
- **API Simulation:** Simulates mobile-app-like requests to bypass some security limits.

## Installation in Termux

1. Update packages:
   ```bash
   pkg update && pkg upgrade
   ```
2. Install Python and Git:
   ```bash
   pkg install python git
   ```
3. Clone the repository:
   ```bash
   git clone https://github.com/jamaatglobal-art/fb-otp-tool.git
   ```
4. Navigate to the directory:
   ```bash
   cd fb-otp-tool
   ```
5. Install requirements:
   ```bash
   pip install requests
   ```

## Usage

1. Open `fb_automation.py` and add your Facebook cookies in the `COOKIES` dictionary.
2. Run the tool:
   ```bash
   python fb_automation.py
   ```

## Disclaimer
**Warning:** This tool is for educational purposes only. Using automation on Facebook may violate their Terms of Service and lead to account suspension or permanent bans. Use at your own risk.

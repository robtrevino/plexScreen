import os
import time
import psutil
import GPUtil
import serial
import socket
import http.server
import socketserver
import urllib.parse
from plexapi.server import PlexServer
from plexapi.exceptions import Unauthorized
from dotenv import load_dotenv, set_key

# Load environment variables from .env file
load_dotenv()

# Configuration
PLEX_URL = os.getenv('PLEX_URL', 'http://localhost:32400')
PLEX_TOKEN = os.getenv('PLEX_TOKEN')
SERIAL_PORT = os.getenv('SERIAL_PORT', 'COM3')
LCD_BRIGHTNESS = int(os.getenv('LCD_BRIGHTNESS', '255'))
BAUD_RATE = 115200 # Higher baud rate for larger payloads
UPDATE_INTERVAL = 2  # Seconds
WEB_SERVER_PORT = 5000

def get_local_ip():
    try:
        # Create a dummy socket to find the local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

class TokenHandler(http.server.SimpleHTTPRequestHandler):
    new_token = None

    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            html = f"""
            <html>
                <body style="font-family: sans-serif; text-align: center; padding: 50px;">
                    <h2>Plex Status Setup</h2>
                    <p>Enter your <b>Plex Token</b> below:</p>
                    <form action="/save" method="GET">
                        <input type="text" name="token" style="width: 300px; padding: 10px;" required>
                        <br><br>
                        <input type="submit" value="Save Token" style="padding: 10px 20px; cursor: pointer;">
                    </form>
                    <p><small>Get yours at <a href="https://plex.tv" target="_blank">plex.tv</a></small></p>
                </body>
            </html>
            """
            self.wfile.write(html.encode())
        elif self.path.startswith('/save'):
            query = urllib.parse.urlparse(self.path).query
            params = urllib.parse.parse_qs(query)
            if 'token' in params:
                TokenHandler.new_token = params['token'][0]
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b"Token received! You can close this tab and check the LCD.")
                # We'll shut down the server in main
            else:
                self.send_error(400, "Missing token")
        else:
            self.send_error(404)

    def log_message(self, format, *args):
        return # Silence logs

def get_plex_status(plex):
    try:
        sessions = plex.sessions()
        if not sessions:
            return "Plex: Idle", ""
        
        if len(sessions) > 1:
            return "Multiple Streams", ""
            
        # Get the first active session
        session = sessions[0]
        title = session.title
        
        # Format: Line 1 (0-20), Line 2 (21-40)
        line1 = f"{title[:20]}"
        line2 = f"{title[20:40]}"
        return line1, line2
    except Exception as e:
        return "Plex: Error", ""

def get_system_metrics():
    # CPU Usage
    cpu_usage = psutil.cpu_percent(interval=None)
    
    # Memory Usage
    memory = psutil.virtual_memory()
    mem_usage = memory.percent
    
    # Disk Usage
    disk = psutil.disk_usage('/')
    disk_usage = disk.percent
    
    # GPU Usage
    gpu_usage = 0
    try:
        gpus = GPUtil.getGPUs()
        if gpus:
            gpu_usage = gpus[0].load * 100
    except Exception:
        pass
    
    # Line 3: CPU and GPU (User style)
    line3 = f"CPU: {cpu_usage:>3.0f}% GPU:{gpu_usage:>3.0f}%"
    
    # Line 4: RAM and Disk
    line4 = f"RAM:{mem_usage:>3.0f}% DISK:{disk_usage:>3.0f}%"
    
    return line3, line4

def get_disks_view():
    lines = []
    try:
        # Get unique physical disks
        partitions = psutil.disk_partitions(all=False)
        seen_mounts = set()
        
        for p in partitions:
            if p.mountpoint in seen_mounts or 'cdrom' in p.opts or not p.fstype:
                continue
            
            try:
                usage = psutil.disk_usage(p.mountpoint)
                percent = usage.percent
                # Label: "C:" (2 chars)
                label = p.mountpoint[:2] if len(p.mountpoint) >= 2 else p.mountpoint[:1] + ":"
                
                # Bar: "[##########]" (12 chars total)
                bar_width = 10
                filled = int(percent / 100 * bar_width)
                bar = "#" * filled + " " * (bar_width - filled)
                
                # Full line: "C:[##########] 100%" (max 20)
                line = f"{label}:[{bar}] {percent:>3.0f}%"
                lines.append(line.ljust(20)[:20])
                seen_mounts.add(p.mountpoint)
            except Exception:
                continue
                
            if len(lines) == 4:
                break
    except Exception:
        lines = ["Disk Error".ljust(20)]

    # Pad with empty lines if fewer than 4 disks
    while len(lines) < 4:
        lines.append(" " * 20)
    return lines

def get_streams_view(plex):
    lines = []
    try:
        sessions = plex.sessions()
        if not sessions:
            return ["No Active Streams".center(20), " " * 20, " " * 20, " " * 20]
        
        count = len(sessions)
        
        if count == 1:
            # Detailed view for single stream
            s = sessions[0]
            title = s.title[:20]
            state = getattr(s, 'state', 'playing').capitalize()
            
            # Progress calculation
            progress_pc = 0
            duration = getattr(s, 'duration', 0)
            offset = getattr(s, 'viewOffset', 0)
            if duration:
                progress_pc = (offset / duration) * 100
                
            lines.append(f"{title}"[:20])
            lines.append(f"State: {state}"[:20])
            
            # Bar
            bar_width = 14
            filled = int(progress_pc / 100 * bar_width)
            bar = "#" * filled + "-" * (bar_width - filled)
            lines.append(f"[{bar}] {progress_pc:>3.0f}%"[:20])
            
            # Resolution/Type info if available
            info = ""
            if hasattr(s, 'media') and s.media:
                m = s.media[0]
                res = getattr(m, 'videoResolution', '')
                codec = getattr(m, 'videoCodec', '')
                info = f"{res}p {codec}".strip()
            lines.append(info.center(20))
            
        elif count <= 4:
            # 1 line per stream (up to 4)
            for s in sessions[:4]:
                title = s.title[:15]
                duration = getattr(s, 'duration', 0)
                offset = getattr(s, 'viewOffset', 0)
                progress_pc = (offset / duration * 100) if duration else 0
                lines.append(f"{title}: {progress_pc:.0f}%"[:20])
                
    except Exception as e:
        lines = [f"Stream Error".center(20), str(e)[:20], " " * 20, " " * 20]

    # Pad with empty lines if fewer than 4
    while len(lines) < 4:
        lines.append(" " * 20)
    return [l.ljust(20)[:20] for l in lines]

def main():
    global PLEX_TOKEN 
    
    print(f"Connecting to Plex at {PLEX_URL}...")
    ser = None
    
    while True: # Outer loop for reconnection (both Plex and Serial)
        # 1. Handle Serial Connection (Retry until connected)
        if ser is None:
            try:
                print(f"Opening Serial Port {SERIAL_PORT}...")
                ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
                print("Waiting for Arduino to reset...")
                time.sleep(3)
                
                # Show immediate feedback
                l1 = "PLEX MONITOR".center(20)
                l2 = "Connecting...".center(20)
                l3 = "".center(20)
                l4 = "".center(20)
                payload = l1 + l2 + l3 + l4
                ser.write(b'!' + payload.encode('ascii') + bytes([255]))
                print(f"Connected to Arduino on {SERIAL_PORT}.")
            except Exception as e:
                print(f"Searching for Arduino on {SERIAL_PORT}... ({e})")
                time.sleep(5)
                continue # Keep trying Serial before proceeding to Plex

        # 2. Handle Plex Connection
        try:
            plex = PlexServer(PLEX_URL, PLEX_TOKEN)
            print("Connected to Plex.")
            break # Success, move to monitoring loop
        except Unauthorized:
            print("Authentication failed. Starting setup web server...")
            ip = get_local_ip()
            setup_url = f"http://{ip}:{WEB_SERVER_PORT}"
            
            with socketserver.TCPServer(("", WEB_SERVER_PORT), TokenHandler) as httpd:
                httpd.timeout = 0.1
                print(f"Setup URL: {setup_url}")
                
                while not TokenHandler.new_token:
                    # Repeatedly update LCD
                    if ser:
                        try:
                            setup_lines = [
                                "SETUP MODE".center(20),
                                setup_url.ljust(40)[:20],
                                setup_url.ljust(40)[20:40],
                                "Enter Plex Token".center(20)
                            ]
                            payload = "".join([l.ljust(20)[:20] for l in setup_lines])
                            ser.write(b'!' + payload.encode('ascii') + bytes([255]))
                        except:
                            ser = None # Lost connection during setup?
                            break 
                    
                    httpd.handle_request()
                    time.sleep(0.5)
                
                if not ser: continue # Retry Serial if lost during setup
                
                print("\nToken received!")
                PLEX_TOKEN = TokenHandler.new_token
                TokenHandler.new_token = None
                try:
                    set_key(".env", "PLEX_TOKEN", PLEX_TOKEN)
                    print("Updated .env with new token.")
                except Exception as e:
                    print(f"Could not update .env: {e}")
            
            print("Retrying connection...")
            time.sleep(2)
        except Exception as e:
            print(f"Connection error: {e}")
            time.sleep(5)
            continue

    view_index = 0
    last_data_update = 0
    
    try:
        while True:
            # Reconnect Serial if lost
            if ser is None:
                try:
                    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
                    time.sleep(2)
                    print(f"Reconnected to Arduino on {SERIAL_PORT}.")
                except:
                    time.sleep(5)
                    continue

            # Check for incoming button press signal ('N')
            try:
                if ser.in_waiting > 0:
                    while ser.in_waiting > 0:
                        char = ser.read().decode('ascii', errors='ignore')
                        if char == 'N':
                            view_index = (view_index + 1) % 3
                            last_data_update = 0 
                            break 
            except Exception as e:
                print(f"Serial Port Lost: {e}")
                ser.close()
                ser = None
                continue

            # Update data/display
            current_time = time.time()
            if current_time - last_data_update >= UPDATE_INTERVAL:
                try:
                    if view_index == 0:
                        p_line1, p_line2 = get_plex_status(plex)
                        s_line3, s_line4 = get_system_metrics()
                        display_lines = [p_line1, p_line2, s_line3, s_line4]
                    elif view_index == 1:
                        display_lines = get_disks_view()
                    else:
                        display_lines = get_streams_view(plex)
                except Unauthorized:
                    print("Token expired. Restarting main...")
                    return main() 
                
                payload_text = "".join([l.ljust(20)[:20] for l in display_lines])
                brightness_byte = bytes([max(0, min(255, LCD_BRIGHTNESS))])
                
                if ser:
                    try:
                        ser.write(b'!' + payload_text.encode('ascii') + brightness_byte)
                    except Exception as e:
                        print(f"Serial Write Error: {e}")
                        ser.close()
                        ser = None
                        continue
                
                last_data_update = current_time

            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("Stopping...")
    finally:
        if ser:
            ser.close()

if __name__ == "__main__":
    main()

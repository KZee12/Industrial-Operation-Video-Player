import snap7
import requests
import uuid
import time
import json
import subprocess
import os
import csv
from datetime import datetime
import logging

class IndustrialVideoClient:
    def __init__(self, server_ip="192.168.0.100", plc_ip="192.168.0.1"):
        self.server_ip = server_ip
        self.plc_ip = plc_ip
        self.client_id = self.get_mac_address()
        self.client = snap7.client.Client()
        self.current_video_process = None
        self.current_video_index = None
        self.client_mappings = {}
        self.setup_logging()
        
    def get_mac_address(self):
        '''Get MAC address of the current machine'''
        mac = uuid.getnode()
        mac_address = ':'.join(['{:02x}'.format((mac >> elements) & 0xff) 
                               for elements in range(0,2*6,2)][::-1])
        return mac_address.upper()
    
    def setup_logging(self):
        '''Setup logging for playback events'''
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('client_video_log.txt'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Client initialized with MAC: {self.client_id}")
    
    def connect_to_plc(self):
        '''Establish connection to PLC'''
        try:
            self.client.connect(self.plc_ip, 0, 1)
            self.logger.info(f"Connected to PLC at {self.plc_ip}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to connect to PLC: {e}")
            return False
    
    def fetch_client_mappings(self):
        '''Fetch video mappings for this specific client from server'''
        try:
            url = f"http://{self.server_ip}:8000/api/client/{self.client_id}/mappings"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                self.client_mappings = response.json()
                self.logger.info(f"Fetched {len(self.client_mappings)} video mappings")
                return True
            else:
                self.logger.error(f"Server returned status {response.status_code}")
                return False
                
        except requests.RequestException as e:
            self.logger.error(f"Failed to fetch mappings from server: {e}")
            return False
    
    def read_plc_data(self):
        '''Read control data from PLC memory'''
        try:
            # Read 2 bytes from DB1 starting at offset 0
            # Byte 0: Playback control (0x00 = Stop, 0x01 = Play)
            # Byte 1: Video index (0x01-0xFF)
            data = self.client.db_read(1, 0, 2)
            
            playback_control = data[0]
            video_index = str(data[1])  # Convert to string for mapping lookup
            
            return playback_control, video_index
            
        except Exception as e:
            self.logger.error(f"Failed to read PLC data: {e}")
            return None, None
    
    def get_video_url(self, video_index):
        '''Get the streaming URL for a specific video index'''
        if video_index not in self.client_mappings:
            self.logger.warning(f"No video mapped for index {video_index}")
            return None
            
        video_filename = self.client_mappings[video_index]
        video_url = f"http://{self.server_ip}:8000/videos/{video_filename}"
        return video_url
    
    def stop_current_video(self):
        '''Stop currently playing video'''
        if self.current_video_process:
            try:
                self.current_video_process.terminate()
                self.current_video_process.wait(timeout=5)
                self.logger.info("Stopped current video playback")
            except subprocess.TimeoutExpired:
                self.current_video_process.kill()
                self.logger.warning("Force killed video process")
            except Exception as e:
                self.logger.error(f"Error stopping video: {e}")
            finally:
                self.current_video_process = None
                self.current_video_index = None
    
    def play_video(self, video_index):
        '''Play video for the given index'''
        video_url = self.get_video_url(video_index)
        if not video_url:
            return False
            
        try:
            # VLC command for streaming playback
            vlc_path = "C:\\Program Files\\VideoLAN\\VLC\\vlc.exe"
            vlc_args = [
                vlc_path,
                video_url,
                "--intf", "dummy",        # No interface
                "--play-and-exit",        # Exit after playback
                "--fullscreen",           # Play in fullscreen
                "--no-video-title-show",  # Don't show title
                "--quiet"                 # Minimal output
            ]
            
            self.current_video_process = subprocess.Popen(vlc_args)
            self.current_video_index = video_index
            
            # Log the playback event
            self.log_playback_event(video_index, video_url)
            self.logger.info(f"Started playing video index {video_index}: {video_url}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start video playback: {e}")
            return False
    
    def log_playback_event(self, video_index, video_url):
        '''Log playback event to CSV file'''
        try:
            log_file = 'playback_log.csv'
            file_exists = os.path.exists(log_file)
            
            with open(log_file, 'a', newline='') as csvfile:
                fieldnames = ['timestamp', 'client_id', 'video_index', 'video_url', 'action']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                if not file_exists:
                    writer.writeheader()
                
                writer.writerow({
                    'timestamp': datetime.now().isoformat(),
                    'client_id': self.client_id,
                    'video_index': video_index,
                    'video_url': video_url,
                    'action': 'play'
                })
                
        except Exception as e:
            self.logger.error(f"Failed to log playback event: {e}")
    
    def run(self):
        '''Main client loop'''
        self.logger.info("Starting Industrial Video Client...")
        
        # Initial setup
        if not self.connect_to_plc():
            self.logger.error("Cannot connect to PLC. Exiting.")
            return
            
        if not self.fetch_client_mappings():
            self.logger.error("Cannot fetch video mappings. Exiting.")
            return
        
        self.logger.info("Client ready for PLC commands")
        
        last_state = (0, "0")  # (playback_control, video_index)
        
        try:
            while True:
                # Read PLC data
                playback_control, video_index = self.read_plc_data()
                
                if playback_control is None:
                    time.sleep(1)
                    continue
                
                current_state = (playback_control, video_index)
                
                # Check if state changed
                if current_state != last_state:
                    self.logger.info(f"PLC state changed: Control={playback_control}, Index={video_index}")
                    
                    if playback_control == 0:  # Stop command
                        self.stop_current_video()
                        
                    elif playback_control == 1 and video_index != "0":  # Play command
                        # Stop current video if different index
                        if self.current_video_index != video_index:
                            self.stop_current_video()
                            
                        # Start new video
                        if not self.current_video_process:
                            self.play_video(video_index)
                    
                    last_state = current_state
                
                # Check if current video process ended
                if self.current_video_process and self.current_video_process.poll() is not None:
                    self.logger.info("Video playback completed")
                    self.current_video_process = None
                    self.current_video_index = None
                
                # Refresh mappings periodically (every 60 seconds)
                if int(time.time()) % 60 == 0:
                    self.fetch_client_mappings()
                
                time.sleep(0.5)  # 500ms polling interval
                
        except KeyboardInterrupt:
            self.logger.info("Client stopped by user")
        except Exception as e:
            self.logger.error(f"Unexpected error in main loop: {e}")
        finally:
            self.stop_current_video()
            if self.client.get_connected():
                self.client.disconnect()
            self.logger.info("Client shutdown complete")

if __name__ == "__main__":
    # Configuration - adjust these IPs for your network
    SERVER_IP = "192.168.0.100"  # IP address of your server
    PLC_IP = "192.168.0.1"       # IP address of your PLC
    
    client = IndustrialVideoClient(SERVER_IP, PLC_IP)
    client.run()

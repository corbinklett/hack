import socket
import json
import time
from audio import AudioProcessor
from utilities import calculate_distance
from triangulate import triangulate_target
from threading import Thread
from typing import Optional, Dict, Tuple
import sounddevice as sd
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
import matplotlib.animation as animation
from multiprocessing import Process

class GroundStation:
    def __init__(self, station_type: str, host: str = '0.0.0.0', port: int = 58392, location=(0,0), plot_enabled=False, name="default", low_cutoff_Hz = 500, thresh_dB = 30, target_filter_alpha = 0.1):
        """
        Initialize a ground station that can act as either sender or receiver
        
        Args:
            station_type (str): Either 'sender' or 'receiver'
            host (str): IP address to connect/listen to
            port (int): Port number to use
            location (tuple): (x, y) coordinates of the station
            plot_enabled (bool): Whether to enable real-time plotting
            name (str): Name of the ground station
            target_filter_alpha (float): Low-pass filter coefficient (0-1). Lower values = more filtering
        """
        if station_type not in ['sender', 'receiver']:
            raise ValueError("station_type must be either 'sender' or 'receiver'")
            
        self.station_type = station_type
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.audio_processor = AudioProcessor(freq_min=low_cutoff_Hz)
        self.running = False
        self.location = location
        self.name = name
        self.thresh_dB = thresh_dB
        # For receiver to track multiple sender connections
        self.clients: Dict[str, socket.socket] = {}
        self.sender_data: Dict[str, Tuple[float, float]] = {}  # {client_addr: (peak_freq, peak_power)}
        
        # Set the backend before importing pyplot
        import matplotlib
        matplotlib.use('Qt5Agg')  # Change from TkAgg to Qt5Agg

        # Initialize data dictionary with empty lists
        self.data = {
            'gnd_ip': [],
            'freq': [],
            'power': [],
            'gnd_location': [],
            'target_distance': [],
            'target_location': None,
            'target_power_dB': [],
            'station_names': []
        }
        
        # Add plotting setup
        self.fig, self.ax = None, None
        self.station_plots = {}
        self.circle_plots = {}
        self.target_plot = None
        
        # Add plotting flag
        self.plot_enabled = plot_enabled
        if self.plot_enabled:
            self._setup_plot()
            # Set up animation
            self.anim = animation.FuncAnimation(
                self.fig, 
                self._animate, 
                interval=100,  # Update every 100ms
                blit=False,
                save_count=100  # Limit frame cache to 100 frames
            )

        self.target_filter_alpha = target_filter_alpha
        self.filtered_target = (0, 0)  # Initialize as tuple instead of int
        
    def start(self):
        """Start the ground station operations"""
        self.running = True
        
        # Start receiver/sender in a separate thread
        if self.station_type == 'receiver':
            network_thread = Thread(target=self._start_receiver)
            network_thread.daemon = True
            network_thread.start()
        else:
            network_thread = Thread(target=self._start_sender)
            network_thread.daemon = True
            network_thread.start()
            
        # Run matplotlib in the main thread
        if self.plot_enabled:
            plt.show(block=True)
        else:
            # If no plot, keep main thread alive
            while self.running:
                time.sleep(0.1)

    def stop(self):
        """Stop the ground station operations"""
        self.running = False
        self.socket.close()
        for client in self.clients.values():
            client.close()

    def _start_receiver(self):
        """Initialize and run the receiver station"""
        self.socket.bind((self.host, self.port))
        self.socket.listen(5)  # Allow up to 5 sender connections
        print(f"Receiver listening on {self.host}:{self.port}")
        
        # Start audio processing thread
        audio_thread = Thread(target=self._process_local_audio)
        audio_thread.daemon = True
        audio_thread.start()
        
        # Accept and handle client connections
        while self.running:
            try:
                client_socket, address = self.socket.accept()
                print(f"New connection from {address}")
                self.clients[address[0]] = client_socket

                # Start a new thread to handle this client
                client_thread = Thread(target=self._handle_client, args=(client_socket, address[0]))
                client_thread.daemon = True
                client_thread.start()
                
            except Exception as e:
                print(f"Receiver error: {e}")

    def _handle_client(self, client_socket: socket.socket, client_addr: str):
        """Handle incoming data from a sender client"""
        # Set TCP keepalive
        client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        # Set non-blocking mode
        client_socket.setblocking(False)
        
        buffer = b""
        while self.running:
            try:
                # First read the message length (4 bytes)
                while len(buffer) < 4:
                    try:
                        chunk = client_socket.recv(4 - len(buffer))
                        if not chunk:
                            raise ConnectionError("Connection closed by client")
                        buffer += chunk
                    except BlockingIOError:
                        time.sleep(0.01)
                        continue
                
                msg_length = int.from_bytes(buffer[:4], byteorder='big')
                buffer = buffer[4:]
                
                # Then read the actual message
                while len(buffer) < msg_length:
                    try:
                        chunk = client_socket.recv(msg_length - len(buffer))
                        if not chunk:
                            raise ConnectionError("Connection closed by client")
                        buffer += chunk
                    except BlockingIOError:
                        time.sleep(0.01)
                        continue
                
                data = buffer[:msg_length]
                buffer = buffer[msg_length:]
                
                received_data = json.loads(data.decode('utf-8'))
                self.sender_data[client_addr] = (
                    received_data['peak_freq'],
                    received_data['peak_power'],
                    received_data['location'],
                    received_data.get('name', f'Station {client_addr}'),
                    received_data['target_power_dB']
                )
                
            except (BlockingIOError, socket.timeout):
                # No data available right now
                time.sleep(0.01)
                continue
            except ConnectionError as e:
                print(f"Connection error with client {client_addr}: {e}")
                break
            except Exception as e:
                print(f"Error handling client {client_addr}: {e}")
                break
                
        # Clean up when client disconnects
        print(f"Client {client_addr} disconnected")
        del self.clients[client_addr]
        if client_addr in self.sender_data:
            del self.sender_data[client_addr]
        client_socket.close()

    def _start_sender(self):
        """Initialize and run the sender station"""
        while self.running:
            try:
                # Create a new socket for each connection attempt
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.settimeout(5.0)
                # Add TCP keepalive
                self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
                
                print(f"Attempting to connect to receiver at {self.host}:{self.port}")
                self.socket.connect((self.host, self.port))
                print(f"Connected to receiver at {self.host}:{self.port}")
                
                with sd.InputStream(callback=self.audio_processor.audio_callback, 
                                  channels=1, 
                                  samplerate=self.audio_processor.sample_rate):
                    print("Streaming audio...")
                    last_send_time = 0
                    while self.running:
                        current_time = time.time()
                        # Increase minimum time between sends from 0.1s to 0.5s
                        if current_time - last_send_time >= 0.2:  # Changed from 0.1
                            peak_freq, peak_power, target_power_dB = self.audio_processor._update_stream(plot=False)
                            
                            if peak_freq is not None and peak_power is not None:
                                data = {
                                    "timestamp": current_time,
                                    "peak_freq": peak_freq,
                                    "peak_power": peak_power,
                                    "location": self.location,
                                    "name": self.name,
                                    "target_power_dB": target_power_dB
                                }
                                
                                try:
                                    json_data = json.dumps(data).encode('utf-8')
                                    # Add message length prefix
                                    msg_length = len(json_data)
                                    header = msg_length.to_bytes(4, byteorder='big')
                                    self.socket.sendall(header + json_data)
                                    last_send_time = current_time
                                except BlockingIOError:
                                    # Socket buffer is full, wait a bit
                                    time.sleep(0.05)
                                    continue
                    
                        time.sleep(0.02)  # Increased from 0.01 to reduce CPU usage
            except Exception as e:
                print(f"Sender error: {e}")
                time.sleep(1)  # Wait before retrying connection

    def _process_local_audio(self):
        """Process audio from local microphone"""
        with sd.InputStream(callback=self.audio_processor.audio_callback, 
                           channels=1, 
                           samplerate=self.audio_processor.sample_rate):
            print("Processing local audio...")
            while self.running:
                peak_freq, peak_power, target_power_dB = self.audio_processor._update_stream(plot=False)
                if peak_freq is not None and peak_power is not None:
                    self.sender_data['local'] = (peak_freq, peak_power, self.location, self.name, target_power_dB)
                    
                    if len(self.sender_data) == len(self.clients) + 1:
                        self._audio_calcs(print_data=True)
                        self.sender_data.clear()
                
                time.sleep(0.2)  # Increased from 0.1 to reduce processing frequency

    def _audio_calcs(self, print_data=False):
        """Calculate audio data - only called by receiver stations"""
        if self.station_type != 'receiver':
            raise RuntimeError("_audio_calcs should only be called by receiver stations")
        
        # Clear old data lists but don't clear sender_data yet
        self.data['gnd_ip'] = []
        self.data['freq'] = []
        self.data['power'] = []
        self.data['gnd_location'] = []
        self.data['target_distance'] = []
        self.data['target_power_dB'] = []
        self.data['station_names'] = []
        
        # Use sender_data directly instead of copying and clearing
        if print_data:
            print("\n=== Current Audio Data ===")

        triangulation_data = []
        for gnd_ip, (freq, power, gnd_location, station_name, target_power_dB) in self.sender_data.items():
            if target_power_dB > self.thresh_dB:
                target_distance = calculate_distance(target_power_dB, reference_db=80.0, reference_distance=2.0)
            else:
                target_distance = 0
            triangulation_data.append((gnd_location, target_distance))
            self.data['gnd_ip'].append(gnd_ip)
            self.data['freq'].append(freq)
            self.data['power'].append(power)
            self.data['gnd_location'].append(gnd_location)
            self.data['target_distance'].append(target_distance)
            self.data['target_power_dB'].append(target_power_dB)
            self.data['station_names'].append(station_name)

            if print_data:
                print(f"Station: {station_name:15} Location: {gnd_location[0]:.2f}, {gnd_location[1]:.2f} Frequency: {freq:.2f} Hz, Power: {power:.2f} dB, Source Distance: {target_distance:.2f} m, Target Power: {target_power_dB:.2f} dB")  
    
        x_target, y_target = triangulate_target(triangulation_data)
        
        # Apply low-pass filter to both x and y coordinates
        filtered_x = self.target_filter_alpha * x_target + (1 - self.target_filter_alpha) * self.filtered_target[0]

        filtered_y = self.target_filter_alpha * y_target + (1 - self.target_filter_alpha) * self.filtered_target[1]
        
        self.filtered_target = (filtered_x, filtered_y)
        x_target, y_target = self.filtered_target
        
        self.data['target_location'] = (self.filtered_target[0], self.filtered_target[1])
        
        if print_data:
            print(f"Target Location: {x_target:.2f}, {y_target:.2f}")
            print("========================\n")

        # Only clear sender_data after we're completely done with processing
        # This ensures the plotting function has access to the data
        self.sender_data.clear()

    
    def _setup_plot(self):
        """Initialize the real-time plotting"""
        plt.ion()  # Enable interactive mode
        self.fig, self.ax = plt.subplots(figsize=(10, 10))
        self.ax.set_xlabel("X Position (m)")
        self.ax.set_ylabel("Y Position (m)")
        self.ax.set_title("Ground Station Positions and Target Triangulation")
        self.ax.grid(True)
        
        # Initialize empty plots that we'll update later
        self.station_plots = {}
        self.circle_plots = {}
        self.target_plot, = self.ax.plot([], [], 'ro', markersize=10)
        
        # Set fixed plot limits
        self.ax.set_xlim(-20, 20)
        self.ax.set_ylim(-2, 50)
        
        plt.tight_layout()
        plt.show(block=False)

    def _animate(self, frame):
        """Animation update function"""
        if not plt.fignum_exists(self.fig.number):
            return
        
        # Update or create station plots and circles
        current_stations = set()
        any_signal_above_threshold = False
        
        for i in range(len(self.data['gnd_ip'])):
            location = self.data['gnd_location'][i]
            distance = self.data['target_distance'][i]
            source = self.data['gnd_ip'][i]
            target_power_dB = self.data['target_power_dB'][i]
            station_name = self.data['station_names'][i]
            current_stations.add(source)
            
            # Check if any station detects signal above threshold
            if target_power_dB > self.thresh_dB:
                any_signal_above_threshold = True
            
            if source not in self.station_plots:
                self.station_plots[source], = self.ax.plot(
                    [location[0]], [location[1]], 'bs'
                )
                # Add text annotation next to the station point
                self.station_plots[source].text_annotation = self.ax.annotate(
                    station_name,
                    (location[0], location[1]),
                    xytext=(5, 5),  # 5 points offset
                    textcoords='offset points'
                )
                self.circle_plots[source] = Circle(
                    location, distance, fill=False, linestyle='--', alpha=0.5
                )
                self.ax.add_patch(self.circle_plots[source])
            else:
                self.station_plots[source].set_data([location[0]], [location[1]])
                # Update text annotation position
                self.station_plots[source].text_annotation.set_position((location[0], location[1]))
                self.circle_plots[source].center = location
                self.circle_plots[source].radius = distance

        # Remove any stations that are no longer present
        for source in list(self.station_plots.keys()):
            if source not in current_stations:
                self.station_plots[source].text_annotation.remove()  # Remove text annotation
                self.station_plots[source].remove()
                self.circle_plots[source].remove()
                del self.station_plots[source]
                del self.circle_plots[source]

        # Update target location only if signal is above threshold
        if self.data['target_location'] is not None and any_signal_above_threshold:
            x_target, y_target = self.data['target_location']
            self.target_plot.set_data([x_target], [y_target])
        else:
            self.target_plot.set_data([], [])

if __name__ == "__main__":
    # Example usage as receiver:
    station = GroundStation('receiver', host='0.0.0.0', port=58392, plot_enabled=True, name="Main", low_cutoff_Hz=500, thresh_dB=30)
    
    # Example usage as sender:
    # station = GroundStation('sender', host='specify host IP', port=58392, location=(4,0), name='stat_name', low_cutoff_Hz=500, thresh_dB=50)
    
    station.start()
    pass

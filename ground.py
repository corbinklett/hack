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

class GroundStation:
    def __init__(self, station_type: str, host: str = '0.0.0.0', port: int = 58392, location=(0,0), plot_enabled=False):
        """
        Initialize a ground station that can act as either sender or receiver
        
        Args:
            station_type (str): Either 'sender' or 'receiver'
            host (str): IP address to connect/listen to
            port (int): Port number to use
        """
        if station_type not in ['sender', 'receiver']:
            raise ValueError("station_type must be either 'sender' or 'receiver'")
            
        self.station_type = station_type
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.audio_processor = AudioProcessor()
        self.running = False
        self.location = location
        
        # For receiver to track multiple sender connections
        self.clients: Dict[str, socket.socket] = {}
        self.sender_data: Dict[str, Tuple[float, float]] = {}  # {client_addr: (peak_freq, peak_power)}
        
        # Set the backend before importing pyplot
        import matplotlib
        matplotlib.use('TkAgg')  # Use TkAgg backend which is more stable for threading

        # Initialize data dictionary with empty lists
        self.data = {
            'gnd_ip': [],
            'freq': [],
            'power': [],
            'gnd_location': [],
            'target_distance': [],
            'target_location': None
        }
        
        # Add plotting setup
        self.fig, self.ax = None, None
        self.station_plots = {}
        self.circle_plots = {}
        self.target_plot = None
        
        # Add plotting flag
        self.plot_enabled = plot_enabled
        if self.plot_enabled:
            self._setup_plot()  # Initialize plot on main thread
        
    def start(self):
        """Start the ground station operations"""
        self.running = True
        
        if self.station_type == 'receiver':
            self._start_receiver()
        else:
            self._start_sender()
            
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
        
        # Start plotting thread for receiver
        if self.plot_enabled:
            plot_thread = Thread(target=self._continuous_plot)
            plot_thread.daemon = True
            plot_thread.start()
        
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
        while self.running:
            try:
                data = client_socket.recv(4096)
                if not data:
                    break
                    
                received_data = json.loads(data.decode('utf-8'))
                # Only update data if we're awaiting new readings
                if client_addr not in self.sender_data:
                    self.sender_data[client_addr] = (
                        received_data['peak_freq'],
                        received_data['peak_power'],
                        received_data['location']
                    )
                
            except Exception as e:
                print(f"Error handling client {client_addr}: {e}")
                break
                
        # Clean up when client disconnects
        print(f"Client {client_addr} disconnected")
        del self.clients[client_addr]
        del self.sender_data[client_addr]
        client_socket.close()

    def _start_sender(self):
        """Initialize and run the sender station"""
        try:
            self.socket.connect((self.host, self.port))
            print(f"Connected to receiver at {self.host}:{self.port}")
            
            # Initialize audio stream
            with sd.InputStream(callback=self.audio_processor.audio_callback, 
                              channels=1, 
                              samplerate=self.audio_processor.sample_rate):
                print("Streaming audio...")
                # Start sending audio processing results
                while self.running:
                    peak_freq, peak_power = self.audio_processor._update_stream(plot=False)
                    
                    if peak_freq is not None and peak_power is not None:
                        data = {
                            "timestamp": time.time(),
                            "peak_freq": peak_freq,
                            "peak_power": peak_power,
                            "location": self.location
                        }
                        
                        json_data = json.dumps(data).encode('utf-8')
                        self.socket.send(json_data)
                        print(f"Sent: {data}")
                    
                    time.sleep(0.1)  # Adjust as needed
                    
        except Exception as e:
            print(f"Sender error: {e}")

    def _process_local_audio(self):
        """Process audio from local microphone"""
        with sd.InputStream(callback=self.audio_processor.audio_callback, 
                           channels=1, 
                           samplerate=self.audio_processor.sample_rate):
            print("Processing local audio...")
            while self.running:
                peak_freq, peak_power = self.audio_processor._update_stream(plot=False)
                if peak_freq is not None and peak_power is not None:
                    self.sender_data['local'] = (peak_freq, peak_power, self.location)
                    
                    # Process when we have fresh data from all connected clients plus local
                    if len(self.sender_data) == len(self.clients) + 1:  # +1 for local
                        self._audio_calcs(print_data=True)
                        # Clear all data after processing
                        self.sender_data.clear()
                
                time.sleep(0.1)

    def _audio_calcs(self, print_data=False):
        """Calculate audio data"""
        # Clear existing data while preserving dictionary structure
        for key in self.data:
            if isinstance(self.data[key], list):
                self.data[key].clear()
            else:
                self.data[key] = None

        if print_data:
            print("\n=== Current Audio Data ===")

        triangulation_data = []
        for gnd_ip, (freq, power, gnd_location) in self.sender_data.items():
            target_distance = calculate_distance(power, reference_db=94.0, reference_distance=1.0)
            triangulation_data.append((gnd_location, target_distance))
            self.data['gnd_ip'].append(gnd_ip)
            self.data['freq'].append(freq)
            self.data['power'].append(power)
            self.data['gnd_location'].append(gnd_location)
            self.data['target_distance'].append(target_distance)

            if print_data:
                print(f"Station: {gnd_ip:15} Location: {gnd_location[0]:.2f}, {gnd_location[1]:.2f} Frequency: {freq:.2f} Hz, Power: {power:.2f} dB, Source Distance: {target_distance:.2f} m")  
    
        x_target, y_target = triangulate_target(triangulation_data)
        self.data['target_location'] = (x_target, y_target)
        
        if print_data:
            print(f"Target Location: {x_target:.2f}, {y_target:.2f}")
            print("========================\n")

    
    def _setup_plot(self):
        """Initialize the real-time plotting"""
        plt.ion()
        self.fig, self.ax = plt.subplots(figsize=(10, 10))
        self.ax.set_xlabel("X Position")
        self.ax.set_ylabel("Y Position")
        self.ax.set_title("Ground Station Positions and Target Triangulation")
        self.ax.grid(True)
        plt.tight_layout()
        plt.show(block=False)

    def _plot_all_data(self):
        """Plot ground station positions, distance circles, and triangulated target"""
        if self.fig is None:
            return

        # Clear previous plots
        self.ax.clear()
        self.station_plots = {}
        self.circle_plots = {}
        self.target_plot = None

        # Calculate distances and prepare triangulation data
        
        for source, (freq, power, location) in self.sender_data.items():

            # Plot station and circle
            self.ax.plot(location[0], location[1], 'bs', label=f'Station {source}')
            circle = Circle(location, distance, fill=False, linestyle='--', alpha=0.5)
            self.ax.add_patch(circle)

        # Calculate and plot triangulated target
        target_location = triangulate_target(triangulation_data)
        if target_location:
            self.ax.plot(target_location[0], target_location[1], 'ro', 
                        markersize=10, label='Target')

        # Update plot settings
        self.ax.grid(True)
        self.ax.legend()
        self._update_plot_limits()
        
        # Force drawing update
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()

    def _update_plot_limits(self):
        """Update plot limits to show all points with some padding"""
        x_coords = []
        y_coords = []
        
        # Collect all x, y coordinates
        for _, (_, _, location) in self.sender_data.items():
            x_coords.append(location[0])
            y_coords.append(location[1])
        
        if x_coords and y_coords:
            x_min, x_max = min(x_coords), max(x_coords)
            y_min, y_max = min(y_coords), max(y_coords)
            
            # Add padding (20% of range)
            x_padding = (x_max - x_min) * 0.2
            y_padding = (y_max - y_min) * 0.2
            
            self.ax.set_xlim(x_min - x_padding, x_max + x_padding)
            self.ax.set_ylim(y_min - y_padding, y_max + y_padding)

    def get_all_peaks(self) -> Dict[str, Tuple[float, float]]:
        """Get peak frequency and power from all sources including local"""
        return self.sender_data

    def _continuous_plot(self):
        """Continuously update the plot at regular intervals"""
        while self.running:
            try:
                if len(self.sender_data) > 0:  # Only plot if we have data
                    self._plot_all_data()
                plt.pause(0.1)  # Gives time for the GUI to update
            except Exception as e:
                print(f"Plot error: {e}")

if __name__ == "__main__":
    # Example usage as receiver:
    station = GroundStation('receiver', host='0.0.0.0', port=58392, plot_enabled=False)
    
    # Example usage as sender:
    # station = GroundStation('sender', port=58392)
    
    station.start()
    pass

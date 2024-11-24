import socket
import json
import time
from audio import AudioProcessor
from threading import Thread
from typing import Optional, Dict, Tuple
import sounddevice as sd

class GroundStation:
    def __init__(self, station_type: str, host: str = '0.0.0.0', port: int = 58392):
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
        
        # For receiver to track multiple sender connections
        self.clients: Dict[str, socket.socket] = {}
        self.sender_data: Dict[str, Tuple[float, float]] = {}  # {client_addr: (peak_freq, peak_power)}

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
                self.sender_data[client_addr] = (
                    received_data['peak_freq'],
                    received_data['peak_power']
                )
                self._print_all_data()
                
            except Exception as e:
                print(f"Error handling client {client_addr}: {e}")
                break
                
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
                            "peak_power": peak_power
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
                    self.sender_data['local'] = (peak_freq, peak_power)
                    # Print all current data
                    self._print_all_data()
                time.sleep(0.1)  # Adjust as needed

    def _print_all_data(self):
        """Print peak frequencies and powers from all sources"""
        print("\n=== Current Audio Data ===")
        for source, (freq, power) in self.sender_data.items():
            print(f"Source: {source:15} Frequency: {freq:.2f} Hz, Power: {power:.2f} dB")
        print("========================\n")

    def get_all_peaks(self) -> Dict[str, Tuple[float, float]]:
        """Get peak frequency and power from all sources including local"""
        return self.sender_data

if __name__ == "__main__":
    # Example usage as receiver:
    station = GroundStation('receiver', host='0.0.0.0', port=58393)
    
    # Example usage as sender:
    # station = GroundStation('sender', host="10.33.1.252", port=58392)
    
    station.start()
    pass

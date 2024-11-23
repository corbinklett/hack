import socket
import json
import time

def start_sender(host='10.33.1.252', port=58392):
    """
    Starts a sender that continuously sends JSON data to a receiver
    
    Args:
        host (str): The receiver's IP address
        port (int): The port number to connect to
    """
    sender_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        # Connect to the receiver
        sender_socket.connect((host, port))
        print(f"Connected to receiver at {host}:{port}")
        
        # Example: continuously send data
        while True:
            # Create sample data - replace with your actual data
            data = {
                "timestamp": time.time(),
                "message": "Hello from sender!",
                "values": [1, 2, 3, 4, 5]
            }
            
            # Convert to JSON and send
            json_data = json.dumps(data).encode('utf-8')
            sender_socket.send(json_data)
            
            print(f"Sent: {data}")
            time.sleep(1)  # Wait 1 second between sends
            
    except Exception as e:
        print(f"Sender error: {e}")
    finally:
        sender_socket.close()


if __name__ == "__main__":
    start_sender(host='192.168.1.100')
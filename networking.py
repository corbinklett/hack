import socket
import json
import time

def start_sender(host='localhost', port=12345):
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

def start_receiver(host='0.0.0.0', port=12345):
    """
    Starts a receiver that listens for incoming JSON data
    
    Args:
        host (str): The IP address to listen on (0.0.0.0 for all available interfaces)
        port (int): The port number to listen on
    """
    receiver_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    receiver_socket.bind((host, port))
    receiver_socket.listen(1)
    
    print(f"Receiver listening on {host}:{port}")
    
    try:
        # Accept incoming connection
        client_socket, address = receiver_socket.accept()
        print(f"Connection from {address}")
        
        # Continuously receive data
        while True:
            # Receive and decode data
            data = client_socket.recv(4096)
            if not data:
                break
                
            # Parse JSON data
            received_data = json.loads(data.decode('utf-8'))
            print(f"Received: {received_data}")
            
    except Exception as e:
        print(f"Receiver error: {e}")
    finally:
        receiver_socket.close()

# Example usage:
if __name__ == "__main__":
    # On the receiver computer, run:
    # start_receiver()
    
    # On the sender computer, run:
    # start_sender(host='RECEIVER_IP_ADDRESS')
    pass

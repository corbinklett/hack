import socket
import json
import time

def start_receiver(host='0.0.0.0', port=58392):
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
    start_receiver()
    pass

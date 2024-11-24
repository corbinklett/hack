import socket
import json

def test_connection():
    # Create a socket and connect to the server
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = ('localhost', 58392)  # Same port as your server
    
    try:
        print(f"Trying to connect to server at {server_address}")
        client.connect(server_address)
        
        # Send some test data
        test_data = {"message": "Hello, server!"}
        client.send(json.dumps(test_data).encode('utf-8'))
        
        print("Data sent successfully")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    test_connection()
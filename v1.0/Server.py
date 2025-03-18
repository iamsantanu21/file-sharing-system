import socket
import os

# Server configuration
HOST = '0.0.0.0'  # Listen on all available interfaces
PORT = 12345       # Port to listen on
SHARE_DIR = '/Users/santanu_mac/Documents/GitHub/Distributed_image_processing/v2.0'  # Directory to share

# Ensure the shared directory exists
if not os.path.exists(SHARE_DIR):
    print(f"Error: The directory '{SHARE_DIR}' does not exist.")
    exit(1)

def list_files_and_folders():
    """Returns a list of files and folders in the shared directory."""
    items = os.listdir(SHARE_DIR)
    files_and_folders = []
    for item in items:
        item_path = os.path.join(SHARE_DIR, item)
        if os.path.isfile(item_path):
            files_and_folders.append(("file", item))
        elif os.path.isdir(item_path):
            files_and_folders.append(("folder", item))
    return files_and_folders

def send_folder_contents(client_socket, folder_path):
    """Send all files in a folder to the client."""
    try:
        for root, _, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, SHARE_DIR)  # Get relative path
                # Send the relative path length and path
                client_socket.sendall(len(relative_path).to_bytes(4, 'big'))
                client_socket.sendall(relative_path.encode('utf-8'))
                # Send the file data
                with open(file_path, 'rb') as f:
                    file_data = f.read()
                    client_socket.sendall(len(file_data).to_bytes(8, 'big'))  # Send file size
                    client_socket.sendall(file_data)  # Send file data
        # Send the "END_OF_FOLDER" signal
        client_socket.sendall(len("END_OF_FOLDER").to_bytes(4, 'big'))
        client_socket.sendall("END_OF_FOLDER".encode('utf-8'))
    except Exception as e:
        print(f"Error sending folder contents: {e}")

def start_server():
    # Create a socket object
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        # Bind the socket to the address and port
        server_socket.bind((HOST, PORT))
        # Listen for incoming connections
        server_socket.listen(5)
        print(f"Server listening on {HOST}:{PORT}...")
        print(f"Sharing directory: {SHARE_DIR}")

        while True:
            # Accept a connection from a client
            client_socket, client_address = server_socket.accept()
            print(f"Connection from {client_address} established.")

            # Handle the client request
            handle_client(client_socket)

def handle_client(client_socket):
    with client_socket:
        try:
            # Receive the client's request
            request = client_socket.recv(1024).decode('utf-8').strip()

            if request == "LIST":
                # Send the list of files and folders in the shared directory
                items = list_files_and_folders()
                if items:
                    client_socket.sendall(str(items).encode('utf-8'))  # Send the list as a string
                else:
                    client_socket.sendall(b"No files or folders found in the shared directory.")  # Handle empty directory
                print("Sent directory listing to client.")
            else:
                # Treat the request as a file or folder name
                item_path = os.path.join(SHARE_DIR, request)

                if os.path.isfile(item_path):
                    # Send the file to the client
                    with open(item_path, 'rb') as file:
                        file_data = file.read()
                        client_socket.sendall(len(file_data).to_bytes(8, 'big'))  # Send file size
                        client_socket.sendall(file_data)  # Send file data
                    print(f"File '{request}' sent successfully.")
                elif os.path.isdir(item_path):
                    # Send the contents of the folder to the client
                    client_socket.sendall(b"FOLDER_TRANSFER_START")  # Signal start of folder transfer
                    send_folder_contents(client_socket, item_path)
                    print(f"Folder '{request}' sent successfully.")
                else:
                    # Send an error message if the item doesn't exist
                    client_socket.sendall(b"File or folder not found.")
                    print(f"File or folder '{request}' not found.")
        except BrokenPipeError:
            print("Client disconnected unexpectedly.")
        except Exception as e:
            print(f"Error handling client request: {e}")

if __name__ == "__main__":
    start_server()
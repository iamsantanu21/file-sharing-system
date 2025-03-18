import socket
import os
import json

# Server configuration
HOST = '127.0.0.1'  # Bind to localhost
PORT = 12345        # Listening port
SHARE_DIR = '/Users/santanu_mac/Documents/GitHub/Distributed_image_processing/v2.0'  # Root shared directory
CHUNK_SIZE = 1024 * 1024  # 1 MB chunks

# Ensure the shared directory exists
if not os.path.exists(SHARE_DIR):
    print(f"Error: The directory '{SHARE_DIR}' does not exist.")
    exit(1)

def list_files_and_folders(directory):
    """Returns a list of files and folders in the specified directory."""
    items = []
    for item in os.listdir(directory):
        item_path = os.path.join(directory, item)
        if os.path.isfile(item_path):
            items.append(("file", item))
        elif os.path.isdir(item_path):
            items.append(("folder", item))
    return items

def send_file(client_socket, file_path):
    """Send a file to the client."""
    try:
        file_size = os.path.getsize(file_path)
        client_socket.sendall(json.dumps({"type": "file", "size": file_size}).encode('utf-8'))

        with open(file_path, 'rb') as f:
            while chunk := f.read(CHUNK_SIZE):
                client_socket.sendall(chunk)

    except Exception as e:
        print(f"Error sending file: {e}")

def handle_client(client_socket):
    """Handle client requests."""
    current_directory = SHARE_DIR  # Maintain per-client directory state

    with client_socket:
        try:
            while True:
                request = client_socket.recv(1024).decode('utf-8').strip()
                if not request:
                    break

                if request == "LIST":
                    items = list_files_and_folders(current_directory)
                    client_socket.sendall(json.dumps(items).encode('utf-8'))

                elif request.startswith("NAVIGATE:"):
                    folder_name = request.split(":", 1)[1]
                    folder_path = os.path.join(current_directory, folder_name)

                    if os.path.isdir(folder_path):
                        current_directory = folder_path  # Persist navigation
                        items = list_files_and_folders(current_directory)
                        client_socket.sendall(json.dumps(items).encode('utf-8'))
                    else:
                        client_socket.sendall(json.dumps({"error": "Folder not found."}).encode('utf-8'))

                elif request == "BACK":
                    if current_directory != SHARE_DIR:
                        current_directory = os.path.dirname(current_directory)
                    items = list_files_and_folders(current_directory)
                    client_socket.sendall(json.dumps(items).encode('utf-8'))

                elif request.startswith("DOWNLOAD:"):
                    item_name = request.split(":", 1)[1]
                    item_path = os.path.join(current_directory, item_name)

                    if os.path.isfile(item_path):
                        send_file(client_socket, item_path)
                    else:
                        client_socket.sendall(json.dumps({"error": "File not found."}).encode('utf-8'))

                else:
                    client_socket.sendall(json.dumps({"error": "Invalid request."}).encode('utf-8'))

        except Exception as e:
            print(f"Error handling client request: {e}")

def start_server():
    """Start the file-sharing server."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind((HOST, PORT))
        server_socket.listen(5)
        print(f"Server listening on {HOST}:{PORT}...")
        print(f"Sharing directory: {SHARE_DIR}")

        while True:
            client_socket, _ = server_socket.accept()
            handle_client(client_socket)

if __name__ == "__main__":
    start_server()

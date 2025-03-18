import socket
import os
import json

# Server configuration
SERVER_HOST = '127.0.0.1'
SERVER_PORT = 12345
CHUNK_SIZE = 1024 * 1024  # 1 MB chunks

def send_request(request):
    """Send a request to the server and return the response."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((SERVER_HOST, SERVER_PORT))
        client_socket.sendall(request.encode('utf-8'))
        response = client_socket.recv(4096).decode('utf-8')
        return json.loads(response)

def download_file(file_name):
    """Request and download a file from the server."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((SERVER_HOST, SERVER_PORT))
        client_socket.sendall(f"DOWNLOAD:{file_name}".encode('utf-8'))

        metadata = json.loads(client_socket.recv(1024).decode('utf-8'))
        if metadata.get("type") == "file":
            file_size = metadata["size"]
            with open(file_name, 'wb') as f:
                bytes_received = 0
                while bytes_received < file_size:
                    chunk = client_socket.recv(min(CHUNK_SIZE, file_size - bytes_received))
                    if not chunk:
                        break
                    f.write(chunk)
                    bytes_received += len(chunk)
            print(f"File '{file_name}' downloaded successfully.")
        else:
            print(metadata.get("error", "Error downloading file."))

def list_files_and_folders():
    """Get list of files and folders from the server."""
    response = send_request("LIST")
    return response if isinstance(response, list) else []

def navigate_folder(folder_name):
    """Navigate into a folder on the server."""
    response = send_request(f"NAVIGATE:{folder_name}")
    return response if isinstance(response, list) else []

def return_to_previous_folder():
    """Return to the parent folder on the server."""
    response = send_request("BACK")
    return response if isinstance(response, list) else []

if __name__ == "__main__":
    items = list_files_and_folders()
    
    while True:
        if items:
            print("\nFiles and folders available on the server:")
            for i, (item_type, item_name) in enumerate(items, start=1):
                print(f"{i}. [{item_type.upper()}] {item_name}")

            print("\nCommands: cd <number>, back, download <number>, exit")
            choice = input("Enter your choice: ").strip()

            if choice.startswith("cd "):
                try:
                    folder_number = int(choice[3:])
                    if 1 <= folder_number <= len(items):
                        item_type, item_name = items[folder_number - 1]
                        if item_type == "folder":
                            items = navigate_folder(item_name)
                        else:
                            print(f"'{item_name}' is not a folder.")
                except ValueError:
                    print("Invalid folder number.")

            elif choice == "back":
                items = return_to_previous_folder()

            elif choice.startswith("download "):
                try:
                    item_number = int(choice[9:])
                    if 1 <= item_number <= len(items):
                        item_type, item_name = items[item_number - 1]
                        if item_type == "file":
                            download_file(item_name)
                        else:
                            print(f"'{item_name}' is a folder. Folder downloads are not supported.")
                    else:
                        print("Invalid item number.")
                except ValueError:
                    print("Invalid item number.")

            elif choice == "exit":
                break

            else:
                print("Invalid command.")

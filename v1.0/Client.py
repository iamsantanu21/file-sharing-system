import socket
import os

# Server configuration
SERVER_HOST = '127.0.0.1'  # Server IP address
SERVER_PORT = 12345        # Server port

def list_files_and_folders():
    """Request a list of files and folders from the server."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        try:
            # Connect to the server
            client_socket.connect((SERVER_HOST, SERVER_PORT))
            print(f"Connected to server at {SERVER_HOST}:{SERVER_PORT}.")

            # Request the list of files and folders
            client_socket.sendall("LIST".encode('utf-8'))
            response = client_socket.recv(1024).decode('utf-8')  # Receive the server's response

            if response == "No files or folders found in the shared directory.":
                print(response)
                return []
            else:
                try:
                    items = eval(response)  # Convert the string back to a list
                    return items
                except SyntaxError:
                    print("Invalid response from the server.")
                    return []
        except Exception as e:
            print(f"Error listing files and folders: {e}")
            return []

def request_file_or_folder(item_name):
    """Request a specific file or folder from the server."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        try:
            # Connect to the server
            client_socket.connect((SERVER_HOST, SERVER_PORT))
            print(f"Connected to server at {SERVER_HOST}:{SERVER_PORT}.")

            # Send the item name to the server
            client_socket.sendall(item_name.encode('utf-8'))

            # Check if the item is a folder
            response = client_socket.recv(1024)
            if response == b"FOLDER_TRANSFER_START":
                # Handle folder transfer
                print(f"Downloading folder '{item_name}'...")
                while True:
                    # Receive the relative path length
                    path_length_bytes = client_socket.recv(4)
                    if not path_length_bytes:
                        break
                    path_length = int.from_bytes(path_length_bytes, 'big')
                    if path_length == 0:
                        break
                    # Receive the relative path
                    relative_path = client_socket.recv(path_length).decode('utf-8')
                    # Check for the "END_OF_FOLDER" signal
                    if relative_path == "END_OF_FOLDER":
                        break
                    # Receive the file size
                    file_size = int.from_bytes(client_socket.recv(8), 'big')
                    # Receive the file data
                    file_data = b""
                    while len(file_data) < file_size:
                        chunk = client_socket.recv(min(1024 * 1024, file_size - len(file_data)))
                        if not chunk:
                            break
                        file_data += chunk
                    # Save the file locally
                    file_path = os.path.join(relative_path)  # Use the relative path directly
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    with open(file_path, 'wb') as file:
                        file.write(file_data)
                    print(f"File '{relative_path}' received and saved.")
                print(f"Folder '{item_name}' downloaded successfully.")
            else:
                # Handle file transfer
                file_size = int.from_bytes(response, 'big')
                file_data = b""
                while len(file_data) < file_size:
                    chunk = client_socket.recv(min(1024 * 1024, file_size - len(file_data)))
                    if not chunk:
                        break
                    file_data += chunk
                # Save the received file locally
                with open(item_name, 'wb') as file:
                    file.write(file_data)
                print(f"File '{item_name}' received and saved successfully.")
        except Exception as e:
            print(f"Error downloading file or folder: {e}")

if __name__ == "__main__":
    # List files and folders in the shared directory
    items = list_files_and_folders()
    if items:
        print("Files and folders available on the server:")
        for i, (item_type, item_name) in enumerate(items):
            print(f"{i + 1}. [{item_type.upper()}] {item_name}")

        # Let the user choose a file or folder to download
        try:
            choice = int(input("Enter the number of the file or folder to download: "))
            if 1 <= choice <= len(items):
                item_type, item_name = items[choice - 1]
                request_file_or_folder(item_name)
            else:
                print("Invalid choice.")
        except ValueError:
            print("Please enter a valid number.")
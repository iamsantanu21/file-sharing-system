import os
import socket

# Server configuration
HOST = '127.0.0.1'  # Server IP
PORT = 12345        # Server port

def receive_listing(s):
    """Receive directory listing from the server."""
    data = ""
    while True:
        chunk = s.recv(1024).decode(errors="ignore")  # Ignore decode errors
        data += chunk
        if "END\n" in data:
            break
    return data

def download_file(s, file_name, file_size):
    """Download a file from the server."""
    with open(file_name, 'wb') as f:
        remaining_bytes = file_size
        while remaining_bytes > 0:
            data = s.recv(min(4096, remaining_bytes))
            if not data or data.endswith(b"EOF\n"):
                break
            f.write(data)
            remaining_bytes -= len(data)

def download_folder(s, folder_name):
    """Download a folder and its contents from the server."""
    os.makedirs(folder_name, exist_ok=True)
    while True:
        metadata = s.recv(1024)
        try:
            metadata = metadata.decode()
        except UnicodeDecodeError:
            print("Received binary data, expected metadata.")
            return

        if metadata.startswith("FILE:"):
            file_info = metadata.split(":")
            file_name = file_info[1].strip()
            file_size = int(file_info[2].strip())
            file_path = os.path.join(folder_name, file_name)
            download_file(s, file_path, file_size)
        elif metadata.startswith("FOLDER:"):
            folder_name = metadata.split(":")[1].strip()
            download_folder(s, folder_name)
        elif metadata.strip() == "EOF":
            break

def main():
    """Connect to the server and interact with it."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        print("Connected to server.")

        while True:
            # Receive directory listing
            listing = receive_listing(s)
            print(listing)

            # Get user input
            command = input("Enter command (cd <number>, back, download <number>, exit): ").strip()
            s.sendall(command.encode())

            if command.startswith("download"):
                metadata = s.recv(1024)
                try:
                    metadata = metadata.decode()
                except UnicodeDecodeError:
                    print("Received binary data unexpectedly.")
                    continue

                if metadata.startswith("FILE:"):
                    file_info = metadata.split(":")
                    file_name = file_info[1].strip()
                    file_size = int(file_info[2].strip())
                    download_file(s, file_name, file_size)
                    print(f"Downloaded file: {file_name}")
                elif metadata.startswith("FOLDER:"):
                    folder_name = metadata.split(":")[1].strip()
                    download_folder(s, folder_name)
                    print(f"Downloaded folder: {folder_name}")
                else:
                    print(metadata)

            elif command == "exit":
                break

            else:
                response = s.recv(1024).decode()
                print(response)

if __name__ == "__main__":
    main()

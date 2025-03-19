import os
import socket
import time

# Server configuration
HOST = '127.0.0.1'  # Server IP
PORT = 12345        # Server port

# Directory to share
INITIAL_DIRECTORY = "/Users/santanu_mac/Documents/GitHub/Distributed_image_processing/v2.0"

def list_directory(path):
    """List directories and files in the given path."""
    try:
        items = os.listdir(path)
        dirs = [item for item in items if os.path.isdir(os.path.join(path, item))]
        files = [item for item in items if os.path.isfile(os.path.join(path, item))]
        return dirs, files
    except Exception as e:
        print(f"Error listing directory: {e}")
        return [], []

def send_directory_listing(conn, dirs, files):
    """Send the directory listing to the client."""
    try:
        conn.sendall("Directories:\n".encode())
        for i, dir in enumerate(dirs):
            conn.sendall(f"{i+1}. [DIR] {dir}\n".encode())
        conn.sendall("Files:\n".encode())
        for i, file in enumerate(files):
            conn.sendall(f"{i+1}. [FILE] {file}\n".encode())
        conn.sendall("END\n".encode())  # Indicate end of listing
    except BrokenPipeError:
        print("Client disconnected while sending directory listing.")
    except Exception as e:
        print(f"Error sending directory listing: {e}")

def send_file(conn, file_path):
    """Send a file to the client."""
    try:
        file_size = os.path.getsize(file_path)
        conn.sendall(f"FILE:{os.path.basename(file_path)}:{file_size}\n".encode())

        with open(file_path, 'rb') as f:
            while True:
                data = f.read(4096)  # Use larger buffer for efficiency
                if not data:
                    break
                conn.sendall(data)
                time.sleep(0.001)  # Small delay to prevent overwhelming the client

        conn.sendall(b"EOF\n")  # Send EOF to indicate completion
    except BrokenPipeError:
        print("Client disconnected while sending file.")
    except Exception as e:
        print(f"Error sending file: {e}")

def send_folder(conn, folder_path):
    """Send a folder and its contents recursively to the client."""
    try:
        conn.sendall(f"FOLDER:{os.path.basename(folder_path)}\n".encode())

        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                send_file(conn, file_path)
    except BrokenPipeError:
        print("Client disconnected while sending folder.")
    except Exception as e:
        print(f"Error sending folder: {e}")

def handle_client(conn, addr):
    """Handle client requests."""
    print(f"Connected by {addr}")
    current_path = INITIAL_DIRECTORY

    while True:
        try:
            # Send directory listing
            dirs, files = list_directory(current_path)
            send_directory_listing(conn, dirs, files)

            # Receive client command
            data = conn.recv(1024).decode().strip()
            if not data:
                break

            # Process client command
            if data.startswith("cd"):
                try:
                    index = int(data.split()[1]) - 1
                    if 0 <= index < len(dirs):
                        current_path = os.path.join(current_path, dirs[index])
                    else:
                        conn.sendall(b"Invalid directory number.\n")
                except (IndexError, ValueError):
                    conn.sendall(b"Invalid command.\n")

            elif data == "back":
                if current_path != INITIAL_DIRECTORY:
                    current_path = os.path.dirname(current_path)
                else:
                    conn.sendall(b"Cannot go back further.\n")

            elif data.startswith("download"):
                try:
                    index = int(data.split()[1]) - 1
                    if 0 <= index < len(dirs):
                        send_folder(conn, os.path.join(current_path, dirs[index]))
                    elif 0 <= index - len(dirs) < len(files):
                        send_file(conn, os.path.join(current_path, files[index - len(dirs)]))
                    else:
                        conn.sendall(b"Invalid item number.\n")
                except (IndexError, ValueError, FileNotFoundError) as e:
                    conn.sendall(f"Error: {str(e)}\n".encode())

            elif data == "exit":
                break

            else:
                conn.sendall(b"Invalid command.\n")

        except Exception as e:
            print(f"Error handling client: {e}")
            break

    conn.close()
    print(f"Connection with {addr} closed.")

def main():
    """Start the server."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        print(f"Server listening on {HOST}:{PORT}")

        while True:
            conn, addr = s.accept()
            handle_client(conn, addr)

if __name__ == "__main__":
    main()

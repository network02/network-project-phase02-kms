import socket
import sys
import time
import os
import struct

print("\nWelcome to the FTP server.\n\nTo get started, connect a client.")

# Initialise socket stuff
TCP_IP = "127.0.0.1"  # Only a local server
TCP_PORT = 1456  # Just a random choice
BUFFER_SIZE = 1024  # Standard size
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((TCP_IP, TCP_PORT))
s.listen(1)
conn, addr = s.accept()

print("\nConnected to by address: {}".format(addr))


def upld():
    # Send message once the server is ready to receive file details
    conn.sendall(b"1")
    # Receive file name length, then file name
    file_name_size = struct.unpack("h", conn.recv(2))[0]
    file_name = conn.recv(file_name_size).decode()
    # Send message to let the client know the server is ready for document content
    conn.sendall(b"1")
    # Receive file size
    file_size = struct.unpack("i", conn.recv(4))[0]
    # Initialize and enter a loop to receive file content
    start_time = time.time()
    output_file = open(file_name, "wb")
    # This keeps track of how many bytes we have received, so we know when to stop the loop
    bytes_received = 0
    print("\nReceiving...")
    while bytes_received < file_size:
        l = conn.recv(BUFFER_SIZE)
        output_file.write(l)
        bytes_received += BUFFER_SIZE
    output_file.close()
    print("\nReceived file: {}".format(file_name))
    # Send upload performance details
    conn.sendall(struct.pack("f", time.time() - start_time))
    conn.sendall(struct.pack("i", file_size))
    return


def list_files():
    print("Listing files...")
    # Get a list of files in the directory
    print(os.getcwd())
    listing = os.listdir(os.getcwd())
    print(listing)
    
    # Send over the number of files so the client knows what to expect (and avoid some errors)
    conn.sendall(struct.pack("i", len(listing)))
    print("After sending the number of files")
    total_directory_size = 0
    # Send over the file names and sizes while totaling the directory size
    for i in listing:
        # File name size
        #print("file name size sending")
        conn.sendall(struct.pack("i", sys.getsizeof(i)))
        conn.recv(BUFFER_SIZE)
        # File name
        #print("file name sending")
        #print(i.encode())
        conn.sendall(i.encode())
        conn.recv(BUFFER_SIZE)
        # File content size
        #print("file content size")
        conn.sendall(struct.pack("i", os.path.getsize(i)))
        conn.recv(BUFFER_SIZE)
        total_directory_size += os.path.getsize(i)
        # Make sure that the client and server are synchronized
        conn.recv(BUFFER_SIZE)
        #print("synced")
    # Sum of file sizes in the directory
    conn.sendall(struct.pack("i", total_directory_size))
    # Final check
    conn.recv(BUFFER_SIZE)
    print("Successfully sent file listing")
    return


def dwld():
    conn.sendall(b"1")
    file_name_length = struct.unpack("h", conn.recv(2))[0]
    print(file_name_length)
    file_name = conn.recv(file_name_length).decode()
    print(file_name)
    if os.path.isfile(file_name):
        # Then the file exists, and send file size
        conn.sendall(struct.pack("i", os.path.getsize(file_name)))
    else:
        # Then the file doesn't exist, and send an error code
        print("File name not valid")
        conn.sendall(struct.pack("i", -1))
        return
    # Wait for ok to send the file
    conn.recv(BUFFER_SIZE)
    # Enter a loop to send the file
    start_time = time.time()
    print("Sending file...")
    content = open(file_name, "rb")
    # Again, break into chunks defined by BUFFER_SIZE
    l = content.read(BUFFER_SIZE)
    while l:
        conn.sendall(l)
        l = content.read(BUFFER_SIZE)
    content.close()
    # Get client go-ahead, then send download details
    conn.recv(BUFFER_SIZE)
    conn.sendall(struct.pack("f", time.time() - start_time))
    return


def delf():
    # Send go-ahead
    conn.sendall(b"1")
    # Get file details
    file_name_length = struct.unpack("h", conn.recv(2))[0]
    file_name = conn.recv(file_name_length).decode()
    # Check if the file exists
    if os.path.isfile(file_name):
        conn.sendall(struct.pack("i", 1))
    else:
        # Then the file doesn't exist
        conn.sendall(struct.pack("i", -1))
        return
    # Wait for deletion confirmation
    confirm_delete = conn.recv(BUFFER_SIZE).decode()
    if confirm_delete == "Y":
        try:
            # Delete the file
            os.remove(file_name)
            conn.sendall(struct.pack("i", 1))
        except:
            # Unable to delete the file
            print("Failed to delete {}".format(file_name))
            conn.sendall(struct.pack("i", -1))
    else:
        # User abandoned deletion
        # The server probably received "N", but else used as a safety catch-all
        print("Delete abandoned by the client!")
        return


def quit_program():
    # Send quit confirmation
    conn.sendall(b"1")
    # Close and restart the server
    conn.close()
    s.close()
    os.execl(sys.executable, sys.executable, *sys.argv)


while True:
    # Enter into a while loop to receive commands from the client
    print("\n\nWaiting for instruction")
    data = conn.recv(BUFFER_SIZE).decode()
    print("\nReceived instruction: {}".format(data))
    # Check the command and respond correctly
    if data == "UPLD":
        upld()
    elif data == "LIST":
        list_files()
    elif data == "DWLD":
        dwld()
    elif data == "DELF":
        delf()
    elif data == "QUIT":
        quit_program()
    # Reset the data to loop
    data = None

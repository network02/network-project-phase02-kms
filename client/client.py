import socket
import sys
import os
import struct

# Initialise socket stuff
TCP_IP = "127.0.0.1"  # Only a local server
TCP_PORT = 1456  # Just a random choice
BUFFER_SIZE = 1024  # Standard choice
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

def connect():
    # Connect to the server
    print("Sending server request...")
    try:
        s.connect((TCP_IP, TCP_PORT))
        print("Connection successful")
    except:
        print("Connection unsuccessful. Make sure the server is online.")

def upld(file_name):
    # Upload a file
    print("\nUploading file: {}...".format(file_name))
    try:
        # Check if the file exists
        content = open(file_name, "rb")
    except:
        print("Couldn't open file. Make sure the file name was entered correctly.")
        return None
    try:
        # Make upload request
        s.sendall(b"UPLD")
    except:
        print("Couldn't make server request. Make sure a connection has been established.")
        return None 
    try:
        # Wait for server acknowledgement then send file details
        # Wait for server ok
        s.recv(BUFFER_SIZE)
        # Send file name size and file name
        s.sendall(struct.pack("h", sys.getsizeof(file_name)))
        s.sendall(file_name.encode())
        # Wait for server ok then send file size
        s.recv(BUFFER_SIZE)
        s.sendall(struct.pack("i", os.path.getsize(file_name)))
    except:
        print("Error sending file details")
    try:
        # Send the file in chunks defined by BUFFER_SIZE
        # Doing it this way allows for unlimited potential file sizes to be sent
        l = content.read(BUFFER_SIZE)
        print("\nSending...")
        while l:
            s.sendall(l)
            l = content.read(BUFFER_SIZE)
        content.close()
        # Get upload performance details
        upload_time = struct.unpack("f", s.recv(4))[0]
        upload_size = struct.unpack("i", s.recv(4))[0]
        print("\nSent file: {}\nTime elapsed: {}s\nFile size: {}b".format(file_name, upload_time, upload_size))
    except:
        print("Error sending file")
        return None
    return None

def list_files():
    # List the files available on the file server
    # Called list_files(), not list() (as in the format of the others) to avoid the standard python function list()
    print("Requesting files...\n")
    try:
        # Send list request
        s.sendall(b"LIST")
    except:
        print("Couldn't make server request. Make sure a connection has been established.")
        return None
    try:
        # First get the number of files in the directory
        number_of_files = struct.unpack("i", s.recv(4))[0]
        # Then enter into a loop to receive details of each, one by one
        for i in range(int(number_of_files)):
            # Get the file name size first to slightly lessen amount transferred over socket
            file_name_size = struct.unpack("i", s.recv(4))[0]
            s.sendall(b"1")
            #print(file_name_size)
            file_name = s.recv(file_name_size).decode()
            s.sendall(b"1")
            #print(file_name)
            # Also get the file size for each item in the server
            file_size = struct.unpack("i", s.recv(4))[0]
            s.sendall(b"1")
            #print(file_size)
            print("\t{} - {}b".format(file_name, file_size))
            # Make sure that the client and server are synchronized
            s.sendall(b"1")
            #print("next")
        # Get the total size of the directory
        total_directory_size = struct.unpack("i", s.recv(4))[0]
        print("Total directory size: {}b".format(total_directory_size))
    except:
        print("Couldn't retrieve listing")
        return None
    try:
        # Final check
        s.sendall(b"1")
        return None
    except:
        print("Couldn't get final server confirmation")
        return None

def dwld(file_name):
    # Download given file
    print("Downloading file: {}".format(file_name))
    try:
        # Send server request
        s.sendall(b"DWLD")
    except:
        print("Couldn't make server request. Make sure a connection has been established.")
        return None
    try:
        # Wait for server ok, then make sure the file exists
        s.recv(BUFFER_SIZE)
        # Send file name length, then name
        s.sendall(struct.pack("h", sys.getsizeof(file_name)))
        s.sendall(file_name.encode())
        # Get file size (if exists)
        file_size = struct.unpack("i", s.recv(4))[0]
        if file_size == -1:
            # If file size is -1, the file does not exist
            print("File does not exist. Make sure the name was entered correctly")
            return None
    except:
        print("Error checking file")
    try:
        # Send ok to receive file content
        s.sendall(b"1")
        # Enter loop to receive file
        output_file = open(file_name, "wb")
        bytes_received = 0
        print("\nDownloading...")
        while bytes_received < file_size:
            # Again, file broken into chunks defined by the BUFFER_SIZE variable
            l = s.recv(BUFFER_SIZE)
            output_file.write(l)
            bytes_received += BUFFER_SIZE
        output_file.close()
        print("Successfully downloaded {}".format(file_name))
        # Tell the server that the client is ready to receive the download performance details
        s.sendall(b"1")
        # Get performance details
        time_elapsed = struct.unpack("f", s.recv(4))[0]
        print("Time elapsed: {}s\nFile size: {}b".format(time_elapsed, file_size))
    except:
        print("Error downloading file")
        return None
    return None

def delf(file_name):
    # Delete specified file from the file server
    print("Deleting file: {}...".format(file_name))
    try:
        # Send request, then wait for go-ahead
        s.sendall(b"DELF")
        s.recv(BUFFER_SIZE)
    except:
        print("Couldn't connect to the server. Make sure a connection has been established.")
        return None
    try:
        # Send file name length, then file name
        s.sendall(struct.pack("h", sys.getsizeof(file_name)))
        s.sendall(file_name.encode())
    except:
        print("Couldn't send file details")
        return None
    try:
        # Get confirmation that file does/doesn't exist
        file_exists = struct.unpack("i", s.recv(4))[0]
        if file_exists == -1:
            print("The file does not exist on the server")
            return None
    except:
        print("Couldn't determine file existence")
        return None
    try:
        # Confirm user wants to delete the file
        confirm_delete = input("Are you sure you want to delete {}? (Y/N)\n".format(file_name)).upper()
        # Make sure input is valid
        # Unfortunately, Python doesn't have a do-while style loop, as that would have been better here
        while confirm_delete != "Y" and confirm_delete != "N" and confirm_delete != "YES" and confirm_delete != "NO":
            # If user input is invalid
            print("Command not recognized, try again")
            confirm_delete = input("Are you sure you want to delete {}? (Y/N)\n".format(file_name)).upper()
    except:
        print("Couldn't confirm deletion status")
        return None
    try:
        # Send confirmation
        if confirm_delete == "Y" or confirm_delete == "YES":
            # User wants to delete the file
            s.sendall(b"Y")
            # Wait for confirmation file has been deleted
            delete_status = struct.unpack("i", s.recv(4))[0]
            if delete_status == 1:
                print("File successfully deleted")
                return None
            else:
                # Client will probably send -1 to get here, but an else is used as more of a catch-all
                print("File failed to delete")
                return None
        else:
            s.sendall(b"N")
            print("Delete abandoned by user!")
            return None
    except:
        print("Couldn't delete the file")
        return None

def make_directory(directory_name):
    # Delete specified file from the file server
    print("Creating Directory: {}...".format(directory_name))
    try:
        # Send request, then wait for go-ahead
        s.sendall(b"MKD")
        s.recv(BUFFER_SIZE)
    except:
        print("Couldn't connect to the server. Make sure a connection has been established.")
        return None
    try:
        # Send directory path name length, then directory path name
        s.sendall(struct.pack("h", sys.getsizeof(directory_name)))
        s.recv(BUFFER_SIZE)
        s.sendall(directory_name.encode())
        s.recv(BUFFER_SIZE)
    except:
        print("Couldn't send Directory details")
        return None
     
    directory_check = int(s.recv(BUFFER_SIZE).decode())
    if directory_check:
        print("directory created successfully.")
    else:
        print("couldn't create the directory.")
    return None


def remove_directory(directory_name):
    # Delete specified file from the file server
    print("Removing Directory: {}...".format(directory_name))
    try:
        # Send request, then wait for go-ahead
        s.sendall(b"RMD")
        s.recv(BUFFER_SIZE)
    except:
        print("Couldn't connect to the server. Make sure a connection has been established.")
        return None
    try:
        # Send directory path name length, then directory path name
        s.sendall(struct.pack("h", sys.getsizeof(directory_name)))
        s.recv(BUFFER_SIZE)
        s.sendall(directory_name.encode())
        s.recv(BUFFER_SIZE)
    except:
        print("Couldn't send Directory details")
        return None
     
    directory_check = int(s.recv(BUFFER_SIZE).decode())
    if directory_check:
        print("directory removed successfully.")
    else:
        print("couldn't remove the directory.")
    return None
        
    
def get_path_directory():
    # Delete specified file from the file server
    print("Getting the path...")
    try:
        # Send request, then wait for go-ahead
        s.sendall(b"PWD")
        s.recv(BUFFER_SIZE)
    except:
        print("Couldn't connect to the server. Make sure a connection has been established.")
        return None
    try:
        # Send directory path name length, then directory path name
        path_len = int(s.recv(BUFFER_SIZE).decode())
        print(path_len)
        s.sendall(b"1")
        path = s.recv(path_len).decode()
        s.sendall(b"1")
        print(path)
    except:
        print("Couldn't receive path.")
        return None
    return None


def change_current_directory(new_path):

    print("Changing Directory: {}...".format(new_path))
    try:
        # Send request, then wait for go-ahead
        s.sendall(b"CWD")
        s.recv(BUFFER_SIZE)
    except:
        print("Couldn't connect to the server. Make sure a connection has been established.")
        return None
    try:
        # Send directory path name length, then directory path name
        s.sendall(struct.pack("h", sys.getsizeof(new_path)))
        s.recv(BUFFER_SIZE)
        s.sendall(new_path.encode())
        s.recv(BUFFER_SIZE)
    except:
        print("Couldn't send Path details")
        return None
     
    change_check = int(s.recv(BUFFER_SIZE).decode())
    if change_check:
        print("path changed successfully.")
    else:
        print("couldn't change path.")
    return None

def noghte_noghte_directory():
    print("Changing Directory: {}...".format('../'))
    try:
        # Send request, then wait for go-ahead
        s.sendall(b"CDUP")
        s.recv(BUFFER_SIZE)
    except:
        print("Couldn't connect to the server. Make sure a connection has been established.")
        return None
    
    change_check = int(s.recv(BUFFER_SIZE).decode())
    if change_check:
        print("path changed successfully.")
    else:
        print("couldn't change path.")
    return None

def quit_program():
    s.sendall(b"QUIT")
    # Wait for server go-ahead
    s.recv(BUFFER_SIZE)
    s.close()
    print("Server connection ended")
    return None

print("""\n\nWelcome to the FTP client.
      
      Call one of the following functions:
      CONN               : Connect to server
      STOR file_path     : Upload file
      LIST               : List files
      RETR file_path     : Download file
      DELE file_path     : Delete file
      MKD directory_name : Create directory
      RMD directory_name : Remove directory
      PWD                : Current path
      CWD path           : changing path
      CDUP               : ../
      QUIT               : Exit""")

while True:
    # Listen for a command
    prompt = input("\nEnter a command: ").split()
    if prompt[0].upper() == "CONN":
        connect()
    elif prompt[0].upper() == "STOR":
        upld(prompt[1])
    elif prompt[0].upper() == "LIST":
        list_files()
    elif prompt[0].upper() == "RETR":
        dwld(prompt[1])
    elif prompt[0].upper() == "DELE":
        delf(prompt[1])
    elif prompt[0].upper() == "MKD":
        make_directory(prompt[1])
    elif prompt[0].upper() == "RMD":
        remove_directory(prompt[1])
    elif prompt[0].upper() == "PWD":
        get_path_directory()
    elif prompt[0].upper() == "CWD":
        change_current_directory(prompt[1])
    elif prompt[0].upper() == "CDUP":
        noghte_noghte_directory()
    elif prompt[0].upper() == "QUIT":
        quit_program()
        break
    else:
        print("Command not recognized; please try again")

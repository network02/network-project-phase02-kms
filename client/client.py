import socket
import sys
import os


TCP_IP = "127.0.0.1"  
TCP_PORT = 1456  
BUFFER_SIZE = 1024  
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

def connect():
    
    print("Sending server request...")
    try:
        s.connect((TCP_IP, TCP_PORT))
        print("200 OK! Connection successful")
    except:
        print("400 Connection unsuccessful. Make sure the host is online.")


def user(username: str):
    try:
        s.sendall(b"USER")
    except Exception as e:
        print("421 Couldn't make server request. Make sure a connection has been established.")
        print(f"{e}, {type(e)}")
        return None
    
    s.sendall(f"{username}".encode())
    s.recv(BUFFER_SIZE)

    message = s.recv(BUFFER_SIZE).decode()
    print(message)


def password(password: str):
    try:
        s.sendall(b"PASS")
    except Exception as e:
        print("421 Couldn't make server request. Make sure a connection has been established.")
        print(f"{e}, {type(e)}")
        return None

    s.sendall(f"{password}".encode())
    message = s.recv(BUFFER_SIZE).decode()
    print(message)


def upload(file_name):
    try:
        s.sendall(b"STOR")
    except Exception as e:
        print("421 Couldn't make server request. Make sure a connection has been established.")
        print(f"{e}, {type(e)}")
        return None
        
    data_port = int(s.recv(BUFFER_SIZE).decode())
    s.sendall(b"1")

    # s.recv(BUFFER_SIZE)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as data_socket:
        try:
            data_socket.connect((TCP_IP, data_port))
            print("200 OK! DATA Connection successful!")
        except Exception as e:
            print(f"{e}, {type(e)}")
            return None

        # Upload a file
        print("\nUploading file: {}...".format(file_name))
        
        try:
            content = open(file_name, "rb")
        except Exception as e:
            print("450 Couldn't open file. Make sure the file name was entered correctly.")
            print(f"{e}, {type(e)}")
            return None
        
        try:
            # Wait for server acknowledgement then send file details
            # Wait for server ok
            data_socket.recv(BUFFER_SIZE)
            # Send file name size and file name
            data_socket.sendall(sys.getsizeof(file_name).encode())
            data_socket.sendall(file_name.encode())
            # Wait for server ok then send file size
            data_socket.recv(BUFFER_SIZE)
            data_socket.sendall(os.path.getsize(file_name).encode())
        except Exception as e:
            print(f"{e}, {type(e)}")
            print("450 Error sending file details")
            
        try:
            # Send the file in chunks defined by BUFFER_SIZE
            # Doing it this way allows for unlimited potential file sizes to be sent
            l = content.read(BUFFER_SIZE)
            print("\nSending...")
            while l:
                data_socket.sendall(l)
                print("...")
                l = content.read(BUFFER_SIZE)
            content.close()
            # Get upload performance details
            upload_time = data_socket.recv(4).decode()
            upload_size = data_socket.recv(4).decode()
            print("\nSent file: {}\nTime elapsed: {}s\nFile size: {}b".format(file_name, upload_time, upload_size))
        except Exception as e:
            print(f"{e}, {type(e)}")
            print("450 Error sending file")
            return None
    return None

def sleeep():
    s.sendall(b"SLEEP")
    s.recv(1024)


def list_files(path_name):
    
    print("Requesting files...\n")
    try:
        s.sendall(b"LIST")
    except Exception as e:
        print(f"{e}, {type(e)}")
        print("421 Couldn't make server request. Make sure a connection has been established.")
        return None
    
    try: 
        s.sendall(sys.getsizeof(path_name).encode())
        s.recv(BUFFER_SIZE)
        s.sendall(path_name.encode())
        s.recv(BUFFER_SIZE)
    except Exception as e:
        print(f"{e}, {type(e)}")
        return None
    
    if os.path.isdir(path_name):    
        try:
            number_of_files = s.recv(4).decode()
            for i in range(int(number_of_files)):
                file_name_size = s.recv(4).decode()
                s.sendall(b"1")
                file_name = s.recv(file_name_size).decode()
                s.sendall(b"1")
                
                file_size = s.recv(BUFFER_SIZE).decode()
                s.sendall(b"1")
                
                print("\t{} - {}b".format(file_name, file_size))
                
                s.sendall(b"1")
                
            total_directory_size = s.recv(4).decode()
            print("Total directory size: {}b".format(total_directory_size))
        except Exception as e:
            print(f"{e}, {type(e)}")
            return None
        
        try:
            s.sendall(b"1")
            return None
        except Exception as e:
            print(f"{e}, {type(e)}")
            print("451 Couldn't get final server confirmation")
            return None
        
    elif os.path.isfile(path_name):
        file_size = s.recv(BUFFER_SIZE).decode()
        s.sendall(b"1")
        bytes_received = 0
        content = ""
        print("\nReceiving...")
        while bytes_received < file_size:
            l = s.recv(BUFFER_SIZE).decode()
            content += l
            bytes_received += BUFFER_SIZE
        print(content)


def download(file_name):
    try:
        s.sendall(b"RETR")
    except Exception as e:
        print(f"{e}, {type(e)}")
        print("421 Couldn't make server request. Make sure a connection has been established.")
        return None
    
    data_port = int(s.recv(BUFFER_SIZE).decode())
    s.sendall(b"1")

    # s.recv(BUFFER_SIZE)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as data_socket:
        try:
            data_socket.connect((TCP_IP, data_port))
            print("200 OK! DATA Connection successful!")
        except Exception as e:
            print(f"{e}, {type(e)}")
            return None
        
        print("Downloading file: {}".format(file_name))
        
        try:
            data_socket.recv(BUFFER_SIZE)
            print("haha")

            data_socket.sendall(sys.getsizeof(file_name).encode())
            data_socket.sendall(file_name.encode())

            file_size = int(data_socket.recv(4).decode())
            if file_size == -1:
                print("450 File does not exist. Make sure the name was entered correctly")
                return None
        except Exception as e:
                print(f"{e}, {type(e)}")
                print("450 Error checking file")
                return None
        try:
            data_socket.sendall(b"1")

            output_file = open(file_name, "wb")
            bytes_received = 0
            print("\nDownloading...")
            while bytes_received < file_size:
                l = data_socket.recv(BUFFER_SIZE)
                output_file.write(l)
                bytes_received += BUFFER_SIZE
            output_file.close()
            print("250 OK! Successfully downloaded {}".format(file_name))
            # client is ready to receive the download performance details
            data_socket.sendall(b"1")
            
            time_elapsed = s.recv(4).decode()
            print("Time elapsed: {}s\nFile size: {}b".format(time_elapsed, file_size))
        except Exception as e:
            print(f"{e}, {type(e)}")
            print("450 Error downloading file")
            return None
    return None

def delete_file(file_name):
    print("Deleting file: {}...".format(file_name))
    
    try:
        s.sendall(b"DELE")
        s.recv(BUFFER_SIZE)
    except Exception as e:
        print(f"{e}, {type(e)}")
        print("421 Couldn't connect to the server. Make sure a connection has been established.")
        return None
    
    try:
        s.sendall(sys.getsizeof(file_name).encode())
        s.sendall(file_name.encode())
    except Exception as e:
        print(f"{e}, {type(e)}")
        print("450 Couldn't send file details")
        return None
    
    try:
        file_exists = s.recv(4).decode()
        if file_exists == -1:
            print("450 The file does not exist on the server")
            return None
    except Exception as e:
        print(f"{e}, {type(e)}")
        print("450 Couldn't determine file existence")
        return None
    
    try:
        confirm_delete = input("Are you sure you want to delete {}? (Y/N)\n".format(file_name)).upper()
        
        while confirm_delete != "Y" and confirm_delete != "N" and confirm_delete != "YES" and confirm_delete != "NO":
            print("502 Command not recognized, try again")
            confirm_delete = input("Are you sure you want to delete {}? (Y/N)\n".format(file_name)).upper()
    except Exception as e:
        print(f"{e}, {type(e)}")
        print("400 Couldn't confirm deletion status")
        return None
    
    try:
        if confirm_delete == "Y" or confirm_delete == "YES":
            s.sendall(b"Y")
            delete_status = int(s.recv(4).decode())
            if delete_status == 1:
                print("250 OK! File successfully deleted")
                return None
            else:
                print("450 File failed to delete")
                return None
        else:
            s.sendall(b"N")
            print("200 OK!Delete abandoned by user!")
            return None
    except:
        print("450 Couldn't delete the file")
        return None

def make_directory(directory_name):
    print("Creating Directory: {}...".format(directory_name))
    try:
        
        s.sendall(b"MKD")
        s.recv(BUFFER_SIZE)
    except:
        print("421 Couldn't connect to the server. Make sure a connection has been established.")
        return None
    
    try:
        s.sendall(sys.getsizeof(directory_name).encode())
        s.recv(BUFFER_SIZE)
        s.sendall(directory_name.encode())
        s.recv(BUFFER_SIZE)
    except:
        print("450 Couldn't send Directory details")
        return None
     
    directory_check = int(s.recv(BUFFER_SIZE).decode())
    if directory_check:
        print("200 OK! directory created successfully.")
    else:
        print("400 couldn't create the directory.")
    return None


def remove_directory(directory_name):
    print("Removing Directory: {}...".format(directory_name))
    try:
        s.sendall(b"RMD")
        s.recv(BUFFER_SIZE)
    except:
        print("421 Couldn't connect to the server. Make sure a connection has been established.")
        return None
    try:
        s.sendall(sys.getsizeof(directory_name).encode())
        s.recv(BUFFER_SIZE)
        s.sendall(directory_name.encode())
        s.recv(BUFFER_SIZE)
    except:
        print("450 Couldn't send Directory details")
        return None
     
    directory_check = int(s.recv(BUFFER_SIZE).decode())
    if directory_check:
        print("200 OK! directory removed successfully.")
    else:
        print("400 couldn't remove the directory.")
    return None
        
    
def get_path_directory():
    print("Getting the path...")
    try:
        s.sendall(b"PWD")
        s.recv(BUFFER_SIZE)
    except:
        print("421 Couldn't connect to the server. Make sure a connection has been established.")
        return None
    
    try:
        path_len = int(s.recv(BUFFER_SIZE).decode())
        print(path_len)
        s.sendall(b"1")
        path = s.recv(path_len).decode()
        s.sendall(b"1")
        print(path)
    except:
        print("452 Couldn't receive path.")
        return None
    return None


def change_current_directory(new_path):

    print("Changing Directory: {}...".format(new_path))
    try:
        s.sendall(b"CWD")
        s.recv(BUFFER_SIZE)
    except:
        print("421 `Couldn't connect to the server. Make sure a connection has been established.")
        return None
    try:
        s.sendall(sys.getsizeof(new_path).encode())
        s.recv(BUFFER_SIZE)
        s.sendall(new_path.encode())
        s.recv(BUFFER_SIZE)
    except:
        print("400 Couldn't send Path details")
        return None
     
    change_check = int(s.recv(BUFFER_SIZE).decode())
    if change_check:
        print("200 OK!path changed successfully.")
    else:
        print("400 couldn't change path.")
    return None

def noghte_noghte_directory():
    print("Changing Directory: {}...".format('../'))
    try:
        s.sendall(b"CDUP")
        s.recv(BUFFER_SIZE)
    except:
        print("421 Couldn't connect to the server. Make sure a connection has been established.")
        return None
    
    change_check = int(s.recv(BUFFER_SIZE).decode())
    if change_check:
        print("200 OK! path changed successfully.")
    else:
        print("400 couldn't change path.")
    return None

def quit_program():
    s.sendall(b"QUIT")
    s.recv(BUFFER_SIZE)
    s.close()
    print("200 OK! Server connection ended")
    return None

print("""\n\nWelcome to the FTP client.
      
      Call one of the following functions:
      CONN               : Connect to server
      USER username      : Enter Username
      PASS password      : Enter Password
      STOR file_path     : Upload file
      LIST path_name     : List files
      RETR file_path     : Download file
      DELE file_path     : Delete file
      MKD directory_name : Create directory
      RMD directory_name : Remove directory
      PWD                : Current path
      CWD path           : changing path
      CDUP               : ../
      QUIT               : Exit""")

while True:
    # handle first command has to be user

    prompt = input("\nEnter a command: ").split()
    if prompt[0].upper() == "CONN":
        connect()
    elif prompt[0].upper() == "USER":
        user(prompt[1])
    elif prompt[0].upper() == "PASS":
        password(prompt[1])
    elif prompt[0].upper() == "STOR":
        upload(prompt[1])
    elif prompt[0].upper() == "LIST":
        list_files(prompt[1])
    elif prompt[0].upper() == "RETR":
        download(prompt[1])
    elif prompt[0].upper() == "DELE":
        delete_file(prompt[1])
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
    elif prompt[0].upper() == "SLEEP":
        sleeep()
    elif prompt[0].upper() == "QUIT":
        quit_program()
        break
    else:
        print("502 Command not recognized; please try again")

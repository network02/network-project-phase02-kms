import socket
import sys
import time
import os
import struct
import random
import json
from threading import Thread

class Client(Thread):
    TCP_IP = "127.0.0.1"
    TCP_PORT = 1456
    TCP_DATA_PORT = random.randint(4000, 5000)
    BUFFER_SIZE = 1024

    def __init__(self, conn) -> None:
        self.conn = conn
        self.exist = False
        self.authenticated = False
        self.username = None
        self.password = None

        super().__init__()

    def run(self):
        while True:
            # Enter into a while loop to receive commands from the client
            print("\n\nWaiting for instruction")
            data = self.conn.recv(Client.BUFFER_SIZE).decode()
            print("\nReceived instruction: {}".format(data))
            # save_history(data)
            # Check the command and respond correctly
            if data == "USER":
                self.check_user()
            elif data == "PASS":
                self.check_password()
            elif self.authenticated:
                if data == "STOR":
                    self.upld()
                elif data == "LIST":
                    self.list_files()
                elif data == "RETR":
                    self.dwld()
                elif data == "DELE":
                    self.delf()
                elif data == "MKD":
                    self.make_directory()
                elif data == "RMD":
                    self.remove_directory()
                elif data == "PWD":
                    self.get_path_directory()
                elif data == "CWD":
                    self.change_current_directory()
                elif data == "CDUP":
                    self.noghte_noghte_directory()
                elif data == "QUIT":
                    self.quit_program()
                    break
                else:
                    pass
            else:
                pass
            # Reset the data to loop
            data = None

    def check_user(self):
        self.authenticated = False
        self.exist = False
        self.username = None
        self.password = None
        username = self.conn.recv(Client.BUFFER_SIZE).decode()
        self.conn.sendall(b"1")

        self.username_exist(username)
        if self.exist:
            self.conn.sendall(b"OK, Enter PASS command to log in.")
        else:
            self.conn.sendall(b"User created, Enter PASS command to log in.")

    def check_password(self):
        password = self.conn.recv(Client.BUFFER_SIZE).decode()

        if self.exist:
            self.user_authentication(password)

            if self.authenticated:
                self.conn.sendall(b"OK, You are logged In.")
            else:
                self.conn.sendall(b"BORO KHONATON!")
        else:
            self.user_create(password)
            self.conn.sendall(b"User created with new password")

    def username_exist(self, username):
        self.username = username
        with open("data.json", "r") as user_file:
            print("file opened:exist")
            for line in user_file:
                print("searching...")
                user = json.loads(line)
                if user['username'] == username:
                    self.exist = True
                    return True
        return False

    def user_authentication(self, password):
        with open("data.json", "r") as user_file:
            print("file opened:auth")
            for line in user_file:
                print("searching...")
                user = json.loads(line)
                if user['password'] == password:
                    self.authenticated = True
                    self.password = password
                    return True
        return False

    def user_create(self, password):
        self.password = password
        user_dict = {"username": self.username, "password": self.password}
        with open("data.json", "a") as user_file:
            json.dump(user_dict, user_file)
            user_file.write("\n")

    def upld(self):
        self.conn.sendall(str(Client.TCP_DATA_PORT).encode())
        self.conn.recv(Client.BUFFER_SIZE)

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as data_socket:
            data_socket.bind((Client.TCP_IP, Client.TCP_DATA_PORT))
            data_socket.listen()
            self.conn.sendall(b"1")
            client_data_socket, client_data_address = data_socket.accept()
            print("\nConnected DATA to by address: {}".format(client_data_address))
            
            client_data_socket.sendall(b"1")
            
            file_name_size = struct.unpack("h", client_data_socket.recv(2))[0]
            file_name = client_data_socket.recv(file_name_size).decode()
            
            client_data_socket.sendall(b"1")
            
            file_size = struct.unpack("i", client_data_socket.recv(4))[0]
            
            start_time = time.time()
            output_file = open(file_name, "wb")

            bytes_received = 0
            print("\nReceiving...")
            while bytes_received < file_size:
                l = client_data_socket.recv(Client.BUFFER_SIZE)
                output_file.write(l)
                bytes_received += Client.BUFFER_SIZE
            output_file.close()
            print("\nReceived file: {}".format(file_name))

            client_data_socket.sendall(struct.pack("f", time.time() - start_time))
            client_data_socket.sendall(struct.pack("i", file_size))
        return None

    def list_files(self):
        print("Listing files...")
        # Get a list of files in the directory
        print(os.getcwd())
        listing = os.listdir(os.getcwd())
        print(listing)
        
        # Send over the number of files so the client knows what to expect (and avoid some errors)
        self.conn.sendall(struct.pack("i", len(listing)))
        print("After sending the number of files")
        total_directory_size = 0
        # Send over the file names and sizes while totaling the directory size
        for i in listing:
            # File name size
            #print("file name size sending")
            self.conn.sendall(struct.pack("i", sys.getsizeof(i)))
            self.conn.recv(Client.BUFFER_SIZE)
            # File name
            #print("file name sending")
            #print(i.encode())
            self.conn.sendall(i.encode())
            self.conn.recv(Client.BUFFER_SIZE)
            # File content size
            #print("file content size")
            self.conn.sendall(struct.pack("i", os.path.getsize(i)))
            self.conn.recv(Client.BUFFER_SIZE)
            total_directory_size += os.path.getsize(i)
            # Make sure that the client and server are synchronized
            self.conn.recv(Client.BUFFER_SIZE)
            #print("synced")
        # Sum of file sizes in the directory
        self.conn.sendall(struct.pack("i", total_directory_size))
        # Final check
        self.conn.recv(Client.BUFFER_SIZE)
        print("Successfully sent file listing")
        return None 

    def dwld(self):
        self.conn.sendall(b"1")
        file_name_length = struct.unpack("h", self.conn.recv(2))[0]
        print(file_name_length)
        file_name = self.conn.recv(file_name_length).decode()
        print(file_name)
        if os.path.isfile(file_name):
            # Then the file exists, and send file size
            self.conn.sendall(struct.pack("i", os.path.getsize(file_name)))
        else:
            # Then the file doesn't exist, and send an error code
            print("File name not valid")
            self.conn.sendall(struct.pack("i", -1))
            return None
        # Wait for ok to send the file
        self.conn.recv(Client.BUFFER_SIZE)
        # Enter a loop to send the file
        start_time = time.time()
        print("Sending file...")
        content = open(file_name, "rb")
        # Again, break into chunks defined by Client.BUFFER_SIZE
        l = content.read(Client.BUFFER_SIZE)
        while l:
            self.conn.sendall(l)
            l = content.read(Client.BUFFER_SIZE)
        content.close()
        # Get client go-ahead, then send download details
        self.conn.recv(Client.BUFFER_SIZE)
        self.conn.sendall(struct.pack("f", time.time() - start_time))
        return None

    def delf(self):
        # Send go-ahead
        self.conn.sendall(b"1")
        # Get file details
        file_name_length = struct.unpack("h", self.conn.recv(2))[0]
        file_name = self.conn.recv(file_name_length).decode()
        # Check if the file exists
        if os.path.isfile(file_name):
            self.conn.sendall(struct.pack("i", 1))
        else:
            # Then the file doesn't exist
            self.conn.sendall(struct.pack("i", -1))
            return None
        # Wait for deletion confirmation
        confirm_delete = self.conn.recv(Client.BUFFER_SIZE).decode()
        if confirm_delete == "Y":
            try:
                # Delete the file
                os.remove(file_name)
                self.conn.sendall(struct.pack("i", 1))
            except:
                # Unable to delete the file
                print("Failed to delete {}".format(file_name))
                self.conn.sendall(struct.pack("i", -1))
        else:
            # User abandoned deletion
            # The server probably received "N", but else used as a safety catch-all
            print("Delete abandoned by the client!")
            return None

    def make_directory(self):
        # Send go-ahead
        self.conn.sendall(b"1")
        # Get Directory details
        directory_name_length = struct.unpack("h", self.conn.recv(2))[0]
        print(directory_name_length)
        self.conn.sendall(b"1")
        directory_name = self.conn.recv(directory_name_length).decode()
        print(directory_name)
        self.conn.sendall(b"1")
        try: 
            os.mkdir(directory_name) 
            self.conn.sendall(b"1")
        except OSError as error: 
            print(error)
            self.conn.sendall(b"0")
        return None

    def remove_directory(self):
        # Send go-ahead
        self.conn.sendall(b"1")
        # Get Directory details
        directory_name_length = struct.unpack("h", self.conn.recv(2))[0]
        print(directory_name_length)
        self.conn.sendall(b"1")
        directory_name = self.conn.recv(directory_name_length).decode()
        print(directory_name)
        self.conn.sendall(b"1")
        try: 
            os.rmdir(directory_name) 
            self.conn.sendall(b"1")
        except OSError as error: 
            print(error)
            self.conn.sendall(b"0")
        return None

    def get_path_directory(self):
        # Send go-ahead
        self.conn.sendall(b"1")

        try:
            cwd = os.getcwd()
            print(cwd)
            self.conn.sendall(str(sys.getsizeof(cwd)).encode())
            self.conn.recv(Client.BUFFER_SIZE)
            self.conn.sendall(cwd.encode())
            self.conn.recv(Client.BUFFER_SIZE)
        except OSError as error: 
            print(error)
        except Exception as e:
            print(e)
            print("couldn't send path.")
        return None

    def change_current_directory(self):
        # Send go-ahead
        self.conn.sendall(b"1")
        # Get Directory details
        new_path_length = struct.unpack("h", self.conn.recv(2))[0]
        self.conn.sendall(b"1")
        new_path = self.conn.recv(new_path_length).decode()
        self.conn.sendall(b"1")
        try: 
            os.chdir(new_path) 
            self.conn.sendall(b"1")
        except OSError as error: 
            print(error)
            self.conn.sendall(b"0")
        return None

    def noghte_noghte_directory(self):
            # Send go-ahead
            self.conn.sendall(b"1")
            # Get Directory details
            
            try: 
                os.chdir('../') 
                self.conn.sendall(b"1")
            except OSError as error: 
                print(error)
                self.conn.sendall(b"0")
            return None

    def quit_program(self):
        # Send quit confirmation
        self.conn.sendall(b"1")
        self.conn.close()
        

if __name__ == "__main__":
        print("\nWelcome to the FTP server.\n\nTo get started, connect a client.")
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((Client.TCP_IP, Client.TCP_PORT))
        s.listen(10)
        try:
            while True:
                # Accept incoming connections
                client_socket, client_address = s.accept()
                print("\nConnected to by address: {}".format(client_address))
                new_client = Client(client_socket)
                new_client.start()
        except Exception as e:
            print(e)
        finally:
            s.close()

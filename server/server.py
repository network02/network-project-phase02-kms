import socket
import sys
import time
import os
import random
import json
from threading import Thread
from typing import Optional


def load_users_from_file() -> list[dict]:
    with open("users.json", "r") as user_file:
        user_list = json.load(user_file)
    return user_list


USER_LIST: list = load_users_from_file()


class Client(Thread):
    TCP_IP = "127.0.0.1"
    TCP_PORT = 1456
    BUFFER_SIZE = 1024


    def __init__(self, conn: socket.socket) -> None:
        self.conn: socket.socket = conn
        self.exist: bool = False
        self.authenticated: bool = False
        self.username: Optional[str]  = None
        self.password: Optional[str] = None
        self.TCP_DATA_PORT = random.randint(4000, 5000)

        super().__init__()

    def run(self):
        while True:
            
            print("\nWaiting for instruction")
            data = self.conn.recv(Client.BUFFER_SIZE).decode()
            print("\nReceived instruction: {}".format(data))
            # save_history(data)

            if data == "USER":
                self.check_user()
            elif data == "PASS":
                self.check_password()
            elif self.authenticated:
                if data == "STOR":
                    self.upload_file()
                elif data == "LIST":
                    self.list_files()
                elif data == "RETR":
                    self.download_file()
                elif data == "DELE":
                    self.delete_file()
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

            data = None

    def check_user(self) -> None:
        self.authenticated = False
        self.exist = False
        self.username = None
        self.password = None

        self.conn.sendall(b"1")
        username = self.conn.recv(Client.BUFFER_SIZE).decode()
        self.conn.sendall(b"1")

        self.username_exist(username)
        if self.exist:
            self.conn.sendall(b"331 User name okay, need password.")
        else:
            self.conn.sendall(b"337 Enter password to create account.")

    def check_password(self) -> None:
        self.conn.sendall(b"1")
        password = self.conn.recv(Client.BUFFER_SIZE).decode()

        if self.exist:
            self.user_authentication(password)

            if self.authenticated:
                self.conn.sendall(b"230 User logged in, proceed.")
            else:
                self.conn.sendall(b"430 Boro khoonaton!")
        elif self.username != None:
            self.user_create(password)
            self.conn.sendall(b"338 User created.")
        else:
            self.conn.sendall(b"530 Not logged in, Enter USER command first.")

    def username_exist(self, username: str) -> None:
        self.username = username
        for user in USER_LIST:
            if user['username'] == username:
                self.exist = True
                return True
        return False

    def user_authentication(self, password: str) -> None:
        for user in USER_LIST:
            if user['password'] == password:
                self.authenticated = True
                self.password = password
                return True
        return False

    def user_create(self, password: str) -> None:
        self.password = password
        user_dict = {"username": self.username, "password": self.password}
        USER_LIST.append(user_dict)
        with open("users.json", "w") as user_file:
            json.dump(USER_LIST, user_file)

    def upload_file(self) -> None:
        # Send data connection port number
        self.conn.sendall(str(self.TCP_DATA_PORT).encode())
        self.conn.recv(Client.BUFFER_SIZE)

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as data_socket:
            data_socket.bind((Client.TCP_IP, self.TCP_DATA_PORT))
            data_socket.listen()
            # self.conn.sendall(b"1")
            client_data_socket, client_data_address = data_socket.accept()
            print(f"\nConnected to DATA socket by address: {client_data_address}, port: {self.TCP_DATA_PORT}")

            client_data_socket.sendall(b"1")
            
            file_name_size = int(client_data_socket.recv(Client.BUFFER_SIZE).decode())
            file_name = client_data_socket.recv(file_name_size).decode()
            
            client_data_socket.sendall(b"1")
            
            file_size = int(client_data_socket.recv(Client.BUFFER_SIZE).decode())
            
            start_time = time.time()

            with open(file_name, "wb") as output_file:
                bytes_received = 0
                print("\nReceiving...")
                while bytes_received < file_size:
                    l = client_data_socket.recv(Client.BUFFER_SIZE)
                    output_file.write(l)
                    bytes_received += Client.BUFFER_SIZE

            print(f"\nReceived file: {file_name}")

            client_data_socket.sendall(str(time.time() - start_time).encode())
            client_data_socket.sendall(str(file_size).encode())

    def list_files(self) -> None:
        path_name_length = int(self.conn.recv(Client.BUFFER_SIZE).decode())
        self.conn.sendall(b"1") 
        path_name = self.conn.recv(path_name_length).decode()
        self.conn.sendall(b"1")
        print(os.path.isdir(path_name))
        print(os.path.isfile(path_name))
        if os.path.isdir(path_name):
            directories_list = os.listdir(path_name)
            print(directories_list)
            self.conn.sendall(str(len(directories_list)).encode())

            total_directory_size = 0
            # self.conn.sendall("6".encode('utf8'))
            self.conn.recv(Client.BUFFER_SIZE)
            for directory in directories_list:
                print(directory)


                self.conn.sendall(str(sys.getsizeof(directory)).encode('utf8'))
                print("file name size sent")
                print(sys.getsizeof(directory))
                self.conn.recv(Client.BUFFER_SIZE)

                self.conn.sendall(directory.encode())
                print("file name sent")
                self.conn.recv(Client.BUFFER_SIZE)

                self.conn.sendall(str(os.path.getsize(directory)).encode())
                print("file size sent")
                self.conn.recv(Client.BUFFER_SIZE)

                total_directory_size += os.path.getsize(directory)

                self.conn.recv(Client.BUFFER_SIZE)

            self.conn.sendall(str(total_directory_size).encode())

            self.conn.recv(Client.BUFFER_SIZE)
            print("Successfully sent file listing")
 
        elif os.path.isfile(path_name):
            with open(path_name, "r") as file:
                self.conn.sendall(str(os.path.getsize(path_name)).encode())
                self.conn.recv(Client.BUFFER_SIZE)
                l = file.read(Client.BUFFER_SIZE)
                print("\nSending...")
                while l:
                    self.conn.sendall(l.encode())
                    l = file.read(Client.BUFFER_SIZE)
        

            

    def download_file(self) -> None:
        # Send data connection port number
        self.conn.sendall(str(Client.TCP_DATA_PORT).encode())
        self.conn.recv(Client.BUFFER_SIZE)

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as data_socket:
            data_socket.bind((Client.TCP_IP, Client.TCP_DATA_PORT))
            data_socket.listen()
            # self.conn.sendall(b"1")
            client_data_socket, client_data_address = data_socket.accept()
            print(f"\nConnected to DATA socket by address: {client_data_address}, port: {self.TCP_DATA_PORT}")
        
            client_data_socket.sendall(b"1")

            file_name_length = int(client_data_socket.recv(Client.BUFFER_SIZE).decode())
            file_name = client_data_socket.recv(file_name_length).decode()

            if os.path.isfile(file_name):
                client_data_socket.sendall(str(os.path.getsize(file_name)).encode())
            else:
                # The file doesn't exist, and send an error code
                print("File name not valid")
                client_data_socket.sendall(b"-1")
                return None
 
            client_data_socket.recv(Client.BUFFER_SIZE)

            start_time = time.time()
            print("Sending file...")

            with open(file_name, "rb") as content:
                l = content.read(Client.BUFFER_SIZE)
                while l:
                    client_data_socket.sendall(l)
                    l = content.read(Client.BUFFER_SIZE)

            client_data_socket.recv(Client.BUFFER_SIZE)
            client_data_socket.sendall(str(time.time() - start_time).encode())
        return None

    def delete_file(self) -> None:
        self.conn.sendall(b"1")

        file_name_length = int(self.conn.recv(Client.BUFFER_SIZE).decode())
        file_name = self.conn.recv(file_name_length).decode()

        # Check if file exist
        if os.path.isfile(file_name):
            self.conn.sendall(b"1")
        else:
            self.conn.sendall(b"-1")
            return None

        confirm_delete = self.conn.recv(Client.BUFFER_SIZE).decode()
        if confirm_delete.upper() == "Y":
            try:
                os.remove(file_name)
                # send delete status
                self.conn.sendall(b"1")
            except OSError as e:
                print(f"Failed to delete {file_name}")
                print(f"{e}, {type(e)}")
                self.conn.sendall(b"-1")
        else:
            print("Delete abandoned by the client!")

    def make_directory(self) -> None:
        self.conn.sendall(b"1")
        directory_name_length = int(self.conn.recv(Client.BUFFER_SIZE).decode())

        self.conn.sendall(b"1")
        directory_name = self.conn.recv(directory_name_length).decode()

        self.conn.sendall(b"1")
        try: 
            os.mkdir(directory_name) 
            self.conn.sendall(b"1")
        except OSError as e: 
            print(f"{e}, {type(e)}")
            self.conn.sendall(b"0")

    def remove_directory(self) -> None:
        self.conn.sendall(b"1")
        directory_name_length = int(self.conn.recv(Client.BUFFER_SIZE).decode())

        self.conn.sendall(b"1")
        directory_name = self.conn.recv(directory_name_length).decode()

        self.conn.sendall(b"1")
        try: 
            os.rmdir(directory_name) 
            self.conn.sendall(b"1")
        except OSError as e: 
            print(f"{e}, {type(e)}")
            self.conn.sendall(b"0")

    def get_path_directory(self) -> None:
        self.conn.sendall(b"1")

        try:
            cwd = os.getcwd()
            print(cwd)
            self.conn.sendall(str(sys.getsizeof(cwd)).encode())
            print(sys.getsizeof(cwd))
            self.conn.recv(Client.BUFFER_SIZE)
            self.conn.sendall(cwd.encode())
            self.conn.recv(Client.BUFFER_SIZE)
        except OSError as e: 
            print(f"{e}, {type(e)}")
        except Exception as e:
            print(f"{e}, {type(e)}")
            print("couldn't send path.")

    def change_current_directory(self):
        self.conn.sendall(b"1")

        new_path_length = int(self.conn.recv(Client.BUFFER_SIZE).decode())
        self.conn.sendall(b"1")

        new_path = self.conn.recv(new_path_length).decode()
        self.conn.sendall(b"1")

        try: 
            os.chdir(new_path) 
            self.conn.sendall(b"1")
        except OSError as e: 
            print(f"{e}, {type(e)}")
            self.conn.sendall(b"0")

    def noghte_noghte_directory(self) -> None:
            self.conn.sendall(b"1")
            
            try: 
                os.chdir('../')
                self.conn.sendall(b"1")
            except OSError as e: 
                print(f"{e}, {type(e)}")
                self.conn.sendall(b"0")

    def quit_program(self) -> None:
        self.conn.sendall(b"1")
        self.conn.close()
        

if __name__ == "__main__":
        print("Welcome to the FTP server.\nTo get started, connect a client.")

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((Client.TCP_IP, Client.TCP_PORT))
            s.listen(10)

            while True:
                client_socket, client_address = s.accept()
                print(f"\nConnected to by address: {client_address}")
                new_client = Client(client_socket)
                new_client.start()

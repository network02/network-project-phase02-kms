import socket
import sys
import time
import os
import random
import json
import logging

from threading import Thread
from typing import Optional


def load_users_from_file() -> list[dict]:
    with open("users.json", "r") as user_file:
        user_list = json.load(user_file)
    return user_list


def load_permissions_from_file() -> dict:
    with open("permissions.json", "r") as permission_file:
        permissions: dict = json.load(permission_file)
    return permissions


def save_permissions() -> None:
    with open("permissions.json", "w") as permission_file:
        json.dump(PERMISSION_LIST, permission_file)


USER_LIST: list = load_users_from_file()
PERMISSION_LIST: dict = load_permissions_from_file()
FIRST_PATH = "/home/arshia2562/Documents/network-project-phase02-kms"
logging.basicConfig(filename="server.log", format='%(asctime)s %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.INFO)


class Client(Thread):
    TCP_IP = "127.0.0.1"
    TCP_PORT = 1456
    BUFFER_SIZE = 1024

    def __init__(self, conn: socket.socket) -> None:
        self.conn: socket.socket = conn
        self.exist: bool = False
        self.authenticated: bool = False
        self.username: Optional[str] = None
        self.password: Optional[str] = None
        self.TCP_DATA_PORT = random.randint(4000, 5000)
        self.PATH = "/server/Public"
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
                # self.conn.sendall(b"1")
                if data == "STOR":
                    self.upload_file()
                elif data == "PROM":
                    self.change_permission()
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
                    # self.exit()
                    return
            # elif not self.authenticated:
            #     self.conn.sendall(b"530 Not logged in.")

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
            logging.info(
                f"{self.username} - USER - 331 User name okay, need password.")
        else:
            self.conn.sendall(b"337 Enter password to create account.")
            logging.info(
                f"{self.username} - USER - 337 Enter password to create account.")

    def check_password(self) -> None:
        self.conn.sendall(b"1")
        password = self.conn.recv(Client.BUFFER_SIZE).decode()

        if self.exist:
            self.user_authentication(password)

            if self.authenticated:
                self.conn.sendall(b"230 User logged in, proceed.")
                logging.info(
                    f"{self.username} - PASS - 230 User logged in, proceed.")
            else:
                self.conn.sendall(b"430 Boro khoonaton!")
                logging.info(f"{self.username} - PASS - 430 Boro khoonaton!")
        elif self.username != None:
            self.user_create(password)
            self.conn.sendall(b"338 User created.")
            logging.info(f"{self.username} - PASS - 338 User created.")
        else:
            self.conn.sendall(b"530 Not logged in, Enter USER command first.")
            logging.info(
                f"{self.username} - PASS - 530 Not logged in, Enter USER command first.")

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
        self.exist = True
        self.authenticated = True

        user_dict = {"username": self.username, "password": self.password}

        USER_LIST.append(user_dict)
        PERMISSION_LIST['/server/Public'].append(self.username)

        with open("users.json", "w") as user_file:
            json.dump(USER_LIST, user_file)

        save_permissions()

    def change_permission(self) -> None:
        self.conn.sendall(b"1")

        requested_directory = self.conn.recv(Client.BUFFER_SIZE).decode()
        self.conn.sendall(b"1")

        name_of_user = self.conn.recv(Client.BUFFER_SIZE).decode()
        access = False
        for directory, user_list in PERMISSION_LIST.items():
            if os.path.isdir(FIRST_PATH + requested_directory):
                if directory == requested_directory:
                    for username in user_list:
                        if username == self.username:
                            access = True
        if access:
            try:
                PERMISSION_LIST[requested_directory].append(name_of_user)
                save_permissions()
                self.conn.sendall(b"200 OK! permission granted.")
                logging.info(
                    f"{self.username} - PROM - 200 OK! permission granted.")
            except KeyError as e:
                self.conn.sendall(b"400 action failed.")
                logging.error(
                    f"{self.username} - PROM - 400 action failed. - {e}")
                print(e)
        else:
            self.conn.sendall(b"400 access denied.")
            logging.error(f"{self.username} - PROM - 400 access denied.")
            return None

    def upload_file(self) -> None:
        # Send data connection port number
        self.conn.sendall(str(self.TCP_DATA_PORT).encode())
        self.conn.recv(Client.BUFFER_SIZE)

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as data_socket:
            data_socket.bind((Client.TCP_IP, self.TCP_DATA_PORT))
            data_socket.listen()
            self.conn.sendall(b"1")
            client_data_socket, client_data_address = data_socket.accept()
            print(
                f"\nConnected to DATA socket by address: {client_data_address}, port: {self.TCP_DATA_PORT}")
            logging.info(
                f"{self.username} - STOR - Connected to DATA socket by address: {client_data_address}, port: {self.TCP_DATA_PORT}")

            client_data_socket.sendall(b"1")

            file_name_size = int(client_data_socket.recv(
                Client.BUFFER_SIZE).decode())
            client_data_socket.sendall(b"1")

            file_path = client_data_socket.recv(file_name_size).decode()
            client_data_socket.sendall(b"1")

            file_size = int(client_data_socket.recv(
                Client.BUFFER_SIZE).decode())
            client_data_socket.sendall(b"1")

            start_time = time.time()
            file_name = file_path.split('/')
            file_name = FIRST_PATH + self.PATH + '/' + file_name[-1]
            with open(file_name, "wb") as output_file:
                bytes_received = 0
                print("\nReceiving...")
                while bytes_received < file_size:
                    l = client_data_socket.recv(Client.BUFFER_SIZE)
                    client_data_socket.sendall(b"1")
                    output_file.write(l)
                    bytes_received += Client.BUFFER_SIZE

            print(f"\nReceived file: {file_name}")
            logging.info(
                f"{self.username} - STOR - 200 OK! Received file: {file_name}. DATA socket closed")
            client_data_socket.recv(Client.BUFFER_SIZE)

            client_data_socket.sendall(str(time.time() - start_time).encode())
            client_data_socket.recv(Client.BUFFER_SIZE)

            client_data_socket.sendall(str(file_size).encode())
            client_data_socket.recv(Client.BUFFER_SIZE)

    def list_files(self) -> None:
        self.conn.sendall(b"1")

        path_name_length = int(self.conn.recv(Client.BUFFER_SIZE).decode())
        self.conn.sendall(b"1")

        path_name = self.conn.recv(path_name_length).decode()
        print(path_name)

        access = False
        for directory, user_list in PERMISSION_LIST.items():
            if os.path.isdir(FIRST_PATH + path_name):
                if directory == path_name:
                    for username in user_list:
                        if username == self.username:
                            access = True

        if access:
            if os.path.isdir(FIRST_PATH + path_name):

                self.conn.sendall(b"1")
                self.conn.recv(Client.BUFFER_SIZE)
                directories_list = os.listdir(FIRST_PATH + path_name)
                # print(directories_list)
                self.conn.sendall(str(len(directories_list)).encode())

                total_directory_size = 0
                # self.conn.sendall("6".encode('utf8'))
                self.conn.recv(Client.BUFFER_SIZE)
                for directory in directories_list:
                    print(directory)

                    self.conn.sendall(str(sys.getsizeof(directory)).encode('utf8'))
                    # print("file name size sent")
                    # print(sys.getsizeof(directory))
                    self.conn.recv(Client.BUFFER_SIZE)

                    self.conn.sendall(directory.encode())
                    # print("file name sent")
                    self.conn.recv(Client.BUFFER_SIZE)

                    self.conn.sendall(
                        str(os.path.getsize(FIRST_PATH + path_name + '/' + directory)).encode())
                    # print("file size sent")
                    self.conn.recv(Client.BUFFER_SIZE)

                    total_directory_size += os.path.getsize(
                        FIRST_PATH + path_name + '/' + directory)

                self.conn.sendall(str(total_directory_size).encode())

                self.conn.recv(Client.BUFFER_SIZE)
                print("Successfully sent file listing")
                logging.info(
                    f"{self.username} - LIST - 200 OK! Successfully sent directory listing")

            elif os.path.isfile(FIRST_PATH + path_name):
                self.conn.sendall(b"0")
                self.conn.recv(Client.BUFFER_SIZE)
                with open(path_name, "r") as file:
                    self.conn.sendall(
                        str(os.path.getsize(FIRST_PATH + path_name)).encode())
                    self.conn.recv(Client.BUFFER_SIZE)
                    l = file.read(Client.BUFFER_SIZE)
                    print("\nSending...")
                    while l:
                        self.conn.sendall(l.encode())
                        self.conn.recv(Client.BUFFER_SIZE)
                        l = file.read(Client.BUFFER_SIZE)
                    logging.info(f"{self.username} - LIST - 200 OK! Successfully sent file data")
                    return None
            else:
                self.conn.sendall(b"-1")
                self.conn.recv(Client.BUFFER_SIZE)
                logging.error(f"{self.username} - LIST - 400 action failed.")
                return None
        else:
            self.conn.sendall(b"-2")
            logging.error(f"{self.username} - LIST - 400 access denied.")
            return None

    def download_file(self) -> None:
        # Send data connection port number
        self.conn.sendall(str(self.TCP_DATA_PORT).encode())
        self.conn.recv(Client.BUFFER_SIZE)

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as data_socket:
            data_socket.bind((Client.TCP_IP, self.TCP_DATA_PORT))
            data_socket.listen()
            self.conn.sendall(b"1")
            client_data_socket, client_data_address = data_socket.accept()
            print(f"\nConnected to DATA socket by address: {client_data_address}, port: {self.TCP_DATA_PORT}")
            logging.info(f"{self.username} - RETR - Connected to DATA socket by address: {client_data_address}, port: {self.TCP_DATA_PORT}")

            client_data_socket.sendall(b"1")

            file_name_length = int(client_data_socket.recv(Client.BUFFER_SIZE).decode())
            client_data_socket.sendall(b"1")

            file_name = client_data_socket.recv(file_name_length).decode()

            if os.path.isfile(FIRST_PATH + file_name):
                client_data_socket.sendall(str(os.path.getsize(FIRST_PATH + file_name)).encode())
            else:
                # The file doesn't exist, and send an error code
                print("File name not valid")
                logging.info(f"{self.username} - RETR - 400 action failed. File name not valid.")
                client_data_socket.sendall(b"-1")
                return None

            client_data_socket.recv(Client.BUFFER_SIZE)
            
            new_path = []
            for folder in file_name.split('/'):
                new_path.append(folder)
            new_path.pop(-1)
            new_path = '/'.join(new_path)

            access = False
            for directory, user_list in PERMISSION_LIST.items():
                if directory == new_path:
                    for username in user_list:
                        if username == self.username:
                            access = True

            if access:
                print("Sending file...")
                self.conn.sendall(b"1")
                self.conn.recv(Client.BUFFER_SIZE)
                with open(file_name, "rb") as content:
                    l = content.read(Client.BUFFER_SIZE)
                    while l:
                        client_data_socket.sendall(l)
                        client_data_socket.recv(Client.BUFFER_SIZE)
                        l = content.read(Client.BUFFER_SIZE)
                    logging.info(f"{self.username} - RETR - 200 OK! file downloaded successfully. DATA socket closed.")
            else:
                self.conn.sendall(b"0")
                self.conn.recv(Client.BUFFER_SIZE)
                logging.info(f"{self.username} - RETR - 400 access denied")
        return None

    def delete_file(self) -> None:
        self.conn.sendall(b"1")

        file_name_length = int(self.conn.recv(Client.BUFFER_SIZE).decode())
        self.conn.sendall(b"1")

        file_name = self.conn.recv(file_name_length).decode()
        

        # Check if file exist
        if os.path.isfile(FIRST_PATH + file_name):
            self.conn.sendall(b"1")
        else:
            self.conn.sendall(b"-1")
            logging.info(
                f"{self.username} - DELE - 400 action failed. File name does not exist.")
            return None

        new_path = []
        for folder in file_name.split('/'):
            new_path.append(folder)
        new_path.pop(-1)
        new_path = '/'.join(new_path)

        access = False
        for directory, user_list in PERMISSION_LIST.items():
            if directory == new_path:
                for username in user_list:
                    if username == self.username:
                        access = True

        self.conn.recv(Client.BUFFER_SIZE)         
        if access:        
            self.conn.sendall(b"1")

            confirm_delete = self.conn.recv(Client.BUFFER_SIZE).decode()
            if confirm_delete.upper() == "Y":
                try:
                    os.remove(FIRST_PATH + file_name)
                    # send delete status
                    self.conn.sendall(b"1")
                    logging.info(f"{self.username} - DELE - 200 OK! file deleted successfully.")
                except OSError as e:
                    print(f"Failed to delete {file_name}")
                    print(f"{e}, {type(e)}")
                    logging.info(f"{self.username} - DELE - Failed to delete {file_name} - {e}")
                    self.conn.sendall(b"-1")
            else:
                print("Delete abandoned by the client!")
                logging.info(f"{self.username} - DELE - Delete abandoned by the client!")
        else:
            self.conn.sendall(b"0")   
            logging.info(f"{self.username} - DELE - 400 access denied")

    def make_directory(self) -> None:
        self.conn.sendall(b"1")
        directory_name_length = int(
            self.conn.recv(Client.BUFFER_SIZE).decode())
        self.conn.sendall(b"1")

        directory_name = self.conn.recv(directory_name_length).decode()

        try:
            access = False
            for directory, user_list in PERMISSION_LIST.items():
                if directory_name[0] == '/':
                    if os.path.isdir(FIRST_PATH + directory_name):
                        if directory == directory_name:
                            for username in user_list:
                                if username == self.username:
                                    access = True
                else:
                    if os.path.isdir(FIRST_PATH + self.PATH + '/' + directory_name):
                        if directory == self.PATH + '/' + directory_name:
                            for username in user_list:
                                if username == self.username:
                                    access = True
        except OSError as e:
            print(f"{e}, {type(e)}")
            logging.info(
                f"{self.username} - RMD - 400 Failed to remove {directory_name}. Access denied. - {e}")
            self.conn.sendall(b"0")
            return None
        if access:
            try:
                if directory_name[0] == '/':
                    os.mkdir(FIRST_PATH + directory_name)
                    PERMISSION_LIST[directory_name] = ['admin']
                    if self.username != "admin:":
                        PERMISSION_LIST[directory_name].append(self.username)
                    save_permissions()

                else:
                    os.mkdir(FIRST_PATH + self.PATH + '/' + directory_name)
                    PERMISSION_LIST[self.PATH + '/' +
                                    directory_name] = ['admin']
                    if self.username != "admin:":
                        PERMISSION_LIST[self.PATH + '/' +
                                        directory_name].append(self.username)
                    save_permissions()

                self.conn.sendall(b"1")
                logging.info(
                    f"{self.username} - MKD - 200 OK! {directory_name} created successfully.")
            except OSError as e:
                print(f"{e}, {type(e)}")
                logging.info(
                    f"{self.username} - MKD - 400 Failed to create {directory_name} - {e}")
                self.conn.sendall(b"0")
        else:
            self.conn.sendall(b"-1")
            logging.info(f"{self.username} - MKD - 400 Access denied.")
            return None

    def remove_directory(self) -> None:
        self.conn.sendall(b"1")
        directory_name_length = int(
            self.conn.recv(Client.BUFFER_SIZE).decode())
        self.conn.sendall(b"1")

        directory_name = self.conn.recv(directory_name_length).decode()

        try:
            access = False
            for directory, user_list in PERMISSION_LIST.items():
                if directory_name[0] == '/':
                    if os.path.isdir(FIRST_PATH + directory_name):
                        if directory == directory_name:
                            for username in user_list:
                                if username == self.username:
                                    access = True
                else:
                    if os.path.isdir(FIRST_PATH + self.PATH + '/' + directory_name):
                        if directory == self.PATH + '/' + directory_name:
                            for username in user_list:
                                if username == self.username:
                                    access = True
        except OSError as e:
            print(f"{e}, {type(e)}")
            logging.info(f"{self.username} - RMD - 400 Failed to remove {directory_name}. access denied. - {e}")
            self.conn.sendall(b"0")
            return None
        if access:
            try:
                if directory_name[0] == '/':
                    os.rmdir(FIRST_PATH + directory_name)
                    PERMISSION_LIST.pop(directory_name)
                    save_permissions()
                else:
                    os.rmdir(FIRST_PATH + self.PATH + '/' + directory_name)
                    PERMISSION_LIST.pop(self.PATH + '/' + directory_name)
                    save_permissions()

                self.conn.sendall(b"1")
                logging.info(f"{self.username} - RMD - 200 OK! {directory_name} removed successfully.")
            except OSError as e:
                print(f"{e}, {type(e)}")
                self.conn.sendall(b"0")
                logging.info(f"{self.username} - RMD - 400 Failed to remove {directory_name}. - {e}")
                return None
        else:
            self.conn.sendall(b"-1")
            logging.info(f"{self.username} - RMD - 400 access denied.")
            return None

    def get_path_directory(self) -> None:
        self.conn.sendall(b"1")

        try:
            self.conn.recv(Client.BUFFER_SIZE)

            self.conn.sendall(str(sys.getsizeof(self.PATH)).encode())
            print(sys.getsizeof(self.PATH))
            self.conn.recv(Client.BUFFER_SIZE)

            self.conn.sendall(self.PATH.encode())
            self.conn.recv(Client.BUFFER_SIZE)
            logging.info(
                f"{self.username} - PWD - 200 Path sent successfully. - Path={self.PATH}")

        except OSError as e:
            print(f"{e}, {type(e)}")
            logging.info(
                f"{self.username} - PWD - 452 Couldn't send path. - Path={self.PATH} - {e}")

        except Exception as e:
            print(f"{e}, {type(e)}")
            logging.info(
                f"{self.username} - PWD - 452 Couldn't send path. - Path={self.PATH} - {e}")

    def change_current_directory(self):
        self.conn.sendall(b"1")

        new_path_length = int(self.conn.recv(Client.BUFFER_SIZE).decode())
        self.conn.sendall(b"1")

        new_path = self.conn.recv(new_path_length).decode()
        try:
            access = False
            for directory, user_list in PERMISSION_LIST.items():
                if new_path[0] == '/':
                    if os.path.isdir(FIRST_PATH + new_path):
                        if directory == new_path:
                            for username in user_list:
                                if username == self.username:
                                    print("bingo")
                                    access = True
                else:
                    if os.path.isdir(FIRST_PATH + self.PATH + '/' + new_path):
                        if directory == self.PATH + '/' + new_path:
                            for username in user_list:
                                if username == self.username:
                                    access = True
        except OSError as e:
            print(f"{e}, {type(e)}")
            self.conn.sendall(b"0")
            logging.info(f"{self.username} - CWD - 400 couldn't change path.")
            return None

        if access:
            try:
                if new_path[0] == '/':
                    self.PATH = new_path
                else:
                    self.PATH += '/' + new_path
                self.conn.sendall(b"1")
                logging.info(
                    f"{self.username} - CWD - 200 OK! path changed successfully. - Path updated to: {self.PATH}")
            except OSError as e:
                print(f"{e}, {type(e)}")
                self.conn.sendall(b"0")
                logging.info(
                    f"{self.username} - CWD - 400 couldn't change path. - {e}")
        else:
            self.conn.sendall(b"-1")
            logging.info(
                f"{self.username} - CWD - 400 access denied. - PATH={self.PATH}")

    def noghte_noghte_directory(self) -> None:
        self.conn.sendall(b"1")
        self.conn.recv(Client.BUFFER_SIZE)
        new_path = []
        for folder in self.PATH.split('/'):
            new_path.append(folder)
        new_path.pop(-1)
        new_path = '/'.join(new_path)

        access = False
        for directory, user_list in PERMISSION_LIST.items():
            if os.path.isdir(FIRST_PATH + new_path):
                if directory == new_path:
                    for username in user_list:
                        if username == self.username:
                            access = True
        if access:
            try:
                self.PATH = new_path

                self.conn.sendall(b"1")
                logging.info(
                    f"{self.username} - CDUP - 200 OK! path changed successfully. - Path updated to: {self.PATH}")
            except OSError as e:
                print(f"{e}, {type(e)}")
                self.conn.sendall(b"0")
                logging.info(
                    f"{self.username} - CDUP - 400 couldn't change path. - {e}")
        else:
            self.conn.sendall(b"-1")
            logging.info(
                f"{self.username} - CDUP - 400 access denied. - PATH: {self.PATH}")

    def quit_program(self) -> None:
        self.conn.sendall(b"1")
        self.conn.close()
        logging.info(
            f"{self.username} - QUIT - 200 OK! Client connection ended.")


if __name__ == "__main__":
    print("Welcome to the FTP server.\nTo get started, connect a client.")
    logging.info("Server ON.")

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((Client.TCP_IP, Client.TCP_PORT))
        s.listen(10)

        while True:
            client_socket, client_address = s.accept()
            print(f"\nConnected to by address: {client_address}")
            logging.info(f"         CONN - {client_address} - connection made successfully.")
            new_client = Client(client_socket)
            new_client.start()

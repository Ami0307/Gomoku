import socket
import threading
import json
import time
import select

BROADCAST_PORT = 12345
DISCOVERY_MESSAGE = "GOMOKU_GAME_DISCOVERY"
RESPONSE_MESSAGE = "GOMOKU_GAME_RESPONSE"
DISCOVERY_RUNNING = False

class Network:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.addr = (self.host, self.port)
        self.client = None
        self.server_socket = None
        self.connected = False
        self.move_lock = threading.Lock()
        self.network_move = None
        self.running = True
        print(f"Using IP address: {socket.gethostbyname(socket.gethostname())}")

    def connect(self):
        if self.connected:
            print("Already connected to server")
            return True
        try:
            self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client.settimeout(5)  # 设置5秒超时
            print(f"Attempting to connect to {self.host}:{self.port}")
            self.client.connect(self.addr)
            self.client.settimeout(None)  # 连接后重置为阻塞模式
            self.connected = True
            print(f"Successfully connected to {self.host}:{self.port}")
            return True
        except socket.timeout:
            print(f"Connection attempt to {self.host}:{self.port} timed out")
        except ConnectionRefusedError:
            print(f"Connection to {self.host}:{self.port} was refused")
        except Exception as e:
            print(f"Failed to connect to {self.host}:{self.port}: {e}")
        self.client = None
        return False

    def send(self, data):
        try:
            self.client.send(json.dumps(data).encode())
            print(f"Sent data: {data}")
        except socket.error as e:
            print(f"Error sending data: {e}")

    def close(self):
        self.running = False
        if self.client:
            self.client.close()
        if self.server_socket:
            self.server_socket.close()
        self.connected = False
        self.client = None

    def send_move(self, row, col):
        move_data = json.dumps({"move": [row, col]})
        self.send(move_data)

    def check_network_data(self):
        with self.move_lock:
            data = self.network_move
            self.network_move = None
        return data

    def receive_move_thread(self):
        while True:
            try:
                data = self.client.recv(2048).decode()
                if not data:
                    break
                print(f"Received raw data: {data}")
                self.handle_received_data(data)
            except Exception as e:
                print(f"Error in receive thread: {e}")
                break
        print("Receive thread ended")

    def handle_received_data(self, data):
        try:
            if data.startswith('"') and data.endswith('"'):
                data = data[1:-1]
            data = data.replace('\\', '')
            
            parsed_data = json.loads(data)
            if isinstance(parsed_data, dict):
                if "type" in parsed_data:
                    # 处理控制消息
                    print(f"Received control message: {parsed_data}")
                    with self.move_lock:
                        self.network_move = parsed_data
                elif "move" in parsed_data:
                    # 处理移动消息
                    if isinstance(parsed_data["move"], list) and len(parsed_data["move"]) == 2:
                        with self.move_lock:
                            self.network_move = parsed_data["move"]
                        print(f"Processed move: {self.network_move}")
                    else:
                        print(f"Received invalid move format: {parsed_data}")
                else:
                    print(f"Received unexpected data format: {parsed_data}")
            else:
                print(f"Received unexpected data type: {type(parsed_data)}")
        except json.JSONDecodeError as e:
            print(f"Received invalid JSON data: {data}")
            print(f"JSON decode error: {e}")
        except Exception as e:
            print(f"Error handling received data: {e}")

    def start_server_receive_thread(self):
        self.running = True
        self.server_receive_thread = threading.Thread(target=self.server_receive_thread_func, daemon=True)
        self.server_receive_thread.start()

    def server_receive_thread_func(self):
        while self.running:
            try:
                if self.client:  # 对于服务器端，这是连接的客户端
                    ready = select.select([self.client], [], [], 0.1)
                    if ready[0]:
                        data = self.client.recv(2048).decode().strip()
                        if not data:
                            print("Client disconnected")
                            break
                        print(f"Received data: {data}")
                        self.handle_received_data(data)
                elif self.connected:  # 对于客户端，我们直接使用self
                    ready = select.select([self.client], [], [], 0.1)
                    if ready[0]:
                        data = self.client.recv(2048).decode().strip()
                        if not data:
                            print("Disconnected from server")
                            break
                        print(f"Received data: {data}")
                        self.handle_received_data(data)
            except Exception as e:
                print(f"Error in server receive thread: {e}")
                if not self.running:
                    break
        print("Server receive thread ended")

    def stop_receive_thread(self):
        self.running = False
        if hasattr(self, 'receive_thread') and isinstance(self.receive_thread, threading.Thread):
            self.receive_thread.join(timeout=1)
        if hasattr(self, 'server_receive_thread') and isinstance(self.server_receive_thread, threading.Thread):
            self.server_receive_thread.join(timeout=1)

    def start_receive_thread(self):
        self.running = True
        self.receive_thread = threading.Thread(target=self.receive_move_thread, daemon=True)
        self.receive_thread.start()

def start_server(host, port, game_instance):
    global server_socket, DISCOVERY_RUNNING
    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((socket.gethostbyname(socket.gethostname()), port))
        server_socket.listen(1)
        server_socket.setblocking(False)
        print(f"Server started on {socket.gethostbyname(socket.gethostname())}:{port}")
        print("Waiting for client connection...")

        network = Network(host, port)
        network.server_socket = server_socket

        # 启动发现服务
        print(f"Current DISCOVERY_RUNNING status: {DISCOVERY_RUNNING}")
        if not DISCOVERY_RUNNING:
            print("Starting discovery service...")
            discovery_thread = threading.Thread(target=start_discovery_service, args=(port,), daemon=True)
            discovery_thread.start()
        else:
            print("Discovery service is already running.")

        # 主动广播服务器信息
        broadcast_server_info(host, port)

        # 启动服务端接收线程
        network.start_server_receive_thread()
        game_instance.player_color = 'White'
        return network, game_instance
    except Exception as e:
        print(f"Failed to start server: {e}")
        return None, game_instance

def broadcast_server_info(host, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    try:
        actual_ip = socket.gethostbyname(socket.gethostname())
        message = f"GOMOKU_SERVER:{json.dumps({'host': actual_ip, 'port': port})}"
        sock.sendto(message.encode(), ('<broadcast>', BROADCAST_PORT))
        print(f"Broadcasted server info: {message}")
    except Exception as e:
        print(f"Error broadcasting server info: {e}")
    finally:
        sock.close()

def start_client(host, port, game_instance):
    if isinstance(port, tuple):
        host, port = port
    network = Network(host, port)
    try:
        if network.connect():
            print(f"已连接到服务器 {host}:{port}")
            network.start_receive_thread()
            game_instance.player_color = "White"
            return network, game_instance
        else:
            print(f"无法连接到服务器 {host}:{port}")
    except Exception as e:
        print(f"连接服务器时出错: {e}")
    return None, game_instance

def start_network_game(game, mode, host='localhost', port=12345):
    global DISCOVERY_RUNNING
    if mode == "server":
        if not DISCOVERY_RUNNING:
            discovery_thread = threading.Thread(target=start_discovery_service, args=(port,), daemon=True)
            discovery_thread.start()
        return start_server(host, port, game)
    elif mode == "client":
        return start_client(host, port, game)
    else:
        print("Invalid network mode")
        return None, game

def start_discovery_service(port):
    global DISCOVERY_RUNNING
    print("Attempting to start discovery service...")
    if DISCOVERY_RUNNING:
        print("Discovery service is already running.")
        return

    DISCOVERY_RUNNING = True
    print(f"Setting up discovery service on port {BROADCAST_PORT}")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    try:
        sock.bind(('', BROADCAST_PORT))
        print(f"Discovery service successfully started on port {BROADCAST_PORT}")
    except Exception as e:
        print(f"Failed to bind discovery service: {e}")
        DISCOVERY_RUNNING = False
        return

    while DISCOVERY_RUNNING:
        try:
            data, addr = sock.recvfrom(1024)
            print(f"Discovery service received data from {addr}")
            if data.decode() == DISCOVERY_MESSAGE:
                response = f"{RESPONSE_MESSAGE}:{json.dumps({'host': socket.gethostbyname(socket.gethostname()), 'port': port})}"
                sock.sendto(response.encode(), addr)
                print(f"Discovery service sent response to {addr}")
        except Exception as e:
            print(f"Error in discovery service: {e}")

    sock.close()
    print("Discovery service stopped")

def get_available_rooms():
    available_rooms = []
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.settimeout(1)

    try:
        print("Searching for available rooms...")
        # Send discovery message
        sock.sendto(DISCOVERY_MESSAGE.encode(), ('<broadcast>', BROADCAST_PORT))

        start_time = time.time()
        while time.time() - start_time < 5:  # Listen for responses for 5 seconds
            try:
                data, addr = sock.recvfrom(1024)
                message = data.decode()
                if message.startswith(RESPONSE_MESSAGE) or message.startswith("GOMOKU_SERVER:"):
                    room_info = json.loads(message.split(':', 1)[1])
                    if room_info not in available_rooms:
                        available_rooms.append(room_info)
                        print(f"Found room: {room_info}")
            except socket.timeout:
                continue
    except Exception as e:
        print(f"An error occurred while searching for rooms: {e}")
    finally:
        sock.close()

    print(f"Found {len(available_rooms)} room(s)")
    return available_rooms

def stop_discovery_service():
    global DISCOVERY_RUNNING
    DISCOVERY_RUNNING = False

def check_for_new_connection(server_socket):
    if server_socket:
        readable, _, _ = select.select([server_socket], [], [], 0)
        if readable:
            client_socket, _ = server_socket.accept()
            # 这里可以进行一些初始化操作
            return client_socket
    return None
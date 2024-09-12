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

    def check_network_move(self):
        with self.move_lock:
            move = self.network_move
            self.network_move = None
        return move

    def receive_move_thread(self):
        while True:
            try:
                data = self.client.recv(2048).decode()
                if not data:
                    break
                move_data = json.loads(data)
                print(f"Received data: {move_data}")
                with self.move_lock:
                    self.network_move = move_data
            except Exception as e:
                print(f"Error in receive thread: {e}")
                break
        print("Receive thread ended")

    def handle_received_data(self, data):
        try:
            move_data = json.loads(data)
            if isinstance(move_data, dict) and "move" in move_data:
                with self.move_lock:
                    self.network_move = move_data["move"]
                print(f"Processed move: {self.network_move}")
            else:
                print(f"Received unexpected data format: {move_data}")
        except json.JSONDecodeError:
            print(f"Received invalid JSON data: {data}")
        except Exception as e:
            print(f"Error handling received data: {e}")

    def start_server_receive_thread(self):
        threading.Thread(target=self.server_receive_thread, daemon=True).start()

    def server_receive_thread(self):
        while self.running:
            if self.client:
                try:
                    ready = select.select([self.client], [], [], 0.1)
                    if ready[0]:
                        data = self.client.recv(2048).decode()
                        if not data:
                            print("Client disconnected")
                            break
                        print(f"Server received data: {data}")
                        self.handle_received_data(data)
                except json.JSONDecodeError:
                    print("Received invalid JSON data")
                except ConnectionResetError:
                    print("Connection reset by client")
                    break
                except Exception as e:
                    print(f"Error in server receive thread: {e}")
                    if not self.running:
                        break
            else:
                time.sleep(0.1)
        print("Server receive thread ended")

def start_server(host, port, game_instance):
    global server_socket, DISCOVERY_RUNNING
    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind(("0.0.0.0", port))
        server_socket.listen(1)
        server_socket.setblocking(False)
        print(f"Server started on 0.0.0.0:{port}")
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
            print(f"Connected to server at {host}:{port}")
            threading.Thread(target=network.receive_move_thread, daemon=True).start()
            game_instance.player_color = "Black"
            return network, game_instance
        else:
            print(f"Failed to connect to server at {host}:{port}")
    except Exception as e:
        print(f"Error connecting to server: {e}")
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
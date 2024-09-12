import socket
import threading
import json
import time

BROADCAST_PORT = 12345
DISCOVERY_MESSAGE = "GOMOKU_GAME_DISCOVERY"
RESPONSE_MESSAGE = "GOMOKU_GAME_RESPONSE"

class Network:
    def __init__(self, host, port):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = host
        self.port = port
        self.addr = (self.host, self.port)
        self.network_move = None
        self.move_lock = threading.Lock()

    def connect(self):
        try:
            self.client.connect(self.addr)
            return True
        except:
            return False

    def send(self, data):
        try:
            self.client.send(json.dumps(data).encode())
            return self.client.recv(2048).decode()
        except socket.error as e:
            print(e)
            return None

    def close(self):
        self.client.close()

    def send_move(self, row, col):
        move = [row, col]
        self.send({"move": move})

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
                self.handle_received_data(data)
            except:
                break

    def handle_received_data(self, data):
        try:
            move_data = json.loads(data)
            if "move" in move_data:
                with self.move_lock:
                    self.network_move = move_data["move"]
        except json.JSONDecodeError:
            print("Received invalid JSON data")
        except KeyError:
            print("Received data does not contain a 'move' key")

def start_server(host, port, game_instance):
    start_discovery_service(port)
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen(1)
    print(f"Server started on {host}:{port}")
    conn, addr = server.accept()
    print(f"New connection from {addr}")
    network = Network(host, port)
    network.client = conn
    threading.Thread(target=network.receive_move_thread, daemon=True).start()
    game_instance.player_color = "White"
    return network, game_instance

def start_client(host, port, game_instance):
    network = Network(host, port)
    if network.connect():
        print(f"Connected to server at {host}:{port}")
        threading.Thread(target=network.receive_move_thread, daemon=True).start()
        game_instance.player_color = "Black"
        return network, game_instance
    else:
        print("Failed to connect to server")
        return None, game_instance

def start_network_game(game, mode, host='localhost', port=12345):
    if mode == "server":
        return start_server(host, port, game)
    elif mode == "client":
        return start_client(host, port, game)
    else:
        print("Invalid network mode")
        return None, game

def get_available_rooms():
    available_rooms = []
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.settimeout(2)  # Set a timeout for receiving responses

    try:
        # Broadcast discovery message
        sock.sendto(DISCOVERY_MESSAGE.encode(), ('<broadcast>', BROADCAST_PORT))

        # Listen for responses
        start_time = time.time()
        while time.time() - start_time < 5:  # Listen for responses for 5 seconds
            try:
                data, addr = sock.recvfrom(1024)
                if data.decode().startswith(RESPONSE_MESSAGE):
                    room_info = json.loads(data.decode().split(':', 1)[1])
                    available_rooms.append(room_info)
            except socket.timeout:
                pass
    finally:
        sock.close()

    return available_rooms

def start_discovery_service(port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.bind(('', BROADCAST_PORT))

    def discovery_thread():
        while True:
            data, addr = sock.recvfrom(1024)
            if data.decode() == DISCOVERY_MESSAGE:
                response = f"{RESPONSE_MESSAGE}:{json.dumps({'host': socket.gethostbyname(socket.gethostname()), 'port': port})}"
                sock.sendto(response.encode(), addr)

    threading.Thread(target=discovery_thread, daemon=True).start()
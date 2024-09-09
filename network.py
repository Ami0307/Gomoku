import socket
import threading
import json

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
                move_data = json.loads(data)
                with self.move_lock:
                    self.network_move = move_data["move"]
            except:
                break

def start_server(host, port, game_instance):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen(2)
    print(f"Server started on {host}:{port}")

    def handle_client(conn, addr, game_instance):
        print(f"New connection from {addr}")
        network = Network(host, port)
        network.client = conn
        threading.Thread(target=network.receive_move_thread, daemon=True).start()
        game_instance.player_color = "White"
        return network

    conn, addr = server.accept()
    return handle_client(conn, addr, game_instance)

def start_client(host, port, game_instance):
    network = Network(host, port)
    if network.connect():
        print(f"Connected to server at {host}:{port}")
        threading.Thread(target=network.receive_move_thread, daemon=True).start()
        game_instance.player_color = "Black"
        return network
    else:
        print("Failed to connect to server")
        return None

def start_network_game(game, mode, host='localhost', port=12345):
    if mode == "server":
        return start_server(host, port, game)
    elif mode == "client":
        return start_client(host, port, game)
    else:
        print("Invalid network mode")
        return None
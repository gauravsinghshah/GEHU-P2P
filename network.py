import socket
import threading
import os
import json
import math

class PeerNetwork:
    def __init__(self, port=8080, file_port=8081, on_peer_discovered=None, on_file_chunk_received=None, on_message_received=None):
        self.port = port
        self.file_port = file_port
        self.message_port = 50008
        self.peers = []
        self.chunk_size = 1024 * 1024  # 1MB chunks
        self.on_peer_discovered = on_peer_discovered
        self.on_file_chunk_received = on_file_chunk_received
        self.on_message_received = on_message_received
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(('', self.port))

    def discover_peers(self):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                s.sendto(b"DISCOVER_PEER", ("<broadcast>", self.port))
        except Exception as e:
            print(f"Error broadcasting discovery: {e}")

    def listen_for_peers(self):
        while True:
            try:
                message, addr = self.socket.recvfrom(1024)
                if message == b"DISCOVER_PEER":
                    peer_ip = addr[0]
                    if peer_ip not in [p[0] for p in self.peers]:
                        self.peers.append(addr)
                        if self.on_peer_discovered:
                            self.on_peer_discovered(addr[0])
                        self.socket.sendto(b"PEER_ACK", addr)
            except Exception as e:
                print(f"Error in peer discovery: {e}")

    def send_message(self, peer_ip, message):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(5)
                s.connect((peer_ip, self.message_port))
                s.sendall(message.encode())
                return True
        except Exception as e:
            print(f"Error sending message to {peer_ip}: {e}")
            return False

    def listen_for_messages(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('', self.message_port))
        s.listen(5)
        while True:
            try:
                conn, addr = s.accept()
                data = conn.recv(4096).decode()
                if data and self.on_message_received:
                    self.on_message_received(data, addr[0])
                conn.close()
            except Exception as e:
                print(f"Error receiving message: {e}")

    def send_file_chunks(self, file_path, peers, role):
        try:
            file_name = os.path.basename(file_path)
            with open(file_path, 'rb') as f:
                file_data = f.read()
            file_size = len(file_data)
            num_chunks = math.ceil(file_size / self.chunk_size)
            chunks = [file_data[i:i + self.chunk_size] for i in range(0, file_size, self.chunk_size)]

            for i, chunk in enumerate(chunks):
                peer_idx = i % len(peers) if peers else 0
                peer_ip = peers[peer_idx][0]
                header = json.dumps({
                    'file_name': file_name,
                    'chunk_id': i,
                    'total_chunks': num_chunks,
                    'chunk_size': len(chunk),
                    'role': role
                })
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(5)
                    s.connect((peer_ip, self.file_port))
                    s.sendall(header.encode() + b'\n' + chunk)
            return True
        except Exception as e:
            print(f"Error sending file chunks: {e}")
            return False

    def listen_for_file_chunks(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('', self.file_port))
        s.listen(5)
        while True:
            try:
                conn, addr = s.accept()
                header_data = b''
                while b'\n' not in header_data:
                    header_data += conn.recv(1024)
                header, chunk_data = header_data.split(b'\n', 1)
                header = json.loads(header.decode())
                file_name = header['file_name']
                chunk_id = header['chunk_id']
                total_chunks = header['total_chunks']
                chunk_size = header['chunk_size']
                role = header['role']

                while len(chunk_data) < chunk_size:
                    chunk_data += conn.recv(4096)

                if self.on_file_chunk_received:
                    self.on_file_chunk_received(file_name, chunk_id, total_chunks, chunk_data, addr[0], role)
                conn.close()

                if role == 'student':
                    for peer in self.peers:
                        if peer[0] != addr[0]:
                            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                                s.settimeout(5)
                                s.connect((peer[0], self.file_port))
                                s.sendall(header.encode() + b'\n' + chunk_data)
            except Exception as e:
                print(f"Error receiving chunk: {e}")
                conn.close()
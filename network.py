import socket
import threading
import os
import json

class PeerNetwork:
    def __init__(self, port=8080, file_port=8081, on_peer_discovered=None, on_file_received=None):
        self.port = port  # For UDP peer discovery
        self.file_port = file_port  # For TCP file transfers
        self.on_peer_discovered = on_peer_discovered
        self.on_file_received = on_file_received
        self.peers = []  # List to store discovered peers

        # UDP socket for discovery
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(('', self.port))

    def listen_for_peers(self):
        """Listen for incoming peer broadcasts"""
        print(f"📡 Listening for peer discovery on UDP port {self.port}...")
        while True:
            try:
                message, address = self.socket.recvfrom(1024)
                message = message.decode('utf-8')
                if message == "DISCOVER_PEER":
                    if address[0] not in [peer[0] for peer in self.peers]:
                        self.peers.append(address)
                        print(f"✅ Discovered new peer: {address[0]}")
                        if self.on_peer_discovered:
                            self.on_peer_discovered(message, address)
            except Exception as e:
                print(f"❌ Error in listening for peers: {e}")

    def discover_peers(self):
        """Broadcast to discover peers"""
        try:
            print("🔎 Broadcasting peer discovery...")
            broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            broadcast_socket.sendto(b"DISCOVER_PEER", ("<broadcast>", self.port))
            broadcast_socket.close()
        except Exception as e:
            print(f"❌ Error broadcasting discovery: {e}")

    def listen_for_files(self):
        """Listen for incoming file transfers over TCP"""
        print(f"📥 Listening for incoming files on TCP port {self.file_port}...")
        file_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        file_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        file_socket.bind(('', self.file_port))
        file_socket.listen(5)

        while True:
            try:
                conn, addr = file_socket.accept()
                thread = threading.Thread(target=self._handle_file_connection, args=(conn, addr))
                thread.daemon = True
                thread.start()
            except Exception as e:
                print(f"❌ Error in file listener: {e}")

    def _handle_file_connection(self, conn, addr):
        try:
            data = conn.recv(4096)
            if not data:
                return

            decoded = data.decode()
            parts = decoded.split(',', 1)

            if len(parts) != 2:
                return

            file_name, file_size = parts
            file_size = int(file_size)
            received_data = b''

            while len(received_data) < file_size:
                chunk = conn.recv(4096)
                if not chunk:
                    break
                received_data += chunk

            print(f"📦 Received file: {file_name} ({len(received_data)} bytes) from {addr[0]}")

            if self.on_file_received:
                payload = json.dumps({
                    "type": "file_transfer",
                    "file_name": file_name,
                    "file_data": received_data.hex()
                }).encode()
                self.on_file_received(payload, addr)

        except Exception as e:
            print(f"❌ Error receiving file: {e}")
        finally:
            conn.close()

    def send_file(self, file_path, peer_ip):
        """Send a file to a specific peer via TCP"""
        try:
            file_name = os.path.basename(file_path)
            with open(file_path, 'rb') as file:
                file_data = file.read()
                file_size = len(file_data)

            peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            peer_socket.connect((peer_ip, self.file_port))

            # Send metadata
            metadata = f"{file_name},{file_size}"
            peer_socket.send(metadata.encode('utf-8'))

            # Send file data
            peer_socket.sendall(file_data)
            peer_socket.close()
            print(f"📤 File sent to {peer_ip}: {file_name} ({file_size} bytes)")
        except Exception as e:
            print(f"❌ Error sending file to {peer_ip}: {e}")

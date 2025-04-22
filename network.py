import socket
import threading
import os

class PeerNetwork:
    def __init__(self, port=8080):
        self.port = port
        self.peers = []  # List to store discovered peers
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(('', self.port))

    def listen_for_peers(self):
        """Listen for incoming peer broadcasts"""
        while True:
            try:
                message, address = self.socket.recvfrom(1024)
                message = message.decode('utf-8')
                if message == "DISCOVER_PEER":
                    if address[0] not in [peer[0] for peer in self.peers]:
                        self.peers.append(address)
                        print(f"Discovered new peer: {address[0]}")
            except Exception as e:
                print(f"Error in listening for peers: {e}")

    def discover_peers(self):
        """Broadcast to discover peers"""
        broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        broadcast_socket.sendto(b"DISCOVER_PEER", ("<broadcast>", self.port))
        broadcast_socket.close()

    def broadcast(self, message):
        """Broadcast a message to all peers"""
        for peer in self.peers:
            self.socket.sendto(message.encode('utf-8'), peer)
            print(f"Message sent to {peer[0]}")

    def send_file(self, file_path, peer_ip):
        """Send a file to a specific peer"""
        try:
            file_name = os.path.basename(file_path)
            with open(file_path, 'rb') as file:
                file_data = file.read()
                file_size = len(file_data)

            peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            peer_socket.connect((peer_ip, self.port))

            # Send file information
            peer_socket.send(f"{file_name},{file_size}".encode('utf-8'))

            # Send file data in chunks
            peer_socket.sendall(file_data)
            peer_socket.close()
            print(f"File sent to {peer_ip}")
        except Exception as e:
            print(f"Error sending file to {peer_ip}: {e}")

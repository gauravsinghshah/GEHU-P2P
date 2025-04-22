import socket
import threading
import json
import os

class PeerNetwork:
    def __init__(self, port=8081):
        self.port = port
        self.host = socket.gethostbyname(socket.gethostname())
        self.peers = {}

    def listen_for_peers(self):
        """Listen for incoming peer broadcasts"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            sock.bind(('', self.port))
            print(f"Listening for peers on port {self.port}...")
        except OSError as e:
            print(f"ERROR: Port {self.port} is already in use. Please close the conflicting process or choose a different port.")
            return  # Exit the function to avoid further issues

        while True:
            data, addr = sock.recvfrom(1024)
            if data:
                try:
                    message = json.loads(data.decode())
                    if message["type"] == "discover":
                        self.peers[addr[0]] = message
                        print(f"Discovered peer: {addr[0]}")
                except json.JSONDecodeError:
                    print(f"Received invalid JSON from {addr}")

    def discover_peers(self):
        """Broadcast presence to local network"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        message = json.dumps({
            "type": "discover",
            "host": self.host,
            "port": self.port
        })
        try:
            sock.sendto(message.encode(), ('<broadcast>', self.port))
            print("Broadcasting presence to local network...")
        except Exception as e:
            print(f"Error broadcasting presence: {str(e)}")
        finally:
            sock.close()

    def broadcast(self, message):
        """Broadcast a message to all known peers"""
        for peer_ip in self.peers:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            try:
                sock.sendto(message.encode(), (peer_ip, self.port))
                print(f"Message sent to {peer_ip}")
            except Exception as e:
                print(f"Error sending message to {peer_ip}: {str(e)}")
            finally:
                sock.close()

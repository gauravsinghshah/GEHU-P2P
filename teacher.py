import sys
import threading
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QTextEdit, QLineEdit, QPushButton, 
                             QLabel, QFileDialog, QMessageBox, QGroupBox, QListWidget)
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot
from network import PeerNetwork

class SignalHandler(QObject):
    # Define custom signals
    peer_discovered = pyqtSignal(str)
    status_update = pyqtSignal(str)
    show_message_box = pyqtSignal(str, str, int)  # title, message, icon type

class TeacherWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GEHU P2P - Teacher")
        self.resize(700, 500)
        
        # Initialize signal handler
        self.signal_handler = SignalHandler()
        self.signal_handler.peer_discovered.connect(self.add_peer_to_list)
        self.signal_handler.status_update.connect(self.update_status)
        self.signal_handler.show_message_box.connect(self.display_message_box)
        
        # Initialize network
        self.network = PeerNetwork(
            port=8080,
            file_port=8081,
            on_peer_discovered=self.on_peer_discovered
        )
        
        self.init_ui()
        self.start_listening()
    
    def init_ui(self):
        # Main widget and layout
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        
        # Connected peers frame
        peers_group = QGroupBox("Connected Peers")
        peers_layout = QVBoxLayout(peers_group)
        
        self.peers_list = QListWidget()
        peers_layout.addWidget(self.peers_list)
        
        refresh_btn = QPushButton("Refresh Peers")
        refresh_btn.clicked.connect(self.refresh_peers)
        peers_layout.addWidget(refresh_btn)
        
        main_layout.addWidget(peers_group)
        
        # Message frame
        message_group = QGroupBox("Broadcast Message")
        message_layout = QVBoxLayout(message_group)
        
        self.message_entry = QTextEdit()
        self.message_entry.setPlaceholderText("Type your message here...")
        message_layout.addWidget(self.message_entry)
        
        send_msg_btn = QPushButton("Broadcast Message")
        send_msg_btn.clicked.connect(self.broadcast_message)
        send_msg_btn.setStyleSheet("background-color: #6C63FF; color: white;")
        message_layout.addWidget(send_msg_btn)
        
        main_layout.addWidget(message_group)
        
        # File sharing frame
        file_group = QGroupBox("Share File")
        file_layout = QHBoxLayout(file_group)
        
        self.file_path_entry = QLineEdit()
        self.file_path_entry.setReadOnly(True)
        file_layout.addWidget(self.file_path_entry, 4)
        
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self.browse_file)
        file_layout.addWidget(browse_btn, 1)
        
        send_file_btn = QPushButton("Send File")
        send_file_btn.clicked.connect(self.send_file_thread)
        send_file_btn.setStyleSheet("background-color: #6C63FF; color: white;")
        file_layout.addWidget(send_file_btn, 1)
        
        main_layout.addWidget(file_group)
        
        # Status bar for feedback
        status_group = QGroupBox("Status")
        status_layout = QVBoxLayout(status_group)
        
        self.status_text = QTextEdit()
        self.status_text.setReadOnly(True)
        self.status_text.setMaximumHeight(100)
        status_layout.addWidget(self.status_text)
        
        main_layout.addWidget(status_group)
        
        self.setCentralWidget(central_widget)
    
    def start_listening(self):
        """Start listening for incoming peers (UDP)"""
        threading.Thread(target=self.network.listen_for_peers, daemon=True).start()
        
        # Broadcast presence to find peers
        self.refresh_peers()
    
    def refresh_peers(self):
        """Broadcast to discover peers"""
        self.network.discover_peers()
        self.signal_handler.status_update.emit("Searching for peers...")
    
    def on_peer_discovered(self, message, address):
        """Callback when a peer is discovered"""
        ip_address = address[0]
        self.signal_handler.peer_discovered.emit(ip_address)
    
    @pyqtSlot(str)
    def add_peer_to_list(self, ip_address):
        """Add discovered peer to the UI list"""
        # Check if already in the list widget
        items = [self.peers_list.item(i).text() for i in range(self.peers_list.count())]
        if ip_address not in items:
            self.peers_list.addItem(ip_address)
            self.signal_handler.status_update.emit(f"New peer discovered: {ip_address}")
    
    @pyqtSlot(str)
    def update_status(self, message):
        """Update status text"""
        self.status_text.append(message)
        # Scroll to bottom
        scrollbar = self.status_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    @pyqtSlot(str, str, int)
    def display_message_box(self, title, message, icon_type=QMessageBox.Information):
        """Safely display a message box from the main thread"""
        if icon_type == QMessageBox.Warning:
            QMessageBox.warning(self, title, message)
        else:
            QMessageBox.information(self, title, message)
    
    def browse_file(self):
        """Browse for file to share"""
        file_path, _ = QFileDialog.getOpenFileName(self, "Select File")
        if file_path:
            self.file_path_entry.setText(file_path)
    
    def broadcast_message(self):
        """Send message to all connected peers"""
        message = self.message_entry.toPlainText().strip()
        if not message:
            self.signal_handler.show_message_box.emit("Empty Message", "Please enter a message to broadcast.", QMessageBox.Warning)
            return
            
        if not self.network.peers:
            self.signal_handler.show_message_box.emit("No Peers", "No peers connected to send message to.", QMessageBox.Warning)
            return
            
        success_count = 0
        failed_count = 0
        
        for peer in self.network.peers:
            peer_ip = peer[0] if isinstance(peer, tuple) else peer
            if self.network.send_message(peer_ip, message):
                success_count += 1
            else:
                failed_count += 1
        
        status = f"Message sent to {success_count} peer(s), failed for {failed_count} peer(s)"
        self.signal_handler.status_update.emit(status)
        
        if success_count > 0:
            self.message_entry.clear()
            self.signal_handler.show_message_box.emit("Success", status, QMessageBox.Information)
        else:
            self.signal_handler.show_message_box.emit("Failed", "Failed to send message to any peers.", QMessageBox.Warning)
    
    def send_file_thread(self):
        """Run send_file in a separate thread"""
        threading.Thread(target=self.send_file, daemon=True).start()
    
    def send_file(self):
        """Send selected file to all peers"""
        file_path = self.file_path_entry.text()
        if not file_path or not os.path.isfile(file_path):
            self.signal_handler.status_update.emit(" Invalid file selected")
            self.signal_handler.show_message_box.emit("Warning", "Please select a valid file to send", QMessageBox.Warning)
            return
        
        if not self.network.peers:
            self.signal_handler.status_update.emit(" No peers discovered")
            self.signal_handler.show_message_box.emit("No Peers", "No peers discovered to send the file to.", QMessageBox.Warning)
            return
        
        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        self.signal_handler.status_update.emit(f"Sending {file_name} ({file_size} bytes) to {len(self.network.peers)} peer(s)...")
        
        successful_sends, failed_sends = 0, 0
        for peer in self.network.peers:
            peer_ip = peer[0] if isinstance(peer, tuple) else peer
            try:
                if self.network.send_file(file_path, peer_ip):
                    successful_sends += 1
                    self.signal_handler.status_update.emit(f" Sent to {peer_ip}")
                else:
                    failed_sends += 1
                    self.signal_handler.status_update.emit(f" Failed sending to {peer_ip}")
            except Exception as e:
                failed_sends += 1
                self.signal_handler.status_update.emit(f" Error sending to {peer_ip}: {str(e)}")
        
        result = f"File successfully sent to {successful_sends} peer(s), failed for {failed_sends}."
        self.signal_handler.status_update.emit(result)
        
        self.signal_handler.show_message_box.emit("File Sent", result, QMessageBox.Information)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TeacherWindow()
    window.show()
    sys.exit(app.exec_())

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QLineEdit, QPushButton, QListWidget, QFileDialog, QMessageBox, QHBoxLayout
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot
import os
import threading

class SignalHandler(QObject):
    peer_discovered = pyqtSignal(str)
    status_update = pyqtSignal(str)
    show_message_box = pyqtSignal(str, str)

class TeacherPanel(QWidget):
    def __init__(self, network, name, username):
        super().__init__()
        self.network = network
        self.name = name
        self.username = username
        self.signal_handler = SignalHandler()
        self.signal_handler.peer_discovered.connect(self.add_peer)
        self.signal_handler.status_update.connect(self.update_status)
        self.signal_handler.show_message_box.connect(self.show_message_box)
        self.init_ui()
        self.start_listening()

    def init_ui(self):
        layout = QVBoxLayout(self)
        self.peers_list = QListWidget()
        layout.addWidget(self.peers_list)
        refresh_btn = QPushButton("Refresh Peers")
        refresh_btn.clicked.connect(self.network.discover_peers)
        refresh_btn.setStyleSheet("background-color: #4f46e5; color: white; padding: 8px; border-radius: 5px;")
        layout.addWidget(refresh_btn)
        self.message_entry = QTextEdit()
        self.message_entry.setPlaceholderText("Broadcast message...")
        layout.addWidget(self.message_entry)
        send_msg_btn = QPushButton("Send Message")
        send_msg_btn.clicked.connect(self.broadcast_message)
        send_msg_btn.setStyleSheet("background-color: #4f46e5; color: white; padding: 8px; border-radius: 5px;")
        layout.addWidget(send_msg_btn)
        self.file_path = QLineEdit()
        self.file_path.setReadOnly(True)
        layout.addWidget(self.file_path)
        file_layout = QHBoxLayout()
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self.browse_file)
        browse_btn.setStyleSheet("background-color: #4f46e5; color: white; padding: 8px; border-radius: 5px;")
        file_layout.addWidget(browse_btn)
        send_file_btn = QPushButton("Send File")
        send_file_btn.clicked.connect(self.send_file)
        send_file_btn.setStyleSheet("background-color: #4f46e5; color: white; padding: 8px; border-radius: 5px;")
        file_layout.addWidget(send_file_btn)
        layout.addLayout(file_layout)
        self.status = QTextEdit()
        self.status.setReadOnly(True)
        self.status.setMaximumHeight(100)
        layout.addWidget(self.status)

    def start_listening(self):
        self.network.on_peer_discovered = lambda ip: self.signal_handler.peer_discovered.emit(ip)
        threading.Thread(target=self.network.listen_for_peers, daemon=True).start()
        self.network.discover_peers()

    @pyqtSlot(str)
    def add_peer(self, ip):
        if ip not in [self.peers_list.item(i).text() for i in range(self.peers_list.count())]:
            self.peers_list.addItem(ip)
            self.signal_handler.status_update.emit(f"Peer discovered: {ip}")

    @pyqtSlot(str)
    def update_status(self, msg):
        self.status.append(msg)
        self.status.verticalScrollBar().setValue(self.status.verticalScrollBar().maximum())

    @pyqtSlot(str, str)
    def show_message_box(self, title, message):
        QMessageBox.information(self, title, message)

    def browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select File")
        if file_path:
            self.file_path.setText(file_path)

    def broadcast_message(self):
        msg = self.message_entry.toPlainText().strip()
        if not msg:
            self.signal_handler.show_message_box.emit("Warning", "Enter a message")
            return
        if not self.network.peers:
            self.signal_handler.show_message_box.emit("Warning", "No peers connected")
            return
        success = sum(self.network.send_message(peer[0], msg) for peer in self.network.peers)
        self.signal_handler.status_update.emit(f"Message sent to {success} peer(s)")
        self.message_entry.clear()

    def send_file(self):
        file_path = self.file_path.text()
        if not file_path or not os.path.isfile(file_path):
            self.signal_handler.show_message_box.emit("Warning", "Select a valid file")
            return
        if not self.network.peers:
            self.signal_handler.show_message_box.emit("Warning", "No peers connected")
            return
        threading.Thread(target=self.network.send_file_chunks, args=(file_path, self.network.peers, 'teacher'), daemon=True).start()
        self.signal_handler.status_update.emit(f"Sending {os.path.basename(file_path)} to {len(self.network.peers)} peer(s)")
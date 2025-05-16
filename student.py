from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QTreeWidget, QTreeWidgetItem, QPushButton, QMessageBox, QFileDialog, QHBoxLayout, QLineEdit, QListWidget, QGroupBox
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot, QObject
import os
from pathlib import Path
import threading

class SignalHandler(QObject):
    message_received = pyqtSignal(str)
    file_received = pyqtSignal(str, str, str)
    show_message_box = pyqtSignal(str, str)
    peer_discovered = pyqtSignal(str, str)
    progress_update = pyqtSignal(str, int, int, float)
    error_occurred = pyqtSignal(str)  # New signal for errors

class StudentPanel(QWidget):
    def __init__(self, network, name, username):
        super().__init__()
        self.network = network
        self.name = name
        self.username = username
        self.chunks = {}
        self.file_history = []  # Store file sharing history
        self.current_file = None  # Track the current file being received
        self.signal_handler = SignalHandler()
        self.signal_handler.message_received.connect(self.update_messages)
        self.signal_handler.file_received.connect(self.add_file_to_list)
        self.signal_handler.show_message_box.connect(self.show_message_box)
        self.signal_handler.peer_discovered.connect(self.add_peer)
        self.signal_handler.progress_update.connect(self.update_progress)
        self.signal_handler.error_occurred.connect(self.handle_error)  # Connect error signal
        self.init_ui()
        self.start_listening()
        self.network.broadcast_name(self.name)  # Broadcast student's name

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Peers panel
        peers_group = QGroupBox("Connected Peers")
        peers_layout = QVBoxLayout()
        self.peers_list = QListWidget()
        peers_layout.addWidget(self.peers_list)
        refresh_btn = QPushButton("Refresh Peers")
        refresh_btn.clicked.connect(self.network.discover_peers)
        refresh_btn.setStyleSheet("background-color: #4f46e5; color: white; padding: 8px; border-radius: 5px;")
        peers_layout.addWidget(refresh_btn)
        peers_group.setLayout(peers_layout)
        layout.addWidget(peers_group)

        # Messages panel
        messages_group = QGroupBox("Messages")
        messages_layout = QVBoxLayout()
        self.messages = QTextEdit()
        self.messages.setReadOnly(True)
        messages_layout.addWidget(self.messages)
        reply_layout = QHBoxLayout()
        self.reply_entry = QLineEdit()
        self.reply_entry.setPlaceholderText("Type your reply...")
        reply_layout.addWidget(self.reply_entry)
        send_reply_btn = QPushButton("Send Reply")
        send_reply_btn.clicked.connect(self.send_reply)
        send_reply_btn.setStyleSheet("background-color: #4f46e5; color: white; padding: 8px; border-radius: 5px;")
        reply_layout.addWidget(send_reply_btn)
        messages_layout.addLayout(reply_layout)
        messages_group.setLayout(messages_layout)
        layout.addWidget(messages_group)

        # Files panel
        files_group = QGroupBox("Received Files")
        files_layout = QVBoxLayout()
        self.files_tree = QTreeWidget()
        self.files_tree.setHeaderLabels(["File", "Size", "Sender"])
        self.files_tree.setColumnWidth(0, 200)
        files_layout.addWidget(self.files_tree)
        download_btn = QPushButton("Download")
        download_btn.clicked.connect(self.download_file)
        download_btn.setStyleSheet("background-color: #4f46e5; color: white; padding: 8px; border-radius: 5px;")
        files_layout.addWidget(download_btn)
        files_group.setLayout(files_layout)
        layout.addWidget(files_group)

        # File sharing history panel
        history_group = QGroupBox("File Sharing History")
        history_layout = QVBoxLayout()
        self.history_list = QTextEdit()
        self.history_list.setReadOnly(True)
        history_layout.addWidget(self.history_list)
        history_group.setLayout(history_layout)
        layout.addWidget(history_group)

    def start_listening(self):
        self.network.on_message_received = self.handle_message
        self.network.on_file_chunk_received = self.handle_file_chunk
        self.network.on_peer_discovered = lambda ip: self.signal_handler.peer_discovered.emit(ip, self.network.peer_names.get(ip, "Unknown"))
        self.network.on_error = lambda msg: self.signal_handler.error_occurred.emit(msg)
        for target in [self.network.listen_for_peers, self.network.listen_for_messages, self.network.listen_for_file_chunks]:
            threading.Thread(target=target, daemon=True).start()
        self.network.discover_peers()

    def handle_message(self, message, sender_ip, sender_name):
        self.signal_handler.message_received.emit(f"From {sender_name}: {message}")

    def handle_file_chunk(self, file_name, chunk_id, total_chunks, chunk_data, sender_ip, role, sender_name):
        try:
            if file_name not in self.chunks:
                self.chunks[file_name] = {}
                self.current_file = file_name
            self.chunks[file_name][chunk_id] = chunk_data
            percentage = ((chunk_id + 1) / total_chunks) * 100
            self.signal_handler.progress_update.emit(file_name, chunk_id + 1, total_chunks, percentage)
            if len(self.chunks[file_name]) == total_chunks:
                self.reconstruct_file(file_name, total_chunks, sender_name)
                self.current_file = None
        except Exception as e:
            self.signal_handler.error_occurred.emit(f"Error handling file chunk: {str(e)}")

    def reconstruct_file(self, file_name, total_chunks, sender_name):
        try:
            file_data = b''.join(self.chunks[file_name][i] for i in range(total_chunks))
            save_dir = Path.home() / "Downloads" / "GEHU_P2P"
            save_dir.mkdir(exist_ok=True)
            file_path = save_dir / file_name
            with open(file_path, 'wb') as f:
                f.write(file_data)
            size = len(file_data)
            size_str = f"{size // 1024} KB" if size >= 1024 else f"{size} bytes"
            self.signal_handler.file_received.emit(file_name, size_str, sender_name)
            self.signal_handler.show_message_box.emit("File Received", f"Saved {file_name} to {file_path}")
            self.file_history.append(f"Received {file_name} ({size_str}) from {sender_name}")
            self.history_list.setText("; ".join(self.file_history))
            del self.chunks[file_name]
        except Exception as e:
            self.signal_handler.error_occurred.emit(f"Error reconstructing file: {str(e)}")

    @pyqtSlot(str)
    def update_messages(self, msg):
        self.messages.append(msg)
        self.messages.verticalScrollBar().setValue(self.messages.verticalScrollBar().maximum())

    @pyqtSlot(str, int, int, float)
    def update_progress(self, file_name, chunk_id, total_chunks, percentage):
        msg = f"Receiving {file_name}: Chunk {chunk_id}/{total_chunks} ({percentage:.1f}%)"
        current_text = self.messages.toPlainText()
        lines = current_text.split("\n")
        if lines and lines[-1].startswith(f"Receiving {file_name}:"):
            lines[-1] = msg
        else:
            lines.append(msg)
        self.messages.setText("\n".join(lines))
        self.messages.verticalScrollBar().setValue(self.messages.verticalScrollBar().maximum())

    @pyqtSlot(str, str, str)
    def add_file_to_list(self, name, size, sender):
        item = QTreeWidgetItem([name, size, sender])
        self.files_tree.addTopLevelItem(item)

    @pyqtSlot(str, str)
    def show_message_box(self, title, message):
        QMessageBox.information(self, title, message)

    @pyqtSlot(str)
    def handle_error(self, error_msg):
        self.signal_handler.show_message_box.emit("Error", error_msg)
        self.messages.append(f"Error: {error_msg}")

    @pyqtSlot(str, str)
    def add_peer(self, ip, name):
        if name not in [self.peers_list.item(i).text() for i in range(self.peers_list.count())]:
            self.peers_list.addItem(name)

    def send_reply(self):
        msg = self.reply_entry.text().strip()
        if not msg:
            self.signal_handler.show_message_box.emit("Warning", "Enter a reply")
            return
        if not self.network.peers:
            self.signal_handler.show_message_box.emit("Warning", "No peers connected")
            return
        success = sum(self.network.send_message(peer[0], msg, self.name) for peer in self.network.peers)
        self.signal_handler.message_received.emit(f"You: {msg}")
        self.reply_entry.clear()

    def download_file(self):
        item = self.files_tree.currentItem()
        if not item:
            self.signal_handler.show_message_box.emit("Warning", "Select a file to download")
            return
        file_name = item.text(0)
        file_path, _ = QFileDialog.getSaveFileName(self, "Save File", file_name)
        if file_path:
            source_path = Path.home() / "Downloads" / "GEHU_P2P" / file_name
            if source_path.exists():
                with open(source_path, 'rb') as src, open(file_path, 'wb') as dst:
                    dst.write(src.read())
                self.signal_handler.show_message_box.emit("Success", f"Saved to {file_path}")
            else:
                self.signal_handler.show_message_box.emit("Error", "File not found")
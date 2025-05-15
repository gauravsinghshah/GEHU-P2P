from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QTreeWidget, QTreeWidgetItem, QPushButton, QMessageBox, QFileDialog
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot, QObject
import os
from pathlib import Path
import threading

class SignalHandler(QObject):
    message_received = pyqtSignal(str)
    file_received = pyqtSignal(str, str, str)
    show_message_box = pyqtSignal(str, str)

class StudentPanel(QWidget):
    def __init__(self, network, name, username):
        super().__init__()
        self.network = network
        self.name = name
        self.username = username
        self.chunks = {}
        self.signal_handler = SignalHandler()
        self.signal_handler.message_received.connect(self.update_messages)
        self.signal_handler.file_received.connect(self.add_file_to_list)
        self.signal_handler.show_message_box.connect(self.show_message_box)
        self.init_ui()
        self.start_listening()

    def init_ui(self):
        layout = QVBoxLayout(self)
        self.messages = QTextEdit()
        self.messages.setReadOnly(True)
        layout.addWidget(self.messages)
        self.files_tree = QTreeWidget()
        self.files_tree.setHeaderLabels(["File", "Size", "Sender"])
        self.files_tree.setColumnWidth(0, 200)
        layout.addWidget(self.files_tree)
        download_btn = QPushButton("Download")
        download_btn.clicked.connect(self.download_file)
        download_btn.setStyleSheet("background-color: #4f46e5; color: white; padding: 8px; border-radius: 5px;")
        layout.addWidget(download_btn)

    def start_listening(self):
        self.network.on_message_received = self.handle_message
        self.network.on_file_chunk_received = self.handle_file_chunk
        for target in [self.network.listen_for_peers, self.network.listen_for_messages, self.network.listen_for_file_chunks]:
            threading.Thread(target=target, daemon=True).start()
        self.network.discover_peers()

    def handle_message(self, message, sender_ip):
        self.signal_handler.message_received.emit(f"From {sender_ip}: {message}")

    def handle_file_chunk(self, file_name, chunk_id, total_chunks, chunk_data, sender_ip, role):
        if file_name not in self.chunks:
            self.chunks[file_name] = {}
        self.chunks[file_name][chunk_id] = chunk_data
        self.signal_handler.message_received.emit(f"Received chunk {chunk_id}/{total_chunks} of {file_name} from {sender_ip}")
        if len(self.chunks[file_name]) == total_chunks:
            self.reconstruct_file(file_name, total_chunks, sender_ip)

    def reconstruct_file(self, file_name, total_chunks, sender_ip):
        file_data = b''.join(self.chunks[file_name][i] for i in range(total_chunks))
        save_dir = Path.home() / "Downloads" / "GEHU_P2P"
        save_dir.mkdir(exist_ok=True)
        file_path = save_dir / file_name
        with open(file_path, 'wb') as f:
            f.write(file_data)
        size = len(file_data)
        size_str = f"{size // 1024} KB" if size >= 1024 else f"{size} bytes"
        self.signal_handler.file_received.emit(file_name, size_str, sender_ip)
        self.signal_handler.show_message_box.emit("File Received", f"Saved {file_name} to {file_path}")
        del self.chunks[file_name]

    @pyqtSlot(str)
    def update_messages(self, msg):
        self.messages.append(msg)
        self.messages.verticalScrollBar().setValue(self.messages.verticalScrollBar().maximum())

    @pyqtSlot(str, str, str)
    def add_file_to_list(self, name, size, sender):
        item = QTreeWidgetItem([name, size, sender])
        self.files_tree.addTopLevelItem(item)

    @pyqtSlot(str, str)
    def show_message_box(self, title, message):
        QMessageBox.information(self, title, message)

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
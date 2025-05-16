from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QLineEdit, QPushButton, QListWidget, QFileDialog, QMessageBox, QHBoxLayout, QGroupBox, QComboBox
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot
import os
import threading
import zipfile
import shutil
from pathlib import Path

class SignalHandler(QObject):
    peer_discovered = pyqtSignal(str, str)
    status_update = pyqtSignal(str)
    show_message_box = pyqtSignal(str, str)
    progress_update = pyqtSignal(int, int, float)
    error_occurred = pyqtSignal(str)  # New signal for errors

class TeacherPanel(QWidget):
    def __init__(self, network, name, username):
        super().__init__()
        self.network = network
        self.name = name
        self.username = username
        self.file_history = []  # Store file sharing history
        self.current_file = None
        self.temp_zip_path = None  # Store path of temporary zip file
        self.signal_handler = SignalHandler()
        self.signal_handler.peer_discovered.connect(self.add_peer)
        self.signal_handler.status_update.connect(self.update_status)
        self.signal_handler.show_message_box.connect(self.show_message_box)
        self.signal_handler.progress_update.connect(self.update_progress)
        self.signal_handler.error_occurred.connect(self.handle_error)  # Connect error signal
        self.init_ui()
        self.start_listening()
        self.network.broadcast_name(self.name)  # Broadcast teacher's name

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

        # Broadcast message panel
        message_group = QGroupBox("Broadcast Message")
        message_layout = QVBoxLayout()
        self.message_entry = QTextEdit()
        self.message_entry.setPlaceholderText("Broadcast message...")
        message_layout.addWidget(self.message_entry)
        send_msg_btn = QPushButton("Send Message")
        send_msg_btn.clicked.connect(self.broadcast_message)
        send_msg_btn.setStyleSheet("background-color: #4f46e5; color: white; padding: 8px; border-radius: 5px;")
        message_layout.addWidget(send_msg_btn)
        message_group.setLayout(message_layout)
        layout.addWidget(message_group)

        # File/Folder sharing panel
        file_group = QGroupBox("Share File or Folder")
        file_layout = QVBoxLayout()
        self.selection_type = QComboBox()
        self.selection_type.addItems(["File", "Folder"])
        file_layout.addWidget(self.selection_type)
        self.file_path = QLineEdit()
        self.file_path.setReadOnly(True)
        file_layout.addWidget(self.file_path)
        file_btn_layout = QHBoxLayout()
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self.browse_file_or_folder)
        browse_btn.setStyleSheet("background-color: #4f46e5; color: white; padding: 8px; border-radius: 5px;")
        file_btn_layout.addWidget(browse_btn)
        send_file_btn = QPushButton("Send")
        send_file_btn.clicked.connect(self.send_file_or_folder)
        send_file_btn.setStyleSheet("background-color: #4f46e5; color: white; padding: 8px; border-radius: 5px;")
        file_btn_layout.addWidget(send_file_btn)
        file_layout.addLayout(file_btn_layout)
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)

        # Status panel (includes progress)
        status_group = QGroupBox("Status")
        status_layout = QVBoxLayout()
        self.status = QTextEdit()
        self.status.setReadOnly(True)
        self.status.setMaximumHeight(100)
        status_layout.addWidget(self.status)
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)

        # File sharing history panel
        history_group = QGroupBox("File Sharing History")
        history_layout = QVBoxLayout()
        self.history_list = QTextEdit()
        self.history_list.setReadOnly(True)
        history_layout.addWidget(self.history_list)
        history_group.setLayout(history_layout)
        layout.addWidget(history_group)

    def start_listening(self):
        self.network.on_peer_discovered = lambda ip: self.signal_handler.peer_discovered.emit(ip, self.network.peer_names.get(ip, "Unknown"))
        self.network.on_message_received = self.handle_message
        # Pass error signal handler to network
        self.network.on_error = lambda msg: self.signal_handler.error_occurred.emit(msg)
        threading.Thread(target=self.network.listen_for_peers, daemon=True).start()
        threading.Thread(target=self.network.listen_for_messages, daemon=True).start()
        self.network.discover_peers()

    def handle_message(self, message, sender_ip, sender_name):
        self.signal_handler.status_update.emit(f"From {sender_name}: {message}")

    @pyqtSlot(str, str)
    def add_peer(self, ip, name):
        if name not in [self.peers_list.item(i).text() for i in range(self.peers_list.count())]:
            self.peers_list.addItem(name)
            self.signal_handler.status_update.emit(f"Peer discovered: {name}")

    @pyqtSlot(str)
    def update_status(self, msg):
        self.status.append(msg)
        self.status.verticalScrollBar().setValue(self.status.verticalScrollBar().maximum())

    @pyqtSlot(int, int, float)
    def update_progress(self, chunk_id, total_chunks, percentage):
        msg = f"Sending: {self.current_file} | Chunk: {chunk_id}/{total_chunks} | Progress: {percentage:.1f}%"
        current_text = self.status.toPlainText()
        lines = current_text.split("\n")
        if lines and lines[-1].startswith(f"Sending: {self.current_file}"):
            lines[-1] = msg
        else:
            lines.append(msg)
        self.status.setText("\n".join(lines))
        self.status.verticalScrollBar().setValue(self.status.verticalScrollBar().maximum())

    @pyqtSlot(str, str)
    def show_message_box(self, title, message):
        QMessageBox.information(self, title, message)

    @pyqtSlot(str)
    def handle_error(self, error_msg):
        self.signal_handler.show_message_box.emit("Error", error_msg)
        self.signal_handler.status_update.emit(f"Error: {error_msg}")

    def browse_file_or_folder(self):
        if self.selection_type.currentText() == "File":
            file_path, _ = QFileDialog.getOpenFileName(self, "Select File")
            if file_path:
                self.file_path.setText(file_path)
        else:
            folder_path = QFileDialog.getExistingDirectory(self, "Select Folder")
            if folder_path:
                self.file_path.setText(folder_path)

    def zip_folder(self, folder_path):
        try:
            folder_name = os.path.basename(folder_path)
            self.temp_zip_path = os.path.join(os.path.dirname(folder_path), f"{folder_name}.zip")
            with zipfile.ZipFile(self.temp_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(folder_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, os.path.dirname(folder_path))
                        zipf.write(file_path, arcname)
            return self.temp_zip_path
        except Exception as e:
            self.signal_handler.error_occurred.emit(f"Failed to zip folder: {str(e)}")
            return None

    def send_file_or_folder(self):
        path = self.file_path.text()
        if not path:
            self.signal_handler.show_message_box.emit("Warning", "Select a file or folder")
            return
        if not self.network.peers:
            self.signal_handler.show_message_box.emit("Warning", "No peers connected")
            return

        try:
            if self.selection_type.currentText() == "File":
                if not os.path.isfile(path):
                    self.signal_handler.show_message_box.emit("Warning", "Select a valid file")
                    return
                self.current_file = os.path.basename(path)
                file_path = path
            else:
                if not os.path.isdir(path):
                    self.signal_handler.show_message_box.emit("Warning", "Select a valid folder")
                    return
                file_path = self.zip_folder(path)
                if not file_path:  # Zipping failed
                    return
                self.current_file = os.path.basename(file_path)

            # Start sending in a thread
            threading.Thread(
                target=self.network.send_file_chunks,
                args=(file_path, self.network.peers, 'teacher', self.name, self.signal_handler.progress_update.emit),
                daemon=True
            ).start()

            # Add to history
            self.file_history.append(f"Sent {self.current_file} to {len(self.network.peers)} peer(s)")
            self.history_list.setText("; ".join(self.file_history))

        except Exception as e:
            self.signal_handler.error_occurred.emit(f"Error preparing file/folder for sending: {str(e)}")
        finally:
            # Safely clean up temporary zip file
            if self.selection_type.currentText() == "Folder" and self.temp_zip_path and os.path.exists(self.temp_zip_path):
                try:
                    os.remove(self.temp_zip_path)
                    self.signal_handler.status_update.emit(f"Cleaned up temporary file: {self.temp_zip_path}")
                except Exception as e:
                    self.signal_handler.error_occurred.emit(f"Failed to clean up temporary file: {str(e)}")
                self.temp_zip_path = None

    def broadcast_message(self):
        msg = self.message_entry.toPlainText().strip()
        if not msg:
            self.signal_handler.show_message_box.emit("Warning", "Enter a message")
            return
        if not self.network.peers:
            self.signal_handler.show_message_box.emit("Warning", "No peers connected")
            return
        success = sum(self.network.send_message(peer[0], msg, self.name) for peer in self.network.peers)
        self.signal_handler.status_update.emit(f"Message sent to {success} peer(s)")
        self.message_entry.clear()
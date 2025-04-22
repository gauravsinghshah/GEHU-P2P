import sys
import threading
import json
import os
from pathlib import Path
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QTextEdit, QTreeWidget, QTreeWidgetItem, 
                             QPushButton, QLabel, QFileDialog, QMessageBox, QGroupBox)
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, Qt
from network import PeerNetwork

class SignalHandler(QObject):
    # Define custom signals
    message_received = pyqtSignal(str)
    file_received = pyqtSignal(str, str, str, int)
    peer_discovered = pyqtSignal(str)

class StudentWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GEHU P2P - Student")
        self.resize(800, 600)
        
        # Initialize signal handler
        self.signal_handler = SignalHandler()
        self.signal_handler.message_received.connect(self.update_messages)
        self.signal_handler.file_received.connect(self.add_file_to_list)
        self.signal_handler.peer_discovered.connect(self.update_messages)
        
        # File storage
        self.received_files = {}  # Dictionary to store received files
        
        # Initialize network
        self.network = PeerNetwork(
            on_file_received=self.handle_file_received,
            on_peer_discovered=self.handle_peer_discovery,
            on_message_received=self.handle_message_received
        )
        
        self.init_ui()
        self.start_listening()
        self.join_session()
    
    def init_ui(self):
        # Main widget and layout
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        
        # Messages group
        messages_group = QGroupBox("Received Messages")
        messages_layout = QVBoxLayout(messages_group)
        
        self.messages_text = QTextEdit()
        self.messages_text.setReadOnly(True)
        messages_layout.addWidget(self.messages_text)
        
        main_layout.addWidget(messages_group)
        
        # Files group
        files_group = QGroupBox("Shared Files")
        files_layout = QVBoxLayout(files_group)
        
        self.files_tree = QTreeWidget()
        self.files_tree.setHeaderLabels(["Name", "Size", "Shared By"])
        self.files_tree.setColumnWidth(0, 250)
        self.files_tree.setColumnWidth(1, 100)
        self.files_tree.setColumnWidth(2, 150)
        files_layout.addWidget(self.files_tree)
        
        download_btn = QPushButton("Download Selected")
        download_btn.clicked.connect(self.download_file)
        download_btn.setStyleSheet("background-color: #6C63FF; color: white;")
        files_layout.addWidget(download_btn)
        
        main_layout.addWidget(files_group)
        
        self.setCentralWidget(central_widget)
    
    def handle_message_received(self, message, sender_address):
        """Handle direct messages from teacher"""
        display_msg = f"Message from {sender_address[0]}: {message}"
        self.signal_handler.message_received.emit(display_msg)
    
    def handle_file_received(self, payload, sender_address):
        """Handles file payloads from the teacher."""
        try:
            data = json.loads(payload.decode())
            file_name = data["file_name"]
            file_data = bytes.fromhex(data["file_data"])
            sender_ip = sender_address[0]
            
            # Save file to downloads folder
            save_dir = Path.home() / "Downloads" / "GEHU_P2P_Received"
            save_dir.mkdir(parents=True, exist_ok=True)
            file_path = save_dir / file_name
            with open(file_path, 'wb') as f:
                f.write(file_data)
            
            # Store file info for later download
            self.received_files[file_name] = {
                'path': str(file_path),
                'size': len(file_data),
                'sender': sender_ip
            }
            
            self.signal_handler.message_received.emit(f"Received file: {file_name} from {sender_ip}")
            self.signal_handler.file_received.emit(file_name, f"{len(file_data) // 1024} KB", sender_ip, len(file_data))
        
        except Exception as e:
            self.signal_handler.message_received.emit(f"Error handling file: {str(e)}")
    
    def handle_peer_discovery(self, message, addr):
        peer_info = f"Discovered peer: {addr[0]}"
        self.signal_handler.peer_discovered.emit(peer_info)
    
    @pyqtSlot(str)
    def update_messages(self, msg):
        self.messages_text.append(msg)
        # Scroll to bottom
        scrollbar = self.messages_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    @pyqtSlot(str, str, str, int)
    def add_file_to_list(self, name, size, sender, raw_size):
        item = QTreeWidgetItem([name, size, sender])
        item.setData(0, Qt.UserRole, raw_size)  # Store raw size for sorting
        self.files_tree.addTopLevelItem(item)
    
    def download_file(self):
        selected_items = self.files_tree.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Warning", "Please select a file to download")
            return
        
        selected_item = selected_items[0]
        file_name = selected_item.text(0)
        
        if file_name not in self.received_files:
            QMessageBox.warning(self, "Error", "File information not found")
            return
        
        source_path = self.received_files[file_name]['path']
        if not os.path.exists(source_path):
            QMessageBox.warning(self, "Error", f"Source file not found at {source_path}")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save File", file_name, "All Files (*.*)"
        )
        
        if file_path:
            try:
                # Copy file from received directory to selected location
                with open(source_path, 'rb') as src, open(file_path, 'wb') as dest:
                    dest.write(src.read())
                QMessageBox.information(self, "Success", f"File {file_name} saved to {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save file: {str(e)}")
    
    def start_listening(self):
        threading.Thread(target=self.network.listen_for_peers, daemon=True).start()
        threading.Thread(target=self.network.listen_for_files, daemon=True).start()
        threading.Thread(target=self.network.listen_for_messages, daemon=True).start()
    
    def join_session(self):
        self.network.discover_peers()
        # Use a small delay before showing the message
        QApplication.instance().processEvents()
        QMessageBox.information(self, "Success", "Connected to the session")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = StudentWindow()
    window.show()
    sys.exit(app.exec_())

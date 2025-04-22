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
    show_message_box = pyqtSignal(str, str, int)  # title, message, icon type

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
        self.signal_handler.show_message_box.connect(self.display_message_box)
        
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
    
    @pyqtSlot(str, str, int)
    def display_message_box(self, title, message, icon_type=QMessageBox.Information):
        """Safely display a message box from the main thread"""
        if icon_type == QMessageBox.Warning:
            QMessageBox.warning(self, title, message)
        else:
            QMessageBox.information(self, title, message)
    
    def handle_message_received(self, message, sender_address):
        """Handle direct messages from teacher"""
        display_msg = f" Message from {sender_address[0]}: {message}"
        self.signal_handler.message_received.emit(display_msg)
    
    def handle_file_received(self, file_data, sender_address):
        """Handles file data from the teacher."""
        try:
            # Extract file info - file_data is now a dictionary
            file_name = file_data["file_name"]
            file_binary = file_data["file_data"]  # This is now raw binary data
            sender_ip = sender_address[0]
            file_size = len(file_binary)
            
            # Save file to downloads folder
            save_dir = Path.home() / "Downloads" / "GEHU_P2P_Received"
            save_dir.mkdir(parents=True, exist_ok=True)
            file_path = save_dir / file_name
            
            with open(file_path, 'wb') as f:
                f.write(file_binary)
            
            self.signal_handler.message_received.emit(f" 📥 Received file: {file_name} ({file_size} bytes) from {sender_ip}")
            
            # Store file info for later download
            self.received_files[file_name] = {
                'path': str(file_path),
                'size': file_size,
                'sender': sender_ip
            }
            
            # Update UI with file info
            size_str = f"{file_size // 1024} KB" if file_size >= 1024 else f"{file_size} bytes"
            self.signal_handler.file_received.emit(file_name, size_str, sender_ip, file_size)
            
            # Show notification
            self.signal_handler.show_message_box.emit(
                "File Received", 
                f"Received file: {file_name} ({size_str}) from {sender_ip}.\n"
                f"The file has been saved to {file_path}",
                QMessageBox.Information
            )
            
        except Exception as e:
            error_msg = f" ❌ Error handling file: {str(e)}"
            self.signal_handler.message_received.emit(error_msg)
            self.signal_handler.show_message_box.emit("File Error", error_msg, QMessageBox.Warning)
    
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
            self.signal_handler.show_message_box.emit("Warning", "Please select a file to download", QMessageBox.Warning)
            return
        
        selected_item = selected_items[0]
        file_name = selected_item.text(0)
        
        if file_name not in self.received_files:
            self.signal_handler.show_message_box.emit("Error", "File information not found", QMessageBox.Warning)
            return
        
        source_path = self.received_files[file_name]['path']
        if not os.path.exists(source_path):
            self.signal_handler.show_message_box.emit(
                "Error", 
                f"Source file not found at {source_path}", 
                QMessageBox.Warning
            )
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save File", file_name, "All Files (*.*)"
        )
        
        if file_path:
            try:
                # Copy file from received directory to selected location
                with open(source_path, 'rb') as src, open(file_path, 'wb') as dest:
                    dest.write(src.read())
                self.signal_handler.show_message_box.emit(
                    "Success", 
                    f"File {file_name} saved to {file_path}", 
                    QMessageBox.Information
                )
            except Exception as e:
                self.signal_handler.show_message_box.emit(
                    "Error", 
                    f"Failed to save file: {str(e)}", 
                    QMessageBox.Warning
                )
    
    def start_listening(self):
        threading.Thread(target=self.network.listen_for_peers, daemon=True).start()
        threading.Thread(target=self.network.listen_for_files, daemon=True).start()
        threading.Thread(target=self.network.listen_for_messages, daemon=True).start()
        threading.Thread(target=self.network.listen_for_acks, daemon=True).start()
    
    def join_session(self):
        self.network.discover_peers()
        # Use a small delay before showing the message
        QApplication.instance().processEvents()
        self.signal_handler.show_message_box.emit("Success", "Connected to the session", QMessageBox.Information)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = StudentWindow()
    window.show()
    sys.exit(app.exec_())

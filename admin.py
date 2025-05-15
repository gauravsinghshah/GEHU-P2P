from PyQt5.QtWidgets import QWidget, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, QMessageBox, QComboBox
import json
import os

class AdminPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.credentials_file = "data/credentials.json"
        self.init_ui()
        self.load_credentials()

    def init_ui(self):
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.role_combo = QComboBox()
        self.role_combo.addItems(["student", "teacher"])
        form_layout.addRow("Role:", self.role_combo)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter username")
        form_layout.addRow("Username:", self.username_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter password")
        self.password_input.setEchoMode(QLineEdit.Password)
        form_layout.addRow("Password:", self.password_input)

        layout.addLayout(form_layout)

        add_btn = QPushButton("Add User")
        add_btn.clicked.connect(self.add_user)
        add_btn.setStyleSheet("background-color: #4f46e5; color: white; padding: 8px; border-radius: 5px;")
        layout.addWidget(add_btn)

        remove_btn = QPushButton("Remove User")
        remove_btn.clicked.connect(self.remove_user)
        remove_btn.setStyleSheet("background-color: #ef4444; color: white; padding: 8px; border-radius: 5px;")
        layout.addWidget(remove_btn)

    def load_credentials(self):
        default_credentials = {
            "student": [],
            "teacher": [],
            "admin": [{"username": "shah", "password": "shah#123"}]
        }
        os.makedirs("data", exist_ok=True)
        if not os.path.exists(self.credentials_file):
            with open(self.credentials_file, "w") as f:
                json.dump(default_credentials, f)
        try:
            with open(self.credentials_file, "r") as f:
                self.credentials = json.load(f)
            if "admin" not in self.credentials or not any(user["username"] == "shah" for user in self.credentials.get("admin", [])):
                self.credentials["admin"] = default_credentials["admin"]
                with open(self.credentials_file, "w") as f:
                    json.dump(self.credentials, f)
        except Exception as e:
            self.credentials = default_credentials
            with open(self.credentials_file, "w") as f:
                json.dump(self.credentials, f)

    def save_credentials(self):
        try:
            with open(self.credentials_file, "w") as f:
                json.dump(self.credentials, f, indent=2)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save credentials: {e}")

    def add_user(self):
        role = self.role_combo.currentText()
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        if not username or not password:
            QMessageBox.warning(self, "Error", "Username and password are required")
            return
        if any(user["username"] == username for user in self.credentials[role]):
            QMessageBox.warning(self, "Error", "Username already exists")
            return
        self.credentials[role].append({"username": username, "password": password})
        self.save_credentials()
        QMessageBox.information(self, "Success", f"Added {username} as {role}")
        self.username_input.clear()
        self.password_input.clear()

    def remove_user(self):
        role = self.role_combo.currentText()
        username = self.username_input.text().strip()
        if not username:
            QMessageBox.warning(self, "Error", "Username is required")
            return
        for user in self.credentials[role]:
            if user["username"] == username:
                self.credentials[role].remove(user)
                self.save_credentials()
                QMessageBox.information(self, "Success", f"Removed {username} from {role}")
                self.username_input.clear()
                self.password_input.clear()
                return
        QMessageBox.warning(self, "Error", f"Username {username} not found in {role}")
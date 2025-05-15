import sys
import os
import json
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QFrame, 
                             QStackedWidget, QSplashScreen, QLineEdit, QFormLayout,
                             QMessageBox, QTabWidget, QComboBox)
from PyQt5.QtCore import Qt, QTimer, QSize
from PyQt5.QtGui import QPixmap, QIcon, QFont, QColor, QPalette, QLinearGradient
from network import PeerNetwork
from student import StudentPanel
from teacher import TeacherPanel
from admin import AdminPanel

class LoginForm(QWidget):
    def __init__(self, on_login, role="student"):
        super().__init__()
        self.on_login = on_login
        self.role = role
        self.credentials_file = "data/credentials.json"
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        form_layout = QFormLayout()
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        form_layout.addRow("Username:", self.username_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.Password)
        form_layout.addRow("Password:", self.password_input)
        
        layout.addLayout(form_layout)

        login_btn = QPushButton("Login")
        login_btn.clicked.connect(self.attempt_login)
        login_btn.setStyleSheet("background-color: #6C63FF; color: white;")
        layout.addWidget(login_btn)
        
        self.setLayout(layout)

    def attempt_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        
        # Default credentials structure
        default_credentials = {
            "student": [],
            "teacher": [],
            "admin": [{"username": "shah", "password": "shah#123"}]
        }
        
        # Ensure credentials file exists
        try:
            os.makedirs("data", exist_ok=True)
            if not os.path.exists(self.credentials_file):
                with open(self.credentials_file, "w") as f:
                    json.dump(default_credentials, f)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create credentials file: {e}")
            return
        
        # Load credentials
        try:
            with open(self.credentials_file, "r") as f:
                credentials = json.load(f)
            # Ensure admin credentials are present
            if "admin" not in credentials or not any(user["username"] == "shah" for user in credentials.get("admin", [])):
                credentials["admin"] = default_credentials["admin"]
                with open(self.credentials_file, "w") as f:
                    json.dump(credentials, f)
            print(f"Loaded credentials for role {self.role}: {credentials.get(self.role, [])}")  # Debug
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load credentials: {e}")
            return

        # Check credentials
        users = credentials.get(self.role, [])
        for user in users:
            if user["username"] == username and user["password"] == password:
                self.on_login(self.role, username, username)  # Pass username as name
                return
        
        QMessageBox.warning(self, "Login Failed", "Invalid credentials")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GEHU P2P Sharing Platform")
        self.setMinimumSize(1000, 700)
        
        # Set application style
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f7;
            }
            QPushButton {
                background-color: #6C63FF;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 12px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5A52E0;
            }
            QPushButton:pressed {
                background-color: #4A43C8;
            }
            QLabel {
                color: #333;
                font-size: 14px;
            }
            #titleLabel {
                font-size: 32px;
                font-weight: bold;
                color: #333;
                margin-bottom: 20px;
            }
            #subtitleLabel {
                font-size: 18px;
                color: #666;
                margin-bottom: 40px;
            }
            .RoleCard {
                background-color: white;
                border-radius: 10px;
                padding: 20px;
                min-height: 250px;
            }
            #roleTitle {
                font-size: 22px;
                font-weight: bold;
                color: #333;
                margin-bottom: 15px;
            }
            #roleDescription {
                font-size: 15px;
                color: #666;
                margin-bottom: 30px;
                line-height: 1.5;
            }
            QTabWidget::pane {
                border: 1px solid #ccc;
                background-color: white;
                border-radius: 5px;
            }
            QTabBar::tab {
                background-color: #e0e0e0;
                color: #666;
                padding: 10px 20px;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
            }
            QTabBar::tab:selected {
                background-color: #6C63FF;
                color: white;
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #ccc;
                border-radius: 5px;
                margin-top: 1ex;
                padding-top: 1ex;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 3px;
            }
        """)
        
        # Create stacked widget to manage different screens
        self.stacked_widget = QStackedWidget()
        
        # Create widgets for different screens
        self.welcome_widget = self.create_welcome_screen()
        self.login_widget = self.create_login_screen()
        self.main_widget = self.create_main_screen()
        
        # Add screens to stacked widget
        self.stacked_widget.addWidget(self.welcome_widget)  # index 0
        self.stacked_widget.addWidget(self.login_widget)    # index 1
        self.stacked_widget.addWidget(self.main_widget)     # index 2
        
        # Set central widget
        self.setCentralWidget(self.stacked_widget)
        
        # Initialize with welcome screen
        self.stacked_widget.setCurrentIndex(0)
        
        # Initialize network - will be used later when a role is selected
        self.network = None
        self.current_user = {"role": None, "name": None, "username": None}
    
    def create_welcome_screen(self):
        """Create the welcome screen with role selection"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(40, 40, 40, 40)
        
        # Header
        header_layout = QVBoxLayout()
        header_layout.setAlignment(Qt.AlignCenter)
        
        # Title
        title_label = QLabel("GEHU P2P Sharing Platform")
        title_label.setObjectName("titleLabel")
        title_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(title_label)
        
        # Subtitle
        subtitle_label = QLabel("Educational File Sharing System for Classroom Use")
        subtitle_label.setObjectName("subtitleLabel")
        subtitle_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(subtitle_label)
        
        layout.addLayout(header_layout)
        
        # Role selection cards
        roles_layout = QHBoxLayout()
        roles_layout.setSpacing(20)
        
        # Student card
        student_card = QFrame()
        student_card.setObjectName("studentCard")
        student_card.setProperty("class", "RoleCard")
        student_layout = QVBoxLayout(student_card)
        student_layout.setAlignment(Qt.AlignCenter)
        
        student_icon_label = QLabel()
        student_icon_label.setText("👨‍🎓")
        student_icon_label.setAlignment(Qt.AlignCenter)
        student_icon_label.setStyleSheet("font-size: 48px;")
        student_layout.addWidget(student_icon_label)
        
        student_title = QLabel("Student")
        student_title.setObjectName("roleTitle")
        student_title.setAlignment(Qt.AlignCenter)
        student_layout.addWidget(student_title)
        
        student_desc = QLabel("Join as a student to receive files and messages from your teacher.")
        student_desc.setObjectName("roleDescription")
        student_desc.setAlignment(Qt.AlignCenter)
        student_desc.setWordWrap(True)
        student_layout.addWidget(student_desc)
        
        student_btn = QPushButton("Join as Student")
        student_btn.clicked.connect(lambda: self.show_login("student"))
        student_layout.addWidget(student_btn)
        
        roles_layout.addWidget(student_card)
        
        # Teacher card
        teacher_card = QFrame()
        teacher_card.setObjectName("teacherCard")
        teacher_card.setProperty("class", "RoleCard")
        teacher_layout = QVBoxLayout(teacher_card)
        teacher_layout.setAlignment(Qt.AlignCenter)
        
        teacher_icon_label = QLabel()
        teacher_icon_label.setText("👩‍🏫")
        teacher_icon_label.setAlignment(Qt.AlignCenter)
        teacher_icon_label.setStyleSheet("font-size: 48px;")
        teacher_layout.addWidget(teacher_icon_label)
        
        teacher_title = QLabel("Teacher")
        teacher_title.setObjectName("roleTitle")
        teacher_title.setAlignment(Qt.AlignCenter)
        teacher_layout.addWidget(teacher_title)
        
        teacher_desc = QLabel("Join as a teacher to broadcast messages and share files.")
        teacher_desc.setObjectName("roleDescription")
        teacher_desc.setAlignment(Qt.AlignCenter)
        teacher_desc.setWordWrap(True)
        teacher_layout.addWidget(teacher_desc)
        
        teacher_btn = QPushButton("Login as Teacher")
        teacher_btn.clicked.connect(lambda: self.show_login("teacher"))
        teacher_layout.addWidget(teacher_btn)
        
        roles_layout.addWidget(teacher_card)
        
        # Admin card
        admin_card = QFrame()
        admin_card.setObjectName("adminCard")
        admin_card.setProperty("class", "RoleCard")
        admin_layout = QVBoxLayout(admin_card)
        admin_layout.setAlignment(Qt.AlignCenter)
        
        admin_icon_label = QLabel()
        admin_icon_label.setText("🔐")
        admin_icon_label.setAlignment(Qt.AlignCenter)
        admin_icon_label.setStyleSheet("font-size: 48px;")
        admin_layout.addWidget(admin_icon_label)
        
        admin_title = QLabel("Administrator")
        admin_title.setObjectName("roleTitle")
        admin_title.setAlignment(Qt.AlignCenter)
        admin_layout.addWidget(admin_title)
        
        admin_desc = QLabel("Manage user credentials and system settings.")
        admin_desc.setObjectName("roleDescription")
        admin_desc.setAlignment(Qt.AlignCenter)
        admin_desc.setWordWrap(True)
        admin_layout.addWidget(admin_desc)
        
        admin_btn = QPushButton("Login as Admin")
        admin_btn.clicked.connect(lambda: self.show_login("admin"))
        admin_layout.addWidget(admin_btn)
        
        roles_layout.addWidget(admin_card)
        
        layout.addLayout(roles_layout)
        
        # Footer
        footer_layout = QHBoxLayout()
        footer_layout.setAlignment(Qt.AlignCenter)
        
        footer_label = QLabel("© 2025 GEHU P2P | Graphic Era Hill University")
        footer_label.setStyleSheet("color: #999; font-size: 14px;")
        footer_layout.addWidget(footer_label)
        
        layout.addLayout(footer_layout)
        
        return widget
    
    def create_login_screen(self):
        """Create the login screen with back button"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(40, 40, 40, 40)
        
        # Header with back button
        header_layout = QHBoxLayout()
        
        back_btn = QPushButton("← Back")
        back_btn.clicked.connect(self.show_welcome)
        back_btn.setStyleSheet("background-color: #999; max-width: 100px;")
        header_layout.addWidget(back_btn, 0, Qt.AlignLeft)
        
        title_label = QLabel("Login")
        title_label.setObjectName("titleLabel")
        title_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(title_label, 1)
        
        layout.addLayout(header_layout)
        
        # Login form container (will be replaced dynamically)
        self.login_container = QVBoxLayout()
        self.login_container.setAlignment(Qt.AlignCenter)
        
        # Placeholder
        placeholder = QLabel("Select a role to login")
        placeholder.setAlignment(Qt.AlignCenter)
        self.login_container.addWidget(placeholder)
        
        layout.addLayout(self.login_container)
        
        return widget
    
    def create_main_screen(self):
        """Create the main application screen with tabbed interface"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Header with logout button and user info
        header_layout = QHBoxLayout()
        
        self.user_info_label = QLabel("Welcome")
        header_layout.addWidget(self.user_info_label, 1)
        
        logout_btn = QPushButton("Logout")
        logout_btn.clicked.connect(self.logout)
        logout_btn.setStyleSheet("background-color: #999; max-width: 100px;")
        header_layout.addWidget(logout_btn, 0, Qt.AlignRight)
        
        layout.addLayout(header_layout)
        
        # Tabbed interface
        self.tab_widget = QTabWidget()
        
        # Create empty tabs (they will be populated when a role logs in)
        # Placeholder widget for panel content
        self.panel_container = QWidget()
        self.panel_layout = QVBoxLayout(self.panel_container)
        
        layout.addWidget(self.panel_container)
        
        return widget
    
    def show_welcome(self):
        """Show the welcome screen"""
        self.stacked_widget.setCurrentIndex(0)
    
    def show_login(self, role):
        """Show the login screen for a specific role"""
        # Clear existing login form
        while self.login_container.count():
            item = self.login_container.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        
        # Add new login form
        login_form = LoginForm(self.on_login, role)
        self.login_container.addWidget(login_form)
        
        self.stacked_widget.setCurrentIndex(1)
    
    def on_login(self, role, name, username):
        """Handle successful login"""
        self.current_user = {
            "role": role,
            "name": name,
            "username": username
        }
        
        # Update user info display
        self.user_info_label.setText(f"Welcome, {name} ({role.capitalize()})")
        
        # Clear existing panel
        while self.panel_layout.count():
            item = self.panel_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        
        # Create appropriate panel based on role
        if role == "student":
            # Initialize network for student if not already initialized
            if not self.network:
                self.network = PeerNetwork()
                
            panel = StudentPanel(self.network, name, username)
            self.panel_layout.addWidget(panel)
            
        elif role == "teacher":
            # Initialize network for teacher if not already initialized
            if not self.network:
                self.network = PeerNetwork()
                
            panel = TeacherPanel(self.network, name, username)
            self.panel_layout.addWidget(panel)
            
        elif role == "admin":
            panel = AdminPanel()
            self.panel_layout.addWidget(panel)
        
        # Switch to main interface
        self.stacked_widget.setCurrentIndex(2)
    
    def logout(self):
        """Log out and return to welcome screen"""
        # Clean up network resources if needed
        if self.network:
            # In a real application, you would properly shut down network connections
            pass
        
        # Reset current user
        self.current_user = {"role": None, "name": None, "username": None}
        
        # Go back to welcome screen
        self.show_welcome()

class SplashScreen(QSplashScreen):
    def __init__(self):
        super().__init__()
        
        # Create splash screen pixmap
        splash_pix = QPixmap(500, 300)
        splash_pix.fill(Qt.white)
        
        # Set up splash screen window
        self.setPixmap(splash_pix)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        
        # Add content to splash screen
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        title = QLabel("GEHU P2P")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 32px; font-weight: bold; color: #6C63FF;")
        
        subtitle = QLabel("Starting up...")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("font-size: 16px; color: #666;")
        
        self.progress = QLabel("Loading resources...")
        self.progress.setAlignment(Qt.AlignCenter)
        self.progress.setStyleSheet("font-size: 14px; color: #999;")
        
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(self.progress)
        
        # Apply layout to splash screen
        self.setLayout(layout)
    
    def update_progress(self, message):
        self.progress.setText(message)
        self.repaint()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Create data directory if it doesn't exist
    if not os.path.exists("data"):
        os.makedirs("data")
    
    # Show splash screen
    splash = SplashScreen()
    splash.show()
    
    # Simulate loading
    for i, message in enumerate(["Initializing application...", 
                               "Loading resources...", 
                               "Setting up network...", 
                               "Ready to start..."]):
        splash.update_progress(message)
        app.processEvents()
        QTimer.singleShot(500, lambda: None)  # Delay to show splash screen
    
    # Launch main window
    window = MainWindow()
    window.show()
    splash.finish(window)
    
    sys.exit(app.exec_())
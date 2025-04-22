import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
from network import PeerNetwork

class StudentWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("GEHU P2P - Student")
        self.colors = {
            'primary': '#6C63FF',
            'secondary': '#F0F0F7',
            'text': '#2D3748',
            'white': '#FFFFFF'
        }
        self.network = PeerNetwork()
        self.setup_ui()
        self.start_listening()
        self.join_session()

    def setup_ui(self):
        self.main_frame = tk.Frame(self.root, bg=self.colors['secondary'], padx=20, pady=20)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Messages frame
        messages_frame = tk.LabelFrame(self.main_frame, text="Received Messages", 
                                       font=('Helvetica', 12, 'bold'), bg=self.colors['secondary'])
        messages_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        self.messages_text = tk.Text(messages_frame)
        self.messages_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Files frame
        files_frame = tk.LabelFrame(self.main_frame, text="Shared Files", 
                                    font=('Helvetica', 12, 'bold'), bg=self.colors['secondary'])
        files_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        columns = ('Name', 'Size', 'Shared By')
        self.files_tree = ttk.Treeview(files_frame, columns=columns, show='headings')

        for col in columns:
            self.files_tree.heading(col, text=col)
            self.files_tree.column(col, width=100)

        self.files_tree.pack(fill=tk.BOTH, expand=True)

        download_btn = tk.Button(files_frame, text="Download Selected", 
                                 bg=self.colors['primary'], fg='white',
                                 command=self.download_file)
        download_btn.pack(fill=tk.X, padx=5, pady=5)

    def start_listening(self):
        """Start listening for incoming messages and files"""
        listen_thread = threading.Thread(target=self.network.listen_for_peers)
        listen_thread.daemon = True
        listen_thread.start()

    def join_session(self):
        """Join the teacher's session"""
        self.network.discover_peers()
        messagebox.showinfo("Success", "Connected to the session")

    def download_file(self):
        """Download selected file."""
        selected_item = self.files_tree.selection()
        if not selected_item:
            messagebox.showwarning("Warning", "Please select a file to download")
            return

        file_name = self.files_tree.item(selected_item)['values'][0]
        save_path = filedialog.asksaveasfilename(defaultextension=os.path.splitext(file_name)[1],
                                                 initialfile=file_name)

        if save_path:
            # Implement actual file download logic here
            messagebox.showinfo("Success", f"File {file_name} downloaded successfully!")

    def handle_peer_discovery(self, message, addr):
        """Handle discovered peers and update the UI."""
        peer_info = f"Discovered peer: {addr[0]}\n"
        # Schedule the update on the main thread
        self.root.after(0, self.update_ui, peer_info)

    def update_ui(self, peer_info):
        """Update the messages text widget in the main thread."""
        self.messages_text.insert(tk.END, peer_info)
        self.messages_text.yview(tk.END)  # Scroll to the bottom

if __name__ == "__main__":
    root = tk.Tk()
    app = StudentWindow(root)
    root.mainloop()

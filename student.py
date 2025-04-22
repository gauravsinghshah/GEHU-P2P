import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
from pathlib import Path
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

        # PeerNetwork setup with callbacks
        self.network = PeerNetwork(
            on_file_received=self.handle_file_received,
            on_peer_discovered=self.handle_peer_discovery
        )

        self.setup_ui()
        self.start_listening()
        self.start_file_listener()
        self.join_session()

    def setup_ui(self):
        self.main_frame = tk.Frame(self.root, bg=self.colors['secondary'], padx=20, pady=20)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Received messages
        messages_frame = tk.LabelFrame(self.main_frame, text="Received Messages",
                                       font=('Helvetica', 12, 'bold'), bg=self.colors['secondary'])
        messages_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        self.messages_text = tk.Text(messages_frame)
        self.messages_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Shared files
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
        """Start listening for broadcast messages"""
        print("📡 Starting peer listener...")
        listen_thread = threading.Thread(target=self.network.listen_for_peers)
        listen_thread.daemon = True
        listen_thread.start()

    def start_file_listener(self):
        """Start listening for file transfers"""
        print("📥 Starting file listener...")
        file_thread = threading.Thread(target=self.network.listen_for_files)
        file_thread.daemon = True
        file_thread.start()

    def join_session(self):
        print("🔎 Looking for peers...")
        self.network.discover_peers()
        messagebox.showinfo("Success", "Connected to the session")

    def handle_peer_discovery(self, message, addr):
        info = f"🔍 Discovered peer: {addr[0]}\n"
        print(info.strip())
        self.root.after(0, lambda: self.update_ui(info))

    def handle_file_received(self, data, addr):
        """Handle file reception"""
        try:
            from json import loads
            message_data = loads(data.decode())
            if message_data.get("type") == "file_transfer":
                file_name = message_data["file_name"]
                file_data = bytes.fromhex(message_data["file_data"])

                save_dir = Path.home() / "Downloads" / "GEHU_P2P_Received"
                save_dir.mkdir(parents=True, exist_ok=True)
                file_path = save_dir / file_name

                with open(file_path, 'wb') as f:
                    f.write(file_data)

                print(f"✅ File received: {file_name} from {addr[0]}")
                self.root.after(0, lambda: self.update_ui(f"✅ Received file: {file_name} from {addr[0]}\n"))
                self.root.after(0, lambda: self.files_tree.insert("", tk.END, values=(
                    file_name, f"{len(file_data)//1024} KB", addr[0])))

        except Exception as e:
            error_msg = f"❌ Error receiving file: {e}\n"
            print(error_msg.strip())
            self.root.after(0, lambda: self.update_ui(error_msg))

    def update_ui(self, msg):
        self.messages_text.insert(tk.END, msg)
        self.messages_text.yview(tk.END)

    def download_file(self):
        selected_item = self.files_tree.selection()
        if not selected_item:
            messagebox.showwarning("Warning", "Please select a file to download")
            return

        file_name = self.files_tree.item(selected_item)['values'][0]
        save_path = filedialog.asksaveasfilename(defaultextension=os.path.splitext(file_name)[1],
                                                 initialfile=file_name)

        if save_path:
            try:
                # Simulate download from local folder
                src_path = Path.home() / "Downloads" / "GEHU_P2P_Received" / file_name
                if src_path.exists():
                    with open(src_path, 'rb') as src, open(save_path, 'wb') as dst:
                        dst.write(src.read())
                    messagebox.showinfo("Success", f"File {file_name} downloaded to {save_path}")
                else:
                    messagebox.showerror("Error", "Original file not found.")
            except Exception as e:
                messagebox.showerror("Error", str(e))
        else:
            messagebox.showwarning("Warning", "Download cancelled")


if __name__ == "__main__":
    root = tk.Tk()
    app = StudentWindow(root)
    root.mainloop()

import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
from network import PeerNetwork

class TeacherWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("GEHU P2P - Teacher")
        self.colors = {
            'primary': '#6C63FF',
            'secondary': '#F0F0F7',
            'text': '#2D3748',
            'white': '#FFFFFF'
        }

        # Initialize PeerNetwork on correct ports
        self.network = PeerNetwork(
            port=8080,
            file_port=8081,
            on_peer_discovered=self.on_peer_discovered
        )

        self.setup_ui()
        self.start_listening()

    def setup_ui(self):
        self.main_frame = tk.Frame(self.root, bg=self.colors['secondary'], padx=20, pady=20)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Message frame
        message_frame = tk.LabelFrame(self.main_frame, text="Broadcast Message", 
                                      font=('Helvetica', 12, 'bold'), bg=self.colors['secondary'])
        message_frame.pack(fill=tk.X, pady=10)

        self.message_entry = tk.Text(message_frame, height=5)
        self.message_entry.pack(fill=tk.X, expand=True, padx=5, pady=5)

        send_msg_btn = tk.Button(message_frame, text="Broadcast Message", 
                                 bg=self.colors['primary'], fg='white',
                                 command=self.broadcast_message)
        send_msg_btn.pack(fill=tk.X, padx=5, pady=5)

        # File sharing frame
        file_frame = tk.LabelFrame(self.main_frame, text="Share File", 
                                   font=('Helvetica', 12, 'bold'), bg=self.colors['secondary'])
        file_frame.pack(fill=tk.X, pady=10)

        self.file_path = tk.StringVar()
        file_entry = tk.Entry(file_frame, textvariable=self.file_path, width=50)
        file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        browse_btn = tk.Button(file_frame, text="Browse", 
                               command=self.browse_file)
        browse_btn.pack(side=tk.LEFT, padx=5)

        send_file_btn = tk.Button(file_frame, text="Send File", 
                                  bg=self.colors['primary'], fg='white',
                                  command=self.send_file_thread)
        send_file_btn.pack(side=tk.LEFT, padx=5)

    def start_listening(self):
        """Start listening for incoming peers (UDP) and optionally file transfers (TCP)"""
        threading.Thread(target=self.network.listen_for_peers, daemon=True).start()

        # Optionally enable this if you want Teacher to receive files too
        # threading.Thread(target=self.network.listen_for_files, daemon=True).start()

        # Broadcast presence to find peers
        self.network.discover_peers()

    def on_peer_discovered(self, message, address):
        ip_address = address[0]
        if ip_address not in self.network.peers:
            self.network.peers.append(ip_address)
            print(f"👋 New peer joined: {ip_address}")

    def browse_file(self):
        """Browse for file to share"""
        file_path = filedialog.askopenfilename()
        if file_path:
            self.file_path.set(file_path)

    def broadcast_message(self):
        message = self.message_entry.get("1.0", tk.END).strip()
        if message:
            for peer_ip in self.network.peers:
                self.network.send_message(peer_ip, message)
            messagebox.showinfo("Success", "Message broadcasted to all peers")
        else:
            messagebox.showwarning("Empty Message", "Please enter a message to broadcast.")

    def send_file_thread(self):
        """Run send_file in a separate thread"""
        threading.Thread(target=self.send_file, daemon=True).start()

    def send_file(self):
        """Send selected file to all peers"""
        file_path = self.file_path.get()
        if not file_path or not os.path.isfile(file_path):
            messagebox.showwarning("Warning", "Please select a valid file to send")
            return

        if not self.network.peers:
            messagebox.showwarning("No Peers", "No peers discovered to send the file to.")
            return

        successful_sends, failed_sends = 0, 0
        for peer_ip in self.network.peers:
            try:
                self.network.send_file(file_path, peer_ip)
                successful_sends += 1
            except Exception as e:
                print(f"❌ Error sending file to {peer_ip}: {e}")
                failed_sends += 1

        messagebox.showinfo("File Sent", f"File successfully sent to {successful_sends} peer(s), failed for {failed_sends}.")

if __name__ == "__main__":
    root = tk.Tk()
    TeacherWindow(root)
    root.mainloop()

import socket
import threading
import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk
from datetime import datetime

HOST = '127.0.0.1'
PORT = 5000

class ChatClient:
    def __init__(self, root):
        self.root = root
        self.root.title("Yattalk chat!")
        self.root.geometry("800x600")
        self.root.minsize(600, 400)
        self.root.configure(bg='#F2D0D3')

        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.stop_threads = False
        self.username = ""

        self.create_widgets()
        self.connect_to_server()

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_widgets(self):
        # Logo banner on top
        try:
            logo_banner = tk.PhotoImage(file="logo200.png")
            logo_label = tk.Label(self.root, image=logo_banner, bg='#F2D0D3')
            logo_label.image = logo_banner
            logo_label.pack(pady=(10, 0))
        except Exception as e:
            print(f"Logo banner load error: {e}")

        main_frame = tk.Frame(self.root, bg='#f0f0f0')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.chat_display = scrolledtext.ScrolledText(
            main_frame,
            wrap=tk.WORD,
            width=60,
            height=20,
            font=('Segoe UI', 10),
            state='disabled',
            bg='white',
            fg='black'
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        self.chat_display.tag_config("normal", foreground="black")
        self.chat_display.tag_config("outgoing", foreground="#0066cc")
        self.chat_display.tag_config("incoming", foreground="#333333")
        self.chat_display.tag_config("system", foreground="#009933")
        self.chat_display.tag_config("error", foreground="#cc0000")
        self.chat_display.tag_config("private", foreground="#990099")

        bottom_frame = tk.Frame(main_frame, bg='#f0f0f0')
        bottom_frame.pack(fill=tk.X)

        self.message_entry = tk.Entry(
            bottom_frame,
            font=('Segoe UI', 12),
            width=50
        )
        self.message_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.message_entry.bind('<Return>', self.send_message)

        send_button = tk.Button(
            bottom_frame,
            text="Send",
            command=self.send_message,
            bg='#4CAF50',
            fg='white',
            font=('Segoe UI', 10, 'bold'),
            relief=tk.FLAT
        )
        send_button.pack(side=tk.LEFT, padx=(0, 5))

        users_button = tk.Button(
            bottom_frame,
            text="Users",
            command=self.request_user_list,
            bg='#2196F3',
            fg='white',
            font=('Arial', 10, 'bold'),
            relief=tk.FLAT
        )
        users_button.pack(side=tk.LEFT, padx=(0, 5))

        quit_button = tk.Button(
            bottom_frame,
            text="Quit",
            command=self.on_closing,
            bg='#f44336',
            fg='white',
            font=('Segoe UI', 10, 'bold'),
            relief=tk.FLAT
        )
        quit_button.pack(side=tk.LEFT)

        self.status_bar = tk.Label(
            self.root,
            text="Connecting to server...",
            bd=1,
            relief=tk.SUNKEN,
            anchor=tk.W,
            bg='#e0e0e0',
            fg='black'
        )
        self.status_bar.pack(fill=tk.X)

    def connect_to_server(self):
        try:
            self.client_socket.connect((HOST, PORT))
            initial_msg = self.client_socket.recv(1024).decode('utf-8')

            login_window = tk.Toplevel(self.root)
            login_window.title("Welcome to Yattalk!")
            login_window.geometry("300x250")
            login_window.resizable(False, False)
            login_window.grab_set()
            login_window.configure(bg='#F291A3')

            try:
                logo = tk.PhotoImage(file="logo100.png")
                img_label = tk.Label(login_window, image=logo, bg='#F291A3')
                img_label.image = logo
                img_label.pack(pady=10)
            except Exception as e:
                print(f"Logo load error: {e}")

            prompt_label = tk.Label(login_window, text=initial_msg, font=('Segoe UI', 10), bg='white')
            prompt_label.pack(pady=(0, 5))

            entry_var = tk.StringVar()
            entry_field = tk.Entry(login_window, textvariable=entry_var, font=('Segoe UI', 12))
            entry_field.pack(pady=(0, 10))
            entry_field.focus()

            def submit_username():
                self.username = entry_var.get().strip()
                if self.username:
                    login_window.destroy()

            def cancel_login():
                self.client_socket.close()
                login_window.destroy()
                self.root.destroy()

            button_frame = tk.Frame(login_window, bg='white')
            button_frame.pack()

            tk.Button(button_frame, text="OK", width=10, command=submit_username).pack(side=tk.LEFT, padx=5)
            tk.Button(button_frame, text="Cancel", width=10, command=cancel_login).pack(side=tk.LEFT, padx=5)

            self.root.wait_window(login_window)

            if not self.username:
                return

            self.client_socket.send(self.username.encode('utf-8'))
            confirm_msg = self.client_socket.recv(1024).decode('utf-8')

            if not confirm_msg.startswith("Welcome"):
                messagebox.showerror("Error", confirm_msg)
                self.root.destroy()
                return

            self.update_chat_display("\ud83d\udccc Available commands:\n" +
                                    "\ud83e\udde3 /users \u2192 list connected users\n" +
                                    "\u274c /quit \u2192 exit the chat\n" +
                                    "\ud83d\udcc1 @username <message> \u2192 send a private message\n",
                                    tag="system")
            self.update_chat_display(f"\n{confirm_msg}\n", tag="system")
            self.status_bar.config(text=f"Connected as {self.username}")

            receive_thread = threading.Thread(target=self.receive_messages, daemon=True)
            receive_thread.start()

        except Exception as e:
            messagebox.showerror("Connection Error", f"Failed to connect to server: {str(e)}")
            self.root.destroy()

    def receive_messages(self):
        while not self.stop_threads:
            try:
                message = self.client_socket.recv(1024).decode('utf-8')
                if message:
                    now = datetime.now().strftime("%H:%M")
                    if message.startswith("[System]"):
                        self.update_chat_display(f"[{now}] {message}\n", tag="system")
                    elif message.startswith(f"{self.username}:"):
                        self.update_chat_display(f"[{now}] {message}\n", tag="private")
                    else:
                        self.update_chat_display(f"[{now}] {message}\n", tag="incoming")
                else:
                    break
            except:
                break

        if not self.stop_threads:
            self.update_chat_display("\n\u26a0\ufe0f Disconnected from server\n", tag="error")
            self.status_bar.config(text="Disconnected from server")

    def send_message(self, event=None):
        msg = self.message_entry.get().strip()
        if not msg:
            return

        self.message_entry.delete(0, tk.END)
        now = datetime.now().strftime("%H:%M")

        if msg == "/quit":
            self.update_chat_display(f"[{now}] Disconnecting...\n", tag="system")
            self.on_closing()
            return
        elif msg == "/users":
            self.update_chat_display(f"[{now}] Requesting user list...\n", tag="system")
        elif msg.startswith("@"): 
            parts = msg.split(" ", 1)
            if len(parts) > 1:
                self.update_chat_display(f"[{now}] To {parts[0][1:]}: {parts[1]}\n", tag="private")
        else:
            self.update_chat_display(f"[{now}] You: {msg}\n", tag="outgoing")

        try:
            self.client_socket.send(msg.encode('utf-8'))
        except:
            self.update_chat_display(f"[{now}] Failed to send message\n", tag="error")
            messagebox.showerror("Error", "Failed to send message")

    def request_user_list(self):
        self.send_message()

    def update_chat_display(self, message, tag="normal"):
        self.chat_display.config(state='normal')
        self.chat_display.insert(tk.END, message, tag)
        self.chat_display.config(state='disabled')
        self.chat_display.see(tk.END)

    def on_closing(self):
        self.stop_threads = True
        try:
            self.client_socket.send("/quit".encode('utf-8'))
            self.client_socket.close()
        except:
            pass
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = ChatClient(root)
    root.mainloop()
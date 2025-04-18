import socket
import threading
import json
import os
from datetime import datetime

HOST = '127.0.0.1'
PORT = 5000

clients = {}  # conn -> username

os.makedirs("messages", exist_ok=True)

def save_message(sender, receiver, message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    data = {
        "timestamp": timestamp,
        "sender": sender,
        "receiver": receiver,
        "message": message
    }

    filename = f"{'_'.join(sorted([sender, receiver]))}.json"
    filepath = os.path.join("messages", filename)

    try:
        history = []
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as file:
                history = json.load(file)

        history.append(data)

        with open(filepath, "w", encoding="utf-8") as file:
            json.dump(history, file, indent=4)

        print(f"[✔] Message saved in: {filepath}")
    except Exception as e:
        print(f"[✘] Error while saving the message: {e}")

def broadcast_system(message, exclude_conn=None):
    for client in clients:
        if client != exclude_conn:
            try:
                client.send(f"[System] {message}".encode('utf-8'))
            except:
                pass

def handle_client(conn, addr):
    try:
        conn.send("Enter your username: ".encode('utf-8'))
        username = conn.recv(1024).decode('utf-8').strip()

        if username in clients.values():
            conn.send("Username already taken. Connection closed.".encode('utf-8'))
            conn.close()
            return

        clients[conn] = username
        print(f"[+] {username} connected from {addr}")

        # Send welcome and currently connected users
        user_list = [u for c, u in clients.items() if c != conn]
        if user_list:
            conn.send(f"Welcome, {username}! Users currently connected: {', '.join(user_list)}".encode('utf-8'))
        else:
            conn.send(f"Welcome, {username}! No other users are currently connected.".encode('utf-8'))

        # Notify others
        broadcast_system(f"{username} has joined the chat.", exclude_conn=conn)

        while True:
            msg = conn.recv(1024).decode('utf-8')
            if not msg:
                break

            if msg == "/users":
                user_list = ", ".join(clients.values())
                conn.send(f"Connected users: {user_list}".encode('utf-8'))

            elif msg == "/quit":
                conn.send("Disconnecting from the chat...".encode('utf-8'))
                break

            elif msg.startswith("@"):
                try:
                    parts = msg.split(" ", 1)
                    receiver_name = parts[0][1:]
                    message_body = parts[1]

                    receiver_conn = next((c for c, name in clients.items() if name == receiver_name), None)

                    if receiver_conn:
                        formatted = f"{username}: {message_body}"
                        receiver_conn.send(formatted.encode('utf-8'))
                        save_message(username, receiver_name, message_body)
                    else:
                        conn.send(f"The user '{receiver_name}' is not connected.".encode('utf-8'))
                except:
                    conn.send("Invalid format. Use: @username <message>".encode('utf-8'))

            else:
                conn.send("Unknown command. Use @username <message>, /users or /quit.".encode('utf-8'))

    except Exception as e:
        print(f"[!] Error: {e}")
    finally:
        print(f"[-] {clients.get(conn, 'Unknown')} disconnected")
        broadcast_system(f"{clients.get(conn, 'Unknown')} has left the chat.", exclude_conn=conn)
        clients.pop(conn, None)
        conn.close()

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen()

print(f"[*] Server running on {HOST}:{PORT}...")

while True:
    conn, addr = server.accept()
    threading.Thread(target=handle_client, args=(conn, addr)).start()

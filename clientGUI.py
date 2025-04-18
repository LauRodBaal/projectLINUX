import socket
import threading
import datetime

HOST = '127.0.0.1'
PORT = 5000

stop_threads = False  # To stop threads when exiting

def receive_messages(sock):
    while not stop_threads:
        try:
            message = sock.recv(1024).decode('utf-8')
            if message:
                now = datetime.datetime.now().strftime("%H:%M")
                print(f"\n[{now}] {message}")
                print(">> ", end="", flush=True)
            else:
                break
        except:
            break

def send_messages(sock):
    global stop_threads
    while not stop_threads:
        try:
            msg = input(">> ").strip()
            if msg == "/quit":
                sock.send("/quit".encode('utf-8'))
                print("Logging out...")
                stop_threads = True
                break
            elif msg == "/users":
                sock.send("/users".encode('utf-8'))
            else:
                sock.send(msg.encode('utf-8'))
        except:
            print("[!] Error while sending the message.")
            break

# Connect to server
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((HOST, PORT))

# Receive welcome message
initial_msg = client_socket.recv(1024).decode('utf-8')
# Use it directly as the input prompt
username = input(initial_msg).strip()

client_socket.send(username.encode('utf-8'))

# Confirmation or rejection
confirm_msg = client_socket.recv(1024).decode('utf-8')
print(confirm_msg)
print("\nAvailable commands:")
print("/users → list connected users")
print("/quit  → exit the chat")
print("@username <message> → send a message to someone\n")

if confirm_msg.startswith("Welcome"):
    recv_thread = threading.Thread(target=receive_messages, args=(client_socket,))
    recv_thread.start()
    send_messages(client_socket)
else:
    client_socket.close()

import socket
import os
import mimetypes
import queue
import threading
import time

PORT = 8080
STATIC_DIR = os.path.abspath("static")
SERVER = 'localhost'
ADDR = (SERVER, PORT)

request_queue = queue.Queue()
NUM_WORKERS = 3

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)

def worker():
    while True:
        conn, addr = request_queue.get()

        try:
            print(
                threading.current_thread().name,
                "handling connection from",
                addr
            )

            conn.settimeout(5)
            handle_client(conn, addr)

        except Exception as e:
            print("Worker error:", e)

        finally:
            request_queue.task_done()


def receive_request(conn):
    data = b""

    # Phase 1: receive until headers are complete
    while b"\r\n\r\n" not in data:
        chunk = conn.recv(1024)

        if not chunk:
            break

        data += chunk

    # Find where headers end
    header_end = data.find(b"\r\n\r\n")

    if header_end == -1:
        return data

    # Read headers only
    headers_data = data[:header_end]
    headers_text = headers_data.decode("utf-8")

    # Find Content-Length
    content_length = 0

    for line in headers_text.split("\r\n"):
        if line.lower().startswith("content-length:"):
            content_length = int(line.split(":", 1)[1].strip())
            break

    # Some body bytes may already have arrived with the headers
    body_start = header_end + 4
    body_received = len(data) - body_start

    bytes_remaining = content_length - body_received

    print("Content-Length:", content_length)
    print("Body already received:", body_received)
    print("Bytes remaining:", bytes_remaining)

    # Phase 2: receive the rest of the body
    while bytes_remaining > 0:
        chunk = conn.recv(min(1024, bytes_remaining))

        if not chunk:
            break

        data += chunk
        bytes_remaining -= len(chunk)

    return data


def parcer(data):
    header_end = data.find("\r\n\r\n")

    headers_text = data[:header_end]
    body = data[header_end + 4:]

    parts = headers_text.split("\r\n")

    # Request line
    req = parts[0].split(" ")

    method = req[0]
    path = req[1]
    version = req[2]

    headers = {}

    for line in parts[1:]:
        key, value = line.split(":", 1)
        headers[key.strip()] = value.strip()

    return method, path, version, headers, body


def handle_client(conn, addr):

    try:
        while True:

            data = receive_request(conn)

            if not data:
                break

            print("START:", addr)
          
            print(data)

            data = data.decode("utf-8")

            method, path, version, headers, message_body = parcer(data)

            # ---------------- ROUTING ----------------

            status = '200 OK'
            content_type = 'text/plain'

            if method != 'GET':
                status = '405 Method Not Allowed'
                body = 'Method Not Allowed'

            elif path == '/about':
                body = 'about hello world'

            else:

                if path == '/':
                    path = '/index.html'

                file_path = os.path.abspath(
                    os.path.join(STATIC_DIR, path.lstrip("/"))
                )

                if os.path.commonpath([STATIC_DIR, file_path]) != STATIC_DIR:
                    status = '403 Forbidden'
                    body = 'Forbidden'

                elif os.path.isfile(file_path):

                    with open(file_path, 'rb') as file:
                        body = file.read()

                    content_type, _ = mimetypes.guess_type(file_path)

                    if content_type is None:
                        content_type = 'application/octet-stream'

                else:
                    status = '404 Not Found'
                    body = 'Not Found'

            # ---------------- RESPONSE ----------------

            if isinstance(body, str):
                body_bytes = body.encode('utf-8')
            else:
                body_bytes = body

            body_length = len(body_bytes)

            response_headers = (
                f"HTTP/1.1 {status}\r\n"
                f"Content-Type: {content_type}\r\n"
                f"Content-Length: {body_length}\r\n"
                f"Connection: keep-alive\r\n"
                f"\r\n"
            ).encode('utf-8')

            message = response_headers + body_bytes

            conn.sendall(message)

            connection_status = headers.get("Connection", "").lower()

            if connection_status == "close":
                break

    except socket.timeout:
        print("Idle connection timeout:", addr)

    finally:
        conn.close()


def start():

    server.listen()

    print("[LISTENING] server is listening")

    for _ in range(NUM_WORKERS):
        thread = threading.Thread(target=worker)
        thread.start()

    while True:
        conn, addr = server.accept()

        request_queue.put((conn, addr))


start()
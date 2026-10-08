import socket

HOST = "localhost"
PORT = 8080

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.settimeout(5)
client.connect((HOST, PORT))


def send_request(path, connection="keep-alive"):
    request = (
        f"GET {path} HTTP/1.1\r\n"
        f"Host: localhost:8080\r\n"
        f"Connection: {connection}\r\n"
        f"\r\n"
    )

    client.sendall(request.encode("utf-8"))

    response = b""

    # Receive the complete response headers
    while b"\r\n\r\n" not in response:
        chunk = client.recv(4096)

        if not chunk:
            raise ConnectionError("Server closed connection unexpectedly")

        response += chunk

    header_end = response.find(b"\r\n\r\n")
    headers = response[:header_end].decode("utf-8")
    body = response[header_end + 4:]

    content_length = None

    for line in headers.split("\r\n")[1:]:
        if line.lower().startswith("content-length:"):
            content_length = int(line.split(":", 1)[1].strip())

    if content_length is None:
        raise ValueError("Missing Content-Length")

    # Receive the complete response body
    while len(body) < content_length:
        chunk = client.recv(4096)

        if not chunk:
            raise ConnectionError("Incomplete response body")

        body += chunk

    body = body[:content_length]

    print(f"\nRequested: {path}")
    print("Status:", headers.split("\r\n")[0])
    print("Body:", body.decode("utf-8", errors="replace"))
    print("Connection:", connection)


try:
    send_request("/")
    send_request("/about")
    send_request("/missing", connection="close")

    print("\nKeep-alive test completed.")

except Exception as e:
    print("\nTEST FAILED:", e)

finally:
    client.close()
import socket

PORT = 8080
SERVER = 'localhost'
ADDR = (SERVER, PORT)

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(ADDR)


# -------- REQUEST 1 --------

req = "GET / HTTP/1.1\r\n"
req += "Host: localhost:8080\r\n"
req += "Connection: keep-alive\r\n"
req += "\r\n"

req = req.encode('utf-8')

client.sendall(req)

response = client.recv(4096)
print("Response 1:")
print(response.decode('utf-8'))


# -------- REQUEST 2 --------

req = "GET /index.html HTTP/1.1\r\n"
req += "Host: localhost:8080\r\n"
req += "Connection: close\r\n"
req += "\r\n"

req = req.encode('utf-8')

client.sendall(req)

response = client.recv(4096)
print("Response 2:")
print(response.decode('utf-8'))


client.close()
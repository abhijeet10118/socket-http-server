import socket
import time
from concurrent.futures import ThreadPoolExecutor

HOST = "localhost"
PORT = 8080
NUM_REQUESTS = 1000
CONCURRENT_CLIENTS = 100

request = (
    "GET / HTTP/1.1\r\n"
    "Host: localhost:8080\r\n"
    "Connection: close\r\n"
    "\r\n"
).encode("utf-8")


def send_request(_):
    start_time = time.perf_counter()

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
            client.settimeout(10)
            client.connect((HOST, PORT))
            client.sendall(request)

            response = b""

            while True:
                chunk = client.recv(4096)

                if not chunk:
                    break

                response += chunk

        elapsed = time.perf_counter() - start_time
        success = response.startswith(b"HTTP/1.1 200")

        return elapsed, success, None

    except (socket.timeout, OSError) as e:
        return None, False, str(e)


overall_start = time.perf_counter()

with ThreadPoolExecutor(max_workers=CONCURRENT_CLIENTS) as executor:
    results = list(
        executor.map(send_request, range(NUM_REQUESTS))
    )

total_time = time.perf_counter() - overall_start

response_times = [
    elapsed for elapsed, success, error in results
    if elapsed is not None
]

successes = sum(success for elapsed, success, error in results)

errors = [
    error for elapsed, success, error in results
    if error is not None
]

print("Successful requests:", successes, "/", NUM_REQUESTS)
print("Failed requests:", NUM_REQUESTS - successes)

if response_times:
    avg_ms = sum(response_times) / len(response_times) * 1000
    print("Average response time:", round(avg_ms, 2), "ms")

print("Total elapsed time:", round(total_time, 3), "seconds")
print("Throughput:", round(successes / total_time, 2), "requests/sec")

if errors:
    print("Errors:", errors[:5])
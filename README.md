# Multithreaded HTTP/1.1 Static File Server

A small HTTP server written in pure Python using only raw sockets and the standard library. No frameworks, no `http.server`. It parses HTTP requests by hand, serves static files, supports persistent (keep-alive) connections, and handles clients concurrently with a fixed-size worker thread pool.

I built this to understand what actually happens underneath web frameworks: TCP streams, request framing, headers, status codes, and concurrency.

## Features

- **Raw socket server** built on `socket.AF_INET` / `SOCK_STREAM`
- **Worker thread pool** (3 workers by default) fed by a thread-safe `queue.Queue`
- **Persistent connections (HTTP keep-alive)**: multiple requests per TCP connection, closed on `Connection: close` or after a 5-second idle timeout
- **Correct request framing**: reads until `\r\n\r\n`, then uses `Content-Length` to read the full body
- **Static file serving** from the `static/` directory with automatic MIME type detection
- **Path traversal protection**: resolved paths must stay inside `static/` (returns `403` otherwise)
- **Basic routing**: `/` maps to `index.html`, plus a custom `/about` route
- **Proper status codes**: `200`, `403`, `404`, `405`

## Project Structure

```
.
├── server.py            # the HTTP server
├── static/              # files served by the server (put index.html here)
│   └── index.html
├── load_test.py         # concurrent load test (1000 requests, 100 clients)
├── keepalive_test.py    # verifies keep-alive over a single connection
└── simple_test.py       # minimal two-request manual test
```

> Rename the files above to match your actual filenames.

## Requirements

- Python 3.8+
- No third-party packages

## Running the Server

1. Create a `static/` folder next to the server file and add an `index.html`.
2. Start the server:

```bash
python server.py
```

3. Visit `http://localhost:8080/` in a browser, or use curl:

```bash
curl -i http://localhost:8080/
curl -i http://localhost:8080/about
curl -i http://localhost:8080/does-not-exist
curl -i -X POST http://localhost:8080/
```

## Configuration

Set at the top of the server file:

| Setting | Default | Meaning |
|---|---|---|
| `PORT` | `8080` | Port to listen on |
| `SERVER` | `localhost` | Interface to bind to |
| `STATIC_DIR` | `./static` | Directory files are served from |
| `NUM_WORKERS` | `3` | Number of worker threads |

The idle timeout for a connection is `conn.settimeout(5)` in `worker()`.

## How It Works

```
 client ──► accept() loop (main thread)
                │  puts (conn, addr)
                ▼
          request_queue  ◄── thread-safe queue
                │  worker threads call get()
                ▼
        worker ──► handle_client(conn)
                      │
                      ├─ receive_request()   read headers, then body by Content-Length
                      ├─ parcer()            split request line, headers, body
                      ├─ routing             method check → /about → static file
                      └─ build + send response, loop for keep-alive
```

1. **Main thread** only accepts connections and pushes them onto a queue.
2. **Worker threads** pull connections off the queue and each serve one connection at a time.
3. **`receive_request`** works in two phases because TCP is a byte stream with no message boundaries: first it reads until the blank line that ends the headers, then it uses `Content-Length` to read exactly the remaining body bytes.
4. **`handle_client`** loops on the same connection, so a client can send several requests without reconnecting. The loop ends when the client sends `Connection: close`, disconnects, or stays idle past the timeout.
5. **File serving** resolves the requested path with `os.path.abspath` and checks it with `os.path.commonpath` so requests like `/../server.py` cannot escape `static/`.

## Testing

All three tests expect the server to be running on `localhost:8080`.

**Load test**: fires 1000 requests from 100 concurrent clients and reports success count, average response time, total time, and throughput:

```bash
python load_test.py
```

**Keep-alive test**: sends `/`, `/about`, and `/missing` over one connection, reading each response fully using `Content-Length`, and closes on the last one:

```bash
python keepalive_test.py
```

**Simple test**: sends two requests on one connection and prints the raw responses:

```bash
python simple_test.py
```

## Known Limitations / Future Work

This is a learning project, so some things are intentionally simple:

- Only `GET` is handled; everything else returns `405` (request bodies are read but not used)
- Query strings (`/page?x=1`) are not stripped, so they will 404 for static files
- With a fixed pool, each worker is tied to one connection until it closes or times out, so idle keep-alive clients can block others (the load test uses `Connection: close` for this reason)
- The response always sends `Connection: keep-alive`, even when the server is about to close
- No chunked transfer encoding, `HEAD`, caching headers, HTTPS, or logging to a file
- Malformed requests are not answered with `400 Bad Request`

Ideas for next steps: return `400` for bad requests, strip query strings, add `HEAD` support, handle `SO_REUSEADDR`, and experiment with `selectors` / `asyncio` for non-blocking I/O.

## Development Notes

The architecture and logic (worker pool design, two-phase request reading, keep-alive loop, path-safety checks, test plan) are my own. I used AI assistance for basic boilerplate coding.



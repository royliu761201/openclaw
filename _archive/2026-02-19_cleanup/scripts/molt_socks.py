import socket
import socketserver
import select
import struct
import time
import threading

LOG_FILE = "/tmp/proxy.log"

def log(msg):
    with open(LOG_FILE, "a") as f:
        f.write(f"[{time.strftime('%H:%M:%S')}] {msg}\n")

class ThreadingTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    daemon_threads = True
    allow_reuse_address = True

class MoltSocksHandler(socketserver.BaseRequestHandler):
    def handle(self):
        client = self.request
        client.settimeout(60)
        
        try:
            # Peek to determine protocol
            first_byte = client.recv(1, socket.MSG_PEEK)
            if not first_byte:
                return

            if first_byte == b'\x05':
                self.handle_socks5(client)
            elif first_byte in [b'C', b'G', b'P', b'H']: # CONNECT, GET, PUT, HEAD
                self.handle_http(client)
            else:
                log(f"Unknown protocol byte: {first_byte}")
                return
        except Exception as e:
            log(f"Handler Error: {e}")
        finally:
            client.close()

    def handle_socks5(self, client):
        # 1. Auth Negotiation
        client.recv(1) # Version 5 (already peeked)
        nmethods = ord(client.recv(1))
        client.recv(nmethods) # Consume methods
        client.send(b"\x05\x00") # No Auth

        # 2. Request
        ver = ord(client.recv(1)) # 5
        cmd = ord(client.recv(1)) # 1=Connect
        rsv = client.recv(1)
        atyp = ord(client.recv(1))

        if cmd != 1:
            log("SOCKS5: Unsupported command")
            return

        if atyp == 1: # IPv4
            addr = socket.inet_ntoa(client.recv(4))
        elif atyp == 3: # Domain
            length = ord(client.recv(1))
            addr = client.recv(length).decode()
        elif atyp == 4: # IPv6
            addr = socket.inet_ntop(socket.AF_INET6, client.recv(16))
        else:
            log("SOCKS5: Unsupported address type")
            return

        port = struct.unpack("!H", client.recv(2))[0]
        log(f"SOCKS5 Request: {addr}:{port}")

        # 3. Connect to Remote
        try:
            remote = socket.create_connection((addr, port), timeout=60)
            bind_addr = remote.getsockname()
            bind_port = bind_addr[1]
            
            # Reply OK
            # BND.ADDR (4 bytes) + BND.PORT (2 bytes)
            # Just use 0.0.0.0:0 for simplicity if needed, or actual bind
            client.send(b"\x05\x00\x00\x01" + socket.inet_aton("0.0.0.0") + struct.pack("!H", 0))
            
            self.proxy_data(client, remote)
        except Exception as e:
            log(f"SOCKS5 Connection Failed: {e}")
            client.send(b"\x05\x04\x00\x01\x00\x00\x00\x00\x00\x00") # Host unreachable

    def handle_http(self, client):
        # Minimal HTTP CONNECT support
        # Read request line: CONNECT host:port HTTP/1.1
        line = b""
        while b"\r\n" not in line:
            chunk = client.recv(1)
            if not chunk: return
            line += chunk
        
        parts = line.split()
        if parts[0] == b'CONNECT':
             target = parts[1].decode()
             if ':' in target:
                 addr, port = target.split(':')
                 port = int(port)
             else:
                 addr = target
                 port = 443 # Default HTTPS
             
             log(f"HTTP CONNECT: {addr}:{port}")
             
             # Consume rest of headers
             while True:
                 line = b""
                 while b"\r\n" not in line:
                     chunk = client.recv(1)
                     if not chunk: return
                     line += chunk
                 if line == b"\r\n": break

             try:
                 remote = socket.create_connection((addr, port), timeout=60)
                 client.send(b"HTTP/1.1 200 Connection Established\r\n\r\n")
                 self.proxy_data(client, remote)
             except Exception as e:
                 log(f"HTTP Connection Failed: {e}")
                 client.send(b"HTTP/1.1 502 Bad Gateway\r\n\r\n")

    def proxy_data(self, client, remote):
        try:
            while True:
                r, w, x = select.select([client, remote], [], [], 60)
                if not r: break
                
                if client in r:
                    data = client.recv(4096)
                    if not data: break
                    remote.sendall(data)
                
                if remote in r:
                    data = remote.recv(4096)
                    if not data: break
                    client.sendall(data)
        except Exception as e:
            pass
        finally:
            client.close()
            remote.close()

if __name__ == "__main__":
    with open(LOG_FILE, "w") as f: f.write("Starting MoltSocks (Robust SOCKS5)...\n")
    server = ThreadingTCPServer(('127.0.0.1', 7890), MoltSocksHandler)
    server.serve_forever()

import socket
import sys

TCP = "TCP"
UDP = "UDP"

def detectar_familia_ip(ip):
    """Detecta se o IP é IPv4 ou IPv6."""
    try:
        socket.inet_pton(socket.AF_INET, ip)
        return socket.AF_INET
    except OSError:
        pass
    try:
        socket.inet_pton(socket.AF_INET6, ip)
        return socket.AF_INET6
    except OSError:
        raise ValueError(f"Endereço IP inválido: {ip}")

def listar_ips():
    """Lista todos os IPs (IPv4 e IPv6) disponíveis na máquina."""
    print("\n--- Endereços disponíveis ---")
    for iface in socket.getaddrinfo(socket.gethostname(), None):
        familia, _, _, _, endereco = iface
        if familia == socket.AF_INET:
            print(f"IPv4: {endereco[0]}")
        elif familia == socket.AF_INET6:
            print(f"IPv6: {endereco[0]}")
    print("----------------------------\n")

class P2PServer:
    def __init__(self, ip, porta, protocolo, timeout=60.0):
        self.ip = ip
        self.porta = porta
        self.protocolo = protocolo
        self.timeout = timeout
        self.sock = None
        self.client_addr = None

    def start(self):
        listar_ips()
        familia = detectar_familia_ip(self.ip)
        tipo = socket.SOCK_STREAM if self.protocolo == TCP else socket.SOCK_DGRAM
        self.sock = socket.socket(familia, tipo)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.settimeout(self.timeout)

        if familia == socket.AF_INET6:
            self.sock.bind((self.ip, self.porta, 0, 0))
        else:
            self.sock.bind((self.ip, self.porta))

        if self.protocolo == TCP:
            self.sock.listen(1)
            conn, addr = self.sock.accept()
            self.sock = conn
        else:
            self.client_addr = None

    def send(self, data):
        if self.protocolo == TCP:
            self.sock.sendall(data.encode("utf-8"))
        else:
            if self.client_addr:
                self.sock.sendto(data.encode("utf-8"), self.client_addr)

    def recv(self):
        try:
            if self.protocolo == TCP:
                data = self.sock.recv(4096)
                return data.decode("utf-8") if data else None
            else:
                data, addr = self.sock.recvfrom(4096)
                self.client_addr = addr
                return data.decode("utf-8")
        except socket.timeout:
            return None

    def stop(self):
        if self.sock:
            self.sock.close()

class P2PClient:
    def __init__(self, ip, porta, protocolo, timeout=60.0):
        self.ip = ip
        self.porta = porta
        self.protocolo = protocolo
        self.timeout = timeout
        self.sock = None

    def connect(self):
        familia = detectar_familia_ip(self.ip)
        tipo = socket.SOCK_STREAM if self.protocolo == TCP else socket.SOCK_DGRAM
        self.sock = socket.socket(familia, tipo)
        self.sock.settimeout(self.timeout)

        if self.protocolo == TCP:
            if familia == socket.AF_INET6:
                self.sock.connect((self.ip, self.porta, 0, 0))
            else:
                self.sock.connect((self.ip, self.porta))

    def send(self, data):
        if self.protocolo == TCP:
            self.sock.sendall(data.encode("utf-8"))
        else:
            self.sock.sendto(data.encode("utf-8"), (self.ip, self.porta))

    def recv(self):
        try:
            data = self.sock.recv(4096)
            return data.decode("utf-8") if data else None
        except socket.timeout:
            return None

    def stop(self):
        if self.sock:
            self.sock.close()


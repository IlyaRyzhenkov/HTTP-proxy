import signal
import socket
import sys
import threading
import select
import filter


class HTTPProxy:
    MAX_REQUEST_SIZE = 10000
    STEPS_TO_FILTER_UPDATE = 100

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.verbose = False
        self.is_run = False
        self.is_shutdown = False

        signal.signal(signal.SIGINT, self.shutdown)

        self.filter = filter.FilterManager()
        self.filter_lock = threading.Lock()
        self.step = 0

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((host, port))

    def run(self):
        self.is_run = True
        sys.stdout.write("http proxy starts at {}:{}\n".format(str(self.host), str(self.port)))
        self.socket.listen(15)

        while not self.is_shutdown:
            s, _, _ = select.select([self.socket], [], [], 0.5)
            if s:
                for sock in s:
                    if sock == self.socket:
                        client, addr = self.socket.accept()
                        thread = threading.Thread(target=self.handle_connection, args=(client, addr, self.verbose, self.filter))
                        thread.setDaemon(True)
                        thread.start()
            self.step += 1
            if self.step == HTTPProxy.STEPS_TO_FILTER_UPDATE:
                with self.filter_lock:
                    self.filter.update()
                self.step = 0

    @staticmethod
    def handle_connection(client_socket, address, verbose, filter):
        data = client_socket.recv(HTTPProxy.MAX_REQUEST_SIZE)
        request = data.decode('ASCII')
        try:
            line = request.split('\n')[0].split(' ')
            mode = line[0]
            url = line[1]
        except:
            return
        if verbose:
            sys.stdout.write('{} {}\n'.format(mode, url))

        http_pos = url.find("://")
        if http_pos == -1:
            temp = url
        else:
            temp = url[(http_pos + 3):]

        port_pos = temp.find(":")

        webserver_pos = temp.find("/")
        if webserver_pos == -1:
            webserver_pos = len(temp)

        webserver = ""
        port = -1
        if port_pos == -1 or webserver_pos < port_pos:
            port = 80
            webserver = temp[:webserver_pos]
        else:
            port = int(temp[port_pos + 1:webserver_pos])
            webserver = temp[:port_pos]

        if not filter.is_addr_allowed(webserver):
            message = b'HTTP/1.1 403 Forbidden\n'
            client_socket.sendall(message)
            client_socket.close()
            return

        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.connect((webserver, port))

        if mode == 'CONNECT':
            conn = b"HTTP/1.1 200 Connection established\nProxy-agent: PythonProxy/1.0.0\n\n"
            client_socket.sendall(conn)
            is_timeout = False
            while not is_timeout:
                s, _, _ = select.select([client_socket, server_socket], [], [], 5)
                if s:
                    try:
                        for sock in s:
                            data = sock.recv(HTTPProxy.MAX_REQUEST_SIZE)
                            if sock == client_socket:
                                server_socket.sendall(data)
                            else:
                                client_socket.sendall(data)
                    except ConnectionError:
                        server_socket.close()
                        client_socket.close()
                        return
                else:
                    is_timeout = True
                    server_socket.close()
                    client_socket.close()
                    return
        server_socket.sendall(data)
        while True:
            data = server_socket.recv(HTTPProxy.MAX_REQUEST_SIZE)
            if data:
                client_socket.sendall(data)
            else:
                break
        server_socket.close()
        client_socket.close()

    def set_verbose(self, flag):
        self.verbose = flag

    def shutdown(self, a, b):
        print('shutdown')
        if self.is_run:
            self.is_shutdown = True

    def set_filter(self, filename):
        self.filter.add_filter(filter.IpFilter(filename))

    def set_addblock(self, filename):
        self.filter.add_filter(filter.Adblock(filename))

    @staticmethod
    def get_host():
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        ip = '64.233.164.100'
        s.connect((ip, 80))
        return s.getsockname()[0]

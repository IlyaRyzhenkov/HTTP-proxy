import socket
import re


class FilterManager:
    def __init__(self):
        self.filters = []

    def update(self):
        for filter in self.filters:
            filter.update()

    def is_addr_allowed(self, addr):
        for filter in self.filters:
            if not filter.is_addr_allowed(addr):
                return False
        return True

    def add_filter(self, filter):
        self.filters.append(filter)


class IpFilter:
    def __init__(self, filename):
        self.is_sent_error_message = False
        self.filename = filename
        self.not_allowed_ip = []
        self.update()

    def update(self):
        try:
            with open(self.filename, 'r') as f:
                ip = []
                for line in f.readlines():
                    line = line.strip()
                    if self.is_ip(line):
                        ip.append(line)
            self.not_allowed_ip = ip
            self.is_sent_error_message = False

        except OSError:
            if not self.is_sent_error_message:
                print("Error reading filter file")
                self.is_sent_error_message = True

    def is_addr_allowed(self, addr):
        name = socket.gethostbyname(addr)
        a = name not in self.not_allowed_ip
        return a

    @staticmethod
    def is_ip(ip):
        try:
            _ = socket.inet_aton(ip)
            return True
        except socket.error:
            return False


class Adblock:
    def __init__(self, filename):
        self.is_sent_error_message = False
        self.filename = filename
        self.regex = []
        self.update()

    def update(self):
        try:
            with open(self.filename, 'r') as f:
                regex = []
                for line in f.readlines():
                    line = line.strip()
                    rg = re.compile(line)
                    regex.append(rg)
            self.regex = regex
            self.is_sent_error_message = False

        except OSError:
            if not self.is_sent_error_message:
                print("Error reading adblock filter file")
                self.is_sent_error_message = True

    def is_addr_allowed(self, addr):
        for rg in self.regex:
            match = rg.findall(addr)
            if match:
                return False
        return True

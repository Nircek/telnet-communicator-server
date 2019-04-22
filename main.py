#!/usr/bin/env python3

# MIT License

# Copyright (c) 2019 Nircek

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


from socket import socket, AF_INET, SOCK_STREAM
from threading import Thread, Lock
from sys import argv

class TelnetListener(Thread):
    def __init__(self, port, callback):
        super().__init__()
        self.port = port
        self.callback = callback
    def run(self):
        try:
            self.socket = socket(AF_INET, SOCK_STREAM)
            self.socket.bind(('', self.port))
            self.socket.listen()
            while True:
                self.callback(*self.socket.accept())
        finally:
            self.socket.close()

class TelnetServer:
    def __init__(self, ports):
        self.ports = ports
        self.threads = [TelnetListener(x, self.new) for x in ports]
        self.clients = []
        self.clients_lock = Lock()
    def new(self, socket, addr):
        with self.clients_lock:
            self.clients += [(socket)]
        fulladdr = ':'.join([str(x) for x in addr])
        socket.send(f'Hello {fulladdr}! Thanks for your connecting.\n'.encode())
        self.remove(socket)
    def remove(self, x):
        with self.clients_lock:
            self.clients.remove(x)
    def start(self):
        for t in self.threads:
            t.start()

if __name__ == '__main__':
    ports = []
    for e in argv[1:]:
        try:
            ports += [int(e)]
        except:
            pass
    if not ports:
        ports = [ 23 ]
    print('Ports:', ports if ports[1:] else ports[0])
    TelnetServer(ports).start()

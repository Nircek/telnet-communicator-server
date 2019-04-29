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


from socket import socket, AF_INET, SOCK_STREAM, SHUT_RD, SOL_SOCKET, SO_REUSEADDR
from threading import Thread, Lock
from sys import argv

class TelnetListener(Thread):
    def __init__(self, port, server):
        super().__init__()
        self.port, self.server, self.down = port, server, False
    def run(self):
        try:
            self.socket = socket(AF_INET, SOCK_STREAM)
            self.socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1) # anti-already-in-use
            self.socket.bind(('', self.port))
            self.socket.listen()
            while True:
                self.server.new(*self.socket.accept())
        except:
            if self.down:
                pass
            else:
                raise
    def stop(self):
        self.down = True
        self.socket.shutdown(SHUT_RD)
        self.socket.close()

class TelnetUserConnector(Thread):
    def __init__(self, server, socket, addr, port):
        super().__init__()
        self.socket, self.addr = socket, addr
        self.port, self.server = port, server
        self.down = False
        self.nick = f'{self.addr}:{self.port}'.encode()
    def send(self, msg):
        try:
            self.socket.sendall(msg)
        except BrokenPipeError:
            self.server.remove(self)
    def run(self):
        try:
            self.down = False
            self.send('Type your nick: '.encode())
            d = self.socket.recv(32)
            if d[-1] == 0x0a: # \n
                d = d[:-1]
            if d[-1] == 0x0d: # \r
                d = d[:-1]
            self.nick = d
            self.server.broadcast(self.nick + ' joined server.\n'.encode())
            while True:
                d = self.socket.recv(2**10)
                if self.down:
                    break
                if d:
                    self.server.broadcast(self.nick + ': '.encode()+d)
                else:
                    self.server.remove(self)
                    self.server.broadcast(self.nick + ' left server.\n'.encode())
        except:
            if self.down:
                pass
            else:
                raise
    def stop(self):
        self.down = True
        try:
            self.socket.shutdown(SHUT_RD)
        except OSError:
            pass
        self.socket.close()

class TelnetServer:
    def __init__(self, ports):
        self.ports = ports
        self.threads = [TelnetListener(x, self) for x in ports]
        self.clients = []
        self.clients_lock = Lock()
    def new(self, socket, addr):
        with self.clients_lock:
            t = TelnetUserConnector(self, socket, *addr)
            self.clients += [t]
            t.start()
    def remove(self, x):
        x.stop()
        with self.clients_lock:
            self.clients.remove(x)
    def start(self):
        for t in self.threads:
            t.start()
    def broadcast(self, msg):
        print(msg)
        for c in self.clients:
            c.send(msg)
    def stop(self):
        self.broadcast('Server is going down...\n'.encode())
        for t in self.threads:
            t.stop()
        for c in self.clients:
            c.stop()
    def block(self):
        for e in self.threads+self.clients:
            e.join()

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
    server = TelnetServer(ports)
    server.start()
    try:
        server.block()
    except KeyboardInterrupt:
        print('Interrupting... ')
    finally:
        server.stop()

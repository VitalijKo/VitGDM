import socket
import threading
import json


class Client:
    def __init__(self,
                 server_host,
                 server_port_tcp=7575,
                 server_port_udp=7575,
                 client_port_udp=7576):

        self.sock_tcp = None
        self.identifier = None
        self.server_message = []
        self.room_id = None
        self.client_udp = ('0.0.0.0', client_port_udp)
        self.lock = threading.Lock()
        self.server_listener = SocketThread(self.client_udp,
                                            self,
                                            self.lock)
        self.server_listener.start()
        self.server_udp = (server_host, server_port_udp)
        self.server_tcp = (server_host, server_port_tcp)

        self.register()

    def create_room(self, room_name=None, level_name=None, level_difficulty=None):
        message = json.dumps(
            {'action': 'create', 'payload': [room_name, level_name, level_difficulty], 'identifier': self.identifier})

        self.sock_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock_tcp.connect(self.server_tcp)
        self.sock_tcp.send(message.encode())
        data = self.sock_tcp.recv(1024)
        self.sock_tcp.close()
        message = self.parse_data(data)
        self.room_id = message

    def join_room(self, room_id):
        self.room_id = room_id

        message = json.dumps({'action': 'join', 'payload': room_id, 'identifier': self.identifier})

        self.sock_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock_tcp.connect(self.server_tcp)
        self.sock_tcp.send(message.encode())
        data = self.sock_tcp.recv(1024)
        self.sock_tcp.close()
        message = self.parse_data(data)
        self.room_id = message

    def leave_room(self):
        message = json.dumps({
            'action': 'leave',
            'room_id': self.room_id,
            'identifier': self.identifier
        })
        self.sock_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock_tcp.connect(self.server_tcp)
        self.sock_tcp.send(message.encode())
        data = self.sock_tcp.recv(1024)
        self.sock_tcp.close()
        message = self.parse_data(data)

    def get_rooms(self):
        message = json.dumps({'action': 'get_rooms', 'identifier': self.identifier})
        self.sock_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock_tcp.connect(self.server_tcp)
        self.sock_tcp.send(message.encode())
        data = self.sock_tcp.recv(1024)
        self.sock_tcp.close()
        message = self.parse_data(data)

        return message

    def send(self, message):
        message = json.dumps({
            'action': 'send',
            'payload': {'message': message},
            'room_id': self.room_id,
            'identifier': self.identifier
        })

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(message.encode(), self.server_udp)

    def register(self):
        message = json.dumps({
            'action': 'register',
            'payload': self.client_udp[1]
        })

        self.sock_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock_tcp.connect(self.server_tcp)
        self.sock_tcp.send(message.encode())
        data = self.sock_tcp.recv(1024)
        self.sock_tcp.close()
        message = self.parse_data(data)
        self.identifier = message

    def parse_data(self, data):
        try:
            data = json.loads(data)

            if data['success'] == 'True':
                return data['message']

            else:
                raise Exception(data['message'])
        except ValueError:
            print(data)

    def get_messages(self):
        message = self.server_message
        self.server_message = []

        return set(message)


class SocketThread(threading.Thread):
    def __init__(self, addr, client, lock):
        threading.Thread.__init__(self)
        self.client = client
        self.lock = lock
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        try:
            self.sock.bind(addr)
        except:
            self.sock.close()

    def run(self):
        try:
            while True:
                data, addr = self.sock.recvfrom(1024)
                self.lock.acquire()

                try:
                    self.client.server_message.append(data)
                finally:
                    self.lock.release()
        except OSError:
            pass

    def stop(self):
        self.sock.close()

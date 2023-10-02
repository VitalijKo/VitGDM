import socket
import json
import argparse
import time
from threading import Thread, Lock
from rooms import Rooms, RoomNotFound, NotInRoom, RoomFull


def main_loop(tcp_port, udp_port, rooms_list):
    global blacklist
    global invisible

    blacklist = []
    invisible = []

    lock = Lock()
    udp_server = UdpServer(udp_port, rooms_list, lock)
    tcp_server = TcpServer(tcp_port, rooms_list, lock)
    udp_server.start()
    tcp_server.start()

    is_running = True

    print('VitGDM')
    print('--------------------------------------')
    print('list : list rooms')
    print('room #room_id : print room information')
    print('info #user_id : print player information')
    print('blacklist #user_id : blacklist user')
    print('unblacklist #user_id : unblacklist user')
    print('inv #user_id : make user invisible')
    print('v #user_id : make user visible')
    print('quit : quit server')
    print('--------------------------------------')

    try:
        while is_running:
            cmd = input('> ')

            if cmd == 'list':
                print('Rooms :')

                for room_id, room in rooms_list.rooms.items():
                    print('%s - %s (%d/%d)' % (room.identifier,
                                               room.name,
                                               len(room.players),
                                               room.capacity))

            elif cmd.startswith('room '):
                try:
                    room_id = cmd[5:]
                    room = rooms_list.rooms[room_id]

                    print('%s - %s (%d/%d)' % (room.identifier,
                                               room.name,
                                               len(room.players),
                                               room.capacity))

                    print('Players :')

                    for player in room.players:
                        print(player.identifier)

                except:
                    print('Error while getting room informations')

            elif cmd.startswith('info '):
                try:
                    player = rooms_list.players[cmd[5:]]

                    print('%s : %s:%d' % (player.identifier,
                                          player.udp_addr[0],
                                          player.udp_addr[1]))
                except:
                    print('Error while getting user information!')

            elif cmd.startswith('blacklist '):
                try:
                    player = rooms_list.players[cmd[2:]]
                    blacklist.append(player)

                    print('Successfully blacklisted', player)
                except:
                    print('Error while blacklisting', player)

            elif cmd.startswith('blacklist '):
                try:
                    player = rooms_list.players[cmd[3:]]
                    blacklist.remove(player)

                    print('Successfully unblacklisted', player)
                except:
                    print('Error while unblacklisting', player)

            elif cmd.startswith('invisible '):
                try:
                    player = rooms_list.players[cmd[2:]]
                    invisible.append(player)

                    print('Successfully made invisible', player)
                except:
                    print('Error while making invisible', player)

            elif cmd.startswith('visible '):
                try:
                    player = rooms_list.players[cmd[3:]]
                    invisible.remove(player)

                    print('Successfully made visible', player)
                except:
                    print('Error while making invisible', player)

            elif cmd == 'quit':
                print('Shutting down server...')

                udp_server.is_listening = False
                tcp_server.is_listening = False
                is_running = False
    except KeyboardInterrupt:
        pass

    udp_server.join()
    tcp_server.join()

    print('Server is off!')


class UdpServer(Thread):
    def __init__(self, udp_port, rooms_list, lock):
        Thread.__init__(self)
        self.sock = None
        self.rooms = rooms_list
        self.lock = lock
        self.is_listening = True
        self.udp_port = int(udp_port)
        self.msg = "{'success': %(success)s, 'message':'%(message)s'}"

    def run(self):
        global blacklist
        global invisible

        self.sock = socket.socket(socket.AF_INET,
                                  socket.SOCK_DGRAM)
        self.sock.bind(('0.0.0.0', self.udp_port))
        self.sock.setblocking(0)
        self.sock.settimeout(5)

        while self.is_listening:
            try:
                data, addr = self.sock.recvfrom(1024)
            except socket.timeout:
                continue

            try:
                data = json.loads(data)

                try:
                    identifier = data['identifier']
                except KeyError:
                    identifier = None

                try:
                    room_id = data['room_id']
                except KeyError:
                    room_id = None

                try:
                    payload = data['payload']
                except KeyError:
                    payload = None

                try:
                    action = data['action']
                except KeyError:
                    action = None

                try:
                    if room_id not in self.rooms.rooms.keys():
                        raise RoomNotFound

                    self.lock.acquire()

                    if identifier not in set(blacklist + invisible):
                        try:
                            if action == 'send':
                                try:
                                    self.rooms.send(identifier,
                                                    room_id,
                                                    payload['message'])
                                except:
                                    pass
                        finally:
                            self.lock.release()
                except RoomNotFound:
                    print('Room not found')
            except KeyError:
                print('Json from %s:%s is not valid' % addr)
            except ValueError:
                print('Message from %s:%s is not valid json string' % addr)

        self.stop()

    def stop(self):
        self.sock.close()


class TcpServer(Thread):
    def __init__(self, tcp_port, rooms_list, lock):
        Thread.__init__(self)
        self.sock = None
        self.lock = lock
        self.tcp_port = int(tcp_port)
        self.rooms = rooms_list
        self.is_listening = True
        self.msg = "{'success': '%(success)s', 'message':'%(message)s'}"

    def run(self):
        self.sock = socket.socket(socket.AF_INET,
                                  socket.SOCK_STREAM)
        self.sock.bind(('0.0.0.0', self.tcp_port))
        self.sock.setblocking(0)
        self.sock.settimeout(5)

        time_reference = time.time()

        self.sock.listen(1)

        while self.is_listening:
            if time_reference + 60 < time.time():
                self.rooms.remove_empty()

                time_reference = time.time()

            try:
                conn, addr = self.sock.accept()
            except socket.timeout:
                continue

            try:
                data = conn.recv(1024)
            except:
                continue

            try:
                data = json.loads(data)
                action = data['action']
                identifier = None

                try:
                    identifier = data['identifier']
                except KeyError:
                    pass

                room_id = None

                try:
                    room_id = data['room_id']
                except KeyError:
                    pass

                payload = None

                try:
                    payload = data['payload']
                except KeyError:
                    pass

                self.lock.acquire()

                try:
                    self.route(conn,
                               addr,
                               action,
                               payload,
                               identifier,
                               room_id)
                finally:
                    self.lock.release()
            except KeyError:
                print('Json from %s:%s is not valid' % addr)
                conn.send('Json is not valid'.encode())
            except ValueError:
                print('Message from %s:%s is not valid json string' % addr)
                conn.send('Message is not a valid json string'.encode())

            conn.close()

        self.stop()

    def route(self,
              sock,
              addr,
              action,
              payload,
              identifier=None,
              room_id=None):
        if action == 'register':
            client = self.rooms.register(addr, int(payload))
            client.send_tcp(True, client.identifier, sock)

            return 0

        if identifier is not None:
            if identifier not in self.rooms.players.keys():
                print('Unknown identifier %s for %s:%s' % (identifier, addr[0], addr[1]))

                sock.send(self.msg % {'success': 'False', 'message': 'Unknown identifier'})

                return 0

            client = self.rooms.players[identifier]

            if action == 'join':
                try:
                    if payload not in self.rooms.rooms.keys():
                        raise RoomNotFound()

                    self.rooms.join(identifier, payload)
                    client.send_tcp(True, payload, sock)
                except RoomNotFound:
                    client.send_tcp(False, room_id, sock)
                except RoomFull:
                    client.send_tcp(False, room_id, sock)

            elif action == 'get_rooms':
                rooms_list = []

                for id_room, room in self.rooms.rooms.items():
                    rooms_list.append({'id': id_room,
                                       'name': room.name,
                                       'nb_players': len(room.players),
                                       'capacity': room.capacity,
                                       'level_name': room.level_name,
                                       'level_difficulty': room.level_difficulty})

                client.send_tcp(True, rooms_list, sock)

            elif action == 'create':
                room_identifier = self.rooms.create(payload)
                self.rooms.join(client.identifier, room_identifier)
                client.send_tcp(True, room_identifier, sock)

            elif action == 'leave':
                try:
                    if room_id not in self.rooms.rooms:
                        raise RoomNotFound()

                    self.rooms.leave(identifier, room_id)
                    client.send_tcp(True, room_id, sock)
                except RoomNotFound:
                    client.send_tcp(False, room_id, sock)
                except NotInRoom:
                    client.send_tcp(False, room_id, sock)

            else:
                sock.send_tcp(self.msg % {'success': 'False',
                                          'message': 'You must register'})

    def stop(self):
        self.sock.close()


if __name__ == '__main__':
    blacklist = []

    parser = argparse.ArgumentParser(description='Simple game server')
    parser.add_argument('--tcpport',
                        dest='tcp_port',
                        help='Listening tcp port',
                        default='7575')
    parser.add_argument('--udpport',
                        dest='udp_port',
                        help='Listening udp port',
                        default='7575')
    parser.add_argument('--capacity',
                        dest='room_capacity',
                        help='Max players per room',
                        default='1000')

    args = parser.parse_args()
    rooms = Rooms(int(args.room_capacity))
    main_loop(args.tcp_port, args.udp_port, rooms)

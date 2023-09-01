import socket
import PortOpener


def open_client_port(port=7575):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(('8.8.8.8', 80))
    private_ip = s.getsockname()[0]
    s.close()

    router_uuid = PortOpener.router_list()

    PortOpener.port_add(router_uuid, 'TCP', port, private_ip, port)
    PortOpener.port_add(router_uuid, 'UDP', port, private_ip, port)

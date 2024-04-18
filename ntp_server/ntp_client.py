import socket
import struct
import time
import ntp_server

client_ntp_packet = ntp_server.create_client_ntp_packet()


def send_request():
    ntp_packet = ntp_server.create_client_ntp_packet()

    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client.connect(('localhost', 123))
    client.send(ntp_packet)
    data = client.recv(1024)
    client.close()

    return data


def get_current_time():
    current_time = time.time()
    ntp_time = current_time + 2208988800  # разница между 1970 и 1900 годом в секундах
    return ntp_time


def calculate_offset():
    data = send_request()
    unpuck_data = ntp_server.unpack_ntp_packet(data)
    print(unpuck_data)

    originate = unpuck_data['originate']  # клиент отправил запрос
    receive = unpuck_data['receive']  # сервер получил пакет
    transmit = unpuck_data['transmit']  # сервер отправил пакет клиенту
    arrive = get_current_time()

    offset = receive - originate + transmit - arrive

    return offset


print(calculate_offset())

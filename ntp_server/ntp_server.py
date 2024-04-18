import argparse
import struct
import socket
import threading
import time

parser = argparse.ArgumentParser(description='SNTP Server')
parser.add_argument('-d', '--delay', type=int, default=0, help='Delay in seconds')
parser.add_argument('-p', '--port', type=int, default=123, help='Port to listen on')

args = parser.parse_args()

DELAY = args.delay
PORT = args.port
HOST = '127.0.0.1'
STRATUM_SERVER = 'pool.ntp.org'


def get_fraction(value, shift):
    return int((value - int(value)) * (2 ** shift))


def create_ntp_packet(leap_indicator, version_number, mode, stratum, pool, precision,
                      root_delay, root_dispersion, reference_identifier, reference_timestamp,
                      originate_timestamp, receive_timestamp, transmit_timestamp):
    return struct.pack("!B B b b h H h H B B B B 8I",
                       #(leap_indicator << 6) + (version_number << 3) + mode,
                       0x1B,
                       stratum,
                       pool,
                       precision,
                       int(root_delay),
                       get_fraction(root_delay, 16),
                       int(root_dispersion),
                       get_fraction(root_dispersion, 16),
                       reference_identifier >> 24,
                       (reference_identifier >> 16) & 0xFF,
                       (reference_identifier >> 8) & 0xFF,
                       reference_identifier & 0xFF,
                       int(reference_timestamp),
                       get_fraction(reference_timestamp, 32),
                       int(originate_timestamp),
                       get_fraction(originate_timestamp, 32),
                       int(receive_timestamp),
                       get_fraction(receive_timestamp, 32),
                       int(transmit_timestamp),
                       get_fraction(transmit_timestamp, 32)
                       )


def get_current_time():
    current_time = time.time()
    ntp_time = current_time + 2208988800  # разница между 1970 и 1900 годом в секундах
    return ntp_time


ORIGINATE = 0

def create_client_ntp_packet():
    current_time = get_current_time()

    ntp_packet = create_ntp_packet(0, 0, 3, 3, 0, 0, 0,
                                   0, 0, 0, current_time, 0, 0)

    return ntp_packet

data = create_client_ntp_packet()

print(data)



def unpack_ntp_packet(data: bytes):
    ntp_packet = {}
    unpacked_data = struct.unpack("!B B b b 11I", data)

    ntp_packet['leap_indicator'] = unpacked_data[0] >> 6  # 2 bits
    ntp_packet['version_number'] = (unpacked_data[0] >> 3) & 0b111  # 3 bits
    ntp_packet['mode'] = unpacked_data[0] & 0b111  # 3 bits

    ntp_packet['stratum'] = unpacked_data[1]  # 1 byte
    ntp_packet['pool'] = unpacked_data[2]  # 1 byte
    ntp_packet['precision'] = unpacked_data[3]  # 1 byte

    ntp_packet['root_delay'] = (unpacked_data[4] >> 16) + (unpacked_data[4] & 0xFFFF) / 2  # 16
    ntp_packet['root_dispersion'] = (unpacked_data[5] >> 16) + (unpacked_data[5] & 0xFFFF) / 2  # 16

    ntp_packet['ref_id'] = str((unpacked_data[6] >> 24) & 0xFF) + " " + \
                           str((unpacked_data[6] >> 16) & 0xFF) + " " + \
                           str((unpacked_data[6] >> 8) & 0xFF) + " " + \
                           str(unpacked_data[6] & 0xFF)

    ntp_packet['reference'] = unpacked_data[7] + unpacked_data[8] / 2 ** 32
    ntp_packet['originate'] = unpacked_data[9] + unpacked_data[10] / 2 ** 32
    ntp_packet['receive'] = unpacked_data[11] + unpacked_data[12] / 2 ** 32
    ntp_packet['transmit'] = unpacked_data[13] + unpacked_data[14] / 2 ** 32

    return ntp_packet

ORIGINATE = (unpack_ntp_packet(data))['originate']

print('originate' + str(ORIGINATE))

def get_stratum_reply():
    ntp_packet = create_client_ntp_packet()

    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client.sendto(ntp_packet, (STRATUM_SERVER, 123))

    data, _ = client.recvfrom(48)  # 1024

    return data


print(get_stratum_reply())


def calculate_offset():
    data = get_stratum_reply()
    unpuck_data = struct.unpack('!12I', data)
    # originate = unpuck_data[8]  # клиент отправил запрос
    # receive = unpuck_data[9]  # сервер получил пакет
    # transmit = unpuck_data[10]  # сервер отправил пакет клиенту
    arrive = get_current_time()

    unpack_data = unpack_ntp_packet(data)

    #originate = unpack_data['originate']
    originate = ORIGINATE
    receive = unpack_data['receive']
    transmit = unpack_data['transmit']
    print(originate, receive, transmit, arrive)
    print(unpack_data)

    # 3922453195 3672479437 3922453195 3922453150.0037947
    # -124986856.50189734

    offset = (receive - originate + transmit - arrive) * 0.5

    return offset


print(calculate_offset())

print(unpack_ntp_packet(create_client_ntp_packet()))

def get_current_time_wth_offset():
    offset = calculate_offset()
    return get_current_time() + offset


def create_server_ntp_packet(originate, recieve, transmit):
    ntp_packet = struct.pack('!12I',
                             0x1C,  # LI, VN, Mode
                             0, 0, 0, 0, 0, 0, 0, 0, originate, recieve,
                             transmit)
    return ntp_packet


def handle_client(client_socket, data, addr, recieve):
    # Обработка соединения с клиентом
    # client_ntp_packet = client_socket.recv(48)
    data = struct.unpack('!12I', data)

    originate = int(data[8])
    transmit = int(get_current_time_wth_offset() + DELAY)

    ntp_packet = create_server_ntp_packet(originate, recieve, transmit)

    # Отправка ответа клиенту
    client_socket.sendto(ntp_packet, addr)

    # Закрытие соединения с клиентом
    # client_socket.close()


def ntp_server(host, port):
    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server.bind((host, port))

    print(f"Server listening on port {port}...")

    while True:
        data, addr = server.recvfrom(48)
        print(f"Accepted connection from {addr}")

        recieve = int(get_current_time())
        client_thread = threading.Thread(target=handle_client, args=(server, data, addr, recieve))
        client_thread.start()


if __name__ == '__main__':
    ntp_server(HOST, PORT)

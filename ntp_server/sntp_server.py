import argparse
import struct
import socket
import time

parser = argparse.ArgumentParser(description='SNTP Server')
parser.add_argument('-d', '--delay', type=int, default=0, help='Delay in seconds')
parser.add_argument('-p', '--port', type=int, default=123, help='Port to listen on')

args = parser.parse_args()

delay = args.delay
port = args.port
host = '127.0.0.1'


def create_sntp_packet():
    # SNTP Header
    li_vn_mode = (0 << 6) | (4 << 3) | 3  # LI = 0, VN = 4 (NTPv4), Mode = 3 (Client)
    stratum = 0
    poll_interval = 0
    precision = 0
    root_delay = 0
    root_dispersion = 0
    reference_identifier = 0
    reference_timestamp = 0
    originate_timestamp = 0
    receive_timestamp = 0
    # transmit_timestamp = int(time.time()) + 2208988800  # Convert to NTP time
    transmit_timestamp = 0
    # Pack the SNTP header fields into a binary string
    sntp_packet = struct.pack("!12I", 0, stratum, poll_interval, precision,
                              root_delay, root_dispersion, reference_identifier, reference_timestamp,
                              originate_timestamp, receive_timestamp, transmit_timestamp, 0)

    return sntp_packet


stratum_ip = 'pool.ntp.org'
port = 123


def get_fraction(value, shift):
    return int((value - int(value)) * (2 ** shift))


def pack(leap_indicator, version_number, mode, stratum, pool, precision,
         root_delay, root_dispersion, reference_identifier, reference_timestamp,
         originate_timestamp, receive_timestamp, transmit_timestamp):
    return struct.pack("!B B b b h H h H B B B B 8I",
                       (leap_indicator << 6) + (version_number << 3) + mode,
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


# Пример вызова функции pack
result = pack(0, 0,
              0, 0, 0, 0, 0,
              0, 0, 0,
              0, 0, 0)
print(result)


def get_reply_from_stratum():
    # Создаем сокет и отправляем NTP-запрос на сервер
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    ntp_packet = create_sntp_packet()
    client_socket.sendto(ntp_packet, (stratum_ip, port))
    # Получаем ответ от сервера и извлекаем NTP-время из пакета
    data, server = client_socket.recvfrom(1024)
    client_socket.close()

    return data


print(get_reply_from_stratum())

import socket
import struct
import time




def create_client_ntp_packet():
    ntp_packet = bytearray(48)
    ntp_packet[0] = 0x1B  # LI, VN, Mode
    ntp_packet[1] = 0  # Stratum
    ntp_packet[2] = 6  # Poll Interval
    ntp_packet[3] = 0xEC  # Precision

    ntp_packet[12:16] = b'NTP'  # Reference Identifier
    current_time = time.time() + 2208988800
    ntp_packet[24:32] = struct.pack('>II', int(current_time), int((current_time - int(current_time)) * 2**32))
    ntp_packet[40:48] = struct.pack('>II', int(0), int(0))

    return ntp_packet

print(create_client_ntp_packet())


def send_request():
    ntp_packet = create_client_ntp_packet()

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
    unpuck_data = struct.unpack('!12I', data)

    originate = unpuck_data[8]  # клиент отправил запрос
    receive = unpuck_data[9]  # сервер получил пакет
    transmit = unpuck_data[10]  # сервер отправил пакет клиенту
    arrive = get_current_time()

    offset = (receive - originate + transmit - arrive) * 0.5

    return offset


print(calculate_offset())

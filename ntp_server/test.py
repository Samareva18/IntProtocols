import socket
import struct
import time

STRATUM_SERVER = 'pool.ntp.org'



def get_current_time():
    current_time = time.time()
    ntp_time = current_time + 2208988800  # разница между 1970 и 1900 годом в секундах
    return ntp_time


def create_client_ntp_packet():
    ntp_packet = bytearray(48)
    ntp_packet[0] = 0x1B  # LI, VN, Mode
    ntp_packet[1] = 0  # Stratum
    ntp_packet[2] = 6  # Poll Interval
    ntp_packet[3] = 0xEC  # Precision

    ntp_packet[12:16] = b'NTP'  # Reference Identifier
    current_time = get_current_time()
    ntp_packet[24:32] = struct.pack('>II', int(current_time), int((current_time - int(current_time)) * 2 ** 32))
    ntp_packet[40:48] = struct.pack('>II', int(time.time()), int(time.time()))

    return ntp_packet

print(create_client_ntp_packet())

def get_stratum_reply():
    ntp_packet = create_client_ntp_packet()

    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client.sendto(ntp_packet, (STRATUM_SERVER, 123))

    data, _ = client.recvfrom(48) #1024

    return data

ntp_packet = get_stratum_reply()
#print(get_stratum_reply())

reference_timestamp = struct.unpack('>II', ntp_packet[16:24])
originate_timestamp = struct.unpack('>II', ntp_packet[24:32])
receive_timestamp = struct.unpack('>II', ntp_packet[32:40])
transmit_timestamp = struct.unpack('>II', ntp_packet[40:48])

print("Reference Timestamp:", reference_timestamp)
print("Originate Timestamp:", originate_timestamp)
print("Receive Timestamp:", receive_timestamp)
print("Transmit Timestamp:", transmit_timestamp)
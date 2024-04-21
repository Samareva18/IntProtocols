import socket
import os
import struct
import select
import re
import ipaddress
import sys


def calculate_checksum(data):
    # Если количество байтов нечетное, добавляем пустой байт в конец
    if len(data) % 2 != 0:
        data += b'\x00'

    checksum = 0
    for i in range(0, len(data), 2):
        word = (data[i] << 8) + data[i + 1]  # Обращаемся к двум байтам одновременно
        checksum += word

    # Добавляем переносы
    checksum = (checksum >> 16) + (checksum & 0xFFFF)
    checksum += (checksum >> 16)

    return ~checksum & 0xFFFF


# Функция для создания ICMP пакета
def create_packet():
    # ICMP Echo Request
    icmp_type = 8
    icmp_code = 0
    icmp_id = os.getpid() & 0xFFFF
    icmp_seq = 1

    # Упаковываем данные в структуру без контрольной суммы
    packet = struct.pack('!BBHHH', icmp_type, icmp_code, 0, icmp_id, icmp_seq)

    # Рассчитываем контрольную сумму
    checksum = calculate_checksum(packet)

    # Заполняем контрольную сумму в пакете
    packet = struct.pack('!BBHHH', icmp_type, icmp_code, checksum, icmp_id, icmp_seq)

    return packet


# Функция для отправки ICMP пакета и получения ответа
def traceroute(host):
    try:
        try:
            # Создаем сокет
            sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)

            # Получаем IP адрес целевого хоста
            ip_address = socket.gethostbyname(host)

            max_ttl = 30
            ttl = 1
            c = 0

            while (ttl <= max_ttl):

                sock.setsockopt(socket.IPPROTO_IP, socket.IP_TTL, ttl)
                # Создаем ICMP пакет
                packet = create_packet()

                # Отправляем ICMP пакет на целевой хост
                sock.sendto(packet, (ip_address, 0))

                # Ждем ответа на ICMP пакет
                ready = select.select([sock], [], [], 1)
                if ready[0]:
                    data, addr = sock.recvfrom(1024)
                    icmp_type = data[20]  # Позиция байта с типом ICMP сообщения

                    if is_local_ip(addr[0]):
                        if addr[0] == '127.0.0.1' or addr[0] == 'localhost':
                            print(str(ttl) + '. ' + addr[0])
                            print('local\n')
                            break
                        else:
                            print(str(ttl) + '. ' + addr[0])
                            print('local\n')

                    elif icmp_type == 0:  # ICMP эхо-ответ
                        print(str(ttl) + '. ' + addr[0])
                        print(get_inf(addr[0]))
                        break
                    elif icmp_type == 11:  # Time Exceeded
                        addr = '.'.join(map(str, data[12:16]))  # Получаем IP-адрес маршрутизатора
                        print(str(ttl) + '. ' + addr)
                        print(get_inf(addr))
                    else:
                        print('Error sending the package')
                        break
                else:
                    print(str(ttl) + '. ' + '*' + '\n')  # таймаут превышен

                ttl += 1
        except socket.gaierror:
            print(f'{host} is invalid')
    except socket.error as e:
        print(f'Socket error: {e}')
    finally:
        sock.close()


def is_local_ip(ip):
    try:
        ip_obj = ipaddress.ip_address(ip)
    except ValueError:
        return False
    return ip_obj.is_private


def send_request_and_get_data(ip, server):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((server, 43))
        s.sendall((ip + "\r\n").encode())
        buff = b""
        while True:
            data = s.recv(1024)
            if not data:
                break
            buff += data
    return buff.decode("utf-8", errors="ignore")


def find_right_whois_server(ip):
    root_whois_server = 'whois.iana.org'
    data = send_request_and_get_data(ip, root_whois_server)
    right_server = re.search(r'whois:(\s*)(.*)', data)[2]
    return right_server


def dec_get_inf(get_inf):
    def wrapper(ip):
        inf = get_inf(ip)
        s = ''
        for i in inf:
            if i:
                if not s:
                    s += i
                else:
                    s += ', ' + i
        return s + '\n'

    return wrapper


@dec_get_inf
def get_inf(ip):
    whois_server = find_right_whois_server(ip)
    data = send_request_and_get_data(ip, whois_server)
    try:
        country = re.search(r'\wountry:(\s*)(\w*)', data)[2]
        if country == 'EU':
            country = None
    except:
        country = None
    try:
        AS = re.search(r'AS(\d+)', data)[1]
    except:
        AS = None
    try:
        netname = re.search(r'\wet\wame:(\s*)(.*)', data)[2]
    except:
        netname = None

    return netname, AS, country


if __name__ == '__main__':
    host = sys.argv[1]
    traceroute(host)

# Локальные адреса:
# Африканский сервер: 102.132.38.246
# Южная Америка: 45.236.171.77
# Япония: 124.156.211.175
# Европейский: 185.225.232.191
# loopback - 127.0.0.1 или localhost

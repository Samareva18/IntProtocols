import socket


def get_protocol_by_port(host, port, protocols):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.settimeout(5)
            s.connect((host, port))

            for protocol in protocols:
                # if protocol == 'HTTP':
                #     # Отправляем HTTP запрос
                #     s.send(b'GET / HTTP/1.1\r\nHost: example.com\r\n\r\n')
                if protocol == 'SNTP':
                     # Отправляем SNTP запрос
                     s.send(b'\x1b' + 47 * b'\0')
                elif protocol == 'DNS':
                     # Отправляем DNS запрос
                     s.send(
                         b'\x00\x00\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x03www\x06google\x03com\x00\x00\x01\x00\x01')
                elif protocol == 'SMTP':
                    # Отправляем SMTP запрос
                    s.send(b'EHLO example.com\r\n')
                elif protocol == 'POP3':
                    # Отправляем POP3 запрос
                    s.send(b'USER test\r\n')
                elif protocol == 'IMAP':
                    # Отправляем IMAP запрос
                    s.send(b'LOGIN test password\r\n')

                response = s.recv(1024).decode('utf-8')
                print(response + 'hahhah')
                if protocol in response:
                    return protocol

            return 'Unknown'
    except (socket.timeout, ConnectionRefusedError):
        return 'Port closed'


host = '127.0.0.1'
port = 123
protocols = {'HTTP', 'SNTP', 'DNS', 'SMTP', 'POP3', 'IMAP'}

protocol = get_protocol_by_port(host, port, protocols)

if protocol == 'Port closed':
    print(f'Port {port} is closed')
else:
    print(f'Port {port} is open with protocol: {protocol}')

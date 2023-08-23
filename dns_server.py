"""
DNS Server
"""

import errno
import signal
import socket
import sys
import time
import dnslib
import pickle


ROOT_IP = '198.41.0.4'
IP = '127.0.0.1'
PORT = 53
cache = {}


def exite_user(signal, frame):
    sys.exit(0)


def update_cache():
    new_cache = {}

    for k in cache:
        if cache[k][0][0].ttl > time.time() - cache[k][1]:
            new_cache[k] = cache[k]

    cache.clear()
    cache.update(new_cache)


def send_request(request, ip, client):
    try:
        client.sendto(request, (ip, 53))
        response, _ = client.recvfrom(2048)
        response = dnslib.DNSRecord.parse(response)

        if response.header.a == 1:
            cache[(response.questions[0].qname, response.questions[0].qtype)] = response.rr, time.time()

        if response.auth:
            cache[(response.auth[0].rname, response.auth[0].rtype)] = response.auth, time.time()

        for additional in response.ar:
            cache[(additional.rname, additional.rtype)] = [additional], time.time()

        with open('cache', 'wb') as f:
            pickle.dump(cache, f)
    except Exception:
        print("Error")


def run():
    try:
        with open('cache', 'rb') as f:
            cache.clear()
            cache.update(pickle.load(f))
            print("Cache loaded from a file")
    except:
        print("The cache file could not be opened, a new cache will be created")

    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server.bind((IP, PORT))

    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client.settimeout(5)

    signal.signal(signal.SIGINT, exite_user)
    server.setblocking(False)

    while True:
        try:
            new_domain = ''
            request, address = server.recvfrom(2048)
            res = dnslib.DNSRecord.parse(request)
            domain = res.questions[0].qname

            print(domain)
            str_domain = str(domain)

            if str_domain.rfind('.') == len(str_domain) - 1:
                str_domain = str_domain[:str_domain.rfind('.')]
                new_domain = str_domain

            update_cache()

            question_type = res.questions[0].qtype
            if not cache.get((domain, question_type)):
                print('from authoritative server')
            else:
                print('from cache')

            need_root_dns_query = False
            need_authoritative_dns_query = False

            while not cache.get((domain, question_type)) and new_domain:

                if need_root_dns_query:
                    send_request(request, ROOT_IP, client)
                    need_root_dns_query = False
                    need_authoritative_dns_query = True

                elif need_authoritative_dns_query:

                    last_dot = new_domain.rfind('.')
                    dt = str_domain[last_dot + 1:]
                    new_domain = new_domain[:last_dot]

                    if cache.get((dnslib.DNSLabel(dt), 2)):
                        ns = cache.get((dnslib.DNSLabel(dt), 2))[0]

                        for i in ns:
                            try:
                                ip = str(cache.get((dnslib.DNSLabel(str(i.rdata)), 1))[0][0].rdata)
                                send_request(request, ip, client)
                            except:
                                pass
                else:
                    last_dot = new_domain.find('.')

                    if not last_dot == -1:
                        dt = str_domain[last_dot + 1:]
                        new_domain = new_domain[last_dot + 1:]
                        try:
                            if cache.get((dnslib.DNSLabel(dt), 2)):
                                ns = cache.get((dnslib.DNSLabel(dt), 2))[0]

                                for i in ns:
                                    ip = str(cache.get((dnslib.DNSLabel(str(i.rdata)), 1))[0][0].rdata)
                                    send_request(request, ip, client)

                                need_authoritative_dns_query = True
                                last_dot = str_domain.rfind('.' + dt)
                                new_domain = str_domain[:last_dot]

                        except Exception as e:
                            print(f'Error: {e}')

                    else:
                        need_root_dns_query = True
                        new_domain = str_domain

            if cache.get((domain, question_type)):
                header = dnslib.DNSHeader(res.header.id, q=1, a=len(cache.get((domain, question_type))[0]))
                response = dnslib.DNSRecord(header, res.questions, cache.get((domain, question_type))[0])
                server.sendto(response.pack(), address)
            else:
                print("Error")
        except KeyboardInterrupt:
            exite_user(None, None)
        except socket.error as e:
            err = e.args[0]
            if err == errno.EAGAIN or err == errno.EWOULDBLOCK:
                pass
            else:
                print(f"Error: {e}")


if __name__ == '__main__':
    run()

import os
import re
from urllib.request import urlopen

error = 0

print('Enter IP address or domain name for tracing AS:')
IP = input()
output_inf_ip = os.popen('tracert  -d ' + IP)
frst_str = output_inf_ip.readline().encode('cp1251').decode('cp866')

try:
    if frst_str == 'Не удается разрешить системное имя узла ' + IP + '.\n':
        error = 1
        raise Exception()
except Exception:
    print('Некорректный ввод данных')

if not error:
    for i in range(3):
        output_inf_ip.readline()

    routers_IP = []
    router_inf = []
    while True:
        router_inf = output_inf_ip.readline().split()
        if not router_inf or router_inf[-1] == ".":
            break
        routers_IP.append(router_inf[-1])

    AS = []
    countries = []
    providers = []
    for ip in routers_IP:
        if ip == routers_IP[0]:
            AS.append('unknown')
            countries.append('unknown')
            providers.append('unknown')
            continue
        url_database_AS = 'https://www.nic.ru/whois/?query=212.193.66.21&searchWord=' + str(ip)
        with urlopen(url_database_AS) as page:
            page = page.read().decode('utf-8', errors='ignore')
            try:
                ip_as = re.search(r'AS\d+', page)
                AS.append(ip_as[0])
            except Exception:
                AS.append('unknown')

            try:
                country = re.search(r'country:(\s*)(.*)', page)
                countries.append(country[2])
            except Exception:
                AS.append('unknown')

            try:
                provider = re.search(r'route: (.*)\ndescr:(\s*)(.*)', page)
                providers.append(provider[3])
            except Exception:
                AS.append('unknown')

    print('№        IP                AS           Country           Provider ')

    for i in range(len(routers_IP)):
        print(str(i + 1) + '    ' + routers_IP[i] + ' ' * (20 - len(routers_IP[i])) + AS[i] + ' ' * (17 - len(AS[i])) +
              countries[i] + ' ' * (13 - len(countries[i])) + providers[i])

output_inf_ip.close()

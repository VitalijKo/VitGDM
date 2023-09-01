import os

os.system('sudo firewall-cmd --zone=public --add-port=7575/tcp --permanent && sudo firewall-cmd --zone=public --add-port=7575/udp --permanent')
os.system('sudo firewall-cmd --reload')

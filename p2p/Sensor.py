from p2p.Message import Message
from p2p.config import LOGGING_ENABLED
import rpyc
import netifaces as ni
import logging
import sys
import threading
import random
import string
import time


class SensorService(rpyc.Service):
    def __init__(self):
        self.id = ni.ifaddresses('eth0')[ni.AF_INET][0]['addr']
        self.default_gateway = ni.gateways()['default'][ni.AF_INET][0]
        self.servers = []
        self.new_data = []

    def __str__(self):
        """
        Stringge alakitas, kiiratashoz kell
        """
        return f'Sensor_{self.id}'

    def log(self, *args, **kwargs):
        """
        Fontosabb esemenyek logolasa konzolra, ha a config-ban LOGGING_ENABLED engedelyezve van.
        Hivas szintaxisa: print-tel megegyezoen
        :param args: kiirando dolgok felsorolasa
        :param kwargs: elvalaszto karakter megadhato sep=' ' formaban, alapertelmezes: szokoz
        """
        if LOGGING_ENABLED:
            if 'sep' in kwargs:
                sep = kwargs.get('sep')
            else:
                sep = ' '
            msg = sep.join(map(str, args))
            print('Sensor ', self.id, ': ', msg, sep='')

    #szerverek tömbjének újramegadása
    def exposed_redefine_servers(self, servers_array):
        self.log('New server list:', servers_array)
        self.servers = servers_array
    
    #megpróbál küldeni a szervernek
    def try_to_send_data(self, server_id, data):
        try:
            msg = Message(self.id, self.servers[0], data)
            conn = rpyc.connect(server_id, 9600)
            result = conn.root.receive_data(msg)
        except Exception as ex:
            self.log('RPC failed:', ex)
            result = False
        return result

    #sorban megpróbál küldeni az összes szervernek
    def send_data(self):
        for data in self.new_data:
            #sajat szervernek probalja eloszor
            self.log('Sending data ', data)
            if self.try_to_send_data(self.default_gateway, data):
                continue
            #utana a tobbieknek
            for server_id in self.servers:
                self.log('Sending recovery data ', data, ' to ', server_id)
                if self.try_to_send_data(self.default_gateway, data):
                    break
            threading.Timer(5.0, self.send_data).start()

    def random_data(self):
        """Generate a random string of letters and digits """
        chars = string.ascii_letters + string.digits
        data = ''.join(random.choice(chars) for i in range(20))
        this.log('Generated data:', data)
        self.new_data.append(data)
        threading.Timer(10.0, self.random_data).start()


def rpyc_start(sensor_instance):
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
    from rpyc.utils.server import ThreadedServer
    t = ThreadedServer(sensor_instance, port=9600, listener_timeout=60, logger=logging.getLogger())
    t.start()


if __name__ == "__main__":
    #fo peldany letrehozasa es szal inditasa az rpyc szervernek
    this = SensorService()
    x = threading.Thread(target=rpyc_start, args=(this,), daemon=True)
    x.start()
    this.log('Default server:', this.default_gateway)
    c = rpyc.connect(this.default_gateway, 9600)
    c.root.add_sensor(this.id)
    this.log('Sensor started!')
    this.random_data()
    this.send_data()
    x.join()

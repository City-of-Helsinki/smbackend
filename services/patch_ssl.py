import ssl
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.poolmanager import PoolManager

class TLS1HttpAdapter(HTTPAdapter):
    """"Transport adapter" that allows us to use TLSv1."""

    def init_poolmanager(self, connections, maxsize, block=False):
        self.poolmanager = PoolManager(num_pools=connections,
                                       maxsize=maxsize,
                                       block=False,
                                       ssl_version=ssl.PROTOCOL_TLSv1)
def get_session():
    s = requests.Session()
    s.mount('https://', TLS1HttpAdapter())
    return s

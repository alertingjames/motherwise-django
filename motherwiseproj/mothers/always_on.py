import requests
from datetime import datetime
from threading import Timer


import time

while True:
    print(datetime.now(), flush=True)
    requests.get('https://www.vacay.company/always_on')
    time.sleep(20)




























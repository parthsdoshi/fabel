from time import sleep
from threading import Thread, Lock
import logging

import requests
from requests import exceptions as httpE

import webview

from server import main

if __name__ == '__main__':
    t = Thread(target=main)
    t.daemon = True
    t.start()

    status_code = None
    tries = 30
    while status_code != 200 and tries > 0:
        try:
            tries -= 1
            status_code = requests.get('http://localhost:4994').status_code
        except (httpE.HTTPError, httpE.ConnectionError) as e:
            if tries == 0:
                print(e)
                exit(-1)
            print(f"Tries left: {tries}")
        sleep(.3)

    # use chrome renderer instead of IE
    webview.gui = 'cef'
    webview.create_window('Fabel', 'http://localhost:4994', debug=True)

# import webview
from cefpython3 import cefpython as cef
cef.DpiAware.EnableHighDpiSupport()

import sys
import ctypes
import platform
from time import sleep
from threading import Thread, Lock
import logging

import requests
from requests import exceptions as httpE

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
    
    sys.excepthook = cef.ExceptHook  # To shutdown all CEF processes on error
    cef.Initialize()
    window_info = cef.WindowInfo()
    parent_handle = 0
    # This call has effect only on Mac and Linux.
    # All rect coordinates are applied including X and Y parameters.
    window_info.SetAsChild(parent_handle, [0, 0, 900, 600])
    browser = cef.CreateBrowserSync(url="http://localhost:4994",
                                    window_info=window_info,
                                    window_title="Fabel")
    if platform.system() == "Windows":
        window_handle = browser.GetOuterWindowHandle()
        insert_after_handle = 0
        # X and Y parameters are ignored by setting the SWP_NOMOVE flag
        SWP_NOMOVE = 0x0002
        # noinspection PyUnresolvedReferences
        ctypes.windll.user32.SetWindowPos(window_handle, insert_after_handle,
                                          0, 0, 900, 600, SWP_NOMOVE)
    cef.MessageLoop()
    cef.Shutdown()

    # use chrome renderer instead of IE
    # webview.config.gui = 'cef'
    # webview.create_window('Fabel', 'http://localhost:4994', debug=True, width=900, height=600)

# -*- coding: utf-8 -*-
"""
server_uwb_v3.py

@author: Geonwoo Ji

Created on Sun Jul 4 22:33:00 2023

version 3.0
"""

#!/usr/bin/env python
# python xxxx.py

import os
import sys
import time
import socket
import cv2 as cv
import numpy as np
import pandas as pd
from time import sleep
import winsound as sd

from datetime import datetime
from pymoduleconnector import ModuleConnector


__version__ = 2



def beep():
    sd.Beep(2000, 1000)


# make directory if there is no required folder
def makedirs(path):
    try:
        if not os.path.exists(path):
            os.makedirs(path)
    except OSError:
        print("Failed to create the directory!!!", path)


# reset Xethru IR-UWB radar
def reset(device_name):
    mc = ModuleConnector(device_name)
    r = mc.get_xep()
    r.module_reset()
    mc.close()
    sleep(3)


# Clears the frame buffer
def clear_buffer(r):
    while r.peek_message_data_float():
        _ = r.read_message_data_float()


def running_server(host, port):
    def read_frame():
        """Gets frame data from module"""
        frame = np.array(r.read_message_data_float().data)

        # Convert the resulting frame to a complex array if downconversion is enabled
        n=len(frame)
        frame = frame[:n//2] + 1j*frame[n//2:]

        return frame

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((host, port))

    server_socket.listen()
    print("Server status...ready")
    print("Waiting for client...")

    locNum = str(input('Enter location!!\n'))
    FILE_PATH = "C:\\x4\\exp1\\"
    IMG_PATH = FILE_PATH + "imgs\\"
    DEVICE_NAME = "COM3"
    baseband = True
    FPS = 30

    TIME_INTERVAL = 60 * 5

    reset(DEVICE_NAME)
    mc = ModuleConnector(DEVICE_NAME)

    cap = cv.VideoCapture(2)

    r = mc.get_xep()

    # Set DAC range
    r.x4driver_set_dac_min(900)
    r.x4driver_set_dac_max(1150)

    # Set integration
    r.x4driver_set_iterations(64)
    r.x4driver_set_pulses_per_step(29)
    r.x4driver_set_frame_area_offset(0.18)

    r.x4driver_set_downconversion(int(baseband))

    print("FirmWareID =", r.get_system_info(2))
    print("Version =", r.get_system_info(3))
    print("Build =", r.get_system_info(4))
    print("VersionList =", r.get_system_info(7))
    
    cnt = 0
    timeInfo = []
    bb_signal = []
    imgValue = []

    sleep(3)
    clear_buffer(r)
    
    client_socket, addr = server_socket.accept()
    # print("Connected by", addr)
    start = time.time()    
    r.x4driver_set_fps(FPS)

    while True:
        timeInfo.append(datetime.now().strftime("%m%d%H%M%S%f")[:-4])
        bb_signal.append(abs(read_frame()))

        ret, fram = cap.read()
        if ret:
            imgValue.append(fram)
        else:
            r.x4driver_set_fps(0)
            cap.release()
            beep()
            beep()
            beep()
            print("unknown Error!")
            sys.exit()

        if cnt == FPS * TIME_INTERVAL + 30:
            break
        else:
            cnt += 1

    print("Running time :", time.time() - start)
    beep()
    r.x4driver_set_fps(0)
    cap.release()


    print("\n.............Data informations.............")

    start = time.time()

    print("Time Info", len(timeInfo))
    print("Signal info", len(bb_signal))
    print("Img values", len(imgValue))

    print("\n.............Saving.............")

    makedirs(IMG_PATH)

    col = [str(cn) for cn in range(180)]

    rf_df = pd.DataFrame(data=bb_signal, columns=col)
    rf_df['180'] = timeInfo
    rf_df.to_feather(FILE_PATH + "data_" + locNum + ".ftr")
    print("\nCSV File created !!")
    print("Running time :", time.time() - start)

    start = time.time()

    for idx, file_name in enumerate(timeInfo):
        img_name = file_name + ".jpg"
        # img_name = file_name
        cv.imwrite(IMG_PATH + img_name, imgValue[idx])

    print("\nIMG File created !!")
    print("\nRunning time :", time.time() - start)
    print("\n################### Complete !! ###################\n")


    print("Disconnected !!")
    beep()
    client_socket.close()
    server_socket.close()


def main(host, port):
    running_server(host, port)


if __name__ == "__main__":
    HOST = "172.16.16.205"
    PORT = 24905

    try:
        main(HOST, PORT)
    except KeyboardInterrupt:
        print("Keyboard interrupt!!")
    except Exception as e:
        print("Error!!", e)
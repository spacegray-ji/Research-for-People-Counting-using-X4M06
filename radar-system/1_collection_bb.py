import os
import sys
import time
import cv2 as cv
import numpy as np
import pandas as pd
from time import sleep

from datetime import datetime
from pymoduleconnector import ModuleConnector


__version__ = 2


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
def clear_buffer():
    while r.peek_message_data_float():
        _ = r.read_message_data_float()


def read_frame():
    """Gets frame data from module"""
    d = r.read_message_data_float()
    frame = np.array(d.data)

    # Convert the resulting frame to a complex array if downconversion is enabled
    # if baseband:
    n=len(frame)
    frame = frame[:n//2] + 1j*frame[n//2:]

    return frame


# Parameter setting

# locNum = int(sys.stdin.readline().rstrip())
locNum = str(input('Enter location!!\n'))

FILE_PATH = "C:\\x4\\exp1\\"
# IMG_PATH = FILE_PATH + "imgs\\" + locNum + "\\"
IMG_PATH = FILE_PATH + "imgs\\"
DEVICE_NAME = "COM3"
baseband = True
FPS = 30

# For 1 min >> 60
# For 5 min >> 60 * 5
TIME_INTERVAL = 60 * 3

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

# etc settnig
cnt = 0
# q = 0
timeInfo = []
bb_signal = []
# imgName = []
imgValue = []

# timeInfo_app = timeInfo.append
# signal_app = bb_signal.append
# imgName_app = imgName.append
# imgValue_app = imgValue.append

print(".............Tuning.............")

# for g in range(30):
#     ret, fram = cap.read()


sleep(3)
clear_buffer()

print(".............Start colelcting.............")
start = time.time()

r.x4driver_set_fps(FPS)

while True:
    # ti = datetime.now().strftime("%m%d%H%M%S%f")[:-4]
    timeInfo.append(datetime.now().strftime("%m%d%H%M%S%f")[:-4])
    bb_signal.append(abs(read_frame()))

    ret, fram = cap.read()
    if ret:
        imgValue.append(fram)
    else:
        r.x4driver_set_fps(0)
        cap.release()
        print("Error!")
        sys.exit()

    if cnt == FPS * TIME_INTERVAL:
        break
    else:
        cnt += 1

r.x4driver_set_fps(0)
cap.release()

print("Running time :", time.time() - start)


print("\n.............Data informations.............")

start = time.time()

print("Time Info", len(timeInfo))
print("Signal info", len(bb_signal))
# print("Img names", len(imgName))
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


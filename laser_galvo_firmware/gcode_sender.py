#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" gcode_sender.py
    Send gcode to the laser galvo module
"""

__version__ = "1.0"

__author__ = "Andrew Miyaguchi"
__copyright__ = "Copyright 2021, Andrew Miyaguchi"
__license__ = "Apache 2.0"

import sys
import time
import serial
from struct import *
from serial.serialutil import Timeout
from serial.win32 import ERROR_OPERATION_ABORTED

G1 = 1
M3 = 3
M5 = 5

if len(sys.argv) == 1:
    print("Please point to a file.\n")
    sys.exit(1)

ser = serial.Serial("COM4", 115200, timeout=1)
print(ser.name)

WALL_DISTANCE = 200

def millis():
    return time.time_ns()/1000000

with open(sys.argv[1], 'r') as f:
    laserEnable = False
    serialReady = False
    serialWatchdog = millis()

    # Wait until the system is ready
    print("> Waiting for system ready...\n")
    while(True):
        if ser.in_waiting:
            line = ser.readline().decode("utf-8")
            print(line, end = '')
            if "sh$" in line:
                break

    print("\n> System ready. Sending commands")
    # Keep looping through the file
    while(True):
        for line in f:
            # Parse G1 commands
            if "G1" in line:
                x = None
                y = None
                z = None
                e = None

                # Extract x, y, and z coordinates0
                for token in line.split():
                    if "X" in token:
                        x = float(token[1:])
                    if "Y" in token:
                        y = float(token[1:])
                    if "Z" in token:
                        z = float(token[1:])
                    if "E" in token:
                        e = float(token[1:])

                # Enable the laser on the first extrusion event
                if e is not None and laserEnable == False:
                    ser.write(pack('c', M3))
                    laserEnable = True
                
                # Disable the laser on the last extrusion event
                elif e == None and laserEnable == True:
                    ser.write(pack('c', M5))
                    laserEnable = False

                # Queue movement command if we have x and y coordinates.
                # y == actually the z axis when projecting on a wall.
                # y becomes the distance to the wall.
                if x is not None and y is not None:
                    ser.write(pack('cfff', x, WALL_DISTANCE, y))

                # Wait until it's time to send another line
                while millis() - serialWatchdog < 10:
                    if ser.inWaiting():
                        print((ser.read()).decode("utf-8"), end='')
                
                serialWatchdog = millis()
            else:
                pass

        else:
            # reset the file loop
            f.seek(0)
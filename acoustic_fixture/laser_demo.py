#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" laser_demo.py: Scan the laser module across a grid
	The grid should be in 1 cm increments. The program scans
	in 20 cm increments
"""

__version__ = "1.0"

__author__ = "Andrew Miyaguchi"
__copyright__ = "Copyright 2021, Andrew Miyaguchi"
__license__ = "Apache 2.0"

import serial, time
from serial_comms import waitFor, sendCommand

# Configuration
COM_PORT = "COM3"   # Laser com port
OFFLINE_MODE = False

STEP = 20
X_MAX = 60
Z_MAX = 40

Z_OFFSET = 18
X_OFFSET = 11

# The mirror of the laser is 24 mm from the front of the device
# Test grid is 304.8 mm + 24 mm = Y328.8 mm
y = 328.8

FWD = True
REV = False

x_dir = FWD
z_dir = FWD

start_time = time.time()

print("Connecting to Laser...")
if not OFFLINE_MODE:
    ser = serial.Serial(COM_PORT, 115200)
    waitFor(ser, "\rsh$ ")    # Wait for the system to initialize
    sendCommand(ser, "M3", "\rsh$ ")
    print("Connected to laser")
else:
    print("Offline mode enabled. Simulating outputs")

# Cycle through the training at least 3 times
while(True):
    z_range = range(-Z_MAX, Z_MAX + STEP, STEP) if z_dir == FWD else range(Z_MAX, -(Z_MAX + STEP), -STEP)
    for z in z_range:
        z += Z_OFFSET

        x_range = range(-X_MAX, X_MAX + STEP, STEP) if x_dir == FWD else range(X_MAX, -(X_MAX + STEP), -STEP)
        for x in x_range:
            x += X_OFFSET
            command = "G1 X%.2f Y%.2f Z%.2f" % (x, y, z)
            if not OFFLINE_MODE:
                sendCommand(ser, command, "\rsh$ ")
            else:
                print("[%12.6f] %s" % (time.time() - start_time, command))

            time.sleep(0.5) # Wait 500ms for the fixture to stabalize before capturing data
            
        # Reverse the direction of x
        x_dir = ~x_dir 
    
    # Reverse the direction of y
    #z_dir = ~z_dir

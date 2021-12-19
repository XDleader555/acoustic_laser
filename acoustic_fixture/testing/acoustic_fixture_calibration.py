#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" calibration_rig.py: trilateration microphone calibration
    Since trilateration doesn't account for the acoustic properties of the sound
    source, the results will be skewed. To account for this, it's possible
    to use machine learning to build a lookup table-like model which takes
    the inputs of the microphones and outputputs the cartesian coordinates
    without actually touching any of the math behind trilateration

    A 3D printer is used as a precise calibration rig to train the model. A
    cellphone is zip tied to the head which produces the approprate tone, and
    data is captured every 20mm

    https://kevinponce.com/blog/python/send-gcode-through-serial-to-a-3d-printer-using-python/
"""

__version__ = "1.0"

__author__ = "Andrew Miyaguchi"
__copyright__ = "Copyright 2021, Andrew Miyaguchi"
__license__ = "Apache 2.0"

import serial
import time
from acoustic_fixture import AcousticFixture as AF, BUFFER, AMPLITUDE_SIZE
import pickle

start_time = time.time()

# Initialize the acoustic fixture in calibration mode
af = AF(cal_mode=True)

# Assume lower left corner of the fixture is located at (0, 0, 0)
FIXTURE_HEIGHT = 56     # Distance to the top of the microphones
PHONE_CENTER = (170, 125, 8)

STEP = 20
X_MAX = 80
Y_MAX = 80
Z_MAX = 120


# Wait for the machine to return ok
def waitFor(ser, response):
    ret = ""
    while True:
        if ser.in_waiting:
            while ser.in_waiting:
                ret = ser.readline().decode("utf-8")
            print("[%12.6f] %s" % (time.time() - start_time, ret.replace("\n", "").replace("\r", "")))

        if ret == response:
            break

# Write a gcode command to the printer
def sendCommand(ser, gcode):
    # Make sure we terminate our gcode
    if gcode[-2:] != "\r\n":
        gcode += "\r\n"

    # Send the command
    print("> %s" % (gcode.replace("\n", "").replace("\r", "")))
    ser.write(str.encode(gcode))
    time.sleep(0.1)
    waitFor(ser, "ok\n")

print("Connecting to printer...")
ser = serial.Serial("COM4", 115200)
waitFor(ser, "LCD status changed\n")    # Wait for the system to initialize

prompt = "Remove the acoustic fixture and phone, then press enter to home all axis"
sendCommand(ser, "M0 %s" % (prompt))
sendCommand(ser, "G28 0 W")               # Home the system
sendCommand(ser, "G1 F9000")            # Set the feed rate

# Move to the phone installation position
sendCommand(ser, "G1 X%d Y%d Z%d" % PHONE_CENTER)
sendCommand(ser, "M400")                # Wait for moves to finish
prompt = "Install the phone into the holder with the bottom flush to the bed"
sendCommand(ser, "M0 %s" % (prompt))

# Make the bed accessable to the user so we can install the acoustic fixture
sendCommand(ser, "G1 X0 Y200 Z100")     
sendCommand(ser, "M400")                # Wait for moves to finish
prompt = "Install the acoustic fixture onto the print table"
sendCommand(ser, "M0 %s" % (prompt))


HEIGHT_OFFSET = 20
center_x, center_y, center_z = PHONE_CENTER
center_z += FIXTURE_HEIGHT + HEIGHT_OFFSET # start some distance above the mics

cal_dict = {}

num_datapoints = 0

FWD = True
REV = False

x_dir = FWD
y_dir = FWD
z_dir = FWD

# Cycle through the training at least 3 times
for i in range(3):
    # Step through each calibration point
    for z in range(0, Z_MAX + STEP, STEP):
        y_range = range(-Y_MAX, Y_MAX + STEP, STEP) if x_dir == FWD else range(Y_MAX, -(Y_MAX + STEP), -STEP)
        for y in y_range:
            x_range = range(-X_MAX, X_MAX + STEP, STEP) if x_dir == FWD else range(X_MAX, -(X_MAX + STEP), -STEP)
            for x in x_range:
                sendCommand(ser, "G1 X%d Y%d Z%d" % (x + center_x, y + center_y, z + center_z))
                sendCommand(ser, "M400")
                time.sleep(0.5) # Wait 500ms for the fixture to stabalize before capturing data

                # initialize the array of data if it doesn't exit
                k = (x, y, z + HEIGHT_OFFSET)
                if k not in cal_dict:
                    cal_dict[k] = []

                # discard the first buffer since the fixture class is asynchronous
                af.update()

                # Take 10 samples of data
                for i in range(AMPLITUDE_SIZE):
                    # fill the buffer with new data
                    af.update()

                    # copy the buffer into our training data set
                    cal_dict[k].append(af.buf_copy)
                    num_datapoints += 1

                # print the average for debug purposes only
                print("[%12.6f] M1: %.4f, M2: %.4f, M3: %.4f, n: %d" % (time.time() - start_time, af.amplitude_avg[0], af.amplitude_avg[1], af.amplitude_avg[2], num_datapoints))
            # Reverse the direction of x
            x_dir = ~x_dir 
        
        # Reverse the direction of y
        y_dir = ~y_dir

# Dump the training data in binary format
pickle.dump(cal_dict, open("training_data.db", 'wb'))

end_time = time.time() - start_time
print("All done! Captured %d samples in %d minutes and %d seconds." % (num_datapoints, int(end_time/60), int(end_time) % 60))

ser.close
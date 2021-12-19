#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" serial_comms.py: communicate over serial"""

__version__ = "1.0"

__author__ = "Andrew Miyaguchi"
__copyright__ = "Copyright 2021, Andrew Miyaguchi"
__license__ = "Apache 2.0"

import time

start_time = time.time()

# Wait for the machine to return ok
def waitFor(ser, response):
    while True:
        ret = ""
        if ser.in_waiting:
            while ser.in_waiting:
                c = ser.read().decode("utf-8")
                ret += c
                if c == "\n":
                    break
            print("[%12.6f] %s" % (time.time() - start_time, ret.replace("\n", "").replace("\r", "")))

        if ret == response:
            break

# Write a gcode command to the printer
def sendCommand(ser, gcode, trigger="ok\n"):
    # Make sure we terminate our gcode
    if gcode[-2:] != "\r\n":
        gcode += "\r"

    # Send the command
    print("> %s" % (gcode.replace("\n", "").replace("\r", "")))
    ser.write(str.encode(gcode))
    time.sleep(0.1)
    waitFor(ser, trigger)
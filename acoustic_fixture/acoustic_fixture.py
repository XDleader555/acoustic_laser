#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" acoustic_fixture.py: Code to receive data from the acoustic fixture
    The mirror of the laser is 24 mm from the front of the device
    Test grid is Y328.8 mm
    Test fixture is 342.9 mm + 80.7 mm + 24 mm = X0 Y447.6 Z56
"""

__version__ = "1.0"

__author__ = "Andrew Miyaguchi"
__copyright__ = "Copyright 2021, Andrew Miyaguchi"
__license__ = "Apache 2.0"

import pyaudio, serial, time
from scipy.interpolate import interp1d
from numpy import cos, pi, zeros, frombuffer, float32, roll, average
from acoustic_trilateration import get_time_shift, trilateration, butter_bandpass_filter
from trilateration_linear_regression_model import predict

from serial_comms import waitFor, sendCommand

# Configuration
COM_PORT = "COM3"   # Laser com port

OFFLINE_MODE = False

USE_MACHINE_LEARNING = 0
RATE = 44100
BUFFER = 882    # RATE must be evenly divisible by BUFFER

LPF = 400
HPF = 480

AMPLITUDE_MS = 500
AMPLITUDE_SIZE = int(AMPLITUDE_MS/RATE*BUFFER)

# Microphone calibrations in mm
CAL_DISTANCE = [0, 25, 50, 100, 150, 200]
M1_CAL = interp1d([1.3250, 0.0990, 0.0300, 0.0098, 0.0048, 0.0030], CAL_DISTANCE, kind='linear', fill_value="extrapolate")
M2_CAL = interp1d([1.3200, 0.0810, 0.0260, 0.0094, 0.0058, 0.0045], CAL_DISTANCE, kind='linear', fill_value="extrapolate")
M3_CAL = interp1d([1.3020, 0.0700, 0.0230, 0.0084, 0.0054, 0.0045], CAL_DISTANCE, kind='linear', fill_value="extrapolate")
MIC_CAL = [M1_CAL, M2_CAL, M3_CAL]
#RADIAL_CAL = interp1d(CAL_DISTANCE, [1.0, 0.892857143, 0.714285714, 0.571428571, 0.5])

# Acoustic fixture properties, variables are part of the trilateration equation
FIXT_MIC_RADIUS = 80
FIXT_D = FIXT_MIC_RADIUS * cos(30 * pi / 180) * 2
FIXT_E = FIXT_D/2
FIXT_F = FIXT_MIC_RADIUS + FIXT_MIC_RADIUS/2
#print([FIXT_D, FIXT_E, FIXT_F])

ser = None

class AcousticFixture:
    mic_dict = {"Mosquito 1":[-1, ""], "Mosquito 2":[-1, ""], "Mosquito 3":[-1, ""]}

    # Pre-allocate buffers
    buf = [zeros(BUFFER) for y in range(len(mic_dict))]
    buf_copy = buf.copy()
    buf_filtered = buf.copy()
    voltage_data = buf.copy()
    amplitude_buffer = [zeros(AMPLITUDE_SIZE) for i in range(len(mic_dict))]
    amplitude_avg = zeros(len(mic_dict) + 1)
    delay_buffer = [zeros(AMPLITUDE_SIZE) for i in range(len(mic_dict))]
    delay_avg = zeros(len(mic_dict) + 1)
    calibration_mode = False

    streams = []
    x = 0
    y = 0
    z = 0

    # Custom callback which inserts the index of the microphone into the local scope
    def portaudio_callback(this, idx):
        def callback(in_data, frame_count, time_info, status):
            this.buf[idx] = frombuffer(in_data,dtype=float32)
            return (this.buf[idx], pyaudio.paComplete)
        return callback

    def active(this):
        for s in this.streams:
            if s.is_active():
                return True
        return False

    def __init__(this, cal_mode = False):
        global ser
        this.calibration_mode = cal_mode

        # Print config
        print("Sample Rate: %d Hz\nBuffer Size: %d frames\nSample Length: %d ms\n" % (RATE, BUFFER, 1/RATE*BUFFER*1000))

        p = pyaudio.PyAudio()

        # Search for our microphones
        print("Searching for microphones by name")
        info = p.get_host_api_info_by_index(0)
        numdevices = info.get('deviceCount')
        for i in range(numdevices):
                if (p.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')) > 0:
                    dev_name = p.get_device_info_by_host_api_device_index(0, i).get('name')
                    #print("Input Device id %d - %s" % (i, dev_name))

                    # Check if this is the correct microphone and set the index
                    for key in this.mic_dict:
                        if key in dev_name:
                            this.mic_dict[key][0] = i
                            this.mic_dict[key][1] = dev_name

        # Verify that all microphones are attached
        for key in this.mic_dict:
            if this.mic_dict[key][0] == -1:
                print("%s not found. Please make sure the device is plugged in." % (key))
                exit()

        # Print all microphone id
        for key in this.mic_dict:
            print("Input Device id %d - %s" % (this.mic_dict[key][0], this.mic_dict[key][1]))

        # Open microphone streams
        for key in this.mic_dict:
            this.streams.append(p.open(
                format = pyaudio.paFloat32,
                channels = 1,
                rate = RATE,
                input = True,
                output = False,
                frames_per_buffer = BUFFER,
                input_device_index = this.mic_dict[key][0],
                stream_callback = this.portaudio_callback(list(this.mic_dict.keys()).index(key))
            ))

        # Aquire the first samples
        for s in this.streams:
            s.start_stream()

        print("Connecting to Laser...")
        if not OFFLINE_MODE:
            ser = serial.Serial(COM_PORT, 115200)
            waitFor(ser, "\rsh$ ")    # Wait for the system to initialize
            sendCommand(ser, "M3", "\rsh$ ")
        print("Offline mode. Laser module disconnected.")

    def update(this, corr_lines=None):
        global ser
        # Wait until all streams stop
        while this.active():
            pass

        # Copy the data to a new buffer
        this.buf_copy = this.buf.copy()
        
        # Start the data aquisition for the next cycle before running the routine
        for s in this.streams:
            s.stop_stream()
            s.start_stream()

        for i in range(len(this.streams)):
            # Apply the bandpass filter and write to global var
            this.buf_filtered[i] = butter_bandpass_filter(this.buf_copy[i], LPF, HPF, RATE, 3)

            # Get the delay relative to the first microphone
            this.delay_buffer[i][0] = get_time_shift(this.buf_filtered[0], this.buf_filtered[i], BUFFER, RATE, corr_lines[i][0] if corr_lines != None else None)
            this.delay_buffer[i] = roll(this.delay_buffer[i], 1)
            this.delay_avg[i] = average(this.delay_buffer[i])

            # Write voltage chart data
            this.voltage_data[i] = (this.buf_filtered[i] * 2.25) + 2.25

            # DEBUG print the buffer for use in offline mode
            #print("signal[%d] = %s" % (i, repr(buf_filtered[i]).replace("array(", "").replace(")", "")))

            # Extrapolate rolling average distance to be fed into trilateration
            if this.calibration_mode or USE_MACHINE_LEARNING:
                this.amplitude_buffer[i][0] = max(this.buf_filtered[i]) # Also enable the mic cal line below
            else:
                this.amplitude_buffer[i][0] = MIC_CAL[i](max(this.buf_filtered[i]))
            
            this.amplitude_buffer[i] = roll(this.amplitude_buffer[i], 1)
            this.amplitude_avg[i] = average(this.amplitude_buffer[i])

        # print average amplitudes
        #amplitude_avg[-1] = average(amplitude_avg[0:-1])    # Calculate overall average
        #print("ampl_avg: %.4f" % (amplitude_avg[-1]))

        # Print raw microphone calibration line
        if this.calibration_mode:
            pass
            #print("M1: %.4f, M2: %.4f, M3: %.4f" % (this.amplitude_avg[0], this.amplitude_avg[1], this.amplitude_avg[2]))

        # Print info line
        else:
            if USE_MACHINE_LEARNING:
                # Predict using machine learning
                this.x, this.y, this.z = predict([this.amplitude_avg[0], this.amplitude_avg[1], this.amplitude_avg[2]])[0]
            else:
                # Calcuate using trilateration
                (this.x, this.y, this.z) = trilateration(this.amplitude_avg[0], this.amplitude_avg[2], this.amplitude_avg[1], FIXT_D, FIXT_E, FIXT_F)

                # Move the origin to the center of the fixture
                this.x -= FIXT_E
                this.y -= FIXT_MIC_RADIUS/2


            if not OFFLINE_MODE:
                # Test fixture is 342.9 mm + 80.7 mm + 24 mm = X0 Y447.6 Z56
                sendCommand(ser, "G1 X%.2f Y%.2f Z%.2f" % (this.x, this.y + 447.6, this.z + 56), "\rsh$ ")

            print("x: %4.0f, y: %4.0f, z: %4.0f, (r1: %3.0f, r2: %3.0f, r3: %3.0f), d1: %5.2f, d2: %5.2f, d3: %5.2f" % (this.x, this.y, this.z, this.amplitude_avg[0], this.amplitude_avg[1], this.amplitude_avg[2], this.delay_avg[0], this.delay_avg[1], this.delay_avg[2]))
        


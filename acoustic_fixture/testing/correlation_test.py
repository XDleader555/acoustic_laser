#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" correlation_test.py: time analysis using correlation
    This file uses freeze frame data extracted from the acoustic trilateration
    visualizer to better analyze the method for determining signal lags.
"""

__version__ = "1.0"

__author__ = "Andrew Miyaguchi"
__copyright__ = "Copyright 2021, Andrew Miyaguchi"
__license__ = "Apache 2.0"

from signal_data import test_signal
import matplotlib.pyplot as plt
import matplotlib.animation
from mpl_toolkits import mplot3d
from scipy import signal
import numpy

# Defininitions
RATE = 44100
BUFFER = 882    # RATE must be evenly divisible by BUFFER
REFRESH_RATE = int(1/RATE*BUFFER*1000)

LPF = 400
HPF = 480

DECAY_MS = 5000 # Set to 0 to disable decay
DECAY_SIZE = int(DECAY_MS/RATE*BUFFER)

AMPLITUDE_MS = 500
AMPLITUDE_SIZE = int(AMPLITUDE_MS/RATE*BUFFER)

PLOT_XMAX = RATE/2+1
mic_dict = {"Mosquito 1":[-1, ""], "Mosquito 2":[-1, ""], "Mosquito 3":[-1, ""]}

# Microphone properties
MIC_VREF = 2.25 # ADC reference voltage
MIC_SENS_DBV = -47 # Microphone sensitivity dBV/Pa
MIC_GAIN = 20
VREF_RMS = 10**(MIC_SENS_DBV/20) # VRMS/Pa

# Global variables
freq_range = range(0,int(RATE/2+1),int(RATE/BUFFER))
time_range = numpy.arange(0, int(1/RATE*BUFFER*1000), 1/RATE*1000)
l = len(freq_range)

decay_buffer = []
decay_avg = []

# Set the plot theme
plt.rcParams.update({
    "lines.color": "white",
    "patch.edgecolor": "white",
    "text.color": "white",
    "axes.facecolor": "1e1e1e",
    "axes.edgecolor": "lightgray",
    "axes.labelcolor": "white",
    "xtick.color": "white",
    "ytick.color": "white",
    "grid.color": "lightgray",
    "figure.facecolor": "1e1e1e",
    "figure.edgecolor": "1e1e1e",
    "savefig.facecolor": "1e1e1e",
    "savefig.edgecolor": "1e1e1e",
    "figure.figsize": (16, 6)})

# Generate chart layouts and axs arrays
fig, all_axs = plt.subplots(len(mic_dict), 3)

# Build specific axes arrays
spectrum_axs = [axs[0] for axs in all_axs]   # First column
voltage_axs = [axs[1] for axs in all_axs]    # Second column
corr_axs = [axs[2] for axs in all_axs]    # Third column


matplotlib.pyplot.get_current_fig_manager().window.wm_iconbitmap("./res/mosquito.ico")
fig.canvas.manager.set_window_title("Acoustic Acquisition System")

for i in range(0, len(spectrum_axs)):
    ax = spectrum_axs[i]
    ax.set(xlabel='Frequency', ylabel='dB SPL')
    ax.set_xlim(0, PLOT_XMAX)
    ax.set_ylim(-60, 60)
    ax.set_title("%s Spectrum" % (list(mic_dict.keys())[i]))
    ax.grid()
    ax.plot([],[])[0] # Process Value line
    ax.plot([],[])[0] # Max Value line

for i in range(0, len(voltage_axs)):
    ax = voltage_axs[i]
    ax.set(xlabel='Time (ms)', ylabel='Volts')
    ax.set_xlim(0, max(time_range))
    ax.set_ylim(MIC_VREF - 0.1, MIC_VREF + 0.1)
    ax.set_title("%s Voltage %d Hz to %d Hz bandpass" % (list(mic_dict.keys())[i], LPF, HPF))
    ax.grid()
    ax.plot([],[])[0] # Voltage line

for i in range(0, len(corr_axs)):
    ax = corr_axs[i]
    ax.set(xlabel='Lag (ms)', ylabel='Correlation Coeff')
    ax.set_xlim(-10, 10)
    ax.set_ylim(-1, 1)
    ax.set_title("%s to %s correlation. Delay = %.2f ms" % (list(mic_dict.keys())[i], list(mic_dict.keys())[0], 0))
    ax.grid()
    ax.plot([],[])[0] # Voltage line

# Build line arrays
spectrum_lines = [ax.get_lines() for ax in spectrum_axs]
voltage_lines = [ax.get_lines() for ax in voltage_axs]
corr_lines = [ax.get_lines() for ax in corr_axs]
all_lines = [line for ax in all_axs.flat for line in ax.get_lines()]

# Fix padding issues
fig.tight_layout()

## get_time_shift
# Find the time delay between two signals using correlation. The lag with the
# highest coefficient is when the two signals best overlap.
# https://stackoverflow.com/questions/41492882/find-time-shift-of-two-signals-using-cross-correlation/56432463
#
# @param  s1 signal 1
# @param  s2 signal 2
# @param  n  buffer size
# @param  sr sampling rate
# @return s2 delay
def get_time_shift(s1, s2, n=BUFFER, sr=RATE, line=None):
    # Get the correlation of s2 to s1, to the ratio of s2/s1
    corr = signal.correlate(s2, s1, mode='same') / numpy.sqrt(signal.correlate(s1, s1, mode='same')[int(n/2)] * signal.correlate(s2, s2, mode='same')[int(n/2)])

    # Find the delay
    delay_arr = numpy.linspace(-0.5*n/sr*1000, 0.5*n/sr*1000, n)
    delay = delay_arr[numpy.argmax(corr)]
    print("Delay: %.2f ms" % (delay))

    if line != None:
        line.set_data(delay_arr, corr)
    
    return delay

# Initialization function
def init_line():
    for line in all_lines:
        try:
            line.set_data(freq_range, [-1000]*l)
        except AttributeError:
            pass

    for i in range(len(corr_axs)):
        delay = get_time_shift(test_signal[0], test_signal[i], line=corr_lines[i][0])
        corr_axs[i].set_title("%s to %s correlation. Delay = %.2f ms" % (list(mic_dict.keys())[i], list(mic_dict.keys())[0], delay))

    return all_lines

def update_line(i):
    global decay_buffer
    global decay_avg

    # Iterate through each microphone
    for i in range(0, len(test_signal)):
        voltage_line = voltage_lines[i][0]
        pv_line = spectrum_lines[i][0]

        # Write voltage chart data
        data = [(x * 2.25) + 2.25 for x in test_signal[i]]
        voltage_line.set_data(time_range, data)

        # Apply the fast fourier transform for the pretty output
        data = numpy.fft.rfft(test_signal[i])

        # TODO: Convert to decibels
        vin_rms_fft = numpy.sqrt(numpy.real(data)**2+numpy.imag(data)**2) / BUFFER
        data_db_fft = 20 * numpy.log10(vin_rms_fft/VREF_RMS)
        data_db_spl_fft = MIC_SENS_DBV + data_db_fft + 94 - MIC_GAIN

        # Write spectrum chart data
        pv_line.set_data(freq_range, data_db_spl_fft)

    # return all lines to be updated
    return all_lines

line_ani = matplotlib.animation.FuncAnimation(
    fig, update_line, init_func=init_line, interval=REFRESH_RATE, blit=True
)

plt.show()
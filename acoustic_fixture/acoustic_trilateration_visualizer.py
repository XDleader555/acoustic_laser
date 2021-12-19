#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" acoustic_trilateration_visualizer.py: Visualize the data from the acoustic fixture
    Visualizer based off https://gist.github.com/netom/8221b3588158021704d5891a4f9c0edd
"""

__version__ = "1.0"

__author__ = "Andrew Miyaguchi"
__copyright__ = "Copyright 2021, Andrew Miyaguchi"
__license__ = "Apache 2.0"

from numpy import zeros, arange, roll, average, fft, sqrt, imag, log10, real, isnan
import matplotlib.pyplot as plt
import matplotlib.animation

from acoustic_fixture import AcousticFixture as AF, RATE, BUFFER, LPF, HPF
from trilateration_linear_regression_model import training_input, training_output

REFRESH_RATE = int(1/RATE*BUFFER*1000)
PLOT_XMAX = RATE/2+1
DECAY_MS = 1000 # Set to 0 to disable decay
DECAY_SIZE = int(DECAY_MS/RATE*BUFFER)

# https://www.analog.com/en/analog-dialogue/articles/understanding-microphone-sensitivity.html
# https://electronics.stackexchange.com/questions/96205/how-to-convert-volts-to-db-spl

# Microphone properties
MIC_VREF = 2.25 # ADC reference voltage
MIC_SENS_DBV = -47 # Microphone sensitivity dBV/Pa
MIC_GAIN = 20
VREF_RMS = 10**(MIC_SENS_DBV/20) # VRMS/Pa

# Global variables
af = AF()
freq_range = range(0,int(RATE/2+1),int(RATE/BUFFER))
time_range = arange(0, int(1/RATE*BUFFER*1000), 1/RATE*1000)
decay_buffer = []
decay_avg = []

for i in range(len(af.mic_dict)):
    decay_avg.append([])
    decay_buffer.append([])
    for j in range(len(freq_range)):
        decay_avg[i].append(-100)
        decay_buffer[i].append(zeros(DECAY_SIZE))


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
    "figure.figsize": (19, 6)})

# Generate chart layouts and axs arrays
fig, all_axs = plt.subplots(len(af.mic_dict), 5)
fig.canvas.manager.window.wm_geometry("+%d+%d" % (0, 0))

# Build specific axes arrays
spectrum_axs = [axs[0] for axs in all_axs]   # First column
voltage_axs = [axs[1] for axs in all_axs]    # Second column
corr_axs = [axs[2] for axs in all_axs]      # Third column
#ml_axs = [axs[3] for axs in all_axs]      # Fourth column

# Combine third column into big plot
for axs in all_axs:
    axs[-2].remove()
    axs[-1].remove()

gs = all_axs[0,-2].get_gridspec()

coord_ax = fig.add_subplot(gs[0:,-2:], projection='3d')

matplotlib.pyplot.get_current_fig_manager().window.wm_iconbitmap("./res/mosquito.ico")
fig.canvas.manager.set_window_title("Acoustic Acquisition System")

for i in range(0, len(spectrum_axs)):
    ax = spectrum_axs[i]
    ax.set(xlabel='Frequency', ylabel='dB SPL')
    ax.set_xlim(0, PLOT_XMAX)
    ax.set_ylim(-60, 60)
    ax.set_title("%s Spectrum" % (list(AF.mic_dict.keys())[i]))
    ax.grid()
    ax.plot([],[])[0] # Process Value line
    ax.plot([],[])[0] # Max Value line

for i in range(0, len(voltage_axs)):
    ax = voltage_axs[i]
    ax.set(xlabel='Time (ms)', ylabel='Volts')
    ax.set_xlim(0, max(time_range))
    ax.set_ylim(MIC_VREF - 0.1, MIC_VREF + 0.1)
    ax.set_title("%s Voltage %d Hz to %d Hz bandpass" % (list(AF.mic_dict.keys())[i], LPF, HPF))
    ax.grid()
    ax.plot([],[])[0] # Voltage line

for i in range(0, len(corr_axs)):
    ax = corr_axs[i]
    ax.set(xlabel='Lag (ms)', ylabel='Correlation Coeff')
    ax.set_xlim(-10, 10)
    ax.set_ylim(-1, 1)
    ax.set_title("%s to %s correlation" % (list(AF.mic_dict.keys())[i].replace("Mosquito ", "M"), list(AF.mic_dict.keys())[0].replace("Mosquito ", "M")))
    ax.grid()
    ax.plot([],[])[0] # Correlation Line


# for i in range(0, len(ml_axs)):
#     ax = ml_axs[i]
#     ax.set(xlabel='distance (mm)', ylabel='amplitude (raw)')
#      ax.set_xlim(-10, 10)
#     # ax.set_ylim(-1, 1)
#     ax.set_title("%s ML Prediction" % (list(AF.mic_dict.keys())[i].replace("Mosquito ", "M")))
#     ax.grid()
#     ax.plot([],[])[0] # Machine Learning Line

# Limit the chart to data we care about
COORD_LIM = 150

coord_ax.set(xlabel='x (mm)', ylabel='y (mm)', zlabel='z (mm)')
coord_ax.set_xlim(-COORD_LIM, COORD_LIM)
coord_ax.set_ylim(-COORD_LIM, COORD_LIM)
coord_ax.set_zlim(0, 200)
coord_ax.set_title("Acoustic Trilateration")
coord_line, = coord_ax.plot([],[],[], linestyle="", marker="o")

# Build line arrays
spectrum_lines = [ax.get_lines() for ax in spectrum_axs]
voltage_lines = [ax.get_lines() for ax in voltage_axs]
corr_lines = [ax.get_lines() for ax in corr_axs]
all_lines = [line for ax in all_axs.flat for line in ax.get_lines()]
all_lines = all_lines + [coord_line]

# Fix padding issues
fig.tight_layout()

# Initialization function
def init_line():
    for line in all_lines:
        try:
            line.set_data(freq_range, [-1000] * len(freq_range))
        except AttributeError:
            pass

    return all_lines

# Update function
def update_line(line_idx):
    global decay_buffer
    global decay_avg

    # Write the data to the charts
    af.update(corr_lines)

    for mic in range(len(af.streams)):
        voltage_line = voltage_lines[mic][0]
        pv_line = spectrum_lines[mic][0]
        max_line = spectrum_lines[mic][1]

        voltage_line.set_data(time_range, af.voltage_data[mic])

        # Apply the fast fourier transform to the unfiltered data for the pretty output
        data = fft.rfft(af.buf_copy[mic].copy())

        # TODO: Convert to decibels
        vin_rms_fft = sqrt(real(data)**2+imag(data)**2) / BUFFER
        data_db_fft = 20 * log10(vin_rms_fft/VREF_RMS)
        data_db_spl_fft = MIC_SENS_DBV + data_db_fft + 94 - MIC_GAIN

        # Max Decay logic
        for freq in range(len(freq_range)):
            if DECAY_MS == 0:
                # Ignore the average calculation
                if data_db_spl_fft[freq] > decay_avg[mic][freq]:
                    decay_avg[mic][freq] = data_db_spl_fft[freq]
                continue
            elif data_db_spl_fft[freq] > decay_avg[mic][freq]:
                # Set all values to max and then average
                decay_buffer[mic][freq][:] = data_db_spl_fft[freq]
            else:
                # Add the value to the buffer and roll the values
                decay_buffer[mic][freq][0] = data_db_spl_fft[freq]
                decay_buffer[mic][freq] = roll(decay_buffer[mic][freq], 1)
            
            # average the values
            decay_avg[mic][freq] = average(decay_buffer[mic][freq])

        # Write spectrum chart data
        pv_line.set_data(freq_range, data_db_spl_fft)
        max_line.set_data(freq_range, decay_avg[mic])
    
    if not isnan(af.z):
        coord_line.set_data_3d([af.x], [af.y], [af.z])

    # return all lines to be updated
    return all_lines

line_ani = matplotlib.animation.FuncAnimation(
    fig, update_line, init_func=init_line, interval=REFRESH_RATE, blit=True
)

plt.show()
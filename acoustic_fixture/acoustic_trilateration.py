#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" acoustic_trilateration.py: custom functions used for trilateration"""

__version__ = "1.0"

__author__ = "Andrew Miyaguchi"
__copyright__ = "Copyright 2021, Andrew Miyaguchi"
__license__ = "Apache 2.0"

import numpy
from scipy.signal import butter, lfilter
from scipy import signal

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
def get_time_shift(s1, s2, n, sr, line=None):
	# Get the correlation of s2 to s1, to the ratio of s2/s1
	corr = signal.correlate(s2, s1, mode='same') / numpy.sqrt(signal.correlate(s1, s1, mode='same')[int(n/2)] * signal.correlate(s2, s2, mode='same')[int(n/2)])

	# Find the delay
	delay_arr = numpy.linspace(-0.5*n/sr*1000, 0.5*n/sr*1000, n)
	delay = delay_arr[numpy.argmax(corr)]
	#print("Delay: %.2f ms" % (delay))

	if line != None:
		line.set_data(delay_arr, corr)
	
	return delay

# Butter bandpass filters
def butter_bandpass(lowcut, highcut, fs, order=5):
	nyq = 0.5 * fs
	low = lowcut / nyq
	high = highcut / nyq
	b, a = butter(order, [low, high], btype='band')
	return b, a

# use lfilter instead of filtfilt. shifted by one phase, but requires less processessing
def butter_bandpass_filter(data, lowcut, highcut, fs, order=5):
	b, a = butter_bandpass(lowcut, highcut, fs, order=order)
	y = lfilter(b, a, data) 
	return y

# Intersection of three spheres
# https://demonstrations.wolfram.com/TrilaterationAndTheIntersectionOfThreeSpheres/
# http://wiki.gis.com/wiki/index.php/Trilateration
def trilateration(r1, r2, r3, d, e, f):
	x = (r1**2 - r2**2 + d**2)/(2*d)
	y = (e**2 + f**2 + r1**2 - r3**2)/(2*f) - ((e/f)*x)
	z = (r1**2 - x**2 - y**2)**(1/2)

	return (x, y, z)
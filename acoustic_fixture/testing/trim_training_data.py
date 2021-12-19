#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" trim_training_data.py - I screwed up and this is how I fix the data
    It takes 1 hour to aquire 3 runs of training data, so it's more cost effective
    to write a script to fix the data rather than re-aquiring it.
"""

__version__ = "1.0"

__author__ = "Andrew Miyaguchi"
__copyright__ = "Copyright 2021, Andrew Miyaguchi"
__license__ = "Apache 2.0"

import pickle
from acoustic_fixture import BUFFER

# Load the training data
data = pickle.load(open("training_data.db", 'rb'))
trimmed_data = {}

n = 0

for key in data:
    print("Unpacking data for (%d, %d, %d)" % key)

    if key not in trimmed_data:
        trimmed_data[key] = []
    
    # Merge the arrays
    buf = [[],[],[]]
    for d in data[key]:
        buf[0].append(d[0])
        buf[1].append(d[1])
        buf[2].append(d[2])
    trimmed_data[key].append(buf)
    
print("Processed %d datapoints" % (n))

# dump the data to be used in training
pickle.dump(trimmed_data, open("training_data_trimmed.db", "wb"))
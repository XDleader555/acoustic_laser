#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" trilateration_linear_regression_model.py: linear regression for multioutput regression"""

__version__ = "1.0"

__author__ = "Andrew Miyaguchi"
__copyright__ = "Copyright 2021, Andrew Miyaguchi"
__license__ = "Apache 2.0"

from sklearn.linear_model import LinearRegression
from sklearn.neighbors import KNeighborsRegressor
from sklearn.tree import DecisionTreeRegressor
from acoustic_trilateration import butter_bandpass_filter
import pickle

RATE = 44100
BUFFER = 882    # RATE must be evenly divisible by BUFFER
LPF = 400
HPF = 480

LOAD_MODEL = 1

model = LinearRegression()
training_input = []
training_output = []


if LOAD_MODEL:
    model = pickle.load(open("model.obj", "rb"))
    training_input = pickle.load(open("training_input.obj", "rb"))
    training_output = pickle.load(open("training_output.obj", "rb"))
else:
    data = pickle.load(open("training_data.db", "rb"))

    n_samples = 0

    for key in data:
        for buf in data[key]:
            training_input.append([max(butter_bandpass_filter(mic, LPF, HPF, RATE, 3)) for mic in buf])
            training_output.append(list(key))
            n_samples += 1

    print("Loaded %d samples" % (n_samples))

    #print(training_input)
    #print(training_output)

    # define and fit the model
    model.fit(training_input, training_output)

    # export the model
    pickle.dump(model, open("model.obj", "wb"))
    pickle.dump(training_input, open("training_input.obj", "wb"))
    pickle.dump(training_output, open("training_output.obj", "wb"))

# make a prediction
#row = [0.50249434, 1.14472371, 0.90159072]
#yhat = model.predict([row])

# summarize prediction
#print(yhat[0])

def predict(arr):
    return model.predict([arr])
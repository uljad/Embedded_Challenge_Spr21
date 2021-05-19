import serial
import csv
import threading
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from uncertainties import ufloat

DATA_PER_SECOND = 100 
TOP_PRESSURE    = 120
BOTTOM_PRESSURE = 60
BAUD_RATE       = 9600
MOV_AVG_WINDOW  = 100
SER_PORT        = "COM12"

raw = serial.Serial(SER_PORT,BAUD_RATE)

data_array = []


def threading_():
    t1 = threading.Thread(target=compute_slope)
    t1.start()


def compute_slope(x, y):
    slope = abs(x - y);
    if slope > 5:
        print("Deflation rate is too high: ", slope)
    elif slope < 2:
        print("Deflation rate is too low: ", slope)
    return


def write_csv():
    with open('yusuf2.csv', 'w', newline='') as myfile:
        wr = csv.writer(myfile, quoting=csv.QUOTE_ALL)
        wr.writerow(data_array)


def read_csv():
    global data_array
    with open('data2.csv', newline='') as f:
        reader = csv.reader(f)
        for row in reader:
            data_array = row
        data_array = list(map(float, data_array))


def get_index(data):
    max_index = data.index(max(data))
    slice=data[max_index:None]

    indx_min = data.index(list(filter(lambda i: i < TOP_PRESSURE, slice))[0])
    indx_max = data.index(list(filter(lambda i: i < BOTTOM_PRESSURE, slice))[0])

    return indx_min,indx_max


def bpm(data):
    time_s = len(data)/DATA_PER_SECOND
    beat_per_second = len(np.where(np.diff(np.sign(data)))[0]) / ( 2 * time_s) 
    return (beat_per_second * 60) 


def sbp_dbp(data, min_, max_):
    mv_mn   = mov_mean[min_:max_]
    d_diff  = data[min_:max_]
    t_max   = max(d_diff)

    idx     = d_diff.index(t_max)
    
    map     = mv_mn[idx]
    print("MAP: ", map) 

    sbp_point     = 0.45 *t_max
    dbp_point     = 0.8 * t_max

    sbp_idx = d_diff.index(list(filter(lambda i: i > sbp_point, d_diff))[0])
    

    rev_d_diff = d_diff
    rev_d_diff.reverse()
    dbp_idx = rev_d_diff.index(list(filter(lambda i: i > dbp_point, rev_d_diff))[0])

    sbp = mv_mn[sbp_idx]
    mv_mn = np.flip(mv_mn)
    dbp = mv_mn[dbp_idx]
    u_sbp   = 0.1 * sbp
    u_dbp   = 0.12 * dbp

    return sbp,u_sbp,dbp,u_dbp



try:
    while True:
        if ( raw.in_waiting > 0 ):
            data_array.append( float(raw.readline().decode('utf-8')) )
            if ( len(data_array) < 100 ):
                compute_slope(data_array[-1], data_array[0])
            else:
                compute_slope(data_array[-1], data_array[len(data_array) - DATA_PER_SECOND])
            print("Current Pressure: ", data_array[-1]) 
except KeyboardInterrupt:
    pass


write_csv();

mov_mean = np.convolve(data_array, np.ones(MOV_AVG_WINDOW)/MOV_AVG_WINDOW, mode='same')
data_diff = [a - b for a, b in zip(data_array, mov_mean)];

min_,max_ = get_index(data_array)
print("BPM: ", bpm(data_diff[min_:max_]))

sbp,u_sbp,dbp,u_dbp = sbp_dbp(data_diff, min_, max_) 
print("SBP: ", ufloat(sbp, u_sbp))
print("DBP: ", ufloat(dbp, u_dbp))

plt.plot(mov_mean[min_:max_],data_diff[min_:max_])
#plt.plot(data_array)
plt.grid()
plt.show() 


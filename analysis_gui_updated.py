import sys
import csv
import time
import serial
import threading
import numpy as np
import matplotlib.pyplot as plt
from uncertainties import ufloat
from scipy.signal import find_peaks, butter, lfilter

from tkinter.ttk import *
import tkinter as tk
from ctypes.wintypes import MSG, SERVICE_STATUS_HANDLE
from tkinter import OptionMenu, StringVar, messagebox




###############################################################################################################################################################
################################################### INIT GUI ##################################################################################################
###############################################################################################################################################################

bg_color = "#34495E"
root = tk.Tk()
root.title("Embedded Challenge 2021") 
root.geometry('700x600') 
root.resizable(0, 0)
root.configure(background=bg_color)

tk.Label(
            root, 
            text='Embedded Challenge 2021 @ Copyright', 
            bg=bg_color,
            font=('calibri', 10), 
            fg='white').pack(side='bottom'
        )
frame = tk.Frame(root, bg="white")
frame.place(relwidth=0.9, relheight=0.9, relx=0.05, rely=0.05)

style = Style()
style.theme_use('classic')
style.configure(
                'TButton',
                font=('calibri', 15),
                borderwidth='0',
                background=bg_color,
                foreground="white",
                width=30
                )
style.map(
            'TButton', 
            foreground=[('active', bg_color)], 
            background=[('active', '#DDE2ED')]
         )

###############################################################################################################################################################
################################################### INIT GUI END###############################################################################################
###############################################################################################################################################################


# -*- coding: utf-8 -*-
'''
GLOBAL VARIABLES:
    DATA_PER_SECOND : Frequecy of data collection
    TOP_PRESSURE    : End point for seraching for SBB, MAP, and DBP
    BOTTOM_PRESSURE : Start point for seraching for SBB, MAP, and DBP
    BAUD_RATE       : Baud rate
    MOV_AVG_WINDOW  : Moving avergge window
    MIN_PEAK_HEIGHT : Minimum height for peak to be considered a peak (found empirically)
    REALTIME        : Value of 0 reads from a csv file ; 1 reads realtime data from sensor
    SER_PORT        : Serial port number
'''
DATA_PER_SECOND = 100  
TOP_PRESSURE    = 120
BOTTOM_PRESSURE = 65
BAUD_RATE       = 9600
MOV_AVG_WINDOW  = 100
MIN_PEAK_HEIGHT = 0.7
REALTIME        = -1
SER_PORT        = "COM12"

# -- Connect to serial port
try:
    raw = serial.Serial(SER_PORT,BAUD_RATE)
except:
    raw = None
    print("Serial port could not be initialized. Try resetting the port.") 
    


# -- array of data points
data_array = []

# -- array of moving average
mov_mean = []

prev_time = 0

'''
ShowInfo    - info gui popup
MessageBox  - message popup
'''

def ShowInfo(label, message):
    messagebox.showinfo(label, message)
    return


def MessageBox(label, message):
    thrd = threading.Thread(target=ShowInfo, args=[label, message])
    thrd.start()
    return


def compute_slope(x, y):
    """ Deflation Rate
    
            Computes deflation rate and notifies the user of the 
            status of the defaltion rate.

    """
    global prev_time
    slope = abs(x - y);

    curr_time = int(round(time.time() * 1000))
    if curr_time - prev_time >= 1000 :
        prev_time = curr_time
        if slope > 6:
            print("Pressure change is too high: ", slope, " mmHg\n")
        elif slope < 2:
            print("Pressure change rate is too low: ", slope, " mmHg\n")
        else:
            print("Pressure change rate: ", slope, " mmHg\n") 
        return
    
    return


def write_csv(filename):
    """ Store Collected Data
    
            On pressing Ctrl+C to stop realtime measurements, this function writes 
            the data in data_array into a csv file with name filename.

    """
    with open(filename, 'w', newline='') as myfile:
        wr = csv.writer(myfile, quoting=csv.QUOTE_ALL)
        wr.writerow(data_array)
    return


def read_csv(filename):
    """ Read Stored Data
    
            This function reads in the data in filename into data_array.

    """
    global data_array
    with open(filename, newline='') as f:
        reader = csv.reader(f)
        for row in reader:
            data_array = row
        data_array = list(map(float, data_array)) 
    return


def get_index(data):
    """ Index of TOP_PRESSURE and BOTTOM_PRESSURE
    
            get_index gets the index of constants TOP_PRESSURE and BOTTOM_PRESSURE
            from the array passed into it.

    """
    max_index = data.index(max(data))
    data_slice=data[max_index:None]

    indx_min = data.index(list(filter(lambda i: i < TOP_PRESSURE, data_slice))[0])
    indx_max = data.index(list(filter(lambda i: i < BOTTOM_PRESSURE, data_slice))[0])

    return indx_min,indx_max


def bpm_crossing(data):
    """ Calculate Heart Rate
    
            This function calculates the heart rate using the number of zero crossings
            in the graph of data.

    """
    t = len(data)/DATA_PER_SECOND
    bps= len(np.where(np.diff(np.sign(data)))[0]) / ( 2 * t) 
    return (bps * 60) 


def bpm_peak(data , min_peak=MIN_PEAK_HEIGHT):
    """ Calculate Heart Rate
    
            This function calculates the heart rate using the number of valid peaks
            in the graph of data. 

    """
    t = len(data)/DATA_PER_SECOND
    bps = len(find_peaks(data, height=min_peak, distance=50)[0]) / t
    return (bps * 60) 


def peaks(data):
    """ Find Peaks
    
            This function returns the index of valid peaks (peaks greater than MIN_PEAK_HEIGHT)
            in the graph of data.

    """
    return find_peaks(data, height=MIN_PEAK_HEIGHT, distance=50)[0] 


def sbp_dbp(data, idmin, idmax):
    global mov_mean
    """ Find Peaks
    
            This function calculates and returns the initial estimated values of the MAP, SBP, DBP as well
            as the uncertainties in their estimation. It finds the maximum peak (MAP). It estimates the
            DBP by finding the first point where data is 0.8*MAP from the left of data. It estimates the
            DBP by finding the first point where data is 0.45*MAP from right of data.

    """
    mv_mn       = mov_mean[idmin:idmax]
    d_diff      = data[idmin:idmax]
    t_max       = max(d_diff)
    idx         = d_diff.index(t_max) 

    map_        = mv_mn[idx]
    print("MAP: ", map_) 

    sbp_pk     = 0.45 * t_max
    dbp_pk     = 0.80 * t_max

    sbp_idx = d_diff.index(list(filter(lambda i: i >= sbp_pk, d_diff))[0]) 

    rev_d_diff = d_diff
    rev_d_diff.reverse()
    idx = rev_d_diff.index(t_max)
    try:
        dbp_idx = rev_d_diff.index(list(filter(lambda i: i >= dbp_pk, rev_d_diff[:idx-50]))[0])
    except:
        dbp_idx = rev_d_diff.index(max(rev_d_diff[:idx-50]))

    sbp = mv_mn[sbp_idx]
    dbp = np.flip(mv_mn)[dbp_idx]
    u_sbp   = 0.10 * sbp
    u_dbp   = 0.12 * dbp

    return map_,sbp,u_sbp,dbp,u_dbp,sbp_pk,dbp_pk


def butter_bandpass(lowcut, highcut, fs, order=5):
    """ Find butterworth filter params
    
            This function calculates the parameters for a butterworth filter with the 
            given input params.

    """
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(order, [low, high], btype='band')
    return b, a


def butter_bandpass_filter(data, lowcut, highcut, fs, order=5):
    """ Bandpass filter data
    
            This function bandpass filters data using a butterworth filter with 
            characteristics set by the input parameters.

    """
    b, a = butter_bandpass(lowcut, highcut, fs, order=order)
    y = lfilter(b, a, data)
    return y.tolist()


def flatten_bottom(data):
    """ Compute peak-to-peak
    
            This function estimates and returns the peak-to-peak values of the oscillations
            in data.

    """
    n_data = [-x for x in data]
    min_idxs = find_peaks(n_data, height=0.3, distance=50)[0]
    for i in range(len(min_idxs) - 1):
        avg = (n_data[min_idxs[i]] + n_data[min_idxs[i+1]]) / 2
        data[min_idxs[i]:min_idxs[i+1]] = [ d+avg for d in data[min_idxs[i]:min_idxs[i+1]]]
    
    return data


"""
    If REALTIME == 1, the snippet in the try block collects realtime data from the microcontroller
    through the serial port. Else if REALTIME == 0, data is read from a csv file. Realtime data collection
    can be stopped by pressing Ctrl+C.
"""

stop_realtime = 0
def start1():
    global data_array
    global REALTIME
    global raw
    global stop_realtime
    data_array = [] 
    REALTIME = 1
    prev = 0
    if raw:
        if REALTIME:
            try:
                while not stop_realtime:
                    if ( raw.in_waiting > 0 ):
                        data_array.append( float(raw.readline().decode('utf-8')) )
                        if ( len(data_array) < 100 ):
                            compute_slope(data_array[-1], data_array[0])
                        else:
                            compute_slope(data_array[-1], data_array[len(data_array) - DATA_PER_SECOND])
                        
                        curr = int(round(time.time() * 1000))
                        if curr - prev >= 1000:
                            prev = curr
                            print("Current Pressure: ", data_array[-1]) 
            
                print("\n... Writing data to csv file ... \n") 
                write_csv(FILENAME) 
                stop_realtime = 0
            except Exception as e:
                print("(start) Something went wrong ", e )
                stop_realtime = 0
                sys.exit()
        else:
            try:
                print("\n... Reading data from csv file ... \n")
                read_csv("uljad2.csv") 
            except:
                print("Error reading from file or file does not exist")
                sys.exit()
    else:
        print("Serial port connection has not been established. Set the port correctly to establish a connection")
        MessageBox("Error", "Serial port connection has not been established. Set the port correctly to establish a connection") 

    return

FILENAME = "newdata.csv"
def process_and_display(filename=FILENAME):
    global data_array
    global mov_mean
    if not REALTIME:
        try:
            read_csv(filename)
        except:
            print("file does not exist")
            return
    
    try:
        # mov_mean is a moving average of the pressure data from the sensor (in mmHg). 
        mov_mean = np.convolve(data_array, np.ones(MOV_AVG_WINDOW)/MOV_AVG_WINDOW, mode='same')

        # data_diff is the difference the moving average and the raw pressure
        data_diff = [a - b for a, b in zip(data_array, mov_mean)];

        # see function get_index()
        min_,max_ = get_index(data_array) 


        print("\n Blood Pressure and Heart Rate data\n") 
        data_diff = butter_bandpass_filter(data_diff, 0.5, 5, DATA_PER_SECOND) 
        data_diff = flatten_bottom(data_diff)
        map_pk = max(data_diff[min_:max_])

        bpm = bpm_peak(data_diff[min_:max_])
        print("BPM: ", bpm) 
        map_,sbp,u_sbp,dbp,u_dbp,sbp_pk,dbp_pk = sbp_dbp(data_diff, min_, max_) 

        """
            The code snippet below adjust the value of SBP and DBP to the pressure of the closest peak 
            to the current SBP and DBP values.
        """
        pks = peaks(data_diff[min_:max_]) 
        max_indxs = [mov_mean[min_:max_][k] for k in pks] 

        c = [abs(k-sbp) for k in max_indxs]
        d = c.index(min(c))
        sbp = max_indxs[d]
        sbp_pk = data_diff[min_:max_][pks[d]]

        c = [abs(k-dbp) for k in max_indxs]
        d = c.index(min(c))
        dbp = max_indxs[d]
        dbp_pk = data_diff[min_:max_][pks[d]]

        for p in pks:
            plt.scatter(mov_mean[min_:max_][p],data_diff[min_:max_][p])

        print("SBP: ", ufloat(sbp, u_sbp))
        print("DBP: ", ufloat(dbp, u_dbp))

        f = plt.figure(1)
        plt.plot(mov_mean[min_:max_],data_diff[min_:max_],linewidth=2)
        plt.title("Processed blood pressure data")
        plt.xlabel("Pressure (mmHg)")
        plt.ylabel("Amplitude") 

        plt.axvline(x=sbp , color='r', linestyle='--')
        plt.axvline(x=dbp , color='r', linestyle='--')
        plt.axvline(x=map_, color='r', linestyle='--') 

        plt.annotate("DBP",(dbp  + .5, dbp_pk))
        plt.annotate("MAP",(map_ + .5, map_pk))
        plt.annotate("SBP",(sbp  + .5, sbp_pk))

        f.show() 

        MessageBox("Results", "\nHeart Rate (bpm): " + str(bpm) + "\n" + "DBP: " + str(ufloat(sbp, u_dbp)) + "\n" + "SBP: " + str(ufloat(sbp, u_sbp)) + "\n" ) 

        
    except Exception as e:
        print('(process_and_display) Something went wrong ', e)

    return

def stop():
    global stop_realtime
    stop_realtime = 1
    print("Realtime data collection stopped") 
    return

def read_from_file(filename, top):
    global REALTIME
    REALTIME = 0
    try:
        test = filename.get()
    except Exception as e:
        print("(read_from_file): ", e) 
        MessageBox("Error", "Invalid file name") 
        return
    file_name = filename.get()
    process_and_display(file_name) 

    return
    


def start():
    t1 = threading.Thread(target=start1)
    t1.start()
    return


def on_closing_root():
    global t1
    global t2 
    global stop_realtime
    stop_realtime = 1
    root.destroy()
    return



def get_filename():
    top = tk.Toplevel()
    top.title("Open File")
    top.geometry('400x200')
    top.resizable(0, 0)
    top.configure(background=bg_color)

    pad_x = 20
    pad_y = 20

    tk.Label(top, text="File Name",  font=('calibri', 13, 'bold'),
             background=bg_color, fg='white').grid(row=0, column=0, padx=pad_x, pady=pad_y)

    filename = tk.Entry(top, width=20, bg="white",
                         borderwidth=2, font=('calibri', 13))
    filename.grid(row=0, column=1, padx=pad_x, pady=pad_y)

    submit_btn = tk.Button(top, text="Visualize",
                           font=('calibri', 13), width=15,
                           background='#D1D5D7',
                           command=lambda: read_from_file(filename, top))
    submit_btn.grid(row=1, column=1, padx=pad_x, pady=pad_y)

    return


def save_file_name(filename, top):
    global FILENAME

    try:
        test = filename.get()
    except Exception as e:
        print("(save_file_name): ", e) 
        MessageBox("Error", "Invalid file name")
        return
    file_name = filename.get()

    FILENAME = file_name
    top.destroy()
    return


def set_filename():
    top = tk.Toplevel()
    top.title("New Data File Name") 
    top.geometry('400x200')
    top.resizable(0, 0)
    top.configure(background=bg_color)

    pad_x = 20
    pad_y = 20

    tk.Label(top, text="File Name",  font=('calibri', 13, 'bold'),
             background=bg_color, fg='white').grid(row=0, column=0, padx=pad_x, pady=pad_y)

    filename = tk.Entry(top, width=20, bg="white",
                         borderwidth=2, font=('calibri', 13))
    filename.grid(row=0, column=1, padx=pad_x, pady=pad_y)

    submit_btn = tk.Button(top, text="Save",
                           font=('calibri', 13), width=15,
                           background='#D1D5D7',
                           command=lambda: save_file_name(filename, top))
    submit_btn.grid(row=1, column=1, padx=pad_x, pady=pad_y)

    return

def set_port():
    global raw
    if not raw:
        try:
            raw = serial.Serial(SER_PORT, BAUD_RATE)
        except Exception as e:
            print("(set_port)(exception): ", e)
            MessageBox("Error", "Cannot connect to this port. Make sure port is available and port number is entered correctly")
            return -1
    return 0


def save_port(port_no, top):
    global SER_PORT

    try:
        test = port_no.get()
    except Exception as e:
        print("(save_port): ", e)
        MessageBox("Error", "Cannot set port. Make sure the entry is not blank")
        return

    port = port_no.get()

    SER_PORT = port
    x = set_port()

    if x == 0:
        print("(save_port): port successfully updated by user to ", SER_PORT)  

    top.destroy()

    return

def get_port():
    top = tk.Toplevel()
    top.title("Serial Port Address ( e.g COM7 )")
    top.geometry('400x200') 
    top.resizable(0, 0)
    top.configure(background=bg_color)

    pad_x = 20
    pad_y = 20

    tk.Label(top, text="Port Address",  font=('calibri', 13, 'bold'),
             background=bg_color, fg='white').grid(row=0, column=0, padx=pad_x, pady=pad_y)

    port_addr = tk.Entry(top, width=20, bg="white",
                       borderwidth=2, font=('calibri', 13))
    port_addr.grid(row=0, column=1, padx=pad_x, pady=pad_y)

    submit_btn = tk.Button(top, text="Set Port",
                           font=('calibri', 13), width=15,
                           background='#D1D5D7',
                           command=lambda: save_port(port_addr, top)) 
    submit_btn.grid(row=1, column=1, padx=pad_x, pady=pad_y)

    return

''' padding for the GUI buttons'''
pad_x = 100
pad_y = 15

WIDTH = 40
start_btn            = Button(
                            frame, 
                            text="START REALTIME MEASUREMENT",
                            command=start, 
                            width=WIDTH)
stop_btn            = Button(
                            frame, 
                            text="STOP REALTIME MEASUREMENT",
                            command=stop, 
                            width=WIDTH)
disp_btn            = Button(
                            frame, 
                            text="VISUALIZE LAST RECORDED DATA",
                            command=process_and_display, 
                            width=WIDTH)                            
rdfile_btn          = Button(
                            frame, 
                            text="VISUALIZE DATA FROM FILE",
                            command=get_filename, 
                            width=WIDTH)

setfile_btn         = Button(
                            frame, 
                            text="SET FILE NAME FOR NEW DATA",
                            command=set_filename, 
                            width=WIDTH) 
port_btn            = Button(
                            frame, 
                            text="ENTER MICROCONTROLLER PORT NUMBER",
                            command=get_port, 
                            width=WIDTH) 

start_btn.grid(row=0, column=0, pady=pad_y, padx=pad_x)
stop_btn.grid(row=1, column=0, pady=pad_y, padx=pad_x)
disp_btn.grid(row=2, column=0, pady=pad_y, padx=pad_x)
rdfile_btn.grid(row=3, column=0, pady=pad_y, padx=pad_x)
setfile_btn.grid(row=4, column=0, pady=pad_y, padx=pad_x)
port_btn.grid(row=5, column=0, pady=pad_y, padx=pad_x) 

root.protocol("WM_DELETE_WINDOW", on_closing_root)

root.mainloop()
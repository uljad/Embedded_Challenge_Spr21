import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import serial

'''
Embedded Systems Challenge Spring 2021
Uljad Berdica (ub352)
Yusuf Jimoh Omotayo (yoj202)

instructions: OPEN THE PLOT WINDOWS IN FULL SCREEN FOR PROPER VIEWING EXPERIENCE
'''

fig, ax = plt.subplots() #setting up figure
line, = ax.plot(np.random.rand(10)) #setting line
ax.set_ylim(0, 200) #pressure limit cause a human arm cannot stand more than 200    
ax.set_xlim(0,400) #xlimit for the first 400 measurements before first update
xdata=[]
ydata=[]
raw = serial.Serial("COM17",9600) #start the pyserial object to get raw bits
# bytesize is EIGHTBIT

#write to txt file just in case
def write_file(name,mode):
    #using context manager to save resources and time
    with open(name,mode)as f:
        f.write(raw.readline().decode('utf-8'))

def animate(data): #animate the frame
    t,y = data
    xdata.append(t) #append data
    ydata.append(y)
    line.set_color('r') #set color
    line.set_fillstyle('full') #can be :full, left, right,bottom
    plt.xticks(rotation=30, ha='right') #making sure everything is properly spaces
    plt.xticks(np.arange(0, 400, 10)) #xlabel tick frequency, step of 10
    plt.yticks(np.arange(0,200,10)) #ylabel tick frequency
    plt.subplots_adjust(bottom=0.20) #make sure it looks decent on full screen
    plt.ylabel("Pressure in mmHg") #Y axis label
    plt.xlabel("Index") #x axis label
    plt.title("Presssure Reading from Sensor") #title
    #if data exceed the heuristic 400 limit
    if (len(xdata)>400):
        ax.set_xlim(0,len(xdata)+10) #expand limit
        plt.xticks(np.arange(0, len(xdata), 10)) #update tick frequency
    line.set_data(xdata, ydata) #draw line 
    # plt.text(365,205,'Last Pressure: '+str(ydata[-1]))
    return line,

def prepare_data(): #preparing pressure value and its index
    t = 0
    while True:
        t+=1
        try:
            dat = int(raw.readline())
            write_file('data.txt','a')
        except:
            dat = -1
        yield t, dat



#animate to start the animation plot window
ani = animation.FuncAnimation(fig, animate, prepare_data, interval=0, blit=False)
plt.grid()
plt.show()


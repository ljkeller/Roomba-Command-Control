import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib
import time
import numpy as np
import socket
import threading
import turtle

#File: EmbeddedSystemsFinal.py
#An asynchronus socket based communication program that acts as a command base for the CprE Roomba Device. Has multithreaded send/receive functionality,
#Live data processing through the use of matplotlib and its animation function, parses several types of sensor data from the roomba, detects objects and their
#width/distance/angle, and uses the terminal for sending bytes to the bot.

#Author: Lucas Keller
#Date last modified 5/3/19
#Python Version: 3.7

matplotlib.use("TkAgg")
#A simple class designed for object detection from the roomba
class MineObject:
    def __init__(self):
        self.found_angle1 = False

    def angle_one(self, angle):
        self.starting_angle = angle
        self.found_angle1 = True

    def angle_two(self, angle):
        self.ending_angle = angle
        self.theta_total = (
                    self.ending_angle - self.starting_angle - 1)  # Two tracks accuracy lost from nature of scanning every two degrees
        self.theta_mid = (self.starting_angle + self.ending_angle) / 2
        self.found_angle1 = False
        print(self.theta_total)

    def set_distance(self, distance_object):
        self.distance_cm = distance_object
        self.width_cm = np.sqrt(2*distance_object**2-2*distance_object**2*np.cos(current_mine.theta_total*np.pi/180))


    def print_Mine_info(self):
        print(
            f'\r\nObject at angle {self.theta_mid} degrees, with width {self.width_cm:.2f} cm and distance {self.distance_cm} cm')
        self.distance_cm = 0
        self.theta_mid = 0
        self.starting_angle = 0
        self.ending_angle = 0



# Helper function for sending chars to roomba
def send_char():
    while True:
        char = input("Enter a character")
        s.send(bytes(char.encode('utf_8'))) #Sends UTF8 encoded bytes to roomba for controlling bot


# Function that reads from data stream one line at a time
def read_line():
    for line in file: #Abstracts steam into file and reads line by line
        if len(line.split()) == 3: #If receiving live scanning data
            theta, ir, snr = line.split()
            return float(theta), float(ir), float(snr)
        elif len(line.split()) > 3: #If receiving bump/cliff/edge detector data
            print("")
            print(line)
            return -1, -1, -1 #Returning -1 values so that can interpret data differently


# Initialize threading
t1 = threading.Thread(target=send_char)

polar_read = plt

# Set gridlines
plt.rc('grid', color='#316931', linewidth=1, linestyle='-')
plt.rc('xtick', labelsize=15)
plt.rc('ytick', labelsize=15)

plt.title('Active Scan')

# Set up figure
fig = plt.figure(figsize=(8, 8))
ax = fig.add_axes([0.1, 0.1, 0.8, 0.8], projection='polar', facecolor='k')
ax.set_xticks(np.pi / 180. * np.linspace(0, 180, 9))

# Initialize socket connection with roomba
TCP_IP = '192.168.1.1'
TCP_PORT = 288
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((TCP_IP, TCP_PORT))

# Initialize send functionality with roomba
t1.start()

# Begin streaming data from roomba
file = s.makefile()

# initialize lists
ir_distance = []
angle = []
sonar_distance = []

# Prepare to find mines
current_mine = MineObject()


def animate(i, angle, ir_distance, sonar_distance, current_mine):
    cur_angle, cur_ir, cur_snr = read_line() #Read line from roomba

    #If data from roomba is not in scan phase
    if cur_angle > -1:
        angle.append(cur_angle * np.pi / 180)
        ir_distance.append(min(cur_ir, 80))
        sonar_distance.append(min(cur_snr, 104))
        # irVal.append(tempIRV)

    #Ensure lists only hold up to 181 pieces of data
    angle = angle[-181:]
    ir_distance = ir_distance[-181:]
    sonar_distance = sonar_distance[-181:]

    #Object detection logic
    if (len(ir_distance) > 2):

        #Object begins if ir value crosses sonar value on an increase in the IR value
        if ir_distance[-2] > cur_snr and ir_distance[-3] > cur_snr and (
                cur_snr and cur_ir < 60.0):
            current_mine.angle_one(cur_angle)
        #Object ends if IR value croses sonar value on the decrease of the IR value
        elif ir_distance[-2] < cur_snr and (ir_distance[
                                                -3] < cur_snr) and cur_snr < 60.0 and cur_ir > cur_snr and current_mine.found_angle1:
            current_mine.angle_two(cur_angle)
            if sonar_distance[int(current_mine.theta_mid)] != 104:
                current_mine.set_distance(sonar_distance[int(current_mine.theta_mid)])
            else:
                current_mine.set_distance(
                    np.min(int(sonar_distance[int(current_mine.starting_angle)]), sonar_distance[int(current_mine.starting_angle)+1]))
            current_mine.print_Mine_info()

    # Retrieve line objects while plotting IR and Sonar
    l1, = ax.plot(angle, ir_distance, 'r')
    l2, = ax.plot(angle, sonar_distance, 'b')

    # ax.set_title('Sonar and IR Scan Data')
    ax.set_thetamin(0)
    ax.set_thetamax(180)
    ax.set_rmin(0)
    ax.set_rmax(105)
    # Create legend for lines drawn
    ax.legend((l1, l2), ('Ir_Distance cm', 'Sonar_Distance cm'))

    last_ir = cur_ir

    if cur_angle == 180 and current_mine.found_angle1:
        current_mine.angle_two(cur_angle)
        current_mine.set_distance(
            sonar_distance[int((cur_angle + current_mine.starting_angle) / 2)])

    plt.title("Sensor Data")
    return l1, l2  # Must do this for blit performance


# Live processing call, 60ms interval
ani = animation.FuncAnimation(fig,
                              animate,
                              fargs=(angle, ir_distance, sonar_distance, current_mine),
                              interval=60, blit=True)
# Display the plot
plt.show()

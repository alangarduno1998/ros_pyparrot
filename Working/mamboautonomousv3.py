# #!/usr/bin/env python3.6
# Written by Isaac Vargas and Alan Garduno
import math
import rospy
import numpy as np
from std_msgs.msg import Empty, String, UInt8
from sensor_msgs.msg import Joy
from geometry_msgs.msg import TransformStamped
from pyparrot.Minidrone import Mambo
#from vicon_python import *
import time
import _thread

def cb_vicon_data1(data):
    global x_1, y_1, z_1
    global rx1, ry1, rz1, rw1
    dt,dr=data.transform.translation, data.transform.rotation
    x_1,y_1,z_1 = dt.x, dt.y,dt.z
    rx1,ry1,rz1,rw1 = dr.x, dr.y, dr.z, dr.w
def cb_vicon_data2(data):
    global x_2, y_2, z_2
    dt,dr=data.transform.translation, data.transform.rotation
    x_2,y_2,z_2 = dt.x, dt.y,dt.z
    rx,ry,rz,rw = dr.x, dr.y, dr.z, dr.w
def cb_vicon_data3(data):
    global x_3, y_3, z_3
    dt,dr=data.transform.translation, data.transform.rotation
    x_3,y_3,z_3 = dt.x, dt.y,dt.z
    rx,ry,rz,rw = dr.x, dr.y, dr.z, dr.w
def doyawangle(yaw):
    global y_1, y_2, x_1, x_2
    real_angle = turn_thresh = 0

    turn_angle = round((math.atan2((y_1-y_2), (x_1-x_2))*180/math.pi), 6)

    if turn_angle < 0:
        real_angle = math.fabs(turn_angle)
    elif turn_angle > 0:
        real_angle = -turn_angle

    real_angle = real_angle - 90

    if real_angle < -180:
        real_angle = 180 - math.fabs(real_angle + 180)

    complement = (yaw*1)
    turn_thresh = (real_angle - complement)

    if turn_thresh < -180:
        turn_thresh = turn_thresh + 360
    elif turn_thresh > 180:
        turn_thresh = turn_thresh - 360
    if math.fabs(turn_thresh) > 30:  # and (math.fabs(turn_thresh) < 180):
        if turn_thresh > 0:
            y = 100
        elif turn_thresh < 0:
            y = -100
    else:
        y = 0
    return y, complement
def doforward(x1, x2, y1, y2, pgain):
    global minSD, maxSD 
    maxSD, minSD = 1.2, 0.4

    distance = math.sqrt(math.pow((x2-x1), 2)+math.sqrt(math.pow((y2-y1), 2)))

    if distance > maxSD:
        p = pgain*70
    elif distance > minSD:
        p = 0
    else: 
        p = 0

    return p, distance  # Distance is "error"
def dovertical(z1, z2):
    global tko, land
    #pid = [0.5, 0.5, 0.5]
    diff = z1 - z2 # this is also the error
    #v = np.clip(pid[0]*diff, )
    if math.fabs(diff) > 0.3:
        if diff < 0:  # z2(remote) object is higher in evelvation
            ver = 35  # movedrone higher
        elif diff > 0:  # z1(autno) object is higher
            ver = -35  # movedrone lower
    else:
        ver = 0  # do nothing
    if math.fabs(diff) > 1.20:
        tko = True
        print('Take off')
    if z2 < 0.1:
        land = True
        print('Land')

    return ver
def quaterion2euler(rx, ry, rz, rw):
    sinr_cosp = 2*(rw*rx + ry*rz)
    cosr_cosp = 1 - 2*(rx*rx + ry*ry)

    roll = math.atan2(sinr_cosp, cosr_cosp)
    sinp = 2*(rw * ry - rz * rx)
    if (math.fabs(sinp)) >= 1:
        pitch = math.copysign(math.pi / 2, sinp)
    else:
        pitch = math.asin(sinp)

    siny_cosp = 2*(rw*rz + ry*rx)
    cosy_cosp = 1 - 2*(rz*rz + ry*ry)

    yaw = math.atan2(siny_cosp, cosy_cosp)

    yaw = yaw*180/math.pi

    if yaw < 0:
        yaw = math.fabs(yaw)
    elif yaw > 0:
        yaw = -yaw

    # print('Vicon Yaw =', round(yaw, 2))

    return roll, pitch, yaw
def mambo_init():
    global tko, land
    # Variable that will store the parameters of the mambo drone
    mamboAdd = "E0:14:A0:AE:3D:C7"
    wifi = False
    retries = 12

    # The mambo object
    mambo = Mambo("", use_wifi=wifi)

    # Checks if the drone is able to communicate with ROS
    success = False

    # Variables of the drone
    tko = land = False
    cannon = auto_tko = need_to_change_mode = need_to_toggle_mode = False
    p_mode = linX = linY = Alt = Hdg = 0

    mambo = Mambo(mamboAdd, use_wifi=wifi)
    success = mambo.connect(retries)
    if(success):
        mambo.smart_sleep(2)
        mambo.ask_for_state_update()
        mambo.smart_sleep(2)
        mambo.flat_trim()
        rate = rospy.Rate(100)
        land, tko = False, True

    return mambo, success 
def checkvfence(x1,y1,z1, yaw,r,p,y,v,dur,mambo):
    global total_time
    r = 0
    if total_time > 2:
        inital_con = True
        total_time = 0
    else:
        inital_con = False
    #if (x1> 3.75) or (x1<-3.25) or (y1> 1.7) or (y1<-2.7) or (z1> 2.1):
    print(total_time)

    if (x1> 3.75) or (x1<-3.4) or (y1> 1.75) or (y1<-2.65) or (z1> 2.1):
        if inital_con == True:
            mambo.fly_direct(roll=(0), pitch=(0), yaw=(0), vertical_movement=(0), duration=0.1)
            inital_con = False
        dur= 0.03
        #print('x1 = ', x1 ,'y1 = ' ,y1 ,'z1 = ', z1)
        cor_x = 0-x1
        cor_y = 0-y1
        cor_z = 0-z1
        if yaw < 0:
            calc_angle = yaw+360
        else:
            calc_angle = yaw

        #YawAngle to Rectangular
        yaw_x = 0.4*math.cos((calc_angle*math.pi/180))
        yaw_y = 0.4*math.sin((calc_angle)*math.pi/180)
        yaw_z = z1

        magnit_cor =math.sqrt(math.pow(cor_x,2)+math.pow(cor_y,2)+math.pow(cor_z,2))
        magnit_yaw =math.sqrt(math.pow(yaw_x,2)+math.pow(yaw_y,2)+math.pow(yaw_z,2))
        cor_angle = cor_x*yaw_x+cor_y*yaw_y+cor_z*yaw_z

        theta=math.acos((cor_angle)/(magnit_cor*magnit_yaw))
        r = 50 * math.sin(theta) 
        p = 50 * math.cos(theta) 
        y = 0
        if z1 > 2.0:
            v = -50
        

    return r,p,y,v,dur
def swap(x1, y1, z1, prev1_x1, prev1_y1, prev1_z1, prev2_x1, prev2_y1, prev2_z1):
    
    prev3_x1 = prev2_x1 
    prev3_y1 = prev2_y1 
    prev3_z1 = prev2_z1 

    prev2_x1 = prev1_x1 
    prev2_y1 = prev1_y1 
    prev2_z1 = prev1_z1 

    prev1_x1 = x1 
    prev1_y1 = y1 
    prev1_z1 = z1 

    return prev1_x1, prev1_y1, prev1_z1, prev2_x1, prev2_y1, prev2_z1, prev3_x1, prev3_y1, prev3_z1
# def swap(current ,prev_1, prev_2)
def low_pass(filtered_x, filtered_y, filtered_z, prev1_x1, prev1_y1, prev1_z1, prev2_x1, prev2_y1, prev2_z1, prev3_x1, prev3_y1, prev3_z1):
    filtered_x = prev1_x1*0.05 + prev2_x1*0.1 + prev3_x1*0.15 + filtered_x * 0.7
    filtered_y = prev1_y1*0.05 + prev2_y1*0.1 + prev3_y1*0.15 + filtered_y * 0.7
    filtered_z = prev1_z1*0.05 + prev2_z1*0.1 + prev3_z1*0.15 + filtered_z * 0.7

    return filtered_x, filtered_y, filtered_z
def pitchcontroller(x1, y1, x2, y2,prev_dis):
    
    if (x2> 3.75) or (x2<-3.4) or (y2> 1.75) or (y2<-2.65):
        if x2 >3.75:
            x2 = 3.7
        if x2 <-3.4:
            x2 = -3.3
        if y2 >1.75:
            y2 = 1.7
        if y2 <-2.65:
            y2 = -2.6

    dist = math.sqrt(math.pow((x2-x1), 2)+math.sqrt(math.pow((y2-y1), 2)))
    
    pgain_pitch = (math.fabs(dist-prev_dis)*0.9 + dist*0.1) #somthing

    return pgain_pitch
def vicon_sys():
#Declare Globals
    global x_3, y_3, z_3 #item number 3 x,y,z location
    global x_2, y_2, z_2 #item number 2 x,y,z location
    global x_1, y_1, z_1, rw1, rx1, ry1, rz1 #item number 1 x,y,z location
    global tko, land
    global total_time
#Declare varibles, i think the global variables are already initialized as 0
    x_1 = y_1 = z_1 = 0
    prev1_x1 = prev1_y1 = prev1_z1 = prev2_x1 = prev2_y1 = prev2_z1 = prev3_x1 = prev3_y1 = prev3_z1 = filtered_x = filtered_y = filtered_z = 0 
    rx1 = ry1 = rz1 = rw1 = 0
    x_2 = y_2 = z_2 = 0
    x_3 = y_3 = z_3 = 0
    r = p = y = v = 0
    dur = 0.01
    total_time = 0
    pgain_pitch = prev_dis = 0
    timemark= time.time()
#Init ROS node + Vicon
    rospy.init_node('vicon_reader', anonymous=True)
    rate = rospy.Rate(100)
    # Choose which topic to listen
    s1_vicon = rospy.Subscriber('/vicon/Mambo_Autonomous/Mambo_Autonomous', TransformStamped, cb_vicon_data1, buff_size=1)
    s3_vicon = rospy.Subscriber('/vicon/SUMO_11_5_2018/SUMO_11_5_2018/', TransformStamped, cb_vicon_data3, buff_size=1)
    s2_vicon = rospy.Subscriber('/vicon/Mambo_KeyboardControlled/Mambo_KeyboardControlled', TransformStamped, cb_vicon_data2, buff_size=1)

    mambo,_ = mambo_init()
#MAIN LOOP
    while not rospy.is_shutdown():
        rate.sleep()
        if tko == True:
            mambo.safe_takeoff(2)
            tko = False
        if land == True:
            mambo.safe_land(2)
            land = False
        r = 0
        roll, pitch, yaw = quaterion2euler(rx1, ry1, rz1, rw1)

        v = dovertical(z_1, z_2)
        y,_ = doyawangle(yaw)

        pgain_pitch = pitchcontroller(x_1,y_1,x_2,y_2,prev_dis)

        if y == 0:
            p, prev_dis = doforward(x_1, x_2, y_1, y_2, pgain_pitch)
        else:
            p =0

        prev1_x1, prev1_y1, prev1_z1, prev2_x1, prev2_y1, prev2_z1, prev3_x1, prev3_y1, prev3_z1 = swap(x_1, y_1, z_1, prev1_x1, prev1_y1, prev1_z1, prev2_x1, prev2_y1, prev2_z1)
        filtered_x, filtered_y, filtered_z = low_pass(filtered_x, filtered_y, filtered_z, prev1_x1, prev1_y1, prev1_z1, prev2_x1, prev2_y1, prev2_z1, prev3_x1, prev3_y1, prev3_z1)
        r,p,y,v, dur  = checkvfence(filtered_x, filtered_y, filtered_z,yaw,r,p,y,v, dur,mambo)
        #mambo.fly_direct(roll=(r), pitch=(p), yaw=(y), vertical_movement=(v), duration=dur)
        mambo.fly_direct(roll=(r), pitch=(p), yaw=(y), vertical_movement=(v), duration=0.1)
        dt = time.time() - timemark
        timemark = time.time()
        total_time = total_time + dt

        time_counter = time.time()
#Main function
if __name__ == '__main__':
    try:
        vicon_sys()
    except rospy.ROSInterruptException:
        print("Exiting...")

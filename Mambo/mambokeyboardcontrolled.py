#!/usr/bin/env python3.6
# Written by Isaac Vargas and Alan Garduno
import time
import keyboard
from pyparrot.Minidrone import Mambo


#Variable that will store the parameters of the mambo drone
#mamboAdd = "D0:3A:EE:30:E6:20" # ViconObject = Mambo_1
#mamboAdd = "E0:14:A0:AE:3D:C7" # ViconObject = Mambo_5
#mamboAdd = "D0:3A:3A:2D:E6:36" # ViconObject = Mambo_3
mamboAdd = "D0:3A:03:39:E6:3B"  # ViconObject = Mambo_4
wifi = False
retries = 12

#The mambo object
mambo = Mambo("",use_wifi=wifi)

#Checks if the drone is able to communicate with ROS
success = False

#Variables of the drone
tko = False
land = False
cannon = False
auto_tko = False
need_to_change_mode = False
need_to_toggle_mode = False
p_mode = 0
linX = 0
linY = 0
Alt = 0
Hdg = 0

#Callback of the land command
def cb_land(data):
    global land
    land = True

#Callback of the take-off command
def cb_take_off(data):
    global tko
    tko = True

#CAllback of the velocities
def cb_cmd_vel(data):
    global linX
    global linY
    global Alt
    global Hdg
    
    linX = data.linear.x
    linY = data.linear.y
    Alt = data.linear.z
    Hdg = data.angular.z

def sat(value, max_value):
    if(value > max_value):
	    value = max_value
    if(value < -max_value):
	    value = -max_value
    return value

def turn_degreees(mambo, degrees):
        """
        Turn the mambo the specified number of degrees (-180, 180). 
        """
        degrees = int(degrees)
        if (degrees > 180):
            degrees = 180
            print("Degrees too large: setting to 180")
        elif (degrees < -180):
            degrees = -180
            print("Degrees too large and negative: setting to -180")

        command_tuple = mambo.command_parser.get_command_tuple("minidrone", "Animations", "Cap")
        return mambo.drone_connection.send_turn_command(command_tuple, degrees)

#Initialization function
def init():
    global tko, land, cannon, auto_tko
    global linX, linY, Alt
    global Hdg, p_mode
    global need_to_change_mode, need_to_toggle_mode
    global okay_signal, tot_time, turn_indicator
    global keywaspressed

    mambo = Mambo(mamboAdd,use_wifi=wifi)
    success = mambo.connect(retries)
    okay_signal = keywaspressed = False
    turn_indicator = 0
    if(success):
        mambo.smart_sleep(2)
        mambo.ask_for_state_update()
        mambo.smart_sleep(2)
        mambo.flat_trim()
        marktime = time.time()
        dt = 0
        tot_time = 0
        while True:

            if tko == True:
                
                mambo.safe_takeoff(2)
                tko = False

            if land == True:
                mambo.safe_land(2)
                land = False
            
            obtain_keyboard()
            r_y = round(linY,2)
            p_x = round(linX,2)
            v_z = round(Alt,2)
            y_z = round(Hdg,2)

            r_y = sat(r_y, 0.98)
            p_x = sat(p_x, 0.98)
            v_z = sat(v_z, 0.98)
            y_z = sat(y_z, 0.98)
            mambo.fly_direct(roll = (-r_y * 25), pitch = (p_x*30),yaw = (-y_z *75), vertical_movement = (v_z*75), duration=0.01)
            if keywaspressed == True:
                mambo.turn_degrees(turn_indicator)
                print('the shit should be turning-----------------------')
                keywaspressed = False

            print(keywaspressed, turn_indicator)

            tot_time = dt + tot_time
            if tot_time > 0.2:
                tot_time = 0
                okay_signal = True
            print(tot_time, okay_signal)
            dt = time.time() - marktime
            marktime = time.time()

def obtain_keyboard():
    global linX
    global linY
    global Alt
    global Hdg
    global tko
    global land
    global okay_signal
    global tot_time
    global turn_indicator
    global keywaspressed

    if keyboard.is_pressed('t'):
        print('TakingOff')
        tko = True
    if keyboard.is_pressed('w'):
        print('Moving Forward')
        linX = rampfunction(linX, 50)
        time.sleep(0.05)
    elif keyboard.is_pressed('s'):
        print('Moving Backward')
        linX = rampfunction(linX, -50)
        time.sleep(0.05)
    else:
        linX = rampfunction(linX, 0)


    if keyboard.is_pressed('a'):

        print('Moving Left')
        linY = rampfunction(linY, 50)
        time.sleep(0.05)
    elif keyboard.is_pressed('d'):
        print('Moving Right')
        linY = rampfunction(linY, -50)
        time.sleep(0.05)
    else:
        linY = rampfunction(linY, 0)

    if okay_signal == True:
        if keyboard.is_pressed('m'):
            print('Turning "90"')
            #mambo.turn_degrees(90)
            turn_indicator = 90
            tot_time = 0
            okay_signal = False
            keywaspressed = True
        if keyboard.is_pressed('n'):
            print('Turning "-90"')
            okay_signal = False
            turn_indicator = -90
            #mambo.turn_degrees(-90)
            tot_time = 0
            keywaspressed = True
        if keyboard.is_pressed('o'):
            print('Turning "180"')
            turn_indicator = 180
            #mambo.turn_degrees(180)
            tot_time = 0
            okay_signal = False
            keywaspressed = True
        if keyboard.is_pressed('p'):
            print('Turning "-180"')
            turn_indicator = -180
            #mambo.turn_degrees(-180)
            tot_time = 0
            okay_signal = False
            keywaspressed = True
        if keyboard.is_pressed('q'):
            print('Turning "0"')
            #mambo.turn_degrees(0)
            turn_indicator = 0
            tot_time = 0
            okay_signal = False
            keywaspressed = True

        

    if keyboard.is_pressed('up arrow'):
        print('Veritcal Up')
        Alt = rampfunction(Alt, 50)
        time.sleep(0.05)
        
    elif keyboard.is_pressed('down arrow'):
        print('Vertical Down')
        Alt = rampfunction(Alt, -50)
    else:
        Alt = rampfunction(Alt, 0)
        
    if keyboard.is_pressed('left arrow'):
        print('Rotating Left')
        Hdg = 2
        time.sleep(0.05)
    elif keyboard.is_pressed('right arrow'):
        print('Rotating Right')
        Hdg = -2
        time.sleep(0.05)
    else:
        Hdg = 0

    if keyboard.is_pressed('l'):
        print('Landing!')
        land = True
    return linY, linX, Alt, Hdg 

def rampfunction(prev_state, proportion): #proportion is desired state (from 0 to 50)
    
    if prev_state > 50:
        proportion = 50
        return proportion #proportion is new state if no changes
    if prev_state < -50:
        proportion = -50
        return proportion
    
    if (prev_state > proportion):
        new_state = prev_state - 25
        if new_state <= -50:
            new_state = -50
        return new_state
            
    if (proportion > prev_state):
        new_state = prev_state + 25
        if new_state >= 50:
            new_state = 50
        return new_state
    return prev_state

#Main function
if __name__=='__main__':
    init()
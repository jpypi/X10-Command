#!/usr/bin/env python
import interface
import scripts
import json
from threading import Thread
from os import name as os_name
import time

import bluetooth

port_name="COM1"
if os_name == "posix":
    port_name="/dev/ttyUSB0"

conn = interface.InterfaceCon(port_name, 4800)
state_mgr = interface.StateManager()
conn.history = state_mgr

try:
    f = open("data/status.stat", "r")
    state_mgr.states = json.loads(f.read().split("\n")[1])
    f.close()
except:
    pass


main_script = scripts.Script("data/commands.txt")


def UpdateX10():
    receive = conn.Read()
    
    if receive == "\x5a": #An X10 Transmission has been sent
        conn.ReceiveTrans() #Tell the X10 interface connection to receive it

    if state_mgr.states.get("A4", (0, ))[0] == "ON":
        conn.SendAddr("A4")
        conn.SendFunc("A DIM", 7)
        
    main_script.Run(conn, state_mgr.states)
    

def SaveAndClose():
    """
    Safely and correctly stops the program. This will wait for the 
    status update thread to be done then save unit states and close
    the connection properly.
    
    SYNTAX:
    
        quit
    """
    global GOING
    GOING=False

    print "Stopping update thread..."
    main_loop_thread.join()
    
    print "Saving command states..."
    main_script.SaveStates()

    print "Saving unit states..."
    try:
        f=open("data/status.stat", "a")
        f.write("\n")
        json.dump(state_mgr.states, f)
        f.close()

    except Exception, e:
        # We couldn't save the unit states for some reason. Don't worry about it.
        # Make sure we close the conn!
        if verbose:
            print "\n\n%s\n\n"%str(e)

        print "WARNING*: Couldn't save unit states!"
        
    print "Closing connection..."
    conn.Close()

    print "Done."


def GetStatus(reset=""):
    """
    Displays the status of all units for the currently
    monitored housecode in a pretty format. If the command
    reset is given the states of the units will all be cleared.
    
    SYNTAX:
    
        status [reset]
    """

    if reset == "reset":
        state_mgr.states={}
        print "States successfully reset."

    elif not reset.strip():
        sorted_keys=state_mgr.states.keys()
        sorted_keys.sort(key=lambda x:int(x[1:]))
        print "{:<7s}{:^8s}{:^20s}".format("Unit:", "State:", "Last Update:")

        for unit in sorted_keys:
            try:
                status = str(round(state_mgr.states[unit][0],1))+"%"
            except TypeError:
                status = state_mgr.states[unit][0]

            t = time.localtime(float(state_mgr.states[unit][1]))
            hr = t.tm_hour
            ampm="am"

            if t.tm_hour>11:
                hr -= 12
                ampm="pm"

            pretty_time = "%s:%s:%s %s %s/%s/%s"%(hr,str(t.tm_min).zfill(2),str(t.tm_sec).zfill(2),ampm,t.tm_mon,t.tm_mday,str(t.tm_year)[2:])
        
            print "{:<8s}{:8s}{:>20s}".format(unit, status, pretty_time)

    else:
        raise TypeError,"Invalid argument!"


def Reload(what):
    """
    The reload takes a single argument which can be either
    commands or triggers.
    
    *NOTICE: Only commands can be reloaded currently.
    
    SYNTAX:
    
        reload commands|triggers
    """
    
    if what == "commands":
        print "Reloading commands..."
        main_script.Reload()
        print "Success!"

    elif what == "triggers":        
        print "NOTICE: Currently,only commands can be reloaded."

    else:
        print "Error: %s is an invalid option!"%what


def IsValidUnitAddress(value):
    try:
        return value[0].isalpha() and 0 < int(value[1:]) < 17
    except:
        return False


def ParseManualCommand(hc, *args):
    """
    do is for manually controlling X10 units.
    
    *NOTICE: Not entirely implimented yet.
    
    SYNTAX:

        do (house_code|house_code_unit#) [unit_numbers] function
        
        If only a house_code is supplied the command will attempt
        to opperate on all the units. Otherwise a list of unit
        numbers may be suplied seperated by a comma with no spaces
        and the function will be applied to only those given.
        
        function can be:
            on
            off
            a number from -100 to 100 representing a power percentage
              (Positive will brighten and negative will dim.)
    """
    arg_count = len(args)
    
    hc = hc.upper()
    cmd = map(lambda s:s.upper(), args)
    
    house_code = hc[0]

    # Check if this is a whole address
    if IsValidUnitAddress(hc):
        conn.SendAddr(hc)
    # ...or just a house code letter (arg_count > 1 -> unit codes + command)
    elif arg_count > 1 and len(hc) == 1 and hc in "ABCDEFGHIJKLMNOP":
        # Parse the next part as if it were numbers which would
        # complete the address
        for n in cmd[0].split(","):
            if n.isdigit() and 0 < int(n) < 17:
                conn.SendAddr(house_code + n)
            else:
                print "Warning: %s is an invalid unit code"%n
    
    # Make sure there is a command to process
    if arg_count > 0:
        if cmd[-1] in ("ON", "OFF", "ALL"):
            conn.SendFunc(house_code + " " + cmd[-1], 0)
            
        elif 0 < abs(int(cmd[-1])) < 101:
            dim_bright_val = int(cmd[-1])
            percent = (abs(dim_bright_val) / 100.0) * 22

            if dim_bright_val < 0:
                conn.SendFunc(house_code + " dim", percent)

            elif dim_bright_val > 0:
                conn.SendFunc(house_code + " bright", percent)

        else:
            print "Error: Command must be ON or OFF and dim/bright level must be between -100% and 100%!"
        

# All software should have this function.
def Oink(times=1):
    """
    The oink command takes a single argument which is the
    number of times to oink. It's output... Well, you'll
    just have to find out for yourself.
    
    SYNTAX:
        
        oink [number_of_times]
    """
    
    print "Oink" + " oink" * (int(times) - 1) + "!"
    

def Help(topic=None):
    """
    Command line interface for serial X10 module CM11A.
    Probably around version 2.2
    (c) James Jenkins 2012, 2013
    """

    if not topic:
        print "Avaliable commands are: "
        print "\n".join(map(lambda x:" "*3+x, filter(lambda c:c!="help", commands)))
        print "Type help command to get help with a specific command."

    elif topic in commands:
        print "Help for %s:"%topic
        print commands[topic].__doc__


verbose=False
def Verbose(on_off="on"):
    """
    Enables verbose error messages.
    
    By default if no argument is supplied verbose will be turned on.
    Optionally a number can be supplied for verbosity level. Valid
    range is 0 to 2. (off==0,on==1,2=show errors)
    
    SYNTAX:
        
        verbose [on|off|level]
    """

    global verbose
    
    if on_off.isdigit():
        int_value = int(on_off)
    else:
        int_value = 1

    if on_off.lower() == "off":
        int_value = 0
        print "Verbose disabled."
    elif on_off.lower() == "on":
        int_value = 1
        print "Verbose enabled."
        
    if -1 < int_value < 3:
        verbose=int_value
        interface.VERBOSE=int_value
    else:
        raise TypeError


def GetHistory(index=0):
    """
    Show raw X10 command history.

    By supplying a number only that number of recent history items will
    be shown.
    
    SYNTAX:

        history [clear|number] 
    """
    if index == "clear":
        state_mgr.entire_history = []
    else:
        print state_mgr.entire_history[int(index):]


def StatusRequest():
    conn.Write("\x8b")
    data=""
    for i in xrange(14):
        data += conn.Read()
    print data
    d=map(lambda x:bin(ord(x)).replace("0b","").zfill(8),data)
    print d
    print "".join(d)


def Receive(socket):
    data = socket.recv(3)
    message_size=ord(data[0])<<8|ord(data[1])
    keep_alive=bool(ord(data[2])&1)
    message=socket.recv(message_size)

    return message,keep_alive


def BluetoothServerThread():
    server_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)

    server_sock.bind(("", bluetooth.PORT_ANY))
    server_sock.listen(2)
    uuid="d1890667-00a8-419f-ac00-2c8ea10b7081" #"de92f5ce-f218-4e39-a08b-72dd386ad41f"#"1dc2dfe1-59c5-4476-aadd-fe041c440277"
    bluetooth.advertise_service(server_sock,"SimpleBTChat",service_id=uuid,
                                service_classes=[uuid,bluetooth.SERIAL_PORT_CLASS],
                                profiles=[bluetooth.SERIAL_PORT_PROFILE])

    print "Waiting for connection..."

    stay_alive=True
    while stay_alive:
        client_sock,address=server_sock.accept()
        print "Accepted connection from",address
        
        data,keep_alive=Receive(client_sock)
        print "Received: [%s]"%data

        inpt=data.strip().lower().split(" ")
        if inpt[0] in commands:
           try:
                commands[inpt[0]](*inpt[1:])
           except TypeError,e:
                print "Error: incorrect argument format. Please refer to documentation."
                if verbose>1: print "\n\n"+str(e)+"\n\n"
                print commands[inpt[0]].__doc__
        else:
           try:
               if len(inpt)==1 and not inpt[0] in ("ALLON",):
                   raise ValueError,"ParseManualCommand requires more arguments."
               ParseManualCommand(*inpt)
           except ValueError:
               print "Error: %s is not a valid command!"%inpt[0]
           except Exception,e:
               if verbose>1:
                   print "\n\n%s\n\n"%str(e)
                   
        if data=="turn off":
            print "Server is shutting down."
            stay_alive=False
        
        client_sock.close()

        
    server_sock.close()


GOING=True
def MonitorX10():
    while GOING:
        UpdateX10()
        time.sleep(2)
        

commands = {
            "quit": SaveAndClose,
            "reload": Reload,
            "status": GetStatus,
            "help": Help,
            "oink": Oink,
            "do": ParseManualCommand,
            "verbose": Verbose,
            "history": GetHistory,
            "reqstat": StatusRequest
           }


# Doing things this way allows the GUI version to import
# things from this script.
if __name__ == "__main__":
    try:
        print "Starting mainloop..."
        main_loop_thread = Thread(target=MonitorX10)
        main_loop_thread.setDaemon(True)
        main_loop_thread.start()

        print "Starting bluetooth thread..."
        bluetooth_thread = Thread(target=BluetoothServerThread)
        bluetooth_thread.setDaemon(True)
        bluetooth_thread.start()
        
        while GOING:
            inpt = raw_input(">>> ").lower().strip().split(" ")
            if inpt[0] in commands:
               try:
                    commands[inpt[0]](*inpt[1:])
               except TypeError,e:
                    print "Error: incorrect argument format. Please refer to documentation."
                    if verbose > 1:
                        print "\n\n" + str(e) + "\n\n"
                    print commands[inpt[0]].__doc__

            elif not (len(inpt) == 1 and not inpt[0]):
               try:
                   if len(inpt) == 1 and inpt[0] != "allon":
                       raise ValueError, "ParseManualCommand requires more arguments."
                   ParseManualCommand(*inpt)

               except ValueError:
                   print "Error: %s is not a valid command!"%inpt[0]

               except Exception,e:
                   if verbose > 1:
                       print "\n\n%s\n\n"%str(e)
                        
    finally:
        conn.Close()

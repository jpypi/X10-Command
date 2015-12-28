import time
from string import ascii_uppercase

import serial

from x10constants import *

VERBOSE=False
TRYOUTS=2


def MakeAddr(code):
    house=code.upper()[0]
    device=code.upper()[1:]
    return house_code[house]<<4|device_code[int(device)]


def MakeFunc(code):
    house, func=code.upper().split(" ", 1)
    return house_code[house]<<4|function_code[func]


def FillByte(num):
    shift=8-len(bin(num).lstrip("0b"))
    return num<<shift


class InterfaceCon:
    def __init__(self, port, baud_rate, timeout=2, parity=serial.PARITY_NONE):
        self.con=serial.Serial(port, baud_rate, timeout=timeout, parity=parity)
        self.history=[]
        self.last_transmission_size=0

    def Read(self):
        data=self.con.read()
        if data == '\xa5':
            self.DownloadTime()
            return False
        else:
            return data

    def ReadBin(self):
        try: print bin(ord(self.con.read()))
        except TypeError: print "Could not read from connection."

    def Write(self, data):
        """
        **DEPRECIATED!**
        Use SendAddr,  SendFunc,  or Action!
        """
        #raise DeprecationWarning, "Use SendAddr,  SendFunc,  or Action!"
        self.con.write(data)

    def Close(self):
        self.con.close()

    def DownloadTime(self):
        # header    seconds  minutes   hours    year_day  week_mask house  stuff
        #"10011011 11111111 11111111 11111111  [11111111 1]1111111  1111  1 1 1 1"
        print "Downloading time..."
        t=time.localtime()
        if t.tm_wday == 6: day_mask=64
        else: day_mask=1<<(5-t.tm_wday)
        bit8=t.tm_yday&1
        time_data="\x9b"+\
                  chr(t.tm_sec)+\
                  chr(t.tm_min)+\
                  chr(t.tm_hour/2)+\
                  chr(t.tm_yday>>1)+\
                  chr(bit8<<7|day_mask)+\
                  chr(house_code["A"]<<4|0b0111)
        self.con.write(time_data)
        if VERBOSE:print "Check sum: %s"%bin(sum(map(ord, list(time_data)))&0xff)
        self.ReadBin()
        print "Done"

    def SendAddr(self, address):
##        if VERBOSE: print "Connection ID: %s"%self.ID
        if VERBOSE: print "Seinding address %s"%address
        data=[0x04, MakeAddr(address)]
        check=chr(sum(data)&0xff)
        self.con.write(serial.to_bytes(data))
        tries=0
        while tries<TRYOUTS:
            con_data=self.con.read()
            if con_data!=check:
                if VERBOSE: print con_data
                self.con.write(serial.to_bytes(data))
                if VERBOSE: print "Resending address"
                tries+=1
            else:
                break
        if tries>=TRYOUTS:
            if VERBOSE:print "Unsucessful address!"
            return False
        self.con.write(chr(0x00))#Checksum correct,  OK to transmit
        while self.con.read()!="U" and tries<TRYOUTS*2:
            time.sleep(0.5);tries+=1
            if VERBOSE:print "Not ready after sending address"
            
        if tries>=TRYOUTS*2:
            if VERBOSE:print "Error after sending address!"
            return False
        
        self.history.append(address)
        return True

    def SendFunc(self, func, dims=0):
##        if VERBOSE: print "Connection ID: %s"%self.ID
        if VERBOSE: print "Seinding function %s"%func
        dims=int(round(dims))
        data=[dims<<3|0b110, MakeFunc(func)]
        check=chr(sum(data)&0xff)
        self.con.write(serial.to_bytes(data))
        tries=0
        while tries<TRYOUTS and self.con.read()!=check:
            self.con.write(serial.to_bytes(data))
            if VERBOSE:print "Resending function"
            tries+=1
        if tries>=TRYOUTS:
            if VERBOSE:print "Unsucessful function!"
            return False
        self.con.write(chr(0x00))
        while self.con.read()!="U" and tries<TRYOUTS*2:
            time.sleep(0.5);tries+=1
            if VERBOSE:print "Not ready after sending function"
        if tries>=TRYOUTS*2:
            if VERBOSE:print "Error after sending function!"
            return False
        
        f=func.upper().replace(" ", "")
        change=dims/22.0*100
        if f[1:] == "DIM": #[1:] removes the housecode from the function
            self.history.append(f+"-%s"%change)
        elif f[1:] == "BRIGHT":
            self.history.append(f+"+%s"%change)
        else:
            self.history.append(f)
        return True
        
    def Action(self, addr, func, dims=0):
        """
        A combo version of SendAddr and SendFunc
        Supports only 1 address! Could easily be re-written to support multiple
        """
        if self.SendAddr(addr):
            if self.SendFunc(func, dims):
                return True
        return False

    def ReceiveTrans(self):
        self.con.write("\xc3")#This is the "it's ok to send data now" code
        received=[self.Read() for i in xrange(ord(self.Read()))]
        if VERBOSE: print "Receieved: "+str(received)
        
        if len(received)>2:
            mask=list(bin(ord(received.pop(0))).lstrip("0b").zfill(8))
            mask.reverse()
            info=[]
            for i, d in enumerate(received):
                if d:
                    d=ord(d)
                    if info and info[-1].find("DIMF") == 1:
                        hc=info[-1][0]
                        info.pop(-1)
                        info.append(hc+"DIM-"+str(d/210.0*100))
                    elif info and info[-1].find("BRIGHTF") == 1:
                        hc=info[-1][0]
                        info.pop(-1)
                        info.append(hc+"BRIGHT+"+str(d/210.0*100))
                    else:
                        hc=str(code_house[d>>4])#house code
                        mask_val=mask[i]
                        if VERBOSE:print bin(d), mask_val
                        if mask_val == "0":
                            dc=str(device_code.index(d&15))#device code
                            info.append(hc+dc)
                        if mask_val == "1":
                            info.append(hc+code_function[d&15]+"F")#function code;The "F" is for denoting a function,  used in detecting dims and brights
                elif VERBOSE>1:
                    print "Receieved error: "+str(received)

            for i in info:
                if i[-1] == "F":i=i[:-1]
                self.history.append(i)


def Log(info):
    try:
        f=open("data/log.txt", "a")
    except:
        f=open("data/log.txt", "w")

    f.write(str(info)+"\n")
    f.close()


class StateManager:
    def __init__(self):
        self.states={}
        self.entire_history=[]
        self.history=[]

    def append(self, data):
        if VERBOSE:
            print "Appending data to history: %s"%str(data)

        self.entire_history.append(data)
        self.history.append(data)
        if data[1:].rstrip("-+1234567890.") in function_code:
            self.UpdateStates()

    def UpdateStates(self):
        parsed_to=0
        last_addresses=[]
        for i, h in enumerate(self.history):
            if h[0].isalpha() and h[1:].isdigit():
                if VERBOSE:
                    print "Found address"
                    if len(last_addresses)>0:
                        print "Last address house code: %s"%last_addresses[-1][0]

                if (last_addresses and last_addresses[-1][0] == h[0]) or not last_addresses:
                    last_addresses.append(h)
                    if VERBOSE:
                        print "Adding address: %s"%h
                    
            elif last_addresses and h[0] == last_addresses[-1][0]:
                if VERBOSE:
                    print "Found command"

                parsed_to=i
                for a in last_addresses:
                    last_value=self.states.get(a, [""])[0]
                    new_state=None
                    
                    if (h.find("BRIGHT") == 1 or h.find("DIM") == 1) and last_value:
                        if type(last_value) == float:
                            level = last_value+float(h.lstrip(ascii_uppercase))
                            if level > 100:
                                level = 100.0
                            if level < 0:
                                level = 0.0
                            new_state = level
                        elif h.find("DIM") == 1:
                            new_state = 100 + float(h.lstrip(ascii_uppercase))
                        else:
                            new_state = "ON"

                    else:
                        if h[1:] == "OFF":
                            new_state=h[1:]
                        # Last_value in on, off is so that when the light is dimmed and
                        # someone presses on we don't record it as being fully on.
                        # Unless, however, we don't know what state it was in beforehand.
                        elif h[1:] == "ON" and (last_value in ("ON", "OFF") or last_value == ""):
                            new_state=h[1:]
                            
                    if new_state:
                        self.states[a]=[new_state, time.time()]
                        Log("%s : %s : %s"%(a, h, time.ctime()))
                    
        del self.history[:parsed_to+1]


# TODO: These look like evidence of bad things
history=[]
last_addr=False
last_addrs=[]


def LastAddrs():
    """
    Returns the last transmited addresses in lifo form

    Last address will be first second to last will be second etc.
    """
    last=[]
    if len(history) == 0:
        return []

    # This makes it so the list is traversed in reverse without changing it's actual order
    for i in xrange(-1, -len(history)-1, -1):
        hval=history[i]
        # Detect only addresses
        if hval[0].isalpha() and hval[1:].isdigit():
            last.append(hval)

    return last
    

def ParseHistory(history, units_states):
    global last_addr
    for h in history:
        if h[0].isalpha() and h[1:].isdigit():
            last_addr=h
        elif last_addr and h[0] == last_addr[0]:#Check housecodes are the same
            try:
                val=units_states[last_addr][0]
            except KeyError: val=""

            new_state=None
            
            if (h.find("BRIGHT") == 1 or h.find("DIM") == 1) and val!="":
                if type(val) == float:
                    level = units_states[last_addr][0] + float(h.lstrip(ascii_uppercase))

                    if level>100:
                        level=100.0
                    if level<0:
                        level=0.0

                    new_state=level
                elif val == "ON" and h.find("DIM") == 1:
                    new_state=100+float(h.lstrip(ascii_uppercase))
                else:
                    new_state="ON"

            # An on or off command and/or there was no previously recorded
            # addr for the action.
            else:
                if h[1:] == "OFF":#Command is off
                    new_state=h[1:]
                # Command is on and light is off or on (The on "on" part is so that we
                # still update the view and log that way I know if someone keeps trying
                # to turn a light on.)
                elif val in ("ON", "OFF") or val == "":
                    new_state=h[1:]

            if new_state:
                if units_states.has_key(last_addr):
                    #if units_states[last_addr][0]!=new_state:
                    units_states[last_addr]=[new_state, time.time()]
                else:
                    units_states[last_addr]=[new_state, time.time()]

                Log("%s : %s : %s"%(last_addr, h, time.ctime()))

    return units_states

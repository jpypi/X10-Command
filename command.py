import datetime
import hashlib

from converters import  * 


class Command(object):
    next_id = 0
    def __init__(self, init_string):
        # Auto generate an id for each command
        self.id = Command.next_id
        Command.next_id += 1

        # Just set this to anything a long time before today
        self.last_run = datetime.date(1990, 1, 1)
        
        self.init_string = init_string.upper().split(" ")
        self.hash = self.GetHash()
        
        self.type = "SET"
        self.days = range(0, 7)
        self.time = None
        self.addresses = []
        self.function = None
        self.dims = 0

        was_special = False
        for unit in self.init_string:
            if not was_special:
                time = Time(unit)
                days = Days(unit)
                addr = Address(unit)
                if time != False:
                    # Must compare time to false because if you get a time of 12am
                    # (==00:00:00) is evaluated to False but is not equal to false
                    self.time=time 
                if days:
                    self.days = days
                if addr:
                    self.addresses.append(addr)
                if unit in ("ON", "OFF", "DIM", "BRIGHT"):
                    self.function = unit
                    if unit in ("DIM", "BRIGHT"):
                        was_special = unit
            else:
                if was_special in ("DIM", "BRIGHT"):
                    if unit.endswith("%"):
                        self.dims = int(round(int(unit.rstrip("%")) / 100.0 * 22))
                    else:
                        self.dims = int(unit)
                was_special = False # Now we can go back to normal mode
                
    def Run(self, conn, current_date, current_time, time_info):
        if current_date>self.last_run and time_info.tm_wday in self.days and\
           current_time >= self.time: # or if this were a KEEP command
            send_function = False
            for address in self.addresses:
                house_code = address[0]
                if conn.SendAddr(address):
                    send_function = True
                
            if send_function and conn.SendFunc(house_code + " " + self.function, self.dims):
                self.last_run = current_date

    def GetHash(self):
        return hashlib.sha1(" ".join(self.init_string)).hexdigest()


if __name__ =="__main__":
    c = Command("a5 dim 11 @ 6:59am MTWTF")

    print c.time
    print c.days
    print c.function
    print c.addresses




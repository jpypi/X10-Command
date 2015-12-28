import datetime

def Time(string):
    """
    Will convert a string to a time object if it can. Valid formats are:
        3:04pm
        03:04pm
        15:04
        10am
    """
    string=string.strip().upper()
    string_len=len(string)
    if string_len>7 or string_len<3:
        return False
    for c in string:
        if c not in ("1234567890APM:"):
            return False
        
    military_time=not (string.endswith("AM") or string.endswith("PM"))
    if not military_time:
        if string_len<=4:
            hr=int(string[:-2])
            if string.endswith("PM") and hr!=12:
                hr+=12
            elif string.endswith("AM") and hr==12:
                hr=0
            return datetime.time(hr)
        else:        
            hr_min=map(int,string[:-2].split(":"))
            if string.endswith("PM") and hr_min[0]!=12:
                hr_min[0]+=12
            elif string.endswith("AM") and hr_min[0]==12:
                hr_min[0]=0
            return datetime.time(hr_min[0],hr_min[1])
    else:
        try:
            hr_min=map(int,string.split(":"))
            return datetime.time(*hr_min)
        except ValueError:
            return False #Must not have been a "time"
        
    
def Date(string):
    """
    Will convert a string to a date object if it can. Valid formats are:
        1-23-13 (month-day-year)
        2013-2-25 (year-month-day)
        January 1, 2012
        March 03 2010
        October 4th, 1996
    """
    pass

##months=("JANUARY","FEBRUARY","MARCH","APRIL","MAY","JUNE","JULY","AUGUST","SEPTEMBER","OCTOBER","NOVEMBER","DECEMBER")
##def InterpretDate(data):
##    for i,month in enumerate(months):
##        data=data.replace(month,str(i+1))
##    try:
##        if len(data)==4 and int(data)>1970:
##            return GetEndOfMonth(datetime.date(int(data),12,1))
##    except ValueError:
##        pass #was a short date e.g. "6/20"
##    if data.isdigit() and int(data)<=12 and int(data)>0:
##        return GetEndOfMonth(datetime.date(local_time.tm_year,int(data),1))
##    else:
##        data=data.split("/")
##        if len(data)==2:
##            if len(data[1])==4:
##                return datetime.date(int(data[1]),int(data[0]),1)
##            else:
##                return datetime.date(local_time.tm_year,int(data[0]),int(data[1]))
##        else:
##            try:
##                return datetime.date(int(data[2]),int(data[0]),int(data[1]))
##            except:
##                return False


def Days(string):
    if len(string)>7:
           return False
    for c in string.upper():
        if c not in ("-MTWTFS"):
            return False
    return [i for i,p in enumerate(string) if p!="-"]


def Address(string):
    string=string.strip().upper()
    if string[0].isalpha() and string[1:].isdigit() and len(string)<=3:
        return string
    else:
        return False


def PrettyTime(datetime_time):
    hr=datetime_time.hour
    ampm="am"
    if hr==0: ampm="am";hr=12
    elif hr>11:
        ampm="pm"
        if hr>12:hr-=12
    return "%s:%s%s"%(hr,str(datetime_time.minute).zfill(2),ampm)
    

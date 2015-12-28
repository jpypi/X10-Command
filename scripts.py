import re
import time
import datetime
import command

line_comment=re.compile("//.*")
stream_comment=re.compile(r"/\*.*?\*/",re.DOTALL)
ref_pat=re.compile("(.+)=(.+)")

KEYWORDS=('ON','OFF','DIM','BRIGHT','AT','BETWEEN','AFTER','BEFORE')

class Script:
    def __init__(self,file_name):
        self.file_name=file_name
        self.variables=[]
        self.commands=[]
        self.Parse()
        self.LoadStates()

    def MakeVars(self,groups):
        var_name=groups.group(1).strip()
        if var_name not in KEYWORDS:
            self.variables.append((var_name.strip(),groups.group(2).strip()))
        else:
            print "Error!: Cannot use %s as variable name. %s is a keyword!"%(var_name,var_name)    
        return ""
        
    def Parse(self):
        f=open(self.file_name,"r")
        data=f.read().upper()
        f.close()
        data=stream_comment.sub("",line_comment.sub("",data))

        self.variables=[]
        data=ref_pat.sub(self.MakeVars,data).strip()
        for var_name,addr in self.variables:
            data=data.replace(var_name,addr)
            
        self.commands=[]        
        for line in data.split("\n"):
            if line.strip():
                self.commands.append(command.Command(line))

                    
    def Run(self,conn,units_states):
        time_info=time.localtime()
        current_time=datetime.time(time_info.tm_hour,time_info.tm_min)
        current_date=datetime.date(time_info.tm_year,time_info.tm_mon,time_info.tm_mday)
        for command in self.commands:
            command.Run(conn,current_date,current_time,time_info)
            
    def SaveStates(self):
        f=open("status.stat","w")
        command_info=map(lambda command:command.hash+":"+str(command.last_run.toordinal()),self.commands)
        f.write(",".join(command_info))
        f.close()

    def LoadStates(self):
        try:
            f=open("status.stat","r")
            data=f.read().split("\n")[0].split(",")
            f.close()
            for stat in data:
                if stat.strip():
                    stat=stat.strip().split(":")
                    for cmd in self.commands:
                        if cmd.hash==stat[0]:
                            cmd.last_run=datetime.date.fromordinal(int(stat[1]))
        except IOError:
            pass #Couldn't find the file. Don't worry about it.

    def Reload(self):
        self.SaveStates()
        self.Parse()
        self.LoadStates()
        


if __name__=="__main__":
    s=Script("commands.txt")

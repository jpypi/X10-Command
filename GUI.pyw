import sys
import time
from threading import Thread

import wx
import wx.lib.mixins.listctrl as listmix

from converters import PrettyTime

days_of_the_week=list("MTWTFSS")


class AutoSizeListCtrl(wx.ListCtrl, listmix.ListCtrlAutoWidthMixin):
    def __init__(self, parent, ID, style=0):
        wx.ListCtrl.__init__(self,parent,ID,style=style)
        listmix.ListCtrlAutoWidthMixin.__init__(self)
        self.units_states=[]

    def OnGetItemText(self, item, col):
        if col == 0:
            return self.units_states[item][col]
        else:
            update_data=self.units_states[item][1][:]
            if col == 2:
                t=time.localtime(float(update_data[col-1]))
                hr=t.tm_hour; ampm="am"
                if t.tm_hour>12: hr-=12; ampm="pm"
                update_data[col-1]="%s:%s:%s %s %s/%s/%s"%(hr,t.tm_min,t.tm_sec,ampm,t.tm_mon,t.tm_mday,str(t.tm_year)[2:])
            elif col == 1:
                try:
                    update_data[col-1]=str(round(float(update_data[col-1]),2))+"%"
                except ValueError:
                    pass

            #-1 is 'cause the other values are in the "values" of a dict.items()
            return update_data[col-1]


class MainWindow(wx.Frame):
    def __init__(self,parent=None,size=(600,400),conn=None,script=None,run=None):
        self.run=run
        self.on_close_callback=None
        self.script=script
        self.conn=conn

        wx.Frame.__init__(self,parent,-1,"JX10 Control",size=size)
        self.panel=wx.Panel(self,-1)
        self.notebook=wx.Notebook(self.panel,-1)

        menu_bar = wx.MenuBar()
        file_menu = wx.Menu()
        file_menu.Append(110,"&Reload Commands\tCtrl+r")
        self.Bind(wx.EVT_MENU,self.ReloadScript,id=110)
        file_menu.AppendSeparator()
        file_menu.Append(100,"&Quit\tCtrl+q")
        self.Bind(wx.EVT_MENU,self.Close,id=100)
        menu_bar.Append(file_menu,"&File")


        command_info=wx.StaticText(self.panel,-1,"Manual Command:")
        self.command=wx.TextCtrl(self.panel,-1,style=wx.WANTS_CHARS)
        self.command.Bind(wx.EVT_KEY_UP,self.ParseManualCommand)


        self.stats_panel=AutoSizeListCtrl(self.notebook, -1,style=wx.LC_REPORT|wx.BORDER_NONE|wx.LC_VIRTUAL)
        for i,col in enumerate(("Unit","State","Last Update")): self.stats_panel.InsertColumn(i,col)
        self.stats_panel.SetItemCount(0)

        self.commands_panel=AutoSizeListCtrl(self.notebook, -1,style=wx.LC_REPORT|wx.BORDER_NONE)
        for i,col in enumerate(("Addresses","Function","Time","Days")): self.commands_panel.InsertColumn(i,col)
        try: self.AddCommands(self.script.commands)
        except AttributeError: pass

        self.triggers_panel=AutoSizeListCtrl(self.notebook, -1,style=wx.LC_REPORT|wx.BORDER_NONE)
        for i,col in enumerate(("Addresses","Function","Time","Days","Dates","Action","Last Trigger")): self.triggers_panel.InsertColumn(i,col)

        self.notebook.AddPage(self.stats_panel, "Unit States")
        self.notebook.AddPage(self.commands_panel, "Commands")
        self.notebook.AddPage(self.triggers_panel, "Triggers")

        main_sizer=wx.BoxSizer(wx.VERTICAL)
        command_sizer=wx.BoxSizer(wx.HORIZONTAL)
        command_sizer.Add(command_info,0,wx.ALIGN_CENTER_VERTICAL|wx.LEFT,4)
        command_sizer.Add(self.command,1,wx.EXPAND|wx.RIGHT,2)

        main_sizer.Add(command_sizer,0,wx.EXPAND|wx.TOP|wx.BOTTOM,2)
        main_sizer.Add(self.notebook,1,wx.EXPAND|wx.LEFT,2)
        self.panel.SetSizer(main_sizer)

        self.SetMenuBar(menu_bar)

        self.go=True
        self.T=Thread(target=self.Run)
        self.T.setDaemon(True)
        self.T.start()
##        self.timer=wx.Timer(self)
##        self.Bind(wx.EVT_TIMER,self.Run,self.timer)
##        self.timer.Start(1000,True)
        self.Bind(wx.EVT_CLOSE,self.Close)

        self.run_commands_stack=[]

    def Close(self,event):
##        self.timer.Stop()
        self.go=False
        if self.on_close_callback:
            self.on_close_callback()
        self.Hide()
        self.T.join(3)
        self.Destroy()

    def AddrSort(self,arg1,arg2):
        a1=int(arg1[0][1:]); a2=int(arg2[0][1:])#This sorts the unit addresses by the number after the house code
        if a1>a2:
            return 1
        elif a1<a2:
            return 2
        return 0

    def UpdateUnitsStates(self,states):
        new_states=states.items()
        if new_states!=self.stats_panel.units_states:#Only update the control if we need to
            self.stats_panel.units_states=new_states
            self.stats_panel.SetItemCount(len(new_states))
            self.stats_panel.Refresh()
        #Now we run manual commands because this is where the update thread is
        #and we now have control of the conn.
        try:
            self.RunManualCommandsStack()
        except:
            self.run_commands_stack=[]

##    def UpdateUnitsStates(self,states):
##        self.stats_panel.DeleteAllItems()
##        states=states.items()
##        states.sort(self.AddrSort)
##        for i,data in enumerate(states):
##            key,value=data
##            index = self.stats_panel.InsertStringItem(sys.maxint, key)
##            try:
##                state_val=str(round(float(value[0]),2))+"%"
##            except ValueError:
##                state_val=str(value[0])


    def AddCommands(self,commands):
        for i,command in enumerate(commands):
            index = self.commands_panel.InsertStringItem(sys.maxint, ", ".join(command.addresses))
            function=command.type+" "+command.function
            if command.function in ("DIM","BRIGHT"):
                function="%s %s %s"%(command.type,command.function,command.dims)
            function=function.title()

            self.commands_panel.SetStringItem(index, 1, function)

            self.commands_panel.SetStringItem(index, 2, PrettyTime(command.time))
            days="";last=-1
            for i in command.days:
                days+="-"*(i-last-1)+days_of_the_week[i]
                last=i
            self.commands_panel.SetStringItem(index, 3, days)
            self.commands_panel.SetItemData(index, i)

    def ParseManualCommand(self,event):
        if event.GetKeyCode() == wx.WXK_RETURN:
            cmd_text=self.command.GetValue()
            if self.conn:
                cmd=cmd_text.strip().upper().split(" ")
                if len(cmd)>1:
                    self.run_commands_stack.append(cmd[:])
                    self.command.SetValue("")

    def RunManualCommandsStack(self):
        if self.run_commands_stack:
            for cmd in self.run_commands_stack:
                func_house_code=""
                function="";dims=0
                for part in cmd:
                    part=part.strip()
                    if part[0].isalpha() and part[1:].isdigit():
                        func_house_code=part[0]
                        self.conn.SendAddr(part)
                    elif part.isdigit():
                        dims=int(part)
                    else:
                        function=part
                if function:
                    self.conn.SendFunc(func_house_code+" "+function,dims)

            self.run_commands_stack=[]

    def ReloadScript(self,event):
        self.script.Reload()
        self.commands_panel.DeleteAllItems()
        self.AddCommands(self.script.commands)

    def Run(self,event=None):
        if self.run!=None:
            while self.go:
                self.run()
##            print "Done!"
##            self.timer.Start(1000,True)


# This is just for testing the GUI part (aka just how it looks)
if __name__ == "__main__":
    app=wx.App()
    win=MainWindow(None)
    win.Show()
    app.MainLoop()


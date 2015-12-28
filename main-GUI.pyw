#!/usr/bin/env python
import json
from os import name as os_name

import interface
import scripts
import GUI
import cli


port_name = "COM1"
if os_name in ('posix',):
    port_name = "/dev/ttyUSB0"
conn = interface.InterfaceCon(port_name, 4800)

main_script = scripts.Script("data/commands.txt")
try:
    f = open("data/status.stat", "r")
    units_states = json.loads(f.read().split("\n")[1])
    f.close()
except:
    units_states = {}


def UpdateX10():
    global units_states, run_commands

    receive = conn.Read()

    if receive == "\x5a": #An X10 Transmission has been sent
        conn.ReceiveTrans() #Tell the X10 interface connection to receive it
    if "A2" in units_states and units_states["A2"] == "ON":
        print "action time!"
        conn.SendAddr("A2")
        conn.SendFunc("A DIM",7)

    main_script.Run(conn,units_states)

    units_states = interface.ParseHistory(conn.history,units_states)
    conn.history = []
    win.UpdateUnitsStates(units_states)


def SaveAndClose():
    main_script.SaveStates()
    try:
        f = open("data/status.stat","a")
        f.write("\n")
        json.dump(units_states,f)
        f.close()
    except: #We couldn't save the unit states for some reason. Don't worry about it. Make sure we close the conn!
        pass
    conn.Close()

try:
    app = GUI.wx.App()
    conn.SendAddr("A2")
    conn.SendFunc("A OFF")
    win = GUI.MainWindow(conn=conn,script=main_script,run=UpdateX10)
    win.Show()
    win.on_close_callback = SaveAndClose
    # We may have loaded some state info from the status file so we need to display it
    # other wise it will show up, but it takes a second till UpdateX10 is called in
    # the main loop stuff
    win.UpdateUnitsStates(units_states)

    app.MainLoop()

finally:
    conn.Close()


# X10 Serial Interface

This project provides a nice abstraction layer for an X10 Home Automation serial interface along with two interfaces: GUI, and of course, CLI. There is also a simple bluetooth server that works with [X10-My Home Android App](https://github.com/jpypi/X10-My-Home). These interfaces will keep track of known state, allow control of units, and viewing scheduled commands. There is a small scheduling syntax for a commands file. This file lets one schedule events such as ON, OFF, DIM, and BRIGHT for any unit at any time repeating on specified days of the week.

Example command script syntax:

```
// Some Variables
living room lamp=a5
master bed left=a2

/*
   C-style comments supported
*/
living room lamp on @ 7:30am MTWRF--
master bed left dim 10 @ 10:00pm MTWR--S
```


## Todo
- Update GUI to work with the new state manager
- Clean repeated code between GUI and CLI main start scripts

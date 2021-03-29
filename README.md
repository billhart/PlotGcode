# PlotGcode
 Python utility libraries for drawbot/nodebox 1,2/plotdevice/shoebot for drawing / writing machines -sends gcode to a serial device or to a file.  Implementing the drawbot et al drawing libraries in Gcode.
 Currently Shoebot seems to be the easiest to support.
 Versions to support -
 	KratzwriterII 	- Drum based writing machine with sprockets and fanfold paper and solenoid pen lifter - Rumba board / Marlin FW (2.x) and hacked Nvidia Shield (Ubuntu 16.04) Python 2
 	KratzwriterIII	- Drum based writing machine with sprockets and fanfold paper and solenoid pen lifter - Marlin FW (2.x) and Jetson board (Ubuntu 18.04) Python 3
 	PlotCNC	- CoreXY drawing machine solenoid pen lifter - Replicape / Redeem (Cubic splines converted to biarcs G2/G3) - Gcode via file
 	PolarCNC	- Wall mounted polargraphs - Firmware / Software controller from Marginally Clever, plot gcode to file, cubic splies converted to biarcs (MC's code for converting DXF/SVG drawings is painfully slow for large files).

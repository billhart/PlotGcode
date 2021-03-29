__author__ = 'Bill Hart'

import numpy as np
import zplib.curve.interpolate as spline
from bezier import *
import serial
import time
import math

header = """
M42 P6 S0
G90
G92 X0 Y0

"""

footer = """
M4107 P3
G0 X0 Y0

"""

penup = """
M107 P3
G4 P300
"""

pendown = """
M106 P3 S255
G4 P120
"""


resolution = 0.1
scale = 1.0
draw = False
ser = False


WIDTH = 100.0
HEIGHT = 100.0
OFFSET = (0.0,0.0)
DRAWSPEED = 2000.0
MOVESPEED = 7500.0

def delta(p1,p2):
    return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)


def gwrite(gcodes):
    global draw,ser
    for gcode in gcodes.splitlines():
        if len(gcode):
            draw.write(gcode + "\n")
            if ser:
                draw.readline()

def size(width,height,offset=(0.0,0.0)):
    global WIDTH, HEIGHT, OFFSET
    WIDTH = width
    HEIGHT = height
    OFFSET = offset

def direct(port):
    global draw
    global ser
    ser = True
    print "Initialising writing"
    draw = serial.Serial(port,115200)
    draw.write("\r\n\r\n")
    time.sleep(10)  # Wait for grbl to initialize
    draw.reset_input_buffer()
    print "writing initalised"
    gwrite(penup)
    print "penup"
    gwrite("G21")
    gwrite("G28 X")
    print "homed"
    gwrite("G90")
    print "ready to go"


def export(filename):
    global draw
    draw = open(filename + ".g","w")
    gwrite(header)

def check(x,y):
    if x >= 0.0 and y>= 0.0 and x <= WIDTH and y <= HEIGHT:
        return True
    else:
        return False

def advance(y):
    gwrite("G0 X0 Y%2.f" % y)
    gwrite("G92 X0 Y0")


def path(pts, smooth=True, filter=False):
    global pen
    #print resolution
    if draw:
        if filter:
            fpts = []
            fpts.append(pts[0])
            for pt in pts[1:]:
                if delta(fpts[-1],pt) > filter:
                    fpts.append(pt)
            if (pt != fpts[-1]).all():
                fpts.append(pt)
            pts = np.array(fpts)
        gcode = "G0 X%.3f Y%.3f F%.0f" % (pts[0, 0], pts[0, 1], MOVESPEED)
        gwrite(gcode)
        gwrite(pendown)
        if smooth and len(pts) > 2:
            tck = spline.fit_spline(pts,smoothing=0.0)
            beziers = spline.spline_to_bezier(tck)
            for bezier in beziers:
#                   bez = map(tuple,beziers.pop(0))
                cubicB = CubicBezier(bezier[0],bezier[1],bezier[2],bezier[3])
                arcs = cubicB.biarc_approximation()
                for arc in arcs:
                    if isinstance(arc,Line):
                        gcode = "G1 X%.3f Y%.3f F%.0f" %(arc.p2.x, arc.p2.y, DRAWSPEED)
                    elif isinstance(arc,Arc):
                        arcv = arc.center - arc.p1
                        if arc.is_clockwise():
                            gcode = "G2 X%.3f Y%.3f I%.3f J%.3f F%.0f" % (arc.p2.x, arc.p2.y, arcv.x, arcv.y, DRAWSPEED)
                        else:
                            gcode = "G3 X%.3f Y%.3f I%.3f J%.3f F%.0f" % (arc.p2.x, arc.p2.y, arcv.x, arcv.y, DRAWSPEED)
                    gwrite(gcode)
        else:
            for pt in pts[1:]:
                gcode = "G1 X%.3f Y%.3f F%.0f" % (pt[0], pt[1], DRAWSPEED)
                gwrite(gcode)
        gwrite(penup)
        #gwrite("G4 P1000")
        #draw.flush()
    else:
        print "Nothing open to draw onto"

def line(x1,y1,x2,y2):
    gcode = "G0 X%.3f Y%.3f F%.0f" % (x1,y1,MOVESPEED)
    gwrite(gcode)
    gwrite(pendown)
    gcode = "G0 X%.3f Y%.3f F%.0f" % (x2,y2,DRAWSPEED)
    gwrite(gcode)
    gwrite(penup)

def close():
    global draw
    if draw:
        gwrite(footer)
        draw.close()
        draw = False


if __name__ == '__main__':
    export("testspline")
    pts = np.array([[1,1],[2,2],[3,3],[1,3],[4,2]]) * 100.0
    path(pts)
    close()
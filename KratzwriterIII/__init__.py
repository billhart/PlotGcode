__author__ = 'Bill Hart'

import numpy as np
import plotcnc.zplib.curve.interpolate as spline
import serial
import time
import math
import re

header = """
M42 P205 S0
G28 X
G90
G92 X0 Y0
M211 S0
M120
M110 N0

"""

footer = """
M400
M42 P205 S0
G0 X0 Y50
G92 X0 Y0
"""

penup = """
M400
M42 P205 S0
G4 P300
"""

pendown = """
M400
M42 P205 S255
G4 P120
"""


resolution = 0.1
scale = 1.0
draw = False
ser = False
nline = 0
resend = re.compile('(^rs [Nn]?)|(^Resend:)')



WIDTH = 100.0
HEIGHT = 100.0
OFFSET = (0.0,0.0)
DRAWSPEED = 1000.0
MOVESPEED = 2000.0

def delta(p1,p2):
    return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)

def checksum(line):
    cs = 0
    for i in range(0,len(line)):
        cs ^= ord(line[i]) & 0xff
    cs &= 0xff
    return str(cs)

def gwrite(gcodes):
    global draw, ser, nline, resend
    glines = gcodes.splitlines()
    n = 0
    while n < len(glines):
        rs = 0
        gcode = glines[n]
        if len(gcode):
            nline += 1
            gcode = "N" +str(nline) + " " + gcode + " "
            gcode = gcode + "*" + checksum(gcode) + "\n"
            draw.write(gcode.encode())
            # print gcode
            if ser:
                result = draw.readline().decode('utf-8')
                while result != "ok\n":
                    print(result)
                    if "Last Line" in result:
                        nline = int(result.split(':')[-1]) + 1
                        gcode = glines[n]
                        gcode = "N" + str(nline) + " " + gcode + " "
                        gcode = gcode + "*" + checksum(gcode) + "\n"
                        draw.write(gcode.encode())
                    elif "Resend" in result:
                        rs += 1
                        draw.write(gcode.encode())
                        if rs == 10:
                            print("Too many resends : ", result, gcode)
                            break
                    result = draw.readline().decode('utf-8')
        n = n + 1



def size(width,height,offset=(0.0,0.0)):
    global WIDTH, HEIGHT, OFFSET
    WIDTH = width
    HEIGHT = height
    OFFSET = offset

def direct(port):
    global draw
    global ser
    ser = True
    print("Initialising writing")
    draw = serial.Serial(port,115200)
    #draw.write("\r\n\r\n".encode())
    time.sleep(10)  # Wait for grbl to initialize
    draw.reset_input_buffer()
    print("writing initalised")
    gwrite(penup)
    print("penup")
    gwrite("G21")
    gwrite("G28 X")
    print("homed")
    gwrite("G90")
    print("ready to go")


def export(filename):
    global draw
    draw = open(filename + ".nc","w")
    gwrite(header)

def check(x,y):
    if x >= 0.0 and y>= 0.0 and x <= WIDTH and y <= HEIGHT:
        return True
    else:
        return False

def advance(y):
    global nline
    gwrite("G0 X0 Y%2.f" % y)
    gwrite("G92 X0 Y0")
    gwrite("M110 N0")
    nline = 0


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
        if smooth and len(pts) > 3:
            tck = spline.fit_spline(pts,smoothing=0.0)
            beziers = spline.spline_to_bezier(tck)
            bezier = beziers.pop(0)
            gcode = "G0 X%.3F Y%.3F F%.0f" % (bezier[0, 0] + OFFSET[0], bezier[0, 1] + OFFSET[1], MOVESPEED)
            gwrite(gcode)
            gwrite(pendown)
            if bezier.shape[0] == 4:
                gcode = "G5 I%.3F J%.3F P%.3F Q%.3F X%.3F Y%.3F F%.0f" % (bezier[1, 0] - bezier[0, 0] + OFFSET[0], bezier[1, 1] - bezier[0, 1] + OFFSET[1],\
                                                                           bezier[2, 0] - bezier[3, 0], bezier[2, 1] - bezier[3, 1],\
                                                                           bezier[3, 0] + OFFSET[0], bezier[3, 1] + OFFSET[1], DRAWSPEED)
            elif bezier.shape[0] == 3:
                gcode = "G5 I%.3F J%.3F P%.3F Q%.3F X%.3F Y%.3F F%.0f" % (bezier[1, 0] - bezier[0, 0] + OFFSET[0], bezier[1, 1] - bezier[0, 1] + OFFSET[1], \
                                                                        bezier[1, 0] - bezier[2, 0], bezier[1, 1] - bezier[2, 1], \
                                                                        bezier[2, 0] + OFFSET[0], bezier[2, 1] + OFFSET[1], DRAWSPEED)
            else:
                gcode = "G1 X%.3F Y%.3F F%.0f" % (bezier[1,0] + OFFSET[0], bezier[1,1] + OFFSET[1], DRAWSPEED)
            gwrite(gcode)

            for bezier in beziers:
                if bezier.shape[0] == 4:
                    gcode = "G5 I%.3F J%.3F P%.3F Q%.3F X%.3F Y%.3F F%.0f" % (bezier[1, 0] - bezier[0, 0] + OFFSET[0], bezier[1, 1] - bezier[0, 1] + OFFSET[1],
                                                                            bezier[2, 0] - bezier[3, 0], bezier[2, 1] - bezier[3, 1], \
                                                                            bezier[3, 0] + OFFSET[0], bezier[3, 1] + OFFSET[1], DRAWSPEED)
                else:
                    gcode = "G5 I%.3F J%.3F P%.3F Q%.3F X%.3F Y%.3F F%.0f" % (bezier[1, 0] - bezier[0, 0] + OFFSET[0], bezier[1, 1] - bezier[0, 1] + OFFSET[1], \
                                                                        bezier[1, 0] - bezier[2, 0], bezier[1, 1] - bezier[2, 1], \
                                                                        bezier[2, 0] + OFFSET[0], bezier[2, 1] + OFFSET[1], DRAWSPEED)
                gwrite(gcode)
        else:
            if delta(pts[0], pts[1]) > 1:
                print("Large Gap ",pts[0],pts[1])
            ptx = pts[:,0]
            pty = pts[:,1]
            gcode = "G0 X%.3F Y%.3F F%.0f" % (ptx[0] + OFFSET[0], pty[0] + OFFSET[1], MOVESPEED)
            gwrite(gcode)
            gwrite(pendown)
            gcode = "G1 X%.3F Y%.3F F%.0f" % (ptx[1] + OFFSET[0], pty[1] + OFFSET[1], DRAWSPEED)
            gwrite(gcode)

        gwrite(penup)
        #gwrite("G4 P1000")
        #draw.flush()
    else:
        print("Nothing open to draw onto")

def close():
    global draw
    if draw:
        gwrite(footer)
        draw.close()
        draw = False

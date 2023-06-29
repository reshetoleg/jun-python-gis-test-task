from cmath import log
from time import sleep
from logging import getLogger
from flask import Flask, request, render_template, redirect, url_for
import os
import math
import base64
import matplotlib.pyplot as plt
import fiona
import random


logger = getLogger(__name__)
app = Flask(__name__)
OUTPUT_TYPE_COLOURIZED = 10011
OUTPUT_TYPE_STYLED = 10012

@app.route('/', methods=['GET'])
def index():
    return render_template('./index.html')
@app.route('/process', methods=['POST'])
def process_file():
    # Check if a file was uploaded
    type = request.form.get('type')
    result = process_shapefile('sample/roads.shp',type)
    return render_template('output.html', result=result)

def process_shapefile(filename,type):
    colors = ['red', 'blue', 'green', 'yellow','black','brown']  # Predefine colors for road
    styles = ['-','--','-.',':']
    roads = []
    icolor = []
    with fiona.open(filename) as shp:
        fig, ax = plt.subplots(figsize=(12, 12)) # Increase the figure size
        prev = None
        prev_color = None
        for street in shp:
     
            roads, road_index = getRoadIndex(roads,street)
            if(road_index == 0):
                color = colors[random.randint(0, 5)]
                coords = street['geometry']['coordinates']
                roads.append([coords[0],coords[-1]])
                icolor.append(color)
            else:
                color = icolor[road_index]
          
            style = styles[random.randint(0, 3)]
            # Plot the street using the unique color
            coords = street['geometry']['coordinates']
            x, y = zip(*coords)
            if int(type) == OUTPUT_TYPE_COLOURIZED:
                ax.plot(x, y, color=color)
            else:
                ax.plot(x, y, linestyle=style,color=color)
            prev = street
            prev_color = color
        # Save the figure as a PNG file
        output_file = 'colored_streets.png'
        plt.savefig(output_file)

        # Convert the PNG file to base64 format
        with open(output_file, 'rb') as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode('utf-8')

        # Return the base64-encoded image
        return encoded_image

def is_connected(coords1, coords2):
    # Implement your logic to check if two lines are connected
    # Here's a simple example where we consider two lines connected
    # if they share at least one coordinate point
    return any(coord in coords2 for coord in coords1)
    
def getRoadIndex(roads,street):
    #emtpy array
    if len(roads) == 0:
        return [],0
    c_coords = street['geometry']['coordinates']
    c_start = c_coords[0]
    c_end = c_coords[-1]
    c_head = getHeading(c_start,c_end)
    i = 0
    connected = []
    for road in roads:
        start = road[0]
        end = road[-1]
        head = getHeading(start,end)
        if start in [c_start,c_end] or end in [c_start, c_end]:
            connected.append([i,abs(c_head-head)])
        i = i + 1
    if len(connected) == 0:
        return roads,0
    else:
        min_heading = 0
        index = 0
        for i,heading in connected:
            print(i,heading)
            if heading>min_heading:
                min_heading = heading
                index = i
       
        roads[index] =  list(set([c_start,c_end,roads[index][0], roads[index][-1]]))
        return roads,index

def getHeading(start_point, end_point):
    x1, y1 = start_point
    x2, y2 = end_point
    delta_x = x2 - x1
    delta_y = y2 - y1
    # Calculate the angle between the two points using arctan2
    angle_rad = math.atan2(delta_y, delta_x)
    # Convert radians to degrees
    angle_deg = math.degrees(angle_rad)

    # Adjust the angle to be between 0 and 360 degrees
    if angle_deg < 0:
        angle_deg += 360

    return angle_deg
if __name__ == '__main__':
    app.run()




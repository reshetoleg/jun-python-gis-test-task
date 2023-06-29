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
from collections import Counter
from shapely.geometry import MultiLineString, LineString, shape
import geopandas as gpd
import networkx as nx

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
    data = gpd.read_file(filename)
    street_lines = []
    graph = nx.Graph()  # Create an empty graph

    for row in data.iterrows():
        geometry = row[1].geometry
        if isinstance(geometry, LineString):
            street_lines.append(geometry)
    fig, ax = plt.subplots(figsize=(12, 12)) # Increase the figure size
    while len(street_lines)>0:
        startnode = street_lines[0]
        street_lines.remove(startnode)
        road,street_lines = find_street(street_lines,[startnode])
        print(len(street_lines))
        color = colors[random.randint(0, 4)]
        # Generate the image with colored streets
        for line in road:
            if isinstance(line, LineString):
                # Extracting the coordinates from the LineString
                coordinates = list(line.coords)
                x, y = zip(*coordinates)
                if int(type) == OUTPUT_TYPE_COLOURIZED:
                    ax.plot(x, y, color=color)
                else:
                    ax.plot(x, y, linestyle=style,color=color)

    # Save the figure as a PNG file
    output_file = 'colored_streets.png'
    plt.savefig(output_file)

    # Convert the PNG file to base64 format
    with open(output_file, 'rb') as image_file:
        encoded_image = base64.b64encode(image_file.read()).decode('utf-8')

    # Return the base64-encoded image
    return encoded_image

def find_street(lines, road):
    startline = merge_linestrings(road)
    if not isinstance(startline, LineString): return road,lines
    heading = getHeading(startline.coords[0], startline.coords[-1])
    connected = []
    for line in lines:
        merged = False
        # Check if the current line intersects with any existing street
        if startline.coords[0] in line.coords or startline.coords[-1] in line.coords:
            connected.append(line)
    if len(connected)==0: 
        return road,lines    
    else:
        #find straight forward the line
        min = 360
        choosed = None
        for line in connected:
            cheading = getHeading(line.coords[0], line.coords[-1])
            if min > abs(heading - cheading):
                min = abs(heading-cheading)
                choosed = line
               
        road.append(choosed)
        lines.remove(choosed)
        find_street(lines, road)
    return road,lines

def merge_linestrings(linestrings):
    merged_coords = []
    for line in linestrings:
        merged_coords.extend(list(line.coords))
    
    merged_linestring = LineString(merged_coords)
    return merged_linestring

def is_connected(coords1, coords2):
    # Implement your logic to check if two lines are connected
    # Here's a simple example where we consider two lines connected
    # if they share at least one coordinate point
    return any(coord in coords2 for coord in coords1)
    
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




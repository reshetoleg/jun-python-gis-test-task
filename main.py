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
from shapely.geometry import MultiLineString, LineString, shape, Point
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
    colors = ['red','blue','green','brown','black',"#851414", "#0c7392", "pink", "#01558f","#e5e614",'#fe14b7']
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

    lines = []

    for line in street_lines:
        segments = devide_into_segment(line)
        lines = lines+segments
    
    fig, ax = plt.subplots(figsize=(12, 12)) # Increase the figure size
    i = 1
    color_set = set()  # Set to store unique colors
    '''
    colors = []
    while len(colors) < len(street_lines):
        color = '#%06x' % random.randint(0, 0xFFFFFF)
        # Sharpen the color by increasing its saturation
        color = color[:-2] + 'FF'
        if color not in color_set:
            color_set.add(color)
            colors.append(color)
    '''

    street_lines.sort(key=lambda line: line.coords[0][0])
    lines.sort(key=lambda line: line.centroid.y,reverse=True)
    
    while len(lines)>0:
        i = i + 1
        startnode = lines[0]
        lines.remove(startnode)
        road,lines = find_street(lines,[startnode],startnode.coords[0],startnode.coords[-1])
        style = styles[random.randint(0, 3)]
        # Generate the image with colored streets
        for line in road:
            if isinstance(line, LineString):
                # Extracting the coordinates from the LineString
                coordinates = list(line.coords)
                x, y = zip(*coordinates)
                if int(type) == OUTPUT_TYPE_COLOURIZED:
                    ax.plot(x, y, color=colors[i%11])
                else:
                    ax.plot(x, y, linestyle=style,color=colors[i%11])

    # Save the figure as a PNG file
    output_file = 'colored_streets.png'
    plt.savefig(output_file)

    # Convert the PNG file to base64 format
    with open(output_file, 'rb') as image_file:
        encoded_image = base64.b64encode(image_file.read()).decode('utf-8')

    # Return the base64-encoded image
    return encoded_image

def devide_into_segment(line):
    segments = []
    if isinstance(line, LineString) and len(line.coords) > 2:
         for i in range(len(line.coords) - 1):
            start_point = line.coords[i]
            end_point = line.coords[i + 1]
            segment = LineString([start_point, end_point])
            segments.append(segment)
    else:
        segments.append(line)
    return segments

def find_street(lines, road, startpoint, lastpoint):
    connected = []
    before = road[-1].coords[0]
    if len(road)>1:
        if lastpoint == road[-1].coords[0]:
            lastpoint = road[-1].coords[-1]
        elif lastpoint == road[-1].coords[-1]:
            lastpoint = road[-1].coords[0]
            before = road[-1].coords[-1]
        else:
            if(lastpoint == road[0].coords[0]):
                before = road[0].coords[-1]
            else:
                before = road[0].coords[0]
            
    heading = getHeading(before[0],before[1],lastpoint[0],lastpoint[1])
  
    for line in lines:   
        # Check if the current line intersects with any existing street
        if  lastpoint in line.coords:
            connected.append(line)

    if len(connected)==0:
        if(startpoint != None):
             find_street(lines, road, None, startpoint)
        else:
            return road,lines    
    else:
        #find straight forward the line
        min = 360
        choosed = None
        for index, line in enumerate(connected):
            cheading = 0
            if  lastpoint == line.coords[0]:
                cheading = getHeading(lastpoint[0], lastpoint[1],line.coords[-1][0], line.coords[-1][1])
            else:
                cheading = getHeading(lastpoint[0], lastpoint[1],line.coords[0][0], line.coords[0][1])
            print(heading,cheading)
            temp = abs(heading - cheading)
            #if there are more than 2 connected and heading is much different not accept
            addition = True
            if len(connected)>1 and temp>80: addition = False
            if min > temp and addition == True:
                min = temp
                choosed = line
        print('-------------') 
        if choosed == None: return road,lines
        road.append(choosed)
        lines.remove(choosed)
        find_street(lines, road, startpoint, lastpoint)
    return road,lines

def divide_into_single_lines(line_streets):
    single_lines = []
    coordinates = list(line_streets.coords)
    single_lines.append(LineString(coordinates))
    return single_lines

def merge_linestrings(linestrings):
    merged_coords = []
    for line in linestrings:
        merged_coords.extend(list(line.coords))
    
    merged_linestring = LineString(merged_coords)
    return merged_linestring
    
def getHeading(lat1, lon1, lat2, lon2):
    # Convert latitude and longitude to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    # Calculate the difference in longitudes
    delta_lon = lon2_rad - lon1_rad

    # Calculate the heading angle using the haversine formula
    y = math.sin(delta_lon) * math.cos(lat2_rad)
    x = math.cos(lat1_rad) * math.sin(lat2_rad) - (math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(delta_lon))
    heading_rad = math.atan2(y, x)

    # Convert radians to degrees
    heading_deg = math.degrees(heading_rad)

    # Adjust the heading angle to be between 0 and 360 degrees
    if heading_deg < 0:
        heading_deg += 360

    return heading_deg

if __name__ == '__main__':
    
    app.run()




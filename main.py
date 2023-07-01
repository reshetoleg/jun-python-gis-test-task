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
    i = 1
    color_set = set()  # Set to store unique colors
    colors = []

    while len(colors) < len(street_lines):
        color = '#%06x' % random.randint(0, 0xFFFFFF)
        if color not in color_set:
            color_set.add(color)
            colors.append(color)

   

    #street_lines.sort(key=lambda line: line.coords[0][0])
    street_lines.sort(key=lambda line: line.centroid.y,reverse=True)
    
    while len(street_lines)>0:
        i = i + 1
        startnode = street_lines[0]
        street_lines.remove(startnode)
        road,street_lines = find_street(street_lines,[startnode],startnode.coords[0])
        style = styles[random.randint(0, 3)]
        # Generate the image with colored streets
        for line in road:
            if isinstance(line, LineString):
                # Extracting the coordinates from the LineString
                coordinates = list(line.coords)
                x, y = zip(*coordinates)
                if int(type) == OUTPUT_TYPE_COLOURIZED:
                    ax.plot(x, y, color=colors[i])
                else:
                    ax.plot(x, y, linestyle=style,color=colors[i])

    # Save the figure as a PNG file
    output_file = 'colored_streets.png'
    plt.savefig(output_file)

    # Convert the PNG file to base64 format
    with open(output_file, 'rb') as image_file:
        encoded_image = base64.b64encode(image_file.read()).decode('utf-8')

    # Return the base64-encoded image
    return encoded_image

def find_street(lines, road, lastpoint):
    startline = merge_linestrings(road)
    if not isinstance(startline, LineString): return road,lines
    direction1 = get_line_direction(road[-1])
    connected = []
    #choose last point from new added line
    before = road[-1].coords[0]
    if lastpoint != road[-1].coords[-1]:
        lastpoint = road[-1].coords[-1]
    else:
        lastpoint = road[-1].coords[0]
        before = road[-1].coords[-1]

    heading = getHeading(road[-1].coords[0], road[-1].coords[-1])

   
    for line in lines:
        if(len(line.coords)>2):
            print(line)
        # Check if the current line intersects with any existing street
        if  lastpoint == line.coords[0] or lastpoint == line.coords[-1]:
            connected.append(line)

    if len(connected)==0: 
        return road,lines    
    else:
        #find straight forward the line
        min = 360
        choosed = None
        for index, line in enumerate(connected):
            cheading = getHeading(line.coords[0], line.coords[-1])
            '''
            if before[0]<lastpoint[0]:
                if line.coords[0][0] < line.coords[-1][0]:
                    cheading = getHeading(line.coords[0], line.coords[-1])
                else:
                    cheading = getHeading(line.coords[-1], line.coords[0])
            else:
                if line.coords[0][0] > line.coords[-1][0]:
                    cheading = getHeading(line.coords[0], line.coords[-1])
                else:
                    cheading = getHeading(line.coords[-1], line.coords[0])
            '''
            direction2  = get_line_direction(line)
            angle = calculate_angle(direction1,direction2)

           
            #if lastpoint == line.coords[-1]:
            #    latlon_angle = calculate_latlonangle(before[0],before[1],lastpoint[0],lastpoint[1], line.coords[0][0], line.coords[0][1])
            #else:
            #    latlon_angle = calculate_latlonangle(before[0],before[1],lastpoint[0],lastpoint[1], line.coords[-1][0], line.coords[-1][1])
            temp = abs(heading - cheading)
            if min > temp :
                min = temp
                choosed = line
            
        if choosed == None: return road,lines    
        road.append(choosed)
        lines.remove(choosed)
        #if len(lines) > 770:
        find_street(lines, road, lastpoint)
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

def get_line_direction(line):
    start_point, end_point = line.coords[0], line.coords[-1]
    return end_point[0] - start_point[0], end_point[1] - start_point[1]

def calculate_angle(vector1, vector2):
    x1, y1 = vector1
    x2, y2 = vector2
    dot_product = x1 * x2 + y1 * y2
    magnitude_product = (x1**2 + y1**2) ** 0.5 * (x2**2 + y2**2) ** 0.5
    return math.degrees(math.acos(dot_product / magnitude_product))

def calculate_latlonangle(lat1, lon1, lat2, lon2, lat3, lon3):
     # Convert latitude and longitude to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    lat3_rad = math.radians(lat3)
    lon3_rad = math.radians(lon3)

    # Calculate the great-circle distances
    dist12 = math.acos(math.sin(lat1_rad) * math.sin(lat2_rad) +
                       math.cos(lat1_rad) * math.cos(lat2_rad) * math.cos(lon2_rad - lon1_rad))
    dist23 = math.acos(math.sin(lat2_rad) * math.sin(lat3_rad) +
                       math.cos(lat2_rad) * math.cos(lat3_rad) * math.cos(lon3_rad - lon2_rad))
    
    # Check for invalid distances
    if math.isnan(dist12) or math.isnan(dist23):
        return 0

    # Calculate the angle using the law of cosines
    try:
        angle = math.acos((math.cos(dist12) - math.cos(dist23) * math.cos(dist12)) /
                          (math.sin(dist23) * math.sin(dist12)))
    except ValueError:
        return 0

    # Convert the angle to degrees
    angle_degrees = math.degrees(angle)

    return angle_degrees

if __name__ == '__main__':
    
    app.run()




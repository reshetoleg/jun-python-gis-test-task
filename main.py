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
    for row in data.iterrows():
        geometry = row[1].geometry
        if isinstance(geometry, LineString):
            street_lines.append(geometry)
    plotted_lines = colorize_streets(street_lines)

    # Generate the image with colored streets
    fig, ax = plt.subplots(figsize=(12, 12)) # Increase the figure size
    for x, y, color in plotted_lines:
        
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

def colorize_streets(lines):
    streets = {}
    colored_lines = []

    for line in lines:
        merged = False
        # Check if the current line intersects with any existing street
        for street_id, street in streets.items():
            if street.intersects(line):
                if is_cross_pattern(street, line):
                    continue  # Skip merging if it forms a cross pattern
                streets[street_id] = street.union(line)
                colored_lines.append((line, street_id))
                merged = True
                break
        
        # If the line doesn't intersect with any existing street, create a new street
        if not merged:
            street_id = len(streets) + 1
            streets[street_id] = line
            colored_lines.append((line, street_id))

    # Assign random colors to each street
    colors = ['#%06x' % random.randint(0, 0xFFFFFF) for _ in range(len(streets))]

    # Convert lines to (x, y) coordinates for plotting
    plotted_lines = []
    for line, street_id in colored_lines:
        x, y = line.xy
        plotted_lines.append((x, y, colors[street_id - 1]))

    return plotted_lines

def is_cross_pattern(street, line):

    # Extract the coordinates of the street and line
    if isinstance(street, LineString):
        street_coords = list(street.coords)
    elif isinstance(street, MultiLineString):
        street_coords = [list(subline.coords) for subline in street.geoms]
    else:
        raise ValueError("Invalid geometry type for street")
    
    line_coords = list(line.coords)

    # Check if any of the street coordinates are within the bounds of the line
    try:
        for coords in street_coords:
            if not isinstance(coords[0],float):
                for coord in coords:
                    x,y = coord
                    if min(line_coords[0][0], line_coords[1][0]) <= x <= max(line_coords[0][0], line_coords[1][0]):
                        # Check if the y-coordinate is within the range of the line
                        if min(line_coords[0][1], line_coords[1][1]) <= y <= max(line_coords[0][1], line_coords[1][1]):
                            print(x,y)
                            return True  # Intersection forms a cross pattern
            x, y = coords
            
            if not isinstance(x, float):
                for coord in coords:
                    x,y = coord
                    if min(line_coords[0][0], line_coords[1][0]) <= x <= max(line_coords[0][0], line_coords[1][0]):
                        # Check if the y-coordinate is within the range of the line
                        if min(line_coords[0][1], line_coords[1][1]) <= y <= max(line_coords[0][1], line_coords[1][1]):
                            print(x,y)
                            return True  # Intersection forms a cross pattern
           
            # Check if the x-coordinate is within the range of the line
            if min(line_coords[0][0], line_coords[1][0]) <= x <= max(line_coords[0][0], line_coords[1][0]):
                # Check if the y-coordinate is within the range of the line
                if min(line_coords[0][1], line_coords[1][1]) <= y <= max(line_coords[0][1], line_coords[1][1]):
                    print(x,y)
                    return True  # Intersection forms a cross pattern
    except:
        return False
    return False  # No cross pattern detected

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
            if heading>min_heading:
                min_heading = heading
                index = i
        counter = Counter([c_start,c_end,roads[index][0], roads[index][1]])
        merged  = [x for x in [c_start,c_end,roads[index][0], roads[index][1]] if counter[x] == 1]
        if len(merged)>0:
            roads[index] = merged
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




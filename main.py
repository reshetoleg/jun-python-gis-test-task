from cmath import log
from time import sleep
from logging import getLogger
from flask import Flask, request, render_template, redirect, url_for
import os
import base64
import matplotlib.pyplot as plt
import fiona
import random

logger = getLogger(__name__)
app = Flask(__name__)

@app.route('/', methods=['GET'])
def index():
    return render_template('./index.html')

@app.route('/process', methods=['POST'])
def process_file():
    # Check if a file was uploaded
    '''
    if 'file' not in request.files:
        return redirect(url_for('index'))

    file = request.files['file']
    if file.filename == '':
        return redirect(url_for('index'))

    # Save the uploaded file
    filename = file.filename
    file.save(filename)

    # Process the uploaded file
    result = process_shapefile(filename)

    # Remove the temporary file
    os.remove(filename)
    '''
    result = process_shapefile('sample/roads.shp')
    return result

def process_shapefile(filename):
    colors = ['red', 'blue', 'green', 'yellow','black','brown']  # Predefine colors for road
    with fiona.open(filename) as shp:
        fig, ax = plt.subplots()
        for street in shp:
            color = colors[random.randint(0, 4)]
            # Plot the street using the unique color
            coords = street['geometry']['coordinates']
            print(coords)
            x, y = zip(*coords)
            ax.plot(x, y, color=color)
        # Save the figure as a PNG file
        output_file = 'colored_streets.png'
        plt.savefig(output_file)

        # Convert the PNG file to base64 format
        with open(output_file, 'rb') as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode('utf-8')

        # Return the base64-encoded image
        return encoded_image

if __name__ == '__main__':
    app.run()




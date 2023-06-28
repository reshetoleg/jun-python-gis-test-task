from cmath import log
from time import sleep
from logging import getLogger
from flask import Flask, request, render_template, redirect, url_for
import os
logger = getLogger(__name__)
app = Flask(__name__)

@app.route('/', methods=['GET'])
def index():
    return render_template('./index.html')

@app.route('/process', methods=['POST'])
def process_file():
    # Check if a file was uploaded
    if 'file' not in request.files:
        return redirect(url_for('index'))

    file = request.files['file']
    if file.filename == '':
        return redirect(url_for('index'))

    # Save the uploaded file
    filename = secure_filename(file.filename)
    file.save(filename)

    # Process the uploaded file
    result = process_shapefile(filename)

    # Remove the temporary file
    os.remove(filename)

    return result

def process_shapefile(filename):
    return "OK"

if __name__ == '__main__':
    app.run()




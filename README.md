## DIY Streetview for Krpano Panoramic Viewer
This repository contains Python tools for linking panoramic images into a self-hosted virtual tour, resembling streetview and generating XML configuration files for the Krpano panoramic viewer. These tools allow you to create a custom Streetview-like experience by connecting and displaying your panoramic images.
Currently, the only tested camera model is Ricoh Theta S. If you want to use it with the images, captured by any other camera, you will need to edit Python scripts to change image resolution and names of the XMP image tags in the `convert_panoramas.py`. You're welcome to open an issue on GitHub if you need help with that.

### Scripts
`convert_panoramas.py`: This script generates a point shapefile from a set of panoramic images using their geolocation data and performs geometric correction of the images using Nona from Hugin tools.

`panoramic_calc.py`: This script connects the panoramic images based on a specified radius or a supplied line shapefile, connecting the location of the images. It also creates XML configuration files for the Krpano panoramic viewer containing metadata for each panoramic image point, such as the connected neighboring points and their azimuths.

### Test shapefiles
The `test_shapefiles` directory contains two example shape files. 
* points.shp - this was file created by `convert_panoramas.py`script from the set of panoramic images. 
* lines.shp - this is an example line shape file with the links between the images. It was created by connecting the image locations from `points.shp` in QGIS. 
You might want to use these files as an imput to the `visualize_connections.py` script to learn how it works.

### Requirements
To run these scripts, you'll need Python 3.x and the following packages:

geopandas
matplotlib
pandas
PyQt5
shapely
You can install them using pip:

`pip install geopandas matplotlib pandas PyQt5 shapely`

### Usage
#### 1. Create Point Shapefile and apply geometric correction to the images
Run create_point_shapefile.py to generate a point shapefile using the geolocation data from your set of panoramic images. You'll need to provide the script with the appropriate input parameters (e.g., input image file folder, output image folder, location to save the output point shapefile).

#### 2. Visualize Connections and Generate Krpano XML Configuration Files
Run the panoramic_calc.py script. A graphical user interface (GUI) will open, allowing you to:

Specify whether to use a search radius or line shapefile for determining connections between panoramic images.
Select the point shapefile created using create_point_shapefile.py.
If not using a search radius, select the line shapefile, that you prepaired using QGIS or any other GIS software package.
Select an output folder where the Krpano XML configuration files will be saved.
Click "Run" to visualize the connections and generate the Krpano XML configuration files.
The generated Krpano XML configuration files will contain the following information for each point:

* Point name
* Names of connected neighboring points
* Azimuths of the connections
* The connections between the points will be visualized in the GUI.

### Integration with Krpano Panoramic Viewer
* Create a virtual tour in the KRPano by dropping your input images to `MAKE VTOUR (NORMAL) droplet.bat`.
* Make a copy of the viewer_template folder to a convenient location
* Copy the created image scenes from your tour to the `panos` folder in the copy of the viewer_template folder.
* Copy the xml files, created by the `panoramic_calc.py` to the `scenes` folder in the copy of the viewer_template folder.
* Start your local testing web server or copy the contents to the web server. Navigate to view.html?s=<name of the panoramic image>. KRPano will display you a specific panoramic image. You can then navigate between the scenes using hotspots, double click or using W,A,S,D keys on the keyboard.
* You might want to create a web map, allowing the users to open the links to view.html?s=<name of the panoramic image> to view different panoramas. See the example on using ArcGIS Online at 
https://github.com/ngolosov/CollegeCourtStreetview You could implement a web map using any open source web mappling API such as Leaflet or OpenLayers.
After generating the Krpano XML configuration files, you can use them to set up the Krpano panoramic viewer for your DIY Streetview project. You need to place the created XML files to the `scenes` catalog within the viewer folder. The viewer configuration files will be published separately.

### License
This project is licensed under the MIT License

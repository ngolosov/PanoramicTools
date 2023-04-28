## DIY Streetview for Krpano Panoramic Viewer
This repository contains Python tools for linking panoramic images into a self-hosted virtual tour, resembling streetview and generating XML configuration files for the Krpano panoramic viewer. These tools allow you to create a custom Streetview-like experience by connecting and displaying your panoramic images.

### Scripts
`create_point_shapefile.py`: This script generates a point shapefile from a set of panoramic images using their geolocation data.

`visualize_connections.py`: This script connects the panoramic images based on a specified radius or a supplied line shapefile, connecting the location of the images. It also creates XML configuration files for the Krpano panoramic viewer containing metadata for each panoramic image point, such as the connected neighboring points and their azimuths.

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
1. Create Point Shapefile and apply geometric correction to the images
Run create_point_shapefile.py to generate a point shapefile using the geolocation data from your set of panoramic images. You'll need to provide the script with the appropriate input parameters and files (e.g., image file paths and geolocation data).

2. Visualize Connections and Generate Krpano XML Configuration Files
Run the visualize_connections.py script. A graphical user interface (GUI) will open, allowing you to:

Specify whether to use a search radius or line shapefile for determining connections between points.
Select the point shapefile created using create_point_shapefile.py.
If not using a search radius, select the line shapefile.
Select an output folder where the Krpano XML configuration files will be saved.
Click "Run" to visualize the connections and generate the Krpano XML configuration files.
The generated Krpano XML configuration files will contain the following information for each point:

Point name
Names of connected neighboring points
Azimuths of the connections
The connections between the points will be visualized on a matplotlib plot embedded in the GUI.

Integration with Krpano Panoramic Viewer
After generating the Krpano XML configuration files, you can use them to set up the Krpano panoramic viewer for your DIY Streetview project. You need to place the created XML files to the `scenes` catalog within the viewer folder.

License
This project is licensed under the MIT License

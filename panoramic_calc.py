import os
import random
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QFileDialog, QLabel, QCheckBox, QSpinBox, QHBoxLayout, QGroupBox, QMessageBox, QSizePolicy
from PyQt5.QtCore import Qt
import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

import xml.etree.ElementTree as ET
from xml.dom import minidom
import pandas as pd
from shapely.geometry import Point, LineString
import math
from shapely.ops import split, snap
from shapely.geometry import LineString
import matplotlib.patheffects as path_effects 


def split_line_by_nearest_points(gdf_line, gdf_points, tolerance):
    """
    Split the union of lines with the union of points resulting 
    Parameters
    ----------
    gdf_line : geoDataFrame
        geodataframe with multiple rows of connecting line segments
    gdf_points : geoDataFrame
        geodataframe with multiple rows of single points
    tolerance : float
        maximum distance to snap points to lines
        
    Returns
    -------
    gdf_segments : geoDataFrame
        geodataframe of segments
    """
    # union all geometries
    line = gdf_line.geometry.unary_union
    coords = gdf_points.geometry.unary_union

    # snap and split coords on line
    # returns GeometryCollection
    split_line = split(line, snap(coords, line, tolerance))

    # transform Geometry Collection to GeoDataFrame
    segments = [feature for feature in split_line.geoms]
    gdf_segments = gpd.GeoDataFrame(list(range(len(segments))), geometry=segments)
    gdf_segments.columns = ['index', 'geometry']
    return gdf_segments


def find_connected_neighbors(point_shp, line_shp, buffer_distance=0.01):
    point_gdf = gpd.read_file(point_shp)
    line_gdf = gpd.read_file(line_shp)

    line_gdf = split_line_by_nearest_points(line_gdf, point_gdf, 0.1)

    result = []

    for index, row in point_gdf.iterrows():
        point = row.geometry
        name = row.NAME
        connected_points = []

        buffer = point.buffer(buffer_distance)
        for _, line in line_gdf.iterrows():
            if line.geometry.intersects(buffer):
                coords = line.geometry.coords
                for coord in coords:
                    if Point(coord).distance(point) > buffer_distance:
                        connected_points.append(Point(coord))
                        break

        neighbor_names = []
        azimuths = []
        
        for connected_point in connected_points:
            for _, point_row in point_gdf.iterrows():
                if point_row.geometry.distance(connected_point) <= buffer_distance:
                    neighbor_names.append(point_row.NAME)
                    azimuths.append(calculate_azimuth(connected_point, point))
            


        result.append((name, ",".join(neighbor_names), ",".join(map(str, azimuths))))

    df = pd.DataFrame(result, columns=["Point_Name", "Neighbor_Names", "Azimuths"])
    return df


def calculate_azimuth(point1, point2):
    angle = math.atan2(point2.x - point1.x, point2.y - point1.y)
    azimuth = math.degrees(angle) + 180
    return azimuth % 360


def find_neighbors_within_radius(point_file, radius):
    # Read the point shapefile
    point_gdf = gpd.read_file(point_file)

    # Create a buffer around each point
    point_gdf["geometry"] = point_gdf.buffer(radius)

    # Calculate neighbors and azimuths
    neighbors = []
    azimuths = []

    for idx, row in point_gdf.iterrows():
        current_point = row.geometry.centroid
        neighbors_within_radius = point_gdf[point_gdf.geometry.intersects(row.geometry)].drop(idx)
        
        neighbor_names = []
        neighbor_azimuths = []

        for _, n_row in neighbors_within_radius.iterrows():
            neighbor_point = n_row.geometry.centroid
            neighbor_names.append(n_row["NAME"])
            neighbor_azimuths.append(calculate_azimuth(neighbor_point, current_point))
        
        neighbors.append(','.join(neighbor_names))
        azimuths.append(','.join([str(azimuth) for azimuth in neighbor_azimuths]))

    # Create the DataFrame
    df = pd.DataFrame({
        "Point_Name": point_gdf["NAME"],
        "Neighbor_Names": neighbors,
        "Azimuths": azimuths
    })

    return df


def prettify(elem):
    rough_string = ET.tostring(elem, 'UTF-8')
    reparsed = minidom.parseString(rough_string)
    pretty_xml = reparsed.toprettyxml(indent="  ")
    # Remove the extra XML declaration line added by minidom
    return pretty_xml.replace('<?xml version="1.0" ?>', '').strip()

def create_xml_file(row, output_dir):
    krpano = ET.Element("krpano")
    image = ET.SubElement(krpano, "image")
    cube = ET.SubElement(image, "cube", {"url": f"../panos/{row['Point_Name']}.tiles/pano_%s.jpg"})

    neighbor_names = row["Neighbor_Names"].split(',')
    azimuths = row["Azimuths"].split(',')

    gps_data = ET.SubElement(krpano, "gps_data", {"name": row["Point_Name"], "total": str(len(neighbor_names))})

    for i, (neighbor_name, azimuth) in enumerate(zip(neighbor_names, azimuths)):
        point = ET.SubElement(gps_data, "point", {"name": f"s{i+1}", "pt": neighbor_name, "pt_bear": azimuth})

    output_file_path = os.path.join(output_dir, f"{row['Point_Name']}.xml")
    with open(output_file_path, "w", encoding="UTF-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write(prettify(krpano))


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        self.setWindowTitle("Plot Point Connections")

        layout = QVBoxLayout()
        layout.setSpacing(1)

        # Checkbox and spinbox
        use_radius_box = QHBoxLayout()
        self.use_radius_checkbox = QCheckBox("Use search radius")
        self.use_radius_checkbox.setChecked(True)
        use_radius_box.addWidget(self.use_radius_checkbox)
        
        self.radius_spinbox = QSpinBox()
        self.radius_spinbox.setValue(9)
        self.radius_spinbox.setMaximum(1000)
        
        radius_layout = QHBoxLayout()
        
        use_radius_box.addWidget(QLabel("Radius(meters):"))
        use_radius_box.addWidget(self.radius_spinbox)
        layout.addLayout(use_radius_box)

        # File dialogs
        self.point_shp_button = QPushButton("Select point shapefile")
        self.point_shp_button.clicked.connect(self.select_point_shp)
        layout.addWidget(self.point_shp_button)
        self.line_shp_button = QPushButton("Select line shapefile")
        self.line_shp_button.clicked.connect(self.select_line_shp)
        layout.addWidget(self.line_shp_button)

        # Output folder selection
        self.output_folder_button = QPushButton("Select output folder")
        self.output_folder_button.clicked.connect(self.select_output_folder)
        layout.addWidget(self.output_folder_button)

        # Run button
        self.run_button = QPushButton("Run")
        self.run_button.clicked.connect(self.run_analysis)
        layout.addWidget(self.run_button)

        # Matplotlib canvas
        self.figure, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)
        # Disable the axes
        self.ax.xaxis.set_visible(False)
        self.ax.yaxis.set_visible(False)

        # Add the navigation toolbar
        self.toolbar = NavigationToolbar(self.canvas, self)
        layout.addWidget(self.toolbar)

        # Main widget
        main_widget = QWidget()
        main_widget.setLayout(layout)
        self.setCentralWidget(main_widget)

        self.point_shp = None
        self.line_shp = None
        self.xml_output_folder = None
        self.use_radius_checkbox.stateChanged.connect(self.toggle_buttons)
        self.toggle_buttons(self.use_radius_checkbox.checkState())
        self.use_radius_checkbox.stateChanged.connect(self.update_run_button_state)
        self.update_run_button_state(self.use_radius_checkbox.checkState())
    
    def update_run_button_state(self, state):
        if state == Qt.Checked:
            if self.point_shp and self.xml_output_folder:
                self.run_button.setEnabled(True)
            else:
                self.run_button.setEnabled(False)
        else:
            if self.point_shp and self.line_shp and self.xml_output_folder:
                self.run_button.setEnabled(True)
            else:
                self.run_button.setEnabled(False)
    
    def toggle_buttons(self, state):
        if state == Qt.Checked:
            self.line_shp_button.setEnabled(False)
            self.radius_spinbox.setEnabled(True)
        else:
            self.line_shp_button.setEnabled(True)
            self.radius_spinbox.setEnabled(False)
    
    def select_point_shp(self):
        file_dialog = QFileDialog()
        file_dialog.setAcceptMode(QFileDialog.AcceptOpen)
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        file_dialog.setNameFilters(["Shapefiles (*.shp)"])
        if file_dialog.exec_():
            point_shp = file_dialog.selectedFiles()[0]
            point_gdf = gpd.read_file(point_shp)
            if all(point_gdf.geom_type == "Point"):
                self.point_shp = point_shp
                self.point_shp_button.setText(f"Points: {self.point_shp}")
                self.update_run_button_state(self.use_radius_checkbox.checkState())
            else:
                QMessageBox.warning(self, "Invalid shapefile", "Please select a valid point shapefile.")

    def select_line_shp(self):
        file_dialog = QFileDialog()
        file_dialog.setAcceptMode(QFileDialog.AcceptOpen)
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        file_dialog.setNameFilters(["Shapefiles (*.shp)"])
        if file_dialog.exec_():
            line_shp = file_dialog.selectedFiles()[0]
            line_gdf = gpd.read_file(line_shp)
            if all(line_gdf.geom_type == "LineString"):
                self.line_shp = line_shp
                self.line_shp_button.setText(f"Lines: {self.line_shp}")
                self.update_run_button_state(self.use_radius_checkbox.checkState())
            else:
                QMessageBox.warning(self, "Invalid shapefile", "Please select a valid line shapefile.")

    def select_output_folder(self):
        folder_dialog = QFileDialog()
        folder_dialog.setAcceptMode(QFileDialog.AcceptOpen)
        folder_dialog.setFileMode(QFileDialog.Directory)
        folder_dialog.setOption(QFileDialog.ShowDirsOnly, True)
        if folder_dialog.exec_():
            self.xml_output_folder = folder_dialog.selectedFiles()[0]
            self.output_folder_button.setText(f"Output folder: {self.xml_output_folder}")
            self.update_run_button_state(self.use_radius_checkbox.checkState())


    def run_analysis(self):
            if not self.point_shp or not self.xml_output_folder:
                return

            use_radius = self.use_radius_checkbox.isChecked()
            radius = self.radius_spinbox.value()

            if use_radius:
                df = find_neighbors_within_radius(self.point_shp, radius)
            else:
                if not self.line_shp:
                    return
                df = find_connected_neighbors(self.point_shp, self.line_shp, buffer_distance=0.1)

            if not os.path.exists(self.xml_output_folder):
                os.makedirs(self.xml_output_folder)

            for _, row in df.iterrows():
                create_xml_file(row, self.xml_output_folder)

            self.plot_point_connections(df, self.point_shp)
        
    def plot_point_connections(self, df, point_shp):
            # Clear the previous plot
            self.ax.clear()
            

            # Read the point shapefile
            point_gdf = gpd.read_file(point_shp)

            # Plot the connections and points
            for idx, row in df.iterrows():
                point = point_gdf.loc[idx, "geometry"]
                neighbors = row["Neighbor_Names"].split(',')

                if not neighbors:
                    continue

                # Generate a random color for each cluster
                cluster_color = (random.random(), random.random(), random.random())

                for neighbor_name in neighbors:
                    try:
                        neighbor = point_gdf.loc[point_gdf["NAME"] == neighbor_name, "geometry"].iloc[0]
                        connection = LineString([point, neighbor])

                        # Plot the connections
                        self.ax.plot(*connection.xy, color=cluster_color)
                    except:
                        continue

                # Plot the points
                self.ax.scatter(point.x, point.y, color=cluster_color)

                # Create a text object for each label with halo effect
                text = self.ax.text(point.x, point.y, row["Point_Name"], fontsize=7, ha='right', va='bottom')
                text.set_path_effects([path_effects.withStroke(linewidth=2, foreground='white')])

            # Set plot limits to avoid labels outside the borders
            self.ax.set_xlim(point_gdf.total_bounds[0], point_gdf.total_bounds[2])
            self.ax.set_ylim(point_gdf.total_bounds[1], point_gdf.total_bounds[3])

            # Redraw the canvas
            self.canvas.draw()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())

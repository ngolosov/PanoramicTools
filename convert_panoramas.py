import sys
import os
import re
import glob
import subprocess
from pathlib import Path
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QProgressBar, QLabel, QFileDialog, QLineEdit, QMessageBox, QGroupBox, QHBoxLayout, QCheckBox
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import piexif
import geopandas as gpd
from shapely.geometry import Point


class Worker(QThread):
    progress_update = pyqtSignal(int)
    progress_finish = pyqtSignal(int)

    def __init__(self, main_func, input_dir, output_dir, shapefile_path, correct_image_geometry_checked, export_shapefile_checked, output_projection):
        super().__init__()
        self.main_func = main_func
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.shapefile_path = shapefile_path
        self.correct_image_geometry_checked = correct_image_geometry_checked
        self.export_shapefile_checked = export_shapefile_checked
        self.output_projection = output_projection

    def run(self):
        processed_images = self.main_func(self.input_dir, self.output_dir, self.shapefile_path, self.correct_image_geometry_checked, self.export_shapefile_checked, self.output_projection, self.progress_update)
        self.progress_finish.emit(processed_images)


class App(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Panorama Converter')
        layout = QVBoxLayout()
        
        # Adding checkboxes
        self.checkbox_group_box = QGroupBox("What to do?")
        self.checkbox_layout = QHBoxLayout()

        self.correct_image_geometry_checkbox = QCheckBox("Correct image geometry with nona")
        self.correct_image_geometry_checkbox.setChecked(True)
        self.checkbox_layout.addWidget(self.correct_image_geometry_checkbox)

        self.export_shapefile_checkbox = QCheckBox("Export shapefile")
        self.export_shapefile_checkbox.setChecked(True)
        self.checkbox_layout.addWidget(self.export_shapefile_checkbox)

        self.checkbox_group_box.setLayout(self.checkbox_layout)
        layout.addWidget(self.checkbox_group_box)

        self.correct_image_geometry_checkbox.stateChanged.connect(self.check_run_button)
        self.export_shapefile_checkbox.stateChanged.connect(self.check_run_button)

        # Add input for utm_18n_crs
        self.output_projection_label = QLabel("Output projection EPSG:")
        layout.addWidget(self.output_projection_label)

        self.output_projection_input = QLineEdit()
        self.output_projection_input.setText("EPSG:32618")
        layout.addWidget(self.output_projection_input)
        
        

        self.browse_input_folder_button = QPushButton('Browse Input Folder')
        self.browse_input_folder_button.clicked.connect(self.browse_input_folder)
        layout.addWidget(self.browse_input_folder_button)

        self.browse_output_folder_button = QPushButton('Browse Output Folder')
        self.browse_output_folder_button.clicked.connect(self.browse_output_folder)
        layout.addWidget(self.browse_output_folder_button)

        self.browse_shapefile_button = QPushButton('Browse Shapefile')
        self.browse_shapefile_button.clicked.connect(self.browse_shapefile)
        layout.addWidget(self.browse_shapefile_button)
        
        self.progress_label = QLabel('Progress:')
        layout.addWidget(self.progress_label)
        
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setMinimumWidth(300)
        layout.addWidget(self.progress_bar)
        
        # Disable the "Run" button initially
        self.run_button = QPushButton('Run')
        self.run_button.clicked.connect(self.run_process)
        self.run_button.setEnabled(False)
        layout.addWidget(self.run_button)

        self.setLayout(layout)

    def browse_input_folder(self):
        input_folder = QFileDialog.getExistingDirectory(self, 'Select Input Folder')
        if input_folder:
            self.browse_input_folder_button.setText(f"Input Folder: {input_folder}")
        self.check_run_button()

    def browse_output_folder(self):
        output_folder = QFileDialog.getExistingDirectory(self, 'Select Output Folder')
        if output_folder:
            self.browse_output_folder_button.setText(f"Output Folder: {output_folder}")
        self.check_run_button()

    def browse_shapefile(self):
        shapefile_path, _ = QFileDialog.getSaveFileName(self, 'Save Shapefile As', filter='Shapefile (*.shp)')
        if shapefile_path:
            self.browse_shapefile_button.setText(f"Shapefile: {shapefile_path}")
        self.check_run_button()
        
    def check_run_button(self):
        input_dir = self.browse_input_folder_button.text()
        output_dir = self.browse_output_folder_button.text()
        shapefile_path = self.browse_shapefile_button.text()
        correct_image_geometry_checked = self.correct_image_geometry_checkbox.isChecked()
        export_shapefile_checked = self.export_shapefile_checkbox.isChecked()

        input_selected = input_dir != 'Browse Input Folder'
        output_selected = output_dir != 'Browse Output Folder'
        shapefile_selected = shapefile_path != 'Browse Shapefile'

        # Disable the Run button if both checkboxes are not checked or if any required field is not selected
        if not (correct_image_geometry_checked or export_shapefile_checked) or not input_selected or not output_selected or not shapefile_selected:
            self.run_button.setEnabled(False)
        else:
            self.run_button.setEnabled(True)

        # Enable or disable the browse shapefile button based on the export_shapefile checkbox
        self.browse_shapefile_button.setEnabled(export_shapefile_checked)
        if not export_shapefile_checked:
            self.browse_shapefile_button.setText('Browse Shapefile')

        # Enable or disable the browse output folder button based on the correct_image_geometry checkbox
        self.browse_output_folder_button.setEnabled(correct_image_geometry_checked)
        if not correct_image_geometry_checked:
            self.browse_output_folder_button.setText('Browse Output Folder')
    
    def update_progress(self, progress_value):
        self.progress_bar.setValue(progress_value)

    def run_process(self):
        input_dir = self.browse_input_folder_button.text().replace("Input Folder: ", "")
        output_dir = self.browse_output_folder_button.text().replace("Output Folder: ", "")
        shapefile_path = self.browse_shapefile_button.text().replace("Shapefile: ", "")

        correct_image_geometry_checked = self.correct_image_geometry_checkbox.isChecked()
        export_shapefile_checked = self.export_shapefile_checkbox.isChecked()
        output_projection = self.output_projection_input.text()

        if not input_dir or not output_dir or not shapefile_path:
            return

        self.run_button.setEnabled(False)
        self.worker = Worker(main, input_dir, output_dir, shapefile_path, correct_image_geometry_checked, export_shapefile_checked, output_projection)
        self.worker.progress_update.connect(self.update_progress)
        self.worker.progress_finish.connect(self.finish_process)
        self.worker.start()


    def finish_process(self, processed_images):
        self.run_button.setEnabled(True)
        self.progress_bar.setValue(0)
        QMessageBox.information(self, "Success", f"{processed_images} files processed successfully")
        
def extract_xmp_and_gps_tags(image_path):
    xmp_start_pattern = b'<x:xmpmeta'
    xmp_end_pattern = b'</x:xmpmeta>'

    heading_pattern = re.compile(b'<GPano:PoseHeadingDegrees>(.*?)</GPano:PoseHeadingDegrees>')
    pitch_pattern = re.compile(b'<GPano:PosePitchDegrees>(.*?)</GPano:PosePitchDegrees>')
    roll_pattern = re.compile(b'<GPano:PoseRollDegrees>(.*?)</GPano:PoseRollDegrees>')

    with open(image_path, "rb") as image_file:
        data = image_file.read()
        xmp_start = data.find(xmp_start_pattern)
        xmp_end = data.find(xmp_end_pattern)
        xmp_data = data[xmp_start:xmp_end]

        heading = re.search(heading_pattern, xmp_data)
        pitch = re.search(pitch_pattern, xmp_data)
        roll = re.search(roll_pattern, xmp_data)

        heading_degrees = float(heading.group(1)) if heading else None
        pitch_degrees = float(pitch.group(1)) if pitch else None
        roll_degrees = float(roll.group(1)) if roll else None
        
    exif_data = piexif.load(image_path)
    
    gps_info = exif_data.get("GPS", {})

    lat = gps_info.get(piexif.GPSIFD.GPSLatitude, None)
    lat_ref = gps_info.get(piexif.GPSIFD.GPSLatitudeRef, None)
    lon = gps_info.get(piexif.GPSIFD.GPSLongitude, None)
    lon_ref = gps_info.get(piexif.GPSIFD.GPSLongitudeRef, None)

    if lat and lat_ref and lon and lon_ref:
        latitude = convert_to_decimal_degrees(lat, lat_ref.decode())
        longitude = convert_to_decimal_degrees(lon, lon_ref.decode())
    else:
        latitude, longitude = None, None

    return heading_degrees, pitch_degrees, roll_degrees, latitude, longitude


def run_nona(pto_file_path, output_folder):
    nona_exe_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "nona", "nona.exe") # resolve path to nona
    output_jpg_path = Path(output_folder, pto_file_path.stem + ".jpg")
    
    result = subprocess.run([nona_exe_path, "-o", str(output_jpg_path), str(pto_file_path)], capture_output=True, text=True)

    if result.returncode == 0:
        print(f"nona.exe successfully processed {pto_file_path}")
        pto_file_path.unlink()
    else:
        print(f"nona.exe failed to process {pto_file_path}")
        print("Error message:")
        print(result.stderr)


def convert_to_decimal_degrees(coordinate, reference):
    degrees, minutes, seconds = [c[0] / c[1] for c in coordinate]
    decimal_degrees = degrees + minutes / 60 + seconds / 3600
    return -decimal_degrees if reference in ['S', 'W'] else decimal_degrees

def create_pto_file(image_path, heading_degrees, pitch_degrees, roll_degrees):
    image_name = image_path.stem
    pto_filename = image_path.with_suffix(".pto")

    with open(pto_filename, "w") as pto_file:
        pto_content = f"i w5376 h2688 f4 v360 r{roll_degrees} p{pitch_degrees} y{heading_degrees} n{image_name}.jpg\n"
        pto_content += 'p w5376 h2688 f2 v360 r0 p0 y0 n"JPEG q99"'
        pto_file.write(pto_content)
    return pto_filename
        
def main(input_dir, output_dir, shapefile_path, correct_image_geometry_checked, export_shapefile_checked, output_projection, progress_callback):
    # Add the contents of the main function from your original code
    # Replace the for loop with this modified version to send progress updates:
    
    crs = "EPSG:4326"  # WGS84

    geodata = []
    
    files = glob.glob(os.path.join(input_dir, "*.jpg"))
    
    for index, file in enumerate(files):
        image_path = Path(file)
        heading_degrees, pitch_degrees, roll_degrees, latitude, longitude = extract_xmp_and_gps_tags(str(image_path))
        
        if correct_image_geometry_checked:
            pto_file_path = create_pto_file(image_path, heading_degrees, pitch_degrees, roll_degrees)
            run_nona(pto_file_path, output_dir)
        
        if export_shapefile_checked and latitude and longitude:
            geodata.append({"NAME": str(image_path.stem), "geometry": Point(longitude, latitude)})
        
        progress_callback.emit(int((index + 1) / len(files) * 100))

    if export_shapefile_checked:
        gdf = gpd.GeoDataFrame(geodata, crs=crs)
        gdf_utm = gdf.to_crs(output_projection)
        gdf_utm.to_file(shapefile_path)
        
    return index


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = App()
    ex.show()
    sys.exit(app.exec_())


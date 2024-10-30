#---------------------------------------------------------------
#__main__.py

#updated by: Clara Bird, October 2024
#----------------------------------------------------------------

#import modules
import pandas as pd
import os, sys
import numpy as np
from pyexifhelper_exiftool import ExifToolHelper
import xml.etree.ElementTree
import argparse
import math
import webbrowser
import traceback
import platform
from datetime import date, datetime, timedelta
from pathlib import Path
from PySide6 import QtCore
from PySide6.QtWidgets import QFileDialog, QApplication, QMainWindow, QPushButton, QCheckBox, QVBoxLayout, QWidget, QMessageBox, QLabel, QLineEdit, QComboBox, QGridLayout, QSpacerItem, QSizePolicy, QScrollArea, QTableView, QToolTip, QToolButton
from PySide6.QtCore import Qt, QMetaObject
from PySide6.QtGui import QFont, QDoubleValidator, QStandardItemModel, QStandardItem, QIcon


# UPDATE WITH UPDATES
cx_version = "v2.0"

class FileSelector:
    def select_file():
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(
            None, "Select File", '', 'CSV Files (*.csv)'
        )
        if file_path:
            print(f"Selected File: {file_path}")
            return file_path
        return None

class DirSelector:
    def select_dir():
        file_dialog = QFileDialog()
        dir_path = file_dialog.getExistingDirectory(
            None, "Select Directory"
        )
        if dir_path:
            return dir_path
        return None
    
class ExifViewer(QMainWindow):
    def __init__(self):
        super().__init__()

        # Create a QTableView and set the model
        self.table_view = QTableView(self)
        self.model = QStandardItemModel()
        self.table_view.setModel(self.model)

        # Set up the layout
        layout = QVBoxLayout()
        layout.addWidget(self.table_view)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        self.setWindowTitle("ExifTag Viewer")

    def set_dataframe(self, dataframe):
        # Update the model with the new DataFrame
        self.model.clear()
        self.model.setHorizontalHeaderLabels(dataframe.columns)
        for row in range(dataframe.shape[0]):
            items = [QStandardItem(str(dataframe.iloc[row, col])) for col in range(dataframe.shape[1])]
            self.model.appendRow(items)

class lidarwranglerWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Wrangle LiDAR Data")

        #set sizing
        D = self.screen().availableGeometry()
        self.move(1,1)#center.x() + .25*D.width() , center.y() - .5*D.height() )
        self.resize( int(.3*D.width()), int(.4*D.height()) )
        self.setWindowState(self.windowState() & ~QtCore.Qt.WindowState.WindowMinimized
                            | QtCore.Qt.WindowState.WindowActive)
        self.activateWindow()
        
        self.grid_layout = QGridLayout()

        spacer1 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        spacer2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        #add inputs
        welcome_label = QLabel("Welcome to the lidar wrangling tool!")
        welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setBold(True)
        welcome_label.setFont(font)  

        ### LIDAR, OUTPUT, and RUN ###
        #lidar folder
        lidarfold_button = QPushButton("Lidar folder",self)
        lidarfold_button.clicked.connect(lambda: self.select_dir(1))
        self.lidarfold_sel_label = QLabel("", self)
        self.lidarfold_sel_label.setStyleSheet("border: 1px dashed black; padding: 2px; font-style: italic;")

        #lidar kind drop box
        self.lidartypes_list = QComboBox(self)
        self.lidartypes_list.addItems(['LightWare (csv)','LemHex (gpx)'])

        #lidar gimbal drop box
        self.gimbal_list = QComboBox(self)
        self.gimbal_list.addItems(['fixed','gimbaled'])

        #output prefix and folder selection
        self.output_prefix_box = QLineEdit()

        outfold_button = QPushButton("Output folder",self)
        outfold_button.clicked.connect(lambda: self.select_dir(2))
        self.outfold_sel_label = QLabel("", self)
        self.outfold_sel_label.setStyleSheet("border: 1px dashed black; padding: 2px; font-style: italic;")

        #run button
        lidarwrangle_run_button = QPushButton("Run!",self)
        lidarwrangle_run_button.setFont(font)
        lidarwrangle_run_button.setStyleSheet("color: red;")
        lidarwrangle_run_button.clicked.connect(self.lidarwrangle)

        #end message
        self.end_msg = QLabel("",self)
        self.end_msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.end_msg.setFont(font)

        #### GRID LAYOUT ####
        #add labels and buttons to grid layout
        self.grid_layout.addWidget(welcome_label,0,0,1,2)
        self.grid_layout.addItem(spacer1, 1, 0,1,2)

        ## LIDAR FOLDER, OUTPUT SETTINGS, and RUN BUTTON
        self.grid_layout.addWidget(QLabel("Click to select folder containing lidar files"),2,1,1,1)
        self.grid_layout.addWidget(lidarfold_button, 2,0,1,1)

        self.grid_layout.addWidget(self.lidarfold_sel_label, 3,0,1,2)

        self.grid_layout.addWidget(QLabel("Select which lidar you used"),4,0,1,1)
        self.grid_layout.addWidget(self.lidartypes_list,4,1,1,1)

        self.grid_layout.addWidget(QLabel("Lidar mount:"),5,0,1,1)
        self.grid_layout.addWidget(self.gimbal_list,5,1,1,1)

        self.grid_layout.addWidget(QLabel("Output prefix:"),6,0,1,1)
        self.grid_layout.addWidget(self.output_prefix_box,6,1,1,1)

        self.grid_layout.addWidget(QLabel("Click to select folder where output should be saved"),7,1,1,1)
        self.grid_layout.addWidget(outfold_button, 7,0,1,1)

        self.grid_layout.addWidget(self.outfold_sel_label, 8,0,1,2)

        self.grid_layout.addItem(spacer2, 9, 0,1,2)

        self.grid_layout.addWidget(lidarwrangle_run_button,10,0,1,2)

        self.grid_layout.addWidget(self.end_msg,11,0,1,2)

        # Create a scroll area and set your grid layout as its widget
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)  # Makes the widget inside the scrollable

        scroll_contents = QWidget()
        scroll_contents.setLayout(self.grid_layout)
        scroll_area.setWidget(scroll_contents)

        main_layout = QVBoxLayout()
        main_layout.addWidget(scroll_area)
        self.setLayout(main_layout)

    def select_dir(self, button_id):
        dir_path = DirSelector.select_dir()
        if dir_path:
            if button_id == 1:
                self.lidarpath = dir_path
                self.lidarfold_sel_label.setText(dir_path)
            elif button_id == 2:
                self.outpath = dir_path
                self.outfold_sel_label.setText(dir_path)

    def lidarwrangle(self):
        # wrangle lightaware data
        if self.lidartypes_list.currentText() == 'LightWare (csv)':
            lidar_files = [os.path.join(r, m) for r, dirs, files in os.walk(self.lidarpath) for m in files if m.endswith(('.csv',".CSV")) & ~m.startswith(".")]
            laser_all = pd.DataFrame(data={})
            for lf in lidar_files:
                df_laser = pd.read_csv(lf,sep='\t',skiprows=2) #read in lidar file, seperator is a tab, skip the first two rows, they have too few columns
                df_laser['laser_altitude_cm'] = df_laser['laser_altitude_cm'].replace(dict.fromkeys([13000,15000], np.nan)) #make the error value (130) to nan
                
                if self.gimbal_list.currentText() == 'fixed':
                    df_laser['converted'] = [math.cos((x) * math.pi / float(180)) for x in df_laser['tilt_deg']] #calculate conversation factor based on tilt degree (from Dawson paper code)
                    df_laser['Laser_Alt'] = (df_laser['laser_altitude_cm'] * df_laser['converted']) / float(100) #use conversation factor to calculate corrected laser altitude (from Dawson)

                elif self.gimbal_list.currentText() == 'gimbaled':
                    df_laser['Laser_Alt'] = df_laser['laser_altitude_cm'] / float(100)

                df_laser['CorrDT'] = [datetime.strptime("{0} {1}".format(x,y),"%Y/%m/%d %H:%M:%S") for x,y in zip(df_laser['#gmt_date'],df_laser['gmt_time'])]
                laser_all = pd.concat([laser_all,df_laser])

            #maybe only export a subset of columns??
            #export 
            laser_all.to_csv(os.path.join(self.outpath,"{0}_CleanedLidar.csv".format(self.output_prefix_box.text())),index=False)

        elif self.lidartypes_list.currentText() == 'LemHex (gpx)':
            #pull laser files
            lidar_files = [os.path.join(r, m) for r, dirs, files in os.walk(self.lidarpath) 
                                        for m in files if m.endswith(".GPX") and not m.startswith(".")]
            #loop through logs and pull out datetime, laser alt, lat ,and lon
            laser_data = []
            for log in lidar_files:
                root = xml.etree.ElementTree.parse(log).getroot()
                alt_collection = root[1][1]
                for alt_point in alt_collection.findall('trkpt'):
                    #pull date and time
                    date_time = alt_point.find('time').text
                    date = date_time.split("T")[0]
                    time = date_time.split("T")[1].split(".")[0]
                    gpxdatetime = datetime.strptime("{0} {1}".format(date,time),"%Y-%m-%d %H:%M:%S")

                    #pull lat and lon
                    lat = alt_point.attrib['lat']
                    lon = alt_point.attrib['lon']

                    #pull laser
                    extensions = alt_point.find("extensions")
                    laser = extensions.find('Laser').text
                    laser = float(laser)

                    #make one row
                    laser_data.append([gpxdatetime, laser, lat, lon])
            
            #make one big dataframe, get rid of error values
            laser_all = pd.DataFrame(laser_data, columns=['CorrDT','Laser_Alt','lat','lon'])
            laser_all['Laser_Alt'] = laser_all['Laser_Alt'].replace(130.00, np.nan)

            #multiple samples per second so take mean
            laser_all = laser_all.groupby('CorrDT').agg({'lat': 'first', 'lon': 'first', 'Laser_Alt': 'mean'}).reset_index()

            #export 
            laser_all.to_csv(os.path.join(self.outpath,"{0}_CleanedLidar.csv".format(self.output_prefix_box.text())),index=False)

        # print message telling user that its done running!
        self.end_msg.setText("Done running - check output folder for files!")

class lidarvideoWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pull LiDAR Data for Videos")

        #set sizing
        D = self.screen().availableGeometry()
        self.move(1,1)#center.x() + .25*D.width() , center.y() - .5*D.height() )
        self.resize( int(.7*D.width()), int(.5*D.height()) )
        self.setWindowState(self.windowState() & ~QtCore.Qt.WindowState.WindowMinimized
                            | QtCore.Qt.WindowState.WindowActive)
        self.activateWindow()
        
        self.grid_layout = QGridLayout()

        spacer1 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        spacer2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        #add inputs
        welcome_label = QLabel("Welcome to the lidar-video match up tool!")
        welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setBold(True)
        welcome_label.setFont(font)

        ### GPS SECTION ###
        #GPS file and timestamp wrangling
        self.gps_button = QPushButton("GPS Time File",self)
        self.gps_button.clicked.connect(lambda: self.select_file(1))
        self.gps_sel_label = QLabel("",self)
        self.gps_sel_label.setStyleSheet("border: 1px dashed black; padding: 2px; font-style: italic;")

        #Checkbox to indicate if the snapshot time is in a column or not (checked = use column)
        self.gpstimecheckbox = QCheckBox("Check if the time in video of the image is in a column\n (named VideoTime)", self)

        #Time drop down set up
        self.example_image_input = QLineEdit()
        self.image_delimiter_input = QLineEdit()

        self.hour_dropdown = QComboBox()
        self.minute_dropdown = QComboBox()
        self.second_dropdown = QComboBox()

        # pull flight prefix out of GPS image
        self.gpsflightcheckbox = QCheckBox("Check if flight prefix is in a column\n (named FlightID)", self)
        self.gpsvideocheckbox = QCheckBox("Check if video prefix is in a column\n (named VideoID)", self)

        self.prefixgps_parts_checkboxes = []
        self.prefixgps_parts_label = QLabel()

        self.prefixvideo_parts_checkboxes = []
        self.prefixvideo_parts_label = QLabel()

        ### VIDEO SECTION ###
        #folder w/ videos
        vidfold_button = QPushButton("Video folder",self)
        vidfold_button.clicked.connect(lambda: self.select_dir(1))
        self.vidfold_sel_label = QLabel("", self)
        self.vidfold_sel_label.setStyleSheet("border: 1px dashed black; padding: 2px; font-style: italic;")

        # exif tag selection
        self.open_exif_help_button = QPushButton("Exif Tag Viewer",self)
        self.open_exif_help_button.clicked.connect(self.open_exif_viewer)

        self.exif_tags_dropdown_name = QComboBox(self)
        self.exif_tags_dropdown_dur = QComboBox(self)
        self.exif_tags_dropdown_date = QComboBox(self)

        #Prefix set up
        self.example_video_input = QLineEdit()

        self.video_delimiter_input = QLineEdit()

        self.prefix_parts_checkboxes = []
        self.prefix_parts_label = QLabel()

        ### LIDAR, OUTPUT, and RUN ###
        #lidar file
        lidarfile_button = QPushButton("Lidar file",self)
        lidarfile_button.clicked.connect(lambda: self.select_file(2))
        self.lidarfile_sel_label = QLabel("", self)
        self.lidarfile_sel_label.setStyleSheet("border: 1px dashed black; padding: 2px; font-style: italic;")

        #output prefix and folder selection
        self.output_prefix_box = QLineEdit()

        outfold_button = QPushButton("Output folder",self)
        outfold_button.clicked.connect(lambda: self.select_dir(2))
        self.outfold_sel_label = QLabel("", self)
        self.outfold_sel_label.setStyleSheet("border: 1px dashed black; padding: 2px; font-style: italic;")

        #run button
        lidarvideo_run_button = QPushButton("Run!",self)
        lidarvideo_run_button.setFont(font)
        lidarvideo_run_button.setStyleSheet("color: red;")
        lidarvideo_run_button.clicked.connect(self.lidarvideo)

        #missing flights message
        self.miss_flights_msg = QLabel("",self)
        self.miss_flights_msg.setStyleSheet("color: red;")       

        #end message
        self.end_msg = QLabel("",self)
        self.end_msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.end_msg.setFont(font)

        #### GRID LAYOUT ####
        #add labels and buttons to grid layout
        self.grid_layout.addWidget(welcome_label,0,0,1,6)
        self.grid_layout.addItem(spacer1, 1, 0,1,6)

        ## GPS FILE section
        self.grid_layout.addWidget(QLabel("Click to upload GPS time file"),2,1,1,1)
        self.grid_layout.addWidget(self.gps_button, 2, 0,1,1)

        self.grid_layout.addWidget(self.gps_sel_label,3,0,1,2)

        self.grid_layout.addWidget(self.gpstimecheckbox,4,0,1,2)

        self.grid_layout.addWidget(QLabel("Enter Example Image Name:"),5,0,1,1)
        self.grid_layout.addWidget(self.example_image_input,5,1,1,1)

        self.grid_layout.addWidget(QLabel("Enter Delimiter:"),6,0,1,1)
        self.grid_layout.addWidget(self.image_delimiter_input,6,1,1,1)

        self.grid_layout.addWidget(QLabel("Select Time Components:"),7,0,1,2)
        self.setup_time_parts_widgets(self.grid_layout)

        self.grid_layout.addWidget(self.gpsflightcheckbox,11,0,1,1)
        self.grid_layout.addWidget(self.gpsvideocheckbox,11,1,1,1)

        self.grid_layout.addWidget(QLabel("Select Flight Prefix Parts:"),12,0,1,2)
        self.grid_layout.addWidget(QLabel("Select Video Prefix Parts:"),12,1,1,2)

        ## FLIGHT PREFIX
        self.grid_layout.addWidget(QLabel("Click to select folder\ncontaining raw drone videos"), 2,3,1,1)
        self.grid_layout.addWidget(vidfold_button, 2,2,1,1)

        self.grid_layout.addWidget(self.vidfold_sel_label, 3,2,1,2)

        self.grid_layout.addWidget(QLabel("Default tag names should appear when\nvideo folder is selected, but if not\nclick the 'Exif Tag Viewer' for help"),4,2,1,1)
        self.grid_layout.addWidget(self.open_exif_help_button,4,3,1,1)
        self.grid_layout.addWidget(QLabel("Select file name exif tag"),5,2,1,1)
        self.grid_layout.addWidget(self.exif_tags_dropdown_name,5,3,1,1)
        self.grid_layout.addWidget(QLabel("Select duration exif tag"),6,2,1,1)
        self.grid_layout.addWidget(self.exif_tags_dropdown_dur,6,3,1,1)
        self.grid_layout.addWidget(QLabel("Select modify date exif tag"),7,2,1,1)
        self.grid_layout.addWidget(self.exif_tags_dropdown_date,7,3,1,1)

        self.grid_layout.addWidget(QLabel("Enter Example Video Name:"),8,2,1,1)
        self.grid_layout.addWidget(self.example_video_input,8,3,1,1)

        self.grid_layout.addWidget(QLabel("Enter Delimiter:"),9,2,1,1)
        self.grid_layout.addWidget(self.video_delimiter_input,9,3,1,1)

        self.grid_layout.addWidget(QLabel("Select Flight Prefix Parts:"),10,2,1,2)

        ## LIDAR FILE, OUTPUT SETTINGS, and RUN BUTTON
        self.grid_layout.addWidget(QLabel("Click to select cleaned lidar file\n(output from lidar wrangle tool)"),2,5,1,1)
        self.grid_layout.addWidget(lidarfile_button, 2,4,1,1)

        self.grid_layout.addWidget(self.lidarfile_sel_label, 3,4,1,2)

        self.grid_layout.addWidget(QLabel("Output prefix:"),4,4,1,1)
        self.grid_layout.addWidget(self.output_prefix_box,4,5,1,2)

        self.grid_layout.addWidget(QLabel("Click to select folder where\n outputs should be saved"),5,5,1,1)
        self.grid_layout.addWidget(outfold_button, 5,4,1,1)

        self.grid_layout.addWidget(self.outfold_sel_label, 6,4,1,2)

        self.grid_layout.addItem(spacer2, 7, 4,1,2)

        self.grid_layout.addWidget(lidarvideo_run_button,8,4,1,2)

        self.grid_layout.addWidget(self.miss_flights_msg,9,4,1,2)

        self.grid_layout.addWidget(self.end_msg,10,4,1,2)

        # Create a scroll area and set your grid layout as its widget
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)  # Makes the widget inside the scrollable

        scroll_contents = QWidget()
        scroll_contents.setLayout(self.grid_layout)
        scroll_area.setWidget(scroll_contents)

        main_layout = QVBoxLayout()
        main_layout.addWidget(scroll_area)
        self.setLayout(main_layout)

        self.image_delimiter_input.textChanged.connect(self.update_time_parts_dropdowns)
        self.image_delimiter_input.textChanged.connect(lambda: self.update_prefix_parts_checkboxes(1))
        self.image_delimiter_input.textChanged.connect(lambda: self.update_prefix_parts_checkboxes(2))
        self.video_delimiter_input.textChanged.connect(lambda: self.update_prefix_parts_checkboxes(3))

        # Initialize default selections
        self.default_selections = {
            self.exif_tags_dropdown_name: 'FileName',
            self.exif_tags_dropdown_dur: 'Duration',
            self.exif_tags_dropdown_date: 'FileModifyDate',
        }

        #exif viewer is now an instance variable
        self.exif_help_window = ExifViewer()

    def update_time_parts_dropdowns(self):
        example_image_name = self.example_image_input.text()

        for dropdown in (self.hour_dropdown, self.minute_dropdown, self.second_dropdown):
            dropdown.clear()
            dropdown.addItem("None")  # Option to skip the time part
            dropdown.addItems(example_image_name.split(self.image_delimiter_input.text()))

    def setup_time_parts_widgets(self, layout):
        layout.addWidget(QLabel("Hour:"),8,0,1,1)
        layout.addWidget(self.hour_dropdown,8,1,1,1)
        layout.addWidget(QLabel("Minute:"),9,0,1,1)
        layout.addWidget(self.minute_dropdown,9,1,1,1)
        layout.addWidget(QLabel("Second:"),10,0,1,1)
        layout.addWidget(self.second_dropdown,10,1,1,1)

    def update_prefix_parts_checkboxes(self, button_id):
        if button_id == 1:
            example_image_name = self.example_image_input.text()
            delimiter = self.image_delimiter_input.text()

            for checkbox in self.prefixgps_parts_checkboxes:
                checkbox.deleteLater()
            self.prefixgps_parts_checkboxes = []

            if delimiter:
                parts = example_image_name.split(delimiter)

                for i, part in enumerate(parts):
                    checkbox = QCheckBox(part)
                    self.prefixgps_parts_checkboxes.append(checkbox)
                    self.grid_layout.addWidget(checkbox,13+i,0,1,1)

        elif button_id == 2:
            example_image_name = self.example_image_input.text()
            delimiter = self.image_delimiter_input.text()

            for checkbox in self.prefixvideo_parts_checkboxes:
                checkbox.deleteLater()
            self.prefixvideo_parts_checkboxes = []

            if delimiter:
                parts = example_image_name.split(delimiter)

                for i, part in enumerate(parts):
                    checkbox = QCheckBox(part)
                    self.prefixvideo_parts_checkboxes.append(checkbox)
                    self.grid_layout.addWidget(checkbox,13+i,1,1,1)

        elif button_id == 3:
            example_image_name = self.example_video_input.text()
            delimiter = self.video_delimiter_input.text()

            for checkbox in self.prefix_parts_checkboxes:
                checkbox.deleteLater()
            self.prefix_parts_checkboxes = []

            if delimiter:
                parts = example_image_name.split(delimiter)

                for i, part in enumerate(parts):
                    checkbox = QCheckBox(part)
                    self.prefix_parts_checkboxes.append(checkbox)
                    self.grid_layout.addWidget(checkbox,10+i,3,1,1)

    def select_file(self, button_id):
        file_path = FileSelector.select_file()
        if file_path:
            if button_id == 1:
                self.gps_sel_label.setText(file_path)
                # Read the file using pandas
                self.dfgps = pd.read_csv(file_path)
                self.gps_file_path = file_path

                if "Image" in self.dfgps.columns and not self.dfgps.empty:
                    first_image = self.dfgps['Image'].iloc[0]
                    self.example_image_input.setText(first_image)
            
            elif button_id == 2:
                self.laser_all = pd.read_csv(file_path)
                self.laser_file_path = file_path
                self.lidarfile_sel_label.setText(file_path)
        
    def select_dir(self, button_id):
        dir_path = DirSelector.select_dir()
        if dir_path:
            if button_id == 1:
                self.vidpath = dir_path
                self.vidfold_sel_label.setText(dir_path)

                #make list of videos
                self.video_names = []
                self.video_list = []
                for root, dirs, files in os.walk(dir_path):
                    self.video_names += [m for m in files if m.endswith((".MOV",".MP4")) & ~m.startswith(".")]
                    self.video_list += [os.path.join(root,m) for m in files if m.endswith((".MOV",".MP4")) & ~m.startswith(".")]

                #pull first video to be displayed
                first_video = self.video_names[0]
                self.example_video_input.setText(first_video)

                # Fetch Exif tags for the selected file
                if os.name == 'nt': #windows
                    exifpath = os.path.join(sys._MEIPASS,"exiftool.exe")
                else: #mac
                    exifpath = '/usr/local/bin/exiftool'

                with ExifToolHelper(exifpath) as et:
                    self.exif_tags = et.get_tags(self.video_list[0],[])

                exif_tags1 = [x.split(":")[1] if len(x.split(":"))>1 else x for x in list(self.exif_tags[0].keys()) ]
                # run update exiftag drop down
                for dropdown, default_selection in self.default_selections.items():
                    self.update_exif_tags(dropdown, exif_tags1, default_selection)

            elif button_id == 2:
                self.outpath = dir_path
                self.outfold_sel_label.setText(dir_path)

    def update_exif_tags(self, dropdown, exif_tags, default_selection):
        # Update the Exif tags dropdown
        dropdown.clear()
        dropdown.addItems(["select tag"])
        dropdown.addItems(exif_tags)

        # Set the default selection
        index = dropdown.findText(default_selection)
        if index != -1:
            dropdown.setCurrentIndex(index)

    def open_exif_viewer(self):
        dfexif = pd.DataFrame.from_dict(self.exif_tags[0],orient='index').reset_index().rename(columns={'index':'tag',0:'value'})

        #pass to exif viewer
        self.exif_help_window.set_dataframe(dfexif)
        self.exif_help_window.show()

    def lidarvideo(self):
        self.end_msg.setText("......running......")
        #### PART 1 - set up video metadata df ####
        # pull meta from videos
        movs = self.video_list

        dfvideo = pd.DataFrame()
        tagnames = []

        #set up path to exiftool
        if os.name == 'nt': #windows
            exifpath = os.path.join(sys._MEIPASS,"exiftool.exe")
        else: #mac
            exifpath = '/usr/local/bin/exiftool'

        with ExifToolHelper(exifpath) as et:
            for d in et.get_tags(movs, tags=[self.exif_tags_dropdown_name.currentText(),
                                             self.exif_tags_dropdown_dur.currentText(),
                                             self.exif_tags_dropdown_date.currentText()]):
                tempdict = {}
                for k, v in d.items():
                    tempdict[k] = v
                    tagnames += [k]
                tempdf = pd.DataFrame(data=tempdict,index=[0])
                dfvideo = pd.concat([dfvideo,tempdf]).reset_index(drop=True)

        tagnames1 = list(set(tagnames))
        nametag = [x for x in tagnames1 if self.exif_tags_dropdown_name.currentText() in x][0]
        durtag = [x for x in tagnames1 if self.exif_tags_dropdown_dur.currentText() in x][0]
        datetag = [x for x in tagnames1 if self.exif_tags_dropdown_date.currentText() in x][0]

        dfvideo = dfvideo.rename(columns={nametag:"MOV",
                                          durtag:"DUR_S",
                                          datetag:"MDT" })
        
        #wrangle exif output
        dfvideo['VideoID'] = [x.replace(".MOV","") for x in dfvideo['MOV']]
        dfvideo['DUR'] = [str(timedelta(seconds=x)).split(".")[0] for x in dfvideo['DUR_S']] #convert duration to timestamp
        dfvideo['MT'] = [x.split("-")[0] for x in dfvideo['MDT']] #extract just the time from the modify date/time
        dfvideo = dfvideo.drop(['SourceFile'],axis=1) #drop the columns that just contain the list outputs

        #convert duration to timedelta
        dfvideo['DUR.TD'] = [
            timedelta(hours = int(x.split(":")[0]),minutes=int(x.split(":")[1]),seconds=int(x.split(":")[2]))
            if "s" not in x else timedelta(seconds=float(x.split(".")[0])) 
            for x in dfvideo['DUR']]

        #convert modify time to timedelta
        dfvideo['MT.DT'] = [datetime.strptime(x,"%Y:%m:%d %H:%M:%S") for x in dfvideo['MT']]
        
        #calculate video start time
        dfvideo['START'] = [x - y for x,y in zip(dfvideo['MT.DT'],dfvideo['DUR.TD'])]

        # make list of indexes for flight prefix in video name
        video_flight_ixs = [i for i, checkbox in enumerate(self.prefix_parts_checkboxes) if checkbox.isChecked()]

        #filter out videos without the full prefix based on length of flight prefix
        dfvideo = dfvideo[dfvideo['MOV'].str.split(self.video_delimiter_input.text()).apply(len) >= len(video_flight_ixs)]

        #add column w/ flight id using prefix
        dfvideo['FlightID'] = [self.video_delimiter_input.text().join(x.split(self.video_delimiter_input.text())[i] for i in video_flight_ixs) 
                               for x in dfvideo['MOV']]        

        #### PART 2 - calculate offset ####
        # get time in video from image name if need be (if checkbox unchecked)
        if self.gpstimecheckbox.isChecked():
            pass
        else:
            # create column with the time in video extracted
            hr_ix = self.hour_dropdown.currentIndex()-1
            min_ix = self.minute_dropdown.currentIndex()-1
            sec_ix = self.second_dropdown.currentIndex()-1

            self.dfgps['VideoTime'] = ["{0}:{1}:{2}".format(x.split(self.image_delimiter_input.text())[hr_ix],
                                                            x.split(self.image_delimiter_input.text())[min_ix],
                                                            x.split(self.image_delimiter_input.text())[sec_ix]
                                                            )
                                                            for x in self.dfgps['Image']]
        # add column for flight if need be (if checkbox unchecked)
        if self.gpsflightcheckbox.isChecked():
            pass
        else:
            #create column with flight ID
            gps_flight_ixs = [i for i, checkbox in enumerate(self.prefixgps_parts_checkboxes) if checkbox.isChecked()]

            self.dfgps['FlightID'] = [self.image_delimiter_input.text().join(x.split(self.image_delimiter_input.text())[i] for i in gps_flight_ixs) 
                                      for x in self.dfgps['Image']]
        
        #add column for video if need be (if checkbox unchecked)
        if self.gpsvideocheckbox.isChecked():
            pass
        else:
            #create column with video ID
            gps_video_ixs = [i for i, checkbox in enumerate(self.prefixvideo_parts_checkboxes) if checkbox.isChecked()]

            self.dfgps['VideoID'] = [self.image_delimiter_input.text().join(x.split(self.image_delimiter_input.text())[i] for i in gps_video_ixs) 
                            for x in self.dfgps['Image']]
            
        # add GPS date time column
        self.dfgps['GPS_DT'] = [datetime.strptime("{0} {1}".format(x,y),"%y%m%d %H:%M:%S") for x,y in zip(self.dfgps['GPS_Date'],self.dfgps['GPS_Time'])]

        # calculate offset
        dfgps_x = self.dfgps.merge(dfvideo[['START','VideoID']],how="left",on='VideoID')
        
        dfgps_x['offset'] = [(x - 
                              (timedelta(hours = int(y.split(":")[0]),minutes=int(y.split(":")[1]),seconds=int(y.split(":")[2])) +
                                z)) for x,y,z in zip(dfgps_x['GPS_DT'],dfgps_x['VideoTime'],dfgps_x['START'])]
        

        #### PART 3 - merge w/ lidar ####
        #merge offset onto video df
        dfvid_x = dfvideo.merge(dfgps_x[['FlightID','offset']],how='left',on='FlightID')
        
        #add offset to start and end time
        dfvid_x['CorrStart'] = [x + y for x,y in zip(dfvid_x['START'],dfvid_x['offset'])]
        dfvid_x['CorrEnd'] = [x + y for x,y in zip(dfvid_x['MT.DT'],dfvid_x['offset'])]

        #filter out flights w/o GPS time and print message to user w list
        missing_flights = list(set(dfvid_x[dfvid_x['CorrStart'].isna()]['FlightID'].tolist()))

        dfvid_x = dfvid_x[dfvid_x['CorrStart'].notna()]

        if len(missing_flights) > 0:
            self.miss_flights_msg.setText("These flights were skipped because they were not in the GPS time csv: {0}".format(missing_flights))
        else: pass

        #explode df to one row per second
        dfvid_x['CorrDT'] = [pd.date_range(start=x,end=y,freq="S") for x,y in zip(dfvid_x['CorrStart'],dfvid_x['CorrEnd'])]

        df_expl = dfvid_x[['FlightID','VideoID','CorrDT','CorrStart']].explode('CorrDT').reset_index(drop=True)
        df_expl['VideoTime'] = df_expl['CorrDT'] - df_expl['CorrStart']
        df_expl = df_expl.drop(columns=['CorrStart'])

        #merge w/ lidar on CorrDT
        self.laser_all['CorrDT'] = [datetime.strptime("{0}".format(x),"%Y-%m-%d %H:%M:%S") for x in self.laser_all['CorrDT']]
        df_lidarvid = df_expl.merge(self.laser_all[['CorrDT','Laser_Alt']],how='left',on='CorrDT')

        #export 
        df_lidarvid.to_csv(os.path.join(self.outpath,"{0}_VideoLidar.csv".format(self.output_prefix_box.text())),index=False)

        # print message telling user that its done running!
        self.end_msg.setText("Done running - check output folders for files!")

class lidarmatchWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Merge LiDAR data from videos with images")

        #set sizing
        D = self.screen().availableGeometry()
        self.move(1,1)#center.x() + .25*D.width() , center.y() - .5*D.height() )
        self.resize( int(.7*D.width()), int(.5*D.height()) )
        self.setWindowState(self.windowState() & ~QtCore.Qt.WindowState.WindowMinimized
                            | QtCore.Qt.WindowState.WindowActive)
        self.activateWindow()
        
        self.grid_layout = QGridLayout()

        spacer1 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        spacer2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        #add inputs
        welcome_label = QLabel("Welcome to the lidar image match up tool!")
        welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setBold(True)
        welcome_label.setFont(font)

        ### IMAGE LIST ###
        #GPS file and timestamp wrangling
        self.imglist_button = QPushButton("Image List File",self)
        self.imglist_button.clicked.connect(lambda: self.select_file(1))
        self.imglist_sel_label = QLabel("",self)
        self.imglist_sel_label.setStyleSheet("border: 1px dashed black; padding: 2px; font-style: italic;")

        #Checkbox to indicate if the snapshot time is in a column or not (checked = use column)
        self.imgtimecheckbox = QCheckBox("Check if the time in video of the image is in a column (named VideoTime)", self)

        #Time drop down set up
        self.example_image_input = QLineEdit()
        self.image_delimiter_input = QLineEdit()

        self.hour_dropdown = QComboBox()
        self.minute_dropdown = QComboBox()
        self.second_dropdown = QComboBox()

        # pull flight prefix out of GPS image
        self.imgvideocheckbox = QCheckBox("Check if video prefix is in a column (named VideoID)", self)

        self.prefixvideo_parts_checkboxes = []
        self.prefixvideo_parts_label = QLabel()

        ### LIDAR, OUTPUT, and RUN ###
        # lidar file outputted by lidar video
        self.lidarfile_button = QPushButton("LiDAR File",self)
        self.lidarfile_button.clicked.connect(lambda: self.select_file(2))
        self.lidarfile_sel_label = QLabel("",self)
        self.lidarfile_sel_label.setStyleSheet("border: 1px dashed black; padding: 2px; font-style: italic;")

        # rolling window checkbox and text enter
        self.timewindowcheckbox = QCheckBox("Check if you want to find a lidar value within a window", self)
        self.windowsize_box = QLineEdit()
        self.windowsize_box.setValidator(QDoubleValidator()) 

        #output prefix and folder selection
        self.output_prefix_box = QLineEdit()

        outfold_button = QPushButton("Output folder",self)
        outfold_button.clicked.connect(self.select_dir)
        self.outfold_sel_label = QLabel("", self)
        self.outfold_sel_label.setStyleSheet("border: 1px dashed black; padding: 2px; font-style: italic;")

        #run button
        lidarmatch_run_button = QPushButton("Run!",self)
        lidarmatch_run_button.setFont(font)
        lidarmatch_run_button.setStyleSheet("color: red;")
        lidarmatch_run_button.clicked.connect(self.lidarmatch)

        #end message
        self.end_msg = QLabel("",self)
        self.end_msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.end_msg.setFont(font)

        #### GRID LAYOUT ####
        #add labels and buttons to grid layout
        self.grid_layout.addWidget(welcome_label,0,0,1,6)
        self.grid_layout.addItem(spacer1, 1, 0,1,6)

        ### IMAGE LIST section
        self.grid_layout.addWidget(QLabel("Click to upload image list file"),2,2,1,2)
        self.grid_layout.addWidget(self.imglist_button, 2, 0,1,2)

        self.grid_layout.addWidget(self.imglist_sel_label,3,0,1,4)

        self.grid_layout.addWidget(QLabel("Enter Example Image Name:"),4,0,1,1)
        self.grid_layout.addWidget(self.example_image_input,4,1,1,1)

        self.grid_layout.addWidget(QLabel("Enter Delimiter:"),4,2,1,1)
        self.grid_layout.addWidget(self.image_delimiter_input,4,3,1,1)

        self.grid_layout.addWidget(self.imgtimecheckbox,5,0,1,2)
        self.grid_layout.addWidget(self.imgvideocheckbox,5,2,1,2)

        self.grid_layout.addWidget(QLabel("Select Time Components:"),6,0,1,2)
        self.setup_time_parts_widgets(self.grid_layout)

        self.grid_layout.addWidget(QLabel("Select Video Prefix Parts:"),6,2,1,2)

        ### LIDAR FILE, OUTPUT SETTINGS, and RUN BUTTON
        self.grid_layout.addWidget(QLabel("Click to select folder containing lidar file"),2,5,1,1)
        self.grid_layout.addWidget(self.lidarfile_button,2,4,1,1)

        self.grid_layout.addWidget(self.lidarfile_sel_label, 3,4,1,2)

        self.grid_layout.addWidget(self.timewindowcheckbox,4,4,1,2)

        self.grid_layout.addWidget(QLabel("Window size (in seconds)"),5,4,1,1)
        self.grid_layout.addWidget(self.windowsize_box,5,5,1,2)

        self.grid_layout.addWidget(QLabel("Output prefix:"),6,4,1,1)
        self.grid_layout.addWidget(self.output_prefix_box,6,5,1,2)

        self.grid_layout.addWidget(QLabel("Click to select folder where outputs should be saved"),7,5,1,1)
        self.grid_layout.addWidget(outfold_button, 7,4,1,1)

        self.grid_layout.addWidget(self.outfold_sel_label, 8,4,1,2)

        self.grid_layout.addItem(spacer2, 9, 4,1,2)

        self.grid_layout.addWidget(lidarmatch_run_button,10,4,1,2)

        self.grid_layout.addWidget(self.end_msg,11,4,1,2)
       
        # Create a scroll area and set your grid layout as its widget
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)  # Makes the widget inside the scrollable

        scroll_contents = QWidget()
        scroll_contents.setLayout(self.grid_layout)
        scroll_area.setWidget(scroll_contents)

        main_layout = QVBoxLayout()
        main_layout.addWidget(scroll_area)
        self.setLayout(main_layout)

        self.image_delimiter_input.textChanged.connect(self.update_time_parts_dropdowns)
        self.image_delimiter_input.textChanged.connect(self.update_prefix_parts_checkboxes)
        
    def update_time_parts_dropdowns(self):
        example_image_name = self.example_image_input.text()

        for dropdown in (self.hour_dropdown, self.minute_dropdown, self.second_dropdown):
            dropdown.clear()
            dropdown.addItem("None")  # Option to skip the time part
            dropdown.addItems(example_image_name.split(self.image_delimiter_input.text()))
    
    def setup_time_parts_widgets(self, layout):
        layout.addWidget(QLabel("Hour:"),7,0,1,1)
        layout.addWidget(self.hour_dropdown,7,1,1,1)
        layout.addWidget(QLabel("Minute:"),8,0,1,1)
        layout.addWidget(self.minute_dropdown,8,1,1,1)
        layout.addWidget(QLabel("Second:"),9,0,1,1)
        layout.addWidget(self.second_dropdown,9,1,1,1)

    def update_prefix_parts_checkboxes(self):
        example_image_name = self.example_image_input.text()
        delimiter = self.image_delimiter_input.text()

        for checkbox in self.prefixvideo_parts_checkboxes:
            checkbox.deleteLater()
        self.prefixvideo_parts_checkboxes = []

        if delimiter:
            parts = example_image_name.split(delimiter)

            for i, part in enumerate(parts):
                checkbox = QCheckBox(part)
                self.prefixvideo_parts_checkboxes.append(checkbox)
                self.grid_layout.addWidget(checkbox,7+i,2,1,1)

    def select_file(self, button_id):
        file_path = FileSelector.select_file()
        if file_path:
            if button_id == 1:
                self.imglist_sel_label.setText(file_path)
                # Read the file using pandas
                self.dfimages = pd.read_csv(file_path)
                self.imagelist_file_path = file_path

                if "Image" in self.dfimages.columns and not self.dfimages.empty:
                    first_image = self.dfimages['Image'].iloc[0]
                    self.example_image_input.setText(first_image)
            
            elif button_id == 2:
                self.lidarfile_sel_label.setText(file_path)
                # Read in the file
                self.dflidar = pd.read_csv(file_path)
                self.lidar_file_path = file_path
        
    def select_dir(self):
        dir_path = DirSelector.select_dir()
        if dir_path:
            self.outpath = dir_path
            self.outfold_sel_label.setText(dir_path)
    
    def lidarmatch(self):
        self.end_msg.setText("......running......")
        #### PART 1 - set up time and video from image list ####
        # get time in video from image name if need be (if checkbox unchecked)
        if self.imgtimecheckbox.isChecked():
            pass
        else:
            # create column with the time in video extracted
            hr_ix = self.hour_dropdown.currentIndex()-1
            min_ix = self.minute_dropdown.currentIndex()-1
            sec_ix = self.second_dropdown.currentIndex()-1

            self.dfimages['VideoTime'] = ["{0}:{1}:{2}".format(x.split(self.image_delimiter_input.text())[hr_ix], 
                                                            x.split(self.image_delimiter_input.text())[min_ix],
                                                            x.split(self.image_delimiter_input.text())[sec_ix])
                                                            for x in self.dfimages['Image']]
            
        self.dfimages['VideoTime'] = [datetime.strptime(str(x), "%H:%M:%S").time() for x in self.dfimages['VideoTime']]

        #add column for video if need be (if checkbox unchecked)
        if self.imgvideocheckbox.isChecked():
            pass
        else:
            #create column with video ID
            img_video_ixs = [i for i, checkbox in enumerate(self.prefixvideo_parts_checkboxes) if checkbox.isChecked()]

            self.dfimages['VideoID'] = [self.image_delimiter_input.text().join(x.split(self.image_delimiter_input.text())[i] for i in img_video_ixs) 
                            for x in self.dfimages['Image']]

        #### PART 2 - merge image and lidar ####
        self.dflidar['VideoTime'] = [datetime.strptime((str(x).split()[-1]), "%H:%M:%S").time() for x in self.dflidar['VideoTime']]
        self.dflidar = self.dflidar.dropna(subset=['Laser_Alt'])

        if self.timewindowcheckbox.isChecked():
            self.dfimages['ImgTime_s'] = [int(timedelta(hours=t.hour, minutes=t.minute, seconds=t.second).total_seconds()) for t in self.dfimages['VideoTime']]
            self.dflidar['LidarTime_s'] = [int(timedelta(hours=t.hour, minutes=t.minute, seconds=t.second).total_seconds()) for t in self.dflidar['VideoTime']]

            self.dfimages['MergeTime'] = [pd.Timestamp(str(x)) for x in self.dfimages['VideoTime']]
            self.dflidar['MergeTime'] = [pd.Timestamp(str(x)) for x in self.dflidar['VideoTime']]

            window = self.windowsize_box.text()

            self.dfimages = self.dfimages.sort_values(by=['MergeTime'])
            self.dflidar = self.dflidar.sort_values(by=['MergeTime'])

            df_lidarmerge = pd.merge_asof(self.dfimages, self.dflidar[['VideoID','VideoTime','LidarTime_s','MergeTime','Laser_Alt']], on="MergeTime", by="VideoID",
                                          direction="nearest",tolerance=pd.Timedelta("{0}s".format(window)),suffixes = ['_image','_lidar'])
            df_lidarmerge['timediff_sec'] = df_lidarmerge["ImgTime_s"] - df_lidarmerge['LidarTime_s']
            df_lidarmerge = df_lidarmerge.drop(columns=['ImgTime_s','LidarTime_s','MergeTime'])
        else:
            df_lidarmerge = self.dfimages.merge(self.dflidar[['VideoID','VideoTime','Laser_Alt']],how='left',on=['VideoID','VideoTime'])

        # export
        df_lidarmerge.to_csv(os.path.join(self.outpath,"{0}_LidarMerge.csv".format(self.output_prefix_box.text())),index=False)

        # print message telling user that its done running!
        self.end_msg.setText("Done running - check output folders for files!")

class lidarimageWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pull and Merge LiDAR Data for Images")

        #set sizing
        D = self.screen().availableGeometry()
        self.move(1,1)#center.x() + .25*D.width() , center.y() - .5*D.height() )
        self.resize( int(.7*D.width()), int(.5*D.height()) )
        self.setWindowState(self.windowState() & ~QtCore.Qt.WindowState.WindowMinimized
                            | QtCore.Qt.WindowState.WindowActive)
        self.activateWindow()
        
        self.grid_layout = QGridLayout()

        spacer1 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        spacer2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        #add inputs
        welcome_label = QLabel("Welcome to the lidar image matchup tool!")
        welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setBold(True)
        welcome_label.setFont(font)

        ### GPS SECTION ###
        self.gpsfold_button = QPushButton("GPS Image folder",self)
        self.gpsfold_button.clicked.connect(lambda: self.select_dir(1))
        self.gpsfold_sel_label = QLabel("", self)
        self.gpsfold_sel_label.setStyleSheet("border: 1px dashed black; padding: 2px; font-style: italic;")

        self.gps_button = QPushButton("GPS Time File",self)
        self.gps_button.clicked.connect(lambda: self.select_file(1))
        self.gps_sel_label = QLabel("",self)
        self.gps_sel_label.setStyleSheet("border: 1px dashed black; padding: 2px; font-style: italic;")

        self.gpsflightcheckbox = QCheckBox("Check if flight prefix is in a column (named FlightID)", self)
        self.gpsflightcheckbox.stateChanged.connect(lambda: self.toggle_delimiter_box(1))

        self.gpsflight_msg = QLabel("",self)

        #prefix selection set up
        self.example_gps_input = QLineEdit()
        self.gps_delimiter_input = QLineEdit()

        self.prefixgps_parts_checkboxes = []
        self.prefixgps_parts_label = QLabel()

        ### IMAGES SECTION ###
        #folder w/ videos
        self.imgfold_button = QPushButton("Image folder",self)
        self.imgfold_button.clicked.connect(lambda: self.select_dir(2))
        self.imgfold_sel_label = QLabel("", self)
        self.imgfold_sel_label.setStyleSheet("border: 1px dashed black; padding: 2px; font-style: italic;")

        #image csv y/n
        self.imglistcheckbox = QCheckBox("Check if you have a csv with an image list", self)
        self.imglistcheckbox.stateChanged.connect(self.toggle_file_upload_button)

        #image csv button
        self.imglist_button = QPushButton("Image List",self)
        self.imglist_button.setEnabled(False)
        self.imglist_button.clicked.connect(lambda: self.select_file(2))
        self.imglist_sel_label = QLabel("",self)
        self.imglist_sel_label.setStyleSheet("border: 1px dashed black; padding: 2px; font-style: italic;")

        #prefix set up
        self.imgflightcheckbox = QCheckBox("Check if flight prefix is in a column (named FlightID)", self)
        self.imgflightcheckbox.stateChanged.connect(lambda: self.toggle_delimiter_box(2))

        self.imgflight_msg = QLabel("",self)

        #exiftag stuff
        self.open_exif_help_button = QPushButton("Exif Tag Viewer",self)
        self.open_exif_help_button.clicked.connect(self.open_exif_viewer)
        self.exif_tags_dropdown_name = QComboBox(self)
        self.exif_tags_dropdown_date = QComboBox(self)       

        # prefix input 
        self.example_img_input = QLineEdit()

        self.img_delimiter_input = QLineEdit()

        self.prefiximg_parts_checkboxes = []
        self.prefiximg_parts_label = QLabel()

        ### LIDAR, OUTPUT, and RUN ###
        #lidar folder
        lidarfile_button = QPushButton("Lidar file",self)
        lidarfile_button.clicked.connect(lambda: self.select_file(3))
        self.lidarfile_sel_label = QLabel("", self)
        self.lidarfile_sel_label.setStyleSheet("border: 1px dashed black; padding: 2px; font-style: italic;")

        # rolling window checkbox and text enter
        self.timewindowcheckbox = QCheckBox("Check if you want to find a lidar value within a window", self)
        self.windowsize_box = QLineEdit()
        self.windowsize_box.setValidator(QDoubleValidator()) 

        #output prefix and folder selection
        self.output_prefix_box = QLineEdit()

        outfold_button = QPushButton("Output folder",self)
        outfold_button.clicked.connect(lambda: self.select_dir(3))
        self.outfold_sel_label = QLabel("", self)
        self.outfold_sel_label.setStyleSheet("border: 1px dashed black; padding: 2px; font-style: italic;")

        #run button
        lidarimage_run_button = QPushButton("Run!",self)
        lidarimage_run_button.setFont(font)
        lidarimage_run_button.setStyleSheet("color: red;")
        lidarimage_run_button.clicked.connect(self.lidarimage)

        #end message
        self.end_msg = QLabel("",self)
        self.end_msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.end_msg.setFont(font)

        ### GRID LAYOUT ###
        #add labels and buttons to grid layout
        self.grid_layout.addWidget(welcome_label,0,0,1,6)
        self.grid_layout.addItem(spacer1, 1, 0,1,6)

        ## GPS FILE section
        self.grid_layout.addWidget(QLabel("Click to select folder containing GPS time images"),2,1,1,1)
        self.grid_layout.addWidget(self.gpsfold_button,2,0,1,1)

        self.grid_layout.addWidget(self.gpsfold_sel_label,3,0,1,2)

        self.grid_layout.addWidget(QLabel("Click to upload GPS time file"),4,1,1,1)
        self.grid_layout.addWidget(self.gps_button, 4, 0,1,1)

        self.grid_layout.addWidget(self.gps_sel_label,5,0,1,2)

        self.grid_layout.addWidget(self.gpsflightcheckbox,6,0,1,1)

        self.grid_layout.addWidget(self.gpsflight_msg,7,0,1,2)

        self.grid_layout.addWidget(QLabel("Enter Example Image Name:"),8,0,1,1)
        self.grid_layout.addWidget(self.example_gps_input,8,1,1,1)

        self.grid_layout.addWidget(QLabel("Enter Delimiter:"),9,0,1,1)
        self.grid_layout.addWidget(self.gps_delimiter_input,9,1,1,1)

        self.grid_layout.addWidget(QLabel("Select Flight Prefix Parts:"),10,0,1,2)

        ## IMAGE FOLDER AND FILE section
        self.grid_layout.addWidget(QLabel("Click to select folder containing images"),2,3,1,1)
        self.grid_layout.addWidget(self.imgfold_button,2,2,1,1)

        self.grid_layout.addWidget(self.imgfold_sel_label,3,2,1,2)

        self.grid_layout.addWidget(QLabel("Default tag names should appear when\nimage folder is selected, but if not\nclick the 'Exif Tag Viewer' for help"),4,2,1,1)
        self.grid_layout.addWidget(self.open_exif_help_button,4,3,1,1)

        self.grid_layout.addWidget(QLabel("Select file name exif tag"),5,2,1,1)
        self.grid_layout.addWidget(self.exif_tags_dropdown_name,5,3,1,1)

        self.grid_layout.addWidget(QLabel("Select create date exif tag"),6,2,1,1)
        self.grid_layout.addWidget(self.exif_tags_dropdown_date,6,3,1,1)

        self.grid_layout.addWidget(self.imglistcheckbox,7,2,1,2)

        self.grid_layout.addWidget(QLabel("Click to select image list file"),8,3,1,1)
        self.grid_layout.addWidget(self.imglist_button,8,2,1,1)

        self.grid_layout.addWidget(self.imglist_sel_label,9,2,1,2)

        self.grid_layout.addWidget(self.imgflightcheckbox,10,2,1,2)

        self.grid_layout.addWidget(self.imgflight_msg,11,2,1,2)

        self.grid_layout.addWidget(QLabel("Enter Example Image Name:"),12,2,1,1)
        self.grid_layout.addWidget(self.example_img_input,12,3,1,1)

        self.grid_layout.addWidget(QLabel("Enter Delimiter:"),13,2,1,1)
        self.grid_layout.addWidget(self.img_delimiter_input,13,3,1,1)

        self.grid_layout.addWidget(QLabel("Select Flight Prefix Parts:"),14,2,1,2)   

        ## LIDAR FILE, OUTPUT SETTINGS, and RUN BUTTON
        self.grid_layout.addWidget(QLabel("Click to select folder containing lidar files"),2,5,1,1)
        self.grid_layout.addWidget(lidarfile_button, 2,4,1,1)

        self.grid_layout.addWidget(self.lidarfile_sel_label, 3,4,1,2)

        self.grid_layout.addWidget(self.timewindowcheckbox,4,4,1,2)

        self.grid_layout.addWidget(QLabel("Window size (in seconds)"),5,4,1,1)
        self.grid_layout.addWidget(self.windowsize_box,5,5,1,2)

        self.grid_layout.addWidget(QLabel("Output prefix:"),6,4,1,1)
        self.grid_layout.addWidget(self.output_prefix_box,6,5,1,2)

        self.grid_layout.addWidget(QLabel("Click to select folder where outputs should be saved"),7,5,1,1)
        self.grid_layout.addWidget(outfold_button, 7,4,1,1)

        self.grid_layout.addWidget(self.outfold_sel_label, 8,4,1,2)

        self.grid_layout.addItem(spacer2, 9, 4,1,2)

        self.grid_layout.addWidget(lidarimage_run_button,10,4,1,2)

        self.grid_layout.addWidget(self.end_msg,11,4,1,2)

        # Create a scroll area and set your grid layout as its widget
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)  # Makes the widget inside the scrollable

        scroll_contents = QWidget()
        scroll_contents.setLayout(self.grid_layout)
        scroll_area.setWidget(scroll_contents)

        main_layout = QVBoxLayout()
        main_layout.addWidget(scroll_area)
        self.setLayout(main_layout)

        self.gps_delimiter_input.textChanged.connect(lambda: self.update_prefix_parts_checkboxes(1))
        self.img_delimiter_input.textChanged.connect(lambda: self.update_prefix_parts_checkboxes(2))

       # Initialize default selections
        self.default_selections = {
            self.exif_tags_dropdown_name: 'FileName',
            self.exif_tags_dropdown_date: 'CreateDate',
        }

        #exif viewer is now an instance variable
        self.exif_help_window = ExifViewer()

    def toggle_delimiter_box(self, button_id):
        if button_id == 1:
            self.gps_delimiter_input.setEnabled(not self.gpsflightcheckbox.isChecked())
            if self.gpsflightcheckbox.isChecked():
                self.gpsflight_msg.setText("No need to fill in the below boxes since FlightID column exists")
            elif not self.gpsflightcheckbox.isChecked():
                self.gpsflight_msg.setText("")
        elif button_id == 2:
            self.img_delimiter_input.setEnabled(not self.imgflightcheckbox.isChecked())
            if self.imgflightcheckbox.isChecked():
                self.imgflight_msg.setText("No need to fill in the below boxes since FlightID column exists")
            elif not self.imgflightcheckbox.isChecked():
                self.imgflight_msg.setText("")

    def toggle_file_upload_button(self):
        self.imglist_button.setEnabled(self.imglistcheckbox.isChecked())

    def update_prefix_parts_checkboxes(self, button_id):
        if button_id == 1:
            example_image_name = self.example_gps_input.text()
            delimiter = self.gps_delimiter_input.text()

            if not self.gpsflightcheckbox.isChecked():
                for checkbox in self.prefixgps_parts_checkboxes:
                    checkbox.deleteLater()
                self.prefixgps_parts_checkboxes = []

                if delimiter:
                    parts = example_image_name.split(delimiter)

                    for i, part in enumerate(parts):
                        checkbox = QCheckBox(part)
                        self.prefixgps_parts_checkboxes.append(checkbox)
                        self.grid_layout.addWidget(checkbox,10+i,1,1,1)

        elif button_id == 2:
            example_image_name = self.example_img_input.text()
            delimiter = self.img_delimiter_input.text()

            if not self.imgflightcheckbox.isChecked():
                for checkbox in self.prefiximg_parts_checkboxes:
                    checkbox.deleteLater()
                self.prefiximg_parts_checkboxes = []

                if delimiter:
                    parts = example_image_name.split(delimiter)

                    for i, part in enumerate(parts):
                        checkbox = QCheckBox(part)
                        self.prefiximg_parts_checkboxes.append(checkbox)
                        self.grid_layout.addWidget(checkbox,14+i,3,1,1)

    def select_file(self, button_id):
        file_path = FileSelector.select_file()
        if file_path:
            if button_id == 1: ## GPS TIME FILE
                self.gps_sel_label.setText(file_path)
                # Read the file using pandas
                self.dfgps = pd.read_csv(file_path)
                self.gps_file_path = file_path

                if "Image" in self.dfgps.columns and not self.dfgps.empty:
                    first_image = self.dfgps['Image'].iloc[0]
                    self.example_gps_input.setText(first_image)

            elif button_id == 2: ## IMAGE LIST FILE
                self.imglist_sel_label.setText(file_path)
                # Read the file using pandas
                self.dfimglist = pd.read_csv(file_path)
                self.imglist_file_path = file_path

                if "Image" in self.dfimglist.columns and not self.dfimglist.empty:
                    first_image = self.dfimglist['Image'].iloc[0]
                    self.example_img_input.setText(first_image)

            elif button_id == 3: ##LIDAR FILE
                self.laser_all = pd.read_csv(file_path)
                self.laser_file_path = file_path
                self.lidarfile_sel_label.setText(file_path)
               
    def select_dir(self, button_id):
        dir_path = DirSelector.select_dir()
        if dir_path:
            if button_id == 1: ## GPS IMG FOLDER
                self.gpsimgpath = dir_path
                self.gpsfold_sel_label.setText(dir_path)

                #make list of images
                self.gpsimg_names = []
                self.gpsimg_list = []
                for root, dirs, files in os.walk(dir_path):
                    self.gpsimg_names += [m for m in files if not m.startswith(".")]
                    self.gpsimg_list += [os.path.join(root,m) for m in files if not m.startswith(".")]

            elif button_id == 2: ## IMAGE FOLDER
                self.imgpath = dir_path
                self.imgfold_sel_label.setText(dir_path)

                #make list of images
                self.img_names = []
                self.img_list = []
                for root, dirs, files in os.walk(dir_path):
                    self.img_names += [m for m in files if not m.startswith(".")]
                    self.img_list += [os.path.join(root,m) for m in files if not m.startswith(".")]

                #pull first video to be displayed
                first_img = self.img_names[0]
                self.example_img_input.setText(first_img)

                # Fetch Exif tags for the selected file
                if os.name == 'nt': #windows
                    exifpath = os.path.join(sys._MEIPASS,"exiftool.exe")
                else: #mac
                    exifpath = '/usr/local/bin/exiftool'
                self.exif_tags = ExifToolHelper(exifpath).get_tags(self.img_list[0],[])
                exif_tags1 = [x.split(":")[1] if len(x.split(":"))>1 else x for x in list(self.exif_tags[0].keys()) ]
                # run update exiftag drop down
                for dropdown, default_selection in self.default_selections.items():
                    self.update_exif_tags(dropdown, exif_tags1, default_selection)

            elif button_id == 3: ## OUTPUT FOLDER
                self.outpath = dir_path
                self.outfold_sel_label.setText(dir_path)

    def update_exif_tags(self, dropdown, exif_tags, default_selection):
        # Update the Exif tags dropdown
        dropdown.clear()
        dropdown.addItems(["select tag"])
        dropdown.addItems(exif_tags)

        # Set the default selection
        index = dropdown.findText(default_selection)
        if index != -1:
            dropdown.setCurrentIndex(index)

    def open_exif_viewer(self):
        dfexif = pd.DataFrame.from_dict(self.exif_tags[0],orient='index').reset_index().rename(columns={'index':'tag',0:'value'})

        #pass to exif viewer
        self.exif_help_window.set_dataframe(dfexif)
        self.exif_help_window.show()

    def lidarimage(self):
        #### PART 1 - get time for each image and prep image df ####
        #use exift tool to pull the image time
        dfimages = pd.DataFrame()
        tagnames = []
        if os.name == 'nt': #windows
            exifpath = os.path.join(sys._MEIPASS,"exiftool.exe")
        else: #mac
            exifpath = '/usr/local/bin/exiftool'
            
        with ExifToolHelper(exifpath) as et:
            for d in et.get_tags(self.img_list, tags=[self.exif_tags_dropdown_name.currentText(),
                                                      self.exif_tags_dropdown_date.currentText()]):
                tempdict = {}
                for k, v in d.items():
                    tempdict[k] = v
                    tagnames += [k]
                tempdf = pd.DataFrame(data=tempdict,index=[0])
                dfimages = pd.concat([dfimages,tempdf]).reset_index(drop=True)

        # clean up dataframe
        tagnames1 = list(set(tagnames))
        nametag = [x for x in tagnames1 if self.exif_tags_dropdown_name.currentText() in x][0]
        datetag = [x for x in tagnames1 if self.exif_tags_dropdown_date.currentText() in x][0]

        dfimages = dfimages.rename(columns={nametag:"Image",
                                            datetag:"ImageDT"
                                            })
        
        dfimages['ImageDT'] = [datetime.strptime(x,"%Y:%m:%d %H:%M:%S") for x in dfimages['ImageDT']]

        if self.imgflightcheckbox.isChecked():
            #just merge with inputted csv
            dfimages = dfimages.merge(self.dfimglist,how='left',on='Image')
        else:
            #add column w/ flight id using prefix
            img_flight_ixs = [i for i, checkbox in enumerate(self.prefiximg_parts_checkboxes) if checkbox.isChecked()]
            dfimages['FlightID'] = [self.img_delimiter_input.text().join(x.split(self.img_delimiter_input.text())[i] for i in img_flight_ixs) 
                                        for x in dfimages['Image']]  
            #merge if exists but doesn't have flight ID column
            if self.imgflightcheckbox.isChecked():
                dfimages = dfimages.merge(self.dfimglist,how='left',on='Image') 

        #### PART 2 - calculate offset using GPS images ####
        dfgpsimgs = pd.DataFrame()
        with ExifToolHelper(exifpath) as et:
            for d in et.get_tags(self.gpsimg_list, tags=["FileName", "EXIF:CreateDate"]):
                tempdict = {}
                for k, v in d.items():
                    tempdict[k] = v
                tempdf = pd.DataFrame(data=tempdict,index=[0])
                dfgpsimgs = pd.concat([dfgpsimgs,tempdf]).reset_index(drop=True)

        # clean up dataframe
        dfgpsimgs = dfgpsimgs.rename(columns={"File:FileName":"Image",
                                            "EXIF:CreateDate":"ImageDT"
                                            })
        dfgpsimgs['ImageDT'] = [datetime.strptime(x,"%Y:%m:%d %H:%M:%S") for x in dfgpsimgs['ImageDT']]

        # merge with inputted csv
        dfgpsimgs = dfgpsimgs.merge(self.dfgps,how='left',on='Image')

        #add flight id column if needed
        if not self.gpsflightcheckbox.isChecked():
            #add column w/ flight id using prefix
            gps_flight_ixs = [i for i, checkbox in enumerate(self.prefixgps_parts_checkboxes) if checkbox.isChecked()]
            dfgpsimgs['FlightID'] = [self.gps_delimiter_input.text().join(x.split(self.gps_delimiter_input.text())[i] for i in gps_flight_ixs) 
                                        for x in dfgpsimgs['Image']]  
        else: pass

        #calculate offset
        # add GPS date time column
        dfgpsimgs['GPS_DT'] = [datetime.strptime("{0} {1}".format(x,y),"%y%m%d %H:%M:%S") for x,y in zip(dfgpsimgs['GPS_Date'],dfgpsimgs['GPS_Time'])]

        dfgpsimgs['offset'] = dfgpsimgs['GPS_DT'] - dfgpsimgs['ImageDT']

        #### PART 3 - merge w/ lidar ####
        # merge image df and gps df to assign per flight offset to each image
        dfimg_x = dfimages.merge(dfgpsimgs[['FlightID','offset']],how='left',on='FlightID')

        # calculate correct time by adding offset 
        dfimg_x['CorrDT'] = dfimg_x['ImageDT'] + dfimg_x['offset']

        # merge with lidar!
        self.laser_all['CorrDT'] = [datetime.strptime("{0}".format(x),"%Y-%m-%d %H:%M:%S") for x in self.laser_all['CorrDT']]
        self.laser_all = self.laser_all.dropna(subset=['Laser_Alt'])

        if self.timewindowcheckbox.isChecked():
            self.df_imgx['MergeTime'] = [pd.Timestamp(str(x)) for x in self.df_imgx['CorrDT']]
            self.laser_all['MergeTime'] = [pd.Timestamp(str(x)) for x in self.laser_all['CorrDT']]
        
            self.dfimg_x['ImgTime_s'] = [int(timedelta(hours=t.hour, minutes=t.minute, seconds=t.second).total_seconds()) for t in self.dfimg_x['MergeTime']]
            self.laser_all['LidarTime_s'] = [int(timedelta(hours=t.hour, minutes=t.minute, seconds=t.second).total_seconds()) for t in self.laser_all['MergeTime']]

            window = self.windowsize_box.text()

            self.dfimages = self.dfimages.sort_values(by=['MergeTime'])
            self.dflidar = self.dflidar.sort_values(by=['MergeTime'])

            df_lidarmerge = pd.merge_asof(self.dfimg_x, self.laser_all[['CorrDT','LidarTime_s','MergeTime','Laser_Alt']], on="MergeTime",
                                          direction="nearest",tolerance=pd.Timedelta("{0}s".format(window)),suffixes = ['_image','_lidar'])
            df_lidarmerge['timediff_sec'] = df_lidarmerge["ImgTime_s"] - df_lidarmerge['LidarTime_s']
            df_lidarmerge = df_lidarmerge.drop(columns=['ImgTime_s','LidarTime_s','MergeTime'])
        else:
            df_lidarimg = dfimg_x.merge(self.laser_all[['CorrDT','Laser_Alt']],how='left',on='CorrDT')

        #narrow down columns kept for export
        df_lidarimg[['SourceFile','Image','Laser_Alt']]

        # export to csv
        df_lidarimg.to_csv(os.path.join(self.outpath,"{0}_ImageLidar.csv".format(self.output_prefix_box.text())),index=False)

        # print message telling user that its done running!
        self.end_msg.setText("Done running - check output folders for files!")

class collateWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Collate MorphoMetriX Outputs")

        #set sizing
        D = self.screen().availableGeometry()
        self.move(0,0)#center.x() + .25*D.width() , center.y() - .5*D.height() )
        self.resize( int(.4*D.width()), int(.5*D.height()) )
        self.setWindowState(self.windowState() & ~QtCore.Qt.WindowState.WindowMinimized
                            | QtCore.Qt.WindowState.WindowActive)
        self.activateWindow()

        #layout grid settings
        grid_layout = QGridLayout()

        #add inputs
        welcome_label = QLabel("Welcome to the collating tool!\nthis tool will collate your morphometrix outputs into on clean csv")
        welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setBold(True)
        welcome_label.setFont(font)

        spacer1 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        spacer2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        spacer3 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        spacer4 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        spacer5 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        spacer6 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        spacer7 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        #animal ID
        aID_label = QLabel("Check if you want the Animal ID to be assigned\nbased on the name of the folder")
        self.aIDcheckbox = QCheckBox("Use folder names for AID?", self)

        #safety y/n
        safecheckbox_label = QLabel("Check if you want to use a safety")
        self.safecheckbox = QCheckBox("Use safety?", self)
        self.safecheckbox.stateChanged.connect(self.toggle_file_upload_button)

        safetyfile_label = QLabel("Click to upload safety file")
        self.safety_button = QPushButton("Safety File",self)
        self.safety_button.setEnabled(False)
        self.safety_button.clicked.connect(self.select_file)
        self.safety_sel_label = QLabel("",self)
        self.safety_sel_label.setStyleSheet("border: 1px dashed black; padding: 2px; font-style: italic;")

        #output prefix
        prefix_label = QLabel("Enter the prefix you'd like for output files")
        self.prefix_box = QLineEdit()

        #folder w/ mmx outputs
        mmxfold_label = QLabel("Click to select folder\ncontaining MorphoMetriX outputs")
        mmxfold_button = QPushButton("MMX folder",self)
        mmxfold_button.clicked.connect(lambda: self.select_dir(1))
        self.mmxfold_sel_label = QLabel("", self)
        self.mmxfold_sel_label.setStyleSheet("border: 1px dashed black; padding: 2px; font-style: italic;")

        #folder where output should be saved
        savefold_label = QLabel("Click to select folder where\noutputs should be saved")
        savefold_button = QPushButton("Output folder",self)
        savefold_button.clicked.connect(lambda: self.select_dir(2))
        self.savefold_sel_label = QLabel("",self)
        self.savefold_sel_label.setStyleSheet("border: 1px dashed black; padding: 2px; font-style: italic;")

        #choose output options
        outtypes_label = QLabel("Select which outputs you'd like\n(if calculating body condition, don't choose 'both in one')")
        self.outtypes_list = QComboBox(self)
        self.outtypes_list.addItems(['Both in seperate files','Both in one file',
                                     'Just pixels','Just meters'])

        #run buttons
        collate_button = QPushButton("Collate Data! (click to run)",self)
        collate_button.clicked.connect(self.collate)

        #end message
        self.end_msg = QLabel("",self)
        self.end_msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setBold(True)
        self.end_msg.setFont(font)

        #add labels and buttons to grid layout
        grid_layout.addWidget(welcome_label,0,0,1,2)
        grid_layout.addItem(spacer1, 1, 0,1,2)

        grid_layout.addWidget(aID_label,2,1,1,1)
        grid_layout.addWidget(self.aIDcheckbox,2,0,1,1)

        grid_layout.addItem(spacer2, 3, 0,1,2)

        grid_layout.addWidget(safecheckbox_label,4,1,1,1)
        grid_layout.addWidget(self.safecheckbox,4,0,1,1)

        grid_layout.addWidget(safetyfile_label,5,1,1,1)
        grid_layout.addWidget(self.safety_button, 5, 0,1,1)

        grid_layout.addWidget(self.safety_sel_label,6,0,1,2)

        grid_layout.addItem(spacer3, 7, 0,1,2)

        grid_layout.addWidget(prefix_label,8,1,1,1)
        grid_layout.addWidget(self.prefix_box, 8, 0,1,1)

        grid_layout.addItem(spacer4, 9, 0,1,2)

        grid_layout.addWidget(mmxfold_label,10,1,1,1)
        grid_layout.addWidget(mmxfold_button, 10, 0,1,1)

        grid_layout.addWidget(self.mmxfold_sel_label,11,0,1,2)

        grid_layout.addItem(spacer5, 12, 0,1,2)

        grid_layout.addWidget(savefold_label,13,1,1,1)
        grid_layout.addWidget(savefold_button, 13, 0,1,1)

        grid_layout.addWidget(self.savefold_sel_label,14,0,1,2)

        grid_layout.addItem(spacer6, 15, 0,1,2)

        grid_layout.addWidget(outtypes_label,16,1,1,1)
        grid_layout.addWidget(self.outtypes_list,16,0,1,1)

        grid_layout.addItem(spacer7, 17, 0,1,2)

        grid_layout.addWidget(collate_button,18,0,1,2)

        grid_layout.addWidget(self.end_msg,19,0,1,2)

        self.setLayout(grid_layout)

        ##set up paths
        self.mmxpath = None
        self.savepath = None

    def toggle_file_upload_button(self):
        self.safety_button.setEnabled(self.safecheckbox.isChecked())

    def select_file(self):
        file_path = FileSelector.select_file()
        if file_path:
            self.safety_sel_label.setText(file_path)
            # Read the file using pandas
            self.dfsafe = pd.read_csv(file_path)
            self.safe_file_path = file_path
        

    def select_dir(self, button_id):
        dir_path = DirSelector.select_dir()
        if dir_path:
            if button_id == 1:
                self.mmxpath = dir_path
                self.mmxfold_sel_label.setText(dir_path)
            elif button_id == 2:
                self.savepath = dir_path
                self.savefold_sel_label.setText(dir_path)
   
    def collate(self):
        self.end_msg.setText("....running....")
        #pull in prefix for naming and saving
        prefix = self.prefix_box.text()
        outfold = self.savepath
        out_option = self.outtypes_list.currentText()

        #make lists
        #for csvs
        csvs_all = []
        csvs = []
        not_mmx = []

        #walk through all folders in GUI folder and collect all csvs
        for root,dirs,files in os.walk(self.mmxpath):
            csvs_all += [os.path.join(root,f) for f in files if f.endswith('.csv') & ~f.startswith(".")]
        #make sure the csvs are morphometrix outputs by checking first row
        csvs += [c for c in csvs_all if 'Value_unit' in pd.read_csv(c).columns]
        #make list of all csvs that were not morphometrix csvs to tell user
        not_mmx += [x for x in csvs_all if x not in csvs]

        #combine all csvs
        df_all = pd.DataFrame()
        #list of csvs containing duplicate measurement names
        dup_csvs = []
        for c in csvs:
            df_temp = pd.read_csv(c)
            image_name = os.path.split(str(df_temp.loc[df_temp['Object']=='Image Path','Value'].item()))[-1]
            df_temp['Image'] = image_name
            df_temp['csv'] = c
            df_temp['Object'] = [x.replace(".0",".00") if ".00" not in x else x for x in df_temp['Object']]
            df_temp['Object'] = ["{0}_w{1}".format(x.split("_w")[0],str(x.split("w")[1]).rjust(5, '0')) if "_w" in x else x for x in df_temp['Object']]

            #if use folder name for aID is checked, replace Image ID w/ folder name
            if self.aIDcheckbox.isChecked():
                Image_ID = Path(df_temp.loc[df_temp['Object']=='Image Path','Value'].item()).parts[-2]
                df_temp.loc[df_temp['Object']=='Image ID','Value'] = Image_ID
            else: pass
            
            #if this df contains duplicate measurement names (ex. TL twice), add to list, this throws problems when pivoting
            dup_check = df_temp.loc[df_temp['Value_unit'] == 'Meters']
            if dup_check.duplicated(subset=['Object']).any() == True:
                dup_csvs += [c]
            else: pass

            df_all = pd.concat([df_all,df_temp])

        #stop run if duplicate measurement names exist
        if len(dup_csvs) > 0:
            #export text file containg list of csvs containing duplicate names
            with open(os.path.join(outfold,"{0}_csvs containing duplicate measurements.txt").format(prefix), "w") as f:
                f.write(f"{dup_csvs}")
            #update message to alert user to this
            self.end_msg.setText("edit duplicate Object names and run script again, see file in output folder for list of csvs")
        else: pass

        #split out into metadata, meters, and pixels
        df_meta = df_all.loc[df_all['Value_unit'] == 'Metadata']
        df_meters = df_all.loc[df_all['Value_unit'].isin(['Meters','Square Meters','Degrees'])]
        df_pixels = df_all.loc[df_all['Value_unit'].isin(['Pixels','Degrees'])]
        

        #pivot metadata
        df_meta1= df_meta.pivot(index=["Image",'csv'],columns='Object',values='Value').reset_index().rename(columns={"Image ID":"Image_ID",
                                                                                                             "Image Path":"Image_Path",
                                                                                                             "Focal Length":"Focal_Length",
                                                                                                             "Pixel Dimension":"Pixel_Dimension",
                                                                                                             "Mirror Side":"Mirror_Side"
                                                                                                             })

        #if safety
        if self.safecheckbox.isChecked():
            #merge with safety to get scaling metadata
            df_safe = df_meta1[['csv','Image','Image_ID','Image_Path','Mirror_Side','Notes']].merge(self.dfsafe,how='left',on='Image')
            df_sx = df_pixels.merge(df_safe,how='left',on=['Image','csv'])

            #set up to run equation
            alt = df_sx['Altitude'].values
            focl = df_sx['Focal_Length'].values
            pixd = df_sx['Pixel_Dimension'].values
            pixc = df_sx['Value'].values.astype(float)
            #run equation to calculate scaled measurements
            df_sx['Value_m'] = ((alt/focl)*pixd)*pixc

            #make meters output df
            df_mx = df_sx.pivot(index=['Image','csv'],columns='Object',values='Value_m').merge(df_safe,how='left',on=['Image','csv'])
            df_mx['metadata_source'] = "safety_file"

            #make pixels output df
            df_px = df_sx.pivot(index=['Image','csv'],columns='Object',values='Value').merge(df_safe,how='left',on=['Image','csv'])
            df_px['metadata_source'] = "safety_file"

            #make both m and px output df
            df_mpx = df_mx.merge(df_sx.pivot(index=['Image','csv'],columns='Object',values='Value'),how='left',on=['Image','csv'],suffixes=['_m','_px'])
            
        else:
            #prep meters output df
            df_mx = df_meters.pivot(index=['Image','csv'],columns='Object',values='Value').merge(df_meta1,how='left',on=['Image','csv'])
            df_mx['metadata_source'] = 'mmx_input'

            #prep pixels output df
            df_px = df_pixels.pivot(index=['Image','csv'],columns='Object',values='Value').merge(df_meta1,how='left',on=['Image','csv']) 
            df_px['metadata_source'] = 'mmx_input'

            #make both m and px output df
            df_mpx = df_mx.merge(df_pixels.pivot(index=['Image','csv'],columns='Object',values='Value'),how='left',on=['Image','csv'],suffixes=['_m','_px'])
            
        #sort columns in all dataframes
        start_columns = ['csv','Image','Image_ID','Image_Path','Altitude','Focal_Length',
                         'Pixel_Dimension','Mirror_Side','Notes','metadata_source']
        #here we split and concatenate so that the start columns are now first
        df_mpx = pd.concat([df_mpx[start_columns],df_mpx.drop(start_columns,axis=1)],axis=1)
        df_px = pd.concat([df_px[start_columns],df_px.drop(start_columns,axis=1)],axis=1)
        df_mx = pd.concat([df_mx[start_columns],df_mx.drop(start_columns,axis=1)],axis=1)

        #export based on option selected
        if out_option == 'Both in one file':
            df_mpx.to_csv(os.path.join(outfold,"{0}_MetersAndPixels.csv".format(prefix)),index=False)
        elif out_option == 'Both in seperate files':
            df_mx.to_csv(os.path.join(outfold,"{0}_Meters.csv".format(prefix)),index=False) 
            df_px.to_csv(os.path.join(outfold,"{0}_Pixels.csv".format(prefix)),index=False)
        elif out_option == 'Just pixels':
            df_px.to_csv(os.path.join(outfold,"{0}_Pixels.csv".format(prefix)),index=False)
        elif out_option == 'Just meters':
            df_mx.to_csv(os.path.join(outfold,"{0}_Meters.csv".format(prefix)),index=False)

        self.end_msg.setText("Done running - check output folders for files!")
        
        #export text file of input data
        #make notes as string
        notes = "CollatriX Run: {0} \n\nAnimal ID from folder name?: {1} \n\nSafety file: {2}\n\nNumber of files collated: {3}\n\n".format(prefix,("yes" if self.aIDcheckbox.isChecked() else "no"), (self.safe_file_path if self.safecheckbox.isChecked() else "no safety used"), len(csvs))
        #write to text file
        with open(os.path.join(outfold,"{0}_ProcessingNotes.txt").format(prefix), "w") as f:
            f.write(f"{notes}")

class bodycondWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Calculate Body Condition Metrics")

        #set sizing
        D = self.screen().availableGeometry()
        self.move(0,0)#center.x() + .25*D.width() , center.y() - .5*D.height() )
        self.resize( int(.4*D.width()), int(.5*D.height()) )
        self.setWindowState(self.windowState() & ~QtCore.Qt.WindowState.WindowMinimized
                            | QtCore.Qt.WindowState.WindowActive)
        self.activateWindow()

        #layout grid settings
        grid_layout = QGridLayout()

        #add inputs
        welcome_label = QLabel("Welcome to the body condition metrix tool!\nthis tool can calculate common cetacean body condition metrics and add them to your output file")
        welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont(); font.setBold(True)
        welcome_label.setFont(font)

        spacer1 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        spacer2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        spacer3 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        spacer4 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        spacer5 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        #collatrix output file
        self.ccxfile_button = QPushButton("Collated Output File",self)
        self.ccxfile_button.clicked.connect(self.select_file)
        self.ccxfile_sel_label = QLabel("",self)
        self.ccxfile_sel_label.setStyleSheet("border: 1px dashed black; padding: 2px; font-style: italic;")

        #calculate body volume
        self.BVcheckbox = QCheckBox("Calculate Body Volume?", self)

        ## BV method choice
        self.BVmeth_list = QComboBox(self)
        self.BVmeth_list.addItems(['Circle','Ellipse', "Both"])

        ## note on ellipse settings
        ellipse_notes = QLabel("Note: ellipse method always uses lower = 0, upper = 100, and interval = 5. If you choose 'Both', enter values for the circle method.")
        font1 = QFont(); font1.setItalic(True)
        ellipse_notes.setFont(font1)

        ## BV inputs
        self.BV_TL_box = QLineEdit() #name of TL
        self.BV_low_box = QLineEdit() #lower bound
        self.BV_low_box.setValidator(QDoubleValidator()) 
        self.BV_upp_box = QLineEdit() #upper bound
        self.BV_upp_box.setValidator(QDoubleValidator())
        self.BV_int_box = QLineEdit() #interval 
        self.BV_int_box.setValidator(QDoubleValidator())

        #calculate BAI
        self.BAIcheckbox = QCheckBox("Calculate Body Area Index (BAI)?",self)

        ## BAI method choice
        self.BAImeth_list = QComboBox(self)
        self.BAImeth_list.addItems(['Parabola','Trapezoid', "Both"])

        ## BAI inputs
        self.BAI_TL_box = QLineEdit() #name of TL
        self.BAI_low_box = QLineEdit() #lower bound
        self.BAI_low_box.setValidator(QDoubleValidator())
        self.BAI_upp_box = QLineEdit() #upper bound
        self.BAI_upp_box.setValidator(QDoubleValidator())
        self.BAI_int_box = QLineEdit() #inter
        self.BAI_int_box.setValidator(QDoubleValidator())

        #output prefix
        self.prefix_box = QLineEdit()

        #folder where output should be saved
        savefold_label = QLabel("Click to select folder where outputs should be saved")
        savefold_button = QPushButton("Output folder",self)
        savefold_button.clicked.connect(lambda: self.select_dir(1))
        self.savefold_sel_label = QLabel("",self)
        self.savefold_sel_label.setStyleSheet("border: 1px dashed black; padding: 2px; font-style: italic;")

        #run buttons
        bodycond_button = QPushButton("Calculated Body Condition! (click to run)",self)
        bodycond_button.clicked.connect(self.calc_bodycond)

        #end message
        self.end_msg = QLabel("",self)
        self.end_msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setBold(True)
        self.end_msg.setFont(font)

        #add labels and buttons to grid layout
        grid_layout.addWidget(welcome_label,0,0,1,2)
        grid_layout.addItem(spacer1, 1, 0,1,2)

        grid_layout.addWidget(QLabel("Click to upload collated output"),2,1,1,1)
        grid_layout.addWidget(self.ccxfile_button,2,0,1,1)

        grid_layout.addWidget(self.ccxfile_sel_label,3,0,1,2)

        grid_layout.addItem(spacer2, 4, 0,1,2)

        grid_layout.addWidget(QLabel("Check if you want to calculate Body Volume"),5,1,1,1)
        grid_layout.addWidget(self.BVcheckbox,5,0,1,1)

        grid_layout.addWidget(QLabel("Select Body Volume calculation method"),6,1,1,1)
        grid_layout.addWidget(self.BVmeth_list,6,0,1,1)

        grid_layout.addWidget(ellipse_notes,7,0,1,2)

        grid_layout.addWidget(QLabel("Length measurement name"),8,0,1,1)
        grid_layout.addWidget(self.BV_TL_box,8,1,1,1)

        grid_layout.addWidget(QLabel("Lower bound"),9,0,1,1)
        grid_layout.addWidget(self.BV_low_box,9,1,1,1)

        grid_layout.addWidget(QLabel("Upper bound"),10,0,1,1)
        grid_layout.addWidget(self.BV_upp_box,10,1,1,1)

        grid_layout.addWidget(QLabel("Interval"),11,0,1,1)
        grid_layout.addWidget(self.BV_int_box,11,1,1,1)

        grid_layout.addItem(spacer3, 12, 0,1,2)

        grid_layout.addWidget(QLabel("Check if you want to calculate Body Area Index (BAI)"),13,1,1,1)
        grid_layout.addWidget(self.BAIcheckbox,13,0,1,1)

        grid_layout.addWidget(QLabel("Select BAI calculation method"),14,1,1,1)
        grid_layout.addWidget(self.BAImeth_list,14,0,1,1)

        grid_layout.addWidget(QLabel("Length measurement name"),15,0,1,1)
        grid_layout.addWidget(self.BAI_TL_box,15,1,1,1)

        grid_layout.addWidget(QLabel("Lower bound"),16,0,1,1)
        grid_layout.addWidget(self.BAI_low_box,16,1,1,1)

        grid_layout.addWidget(QLabel("Upper bound"),17,0,1,1)
        grid_layout.addWidget(self.BAI_upp_box,17,1,1,1)

        grid_layout.addWidget(QLabel("Interval"),18,0,1,1)
        grid_layout.addWidget(self.BAI_int_box,18,1,1,1)

        grid_layout.addItem(spacer4, 19, 0,1,2)

        grid_layout.addWidget(QLabel("Enter prefix for output file"),20,1,1,1)
        grid_layout.addWidget(self.prefix_box,20,0,1,1)

        grid_layout.addWidget(savefold_label,21,1,1,1)
        grid_layout.addWidget(savefold_button, 21, 0,1,1)

        grid_layout.addWidget(self.savefold_sel_label,22,0,1,2)

        grid_layout.addItem(spacer5, 23, 0,1,2)

        grid_layout.addWidget(bodycond_button,24,0,1,2)

        grid_layout.addWidget(self.end_msg,25,0,1,2)

        self.setLayout(grid_layout)

        ##set up paths
        self.mmxpath = None
        self.savepath = None

    def toggle_file_upload_button(self):
        self.safety_button.setEnabled(self.safecheckbox.isChecked())

    def select_file(self):
        file_path = FileSelector.select_file()
        if file_path:
            self.ccxfile_sel_label.setText(file_path)
            # Read the file using pandas
            self.dfccx = pd.read_csv(file_path)
            self.ccx_file_path = file_path

    def select_dir(self, button_id):
        dir_path = DirSelector.select_dir()
        if dir_path:
            if button_id == 1:
                self.savepath = dir_path
                self.savefold_sel_label.setText(dir_path)
    
    def calc_bodycond(self):
        #set inputs
        df_all = self.dfccx; df_all['Image_ID'] = df_all['Image_ID'].astype(str)
        prefix = self.prefix_box.text()
        outfold = self.savepath

        #### BODY VOLUME
        if self.BVcheckbox.isChecked():
            tl_name = self.BV_TL_box.text()
            lower = self.BV_low_box.text()
            upper = self.BV_upp_box.text()
            interval = self.BV_int_box.text()

            bv_method = self.BVmeth_list.currentText()

            if bv_method == 'Ellipse':
                df_vol = self.bv_ellipse(df_all,tl_name)
                BV_inputs = "TL name = {0}\n\nBV method = {1}\n\nlower bound = {2}\n\nupper bound = {3}\n\ninterval = {4}".format(tl_name,bv_method,0,100,5)
            elif bv_method == 'Circle':
                df_vol= self.bv_circle(df_all,tl_name,interval,lower,upper)
                BV_inputs = "TL name = {0}\n\nBV method = {1}\n\nlower bound = {2}\n\nupper bound = {3}\n\ninterval = {4}".format(tl_name,bv_method,lower,upper,interval)
            elif bv_method == 'Both':
                df_ell = self.bv_ellipse(df_all,tl_name)
                df_frust = self.bv_circle(df_all,tl_name,interval,lower,upper)
                df_vol = pd.merge(df_ell,df_frust,on=['Image_ID','Image'])
                BV_inputs = "TL name = {0}\n\nBV method = Both\n\nFor Ellipse: set lower, upper, and interval of 0,100,5\n\nFor circular:lower bound = {1}\n\nupper bound = {2}\n\ninterval = {3}".format(tl_name,lower,upper,interval)

            # merge w/ big data frame 
            df_allx = pd.merge(df_all,df_vol,on=['Image_ID','Image'])

        else: 
            BV_inputs = "Body volume not calculated"
            df_allx = df_all

        #### BODY AREA INDEX
        if self.BAIcheckbox.isChecked():
            tl_name = self.BAI_TL_box.text()
            b_lower = self.BAI_low_box.text()
            b_upper = self.BAI_upp_box.text()
            b_interval = self.BAI_int_box.text()

            bai_method = self.BAImeth_list.currentText()

            BAI_inputs = "BAI method = {1}\n\nTL name = {0}\n\nlower bound = {2}\n\nupper bound = {3}\n\ninterval = {4}".format(tl_name,bai_method,b_lower,b_upper,b_interval)

            if bai_method == 'Parabola':
                df_bai = self.bai_parabola(df_allx,tl_name,b_interval,b_lower,b_upper)
            elif bai_method == 'Trapezoid':
                df_bai = self.bai_trapezoid(df_allx,tl_name,b_interval,b_lower,b_upper)
            elif bai_method == 'Both':
                df_par = self.bai_parabola(df_allx,tl_name,b_interval,b_lower,b_upper)
                df_trap = self.bai_trapezoid(df_allx,tl_name,b_interval,b_lower,b_upper)
                df_bai = pd.merge(df_par,df_trap,on = ['Image_ID','Image'])

            df_all1 = pd.merge(df_allx,df_bai,on=['Image_ID','Image'])

        else:
            BAI_inputs = "BAI not calculated"
            df_all1 = df_allx

        #### PREP for export
        if 'index' in df_all1.columns:
            df_all1 = df_all1.drop(['index'],axis=1)
        else:
            df_all1 = df_all1

        outcsv = os.path.join(outfold,"{0}_bodycondition.csv".format(prefix))
        df_all1.to_csv(outcsv,sep = ',',index_label = 'IX')

        self.end_msg.setText("Done running - check output folders for files!")
        
        #export text file of input data
        #make notes as string
        notes = "CollatriX Body Condition Run: {0}\n\nInput File: {1}\n\nBody Volume: \n\n{2}\n\n\n\nBody Area Index:\n\n{3}".format(prefix, self.ccx_file_path, BV_inputs, BAI_inputs)
        #write to text file
        with open(os.path.join(outfold,"{0}_ProcessingNotes.txt").format(prefix), "w") as f:
            f.write(f"{notes}")

    #body volume circular frustrum function
    def bv_circle(self,df_all,tl_name,interval,lower,upper):
        body_name = "BVcir_{0}perc".format(interval) #name of body volume column will use interval amount
        volm = [] #make empty list of widths
        #now fill list with the names of the width columns we want
        volm += ["{0}_w{1}".format(tl_name,format(x, f".{2}f")) for x in np.arange(float(lower),(float(upper)+ float(interval)), float(interval))]
        #check that those columns are in the dataframe
        colarr = np.array(df_all.columns)
        mask = np.isin(colarr,volm)
        cc = list(colarr[mask])
        vlist = ['index',tl_name]
        vlist.extend(cc)
        ##calculate body col
        df_all_ix = df_all
        df_all_ix['index'] = df_all_ix['Image_ID']+"*"+df_all_ix['Image'] #make column thats Image and AID combined
        df1 = df_all_ix[vlist] #subset dataframe to just columns we want to use
        df1['spacer'] = np.NaN #add row of nans, we need this for the roll
        dfnp = np.array(df1) #convert dataframe to a numpy array
        ids = dfnp[:,0] #isolate array of just IDs
        tl = dfnp[:,1] #isolate array of just TLs
        r = (dfnp[:,2:])/2 #isolate array of just widths and divide each val by 2 (calculate radius)
        R = (np.roll(r,1,axis=1)) #make second array that's shifted over 1
        p2 = ((r**2)+(r*R)+(R**2)) #calculate the part of the equation that invovles the widths
        p1 = (tl*(float(interval)/100))*(1/3)*math.pi #calculate the part of the equation that invovles TL
        v = p1[:,None]*p2 #calculate the volume of each frustrum
        vsum = np.nansum(v,axis=1) #sum all frustrums per ID
        vol_arr = np.column_stack((ids,vsum)) #make 2D array (df) of IDs and volumes
        dfvx = pd.DataFrame(data=vol_arr,columns=["index",body_name]) #convert array to dataframe
        #make Animal_ID and Image columns again and drop index
        dfvx['Image_ID'] = [x.split("*")[0] for x in dfvx['index']]
        dfvx['Image'] = [x.split("*")[1] for x in dfvx['index']]
        dfvx = dfvx.drop(["index"],axis=1)
        #check for duplicates and group
        cls = dfvx.columns.tolist() #get list of column headers
        grBy = ['Image_ID','Image'] #list of columns to group by
        groups = [x for x in cls if x not in grBy] #get list of columns to be grouped
        df_vol = dfvx.groupby(['Image_ID','Image'])[groups].apply(lambda x: x.astype(float).sum()).reset_index() #group to make sure no duplicates
        return df_vol
    
    #body volume ellipse frustrum
    ## this code is based on Christiansen et al 2019 https://datadryad.org/stash/dataset/doi:10.5061/dryad.m0087p4
    def bv_ellipse(self,df_all,tl_name):
        # first, we need to add height columns
        ## for 5-85% we'll use the ratio column
        for x in np.arange(5,90,5):
            w = "{0}_w{1}".format(tl_name,format(x, f".{2}f"))
            # add error flag here if column doesn't exist
            h = w.replace("w","h")
            # pull ratio column
            r = w.replace("w","ratio")

            df_all[h] = df_all[w] * df_all[r]

        ## for 0, 100, 90, and 95...
        # 0 and 100 are set to 0. 90 and 95 are interpolated based on the 85% value
        # need 85% values
        w85 = "{0}_w{1}".format(tl_name,format(85, f".{2}f")) #set up column name
        h85 = "{0}_h{1}".format(tl_name,format(85, f".{2}f")) #set up column name

        for x in [90,95,0,100]:
            # set up column that is being calculated
            wx = "{0}_w{1}".format(tl_name,format(x, f".{2}f")) #set up column name
            hx = "{0}_h{1}".format(tl_name,format(x, f".{2}f")) #set up column name

            # if 90 or 95, interpolate
            if x == 90:
                df_all[wx] = df_all[w85] - (1*(df_all[w85]/3))
                df_all[hx] = df_all[h85] - (1*(df_all[h85]/3))
            elif x == 95:
                df_all[wx] = df_all[w85] - (2*(df_all[w85]/3))
                df_all[hx] = df_all[h85] - (2*(df_all[h85]/3))
            
            #if 0 or 100, set to 0
            else:
                df_all[wx] = 0; df_all[hx] = 0

        # now for the actual calculation
        # calculate BVe
        ## set up column lists
        lower = 0; upper = 100; interval = 5
        body_name = "BVell_{0}perc".format(interval) #name of body volume column will use interval amount
        volm = [] #make empty list of widths
        for x in range(lower,(upper + interval), interval): #loop through range of widths
            xx = "{0}_w{1}".format(tl_name,format(x, f".{2}f")) #create the name of the headers to pull measurements from
            volm += [xx] #add to list
        wlist = []
        for i in volm: #loop through column headers
            for ii in df_all.columns:
                if i in ii:
                    wlist += [ii]
        hlist = [x.replace("w","h") for x in wlist]

        ## actually calculate
        ### but first, make our own quad function since scipy doesn't have a universal mac distribution
        def quad_function(ww, WW, hh, HH, TL, interval):
            ph = float(interval) / float(100)
            tl_h = float(TL) * ph

            # Set up equation for volume of elliptical frustum
            def efunc(x, ww, WW, hh, HH):
                return math.pi * ((ww + (WW - ww) * x) / 2) * ((hh + (HH - hh) * x) / 2)

            # Manually integrate using the trapezoidal rule
            integral = 0.0
            num_steps = 100
            step_size = 1.0 / num_steps

            for j in range(num_steps):
                x0 = j * step_size; x1 = (j + 1) * step_size
                y0 = efunc(x0, ww, WW, hh, HH)
                y1 = efunc(x1, ww, WW, hh, HH)
                trap_area = 0.5 * (x1 - x0) * (y0 + y1)
                integral += trap_area

            return integral * tl_h
        
        ### ok now loop through 5% section
        ids = []; vs = []; imgs = []
        for i,j in enumerate(wlist[:-1]):
            jj = wlist[i+1]
            k = hlist[i]
            kk = hlist[i+1]
            #calculate volume by looping through two columns at a time
            for ww, WW, hh,HH,TL,anid,img in zip(df_all[j],df_all[jj],df_all[k],df_all[kk],df_all[tl_name],df_all['Image_ID'],df_all['Image']):
                #run quad function
                v1 = quad_function(ww, WW, hh, HH, TL, interval)
                
                # add values to lists
                ids += [anid]; vs += [v1]; imgs += [img]
        
        d = {'Image_ID':ids, body_name:vs, 'Image':imgs} #make dataframe of id and body volume
        df = pd.DataFrame(data = d) #make dataframe
        cls = df.columns.tolist() #get list of column headers
        grBy = ['Image_ID','Image'] #list of columns to group by
        groups = [x for x in cls if x not in grBy] #get list of columns to be grouped
        dfvol = df.groupby(['Image_ID','Image'])[groups].apply(lambda x: x.astype(float).sum()).reset_index() #group to make sure no duplicates
        return(dfvol)


    #BAI from parabola functions
    def bai_parabola(self,df_all,tl_name,b_interval,b_lower,b_upper):
        b_interval = float(b_interval)
        b_lower = float(b_lower)
        b_upper = float(b_upper)
        df_all = df_all.dropna(how="all",axis='rows').reset_index()
        bai_name = "BAIpar_{0}perc".format(b_interval) #create BAI column header using interval
        sa_name = 'SA_{0}perc'.format(b_interval)
        bai = [] #list of columns containing the width data we want to use to calculate BAI
        perc_l = []
        for x in np.arange(b_lower,(b_upper + b_interval), b_interval): # loop through columns w/in range we want
            xx = "{0}_w{1}".format(tl_name,format(x, f".{2}f")) #set up column name
            bai += [xx]
            perc_l += [x/100]
        #here we check that the widths are actually in the column headers
        colarr = np.array(df_all.columns)
        mask = np.isin(colarr,bai)
        cc = list(colarr[mask])
        blist = []
        blist.extend(cc)
        #calculate BAI
        df_all_ix = df_all
        df_all_ix['index'] = df_all_ix['Image_ID']+"*"+df_all_ix['Image'] #make column thats Image and AID combined
        npy = np.array(df_all_ix[bai]) #make array out of width values to be used
        ids = np.array(df_all_ix['index'])
        plist = np.array(perc_l) #make array of the percents
        npTL = np.array(df_all_ix[tl_name]) #make array of the total lengths
        x = np.tile(npTL.reshape(npTL.shape[0],-1), (1,plist.size)) #make a 2D array of TL's repeating to be multiplied with the percs
        npx = x * plist #make 2D array of the x values for the regression
        min_tl = npTL*(b_lower/100)
        max_tl = npTL*(b_upper/100)
        newx = np.linspace(min_tl,max_tl,1000)
        sas = []
        for i in range(npx.shape[0]):
            xx = npx[i,:]; yy = npy[i,:]; newxx = newx[:,i]
            lm = np.polyfit(xx,yy,2)
            fit = np.poly1d(lm)
            # Integrate the polynomial fit manually using the trapezoidal rule
            integral = 0.0
            for j in range(len(newxx) - 1):
                x0 = newxx[j]
                x1 = newxx[j + 1]
                y0 = fit(x0)
                y1 = fit(x1)
                trap_area = 0.5 * (x1 - x0) * (y0 + y1)
                integral += trap_area
            sas.append(integral)
        bais = (sas/((npTL*((b_upper-b_lower)/float(100)))**2))*100
        bai_arr = np.column_stack((ids,bais,sas))
        dfb = pd.DataFrame(data = bai_arr,columns= ['index',bai_name,sa_name])
        dfb['Image_ID'] = [x.split("*")[0] for x in dfb['index']]
        dfb['Image'] = [x.split("*")[1] for x in dfb['index']]
        dfb = dfb.drop(["index"],axis=1)
        cls = dfb.columns.tolist()
        grBy = ['Image_ID','Image'] #list of columns to group by
        groups = [x for x in cls if x not in grBy]
        dfp = dfb.groupby(["Image_ID",'Image'])[groups].apply(lambda x: x.astype(float).sum()).reset_index()
        return dfp

    #BAI trapezoid function
    def bai_trapezoid(self,df_all,tl_name,b_interval,b_lower,b_upper):
        b_interval = float(b_interval)
        b_lower = float(b_lower)
        b_upper = float(b_upper)
        bai_name = "BAItrap_{0}perc".format(b_interval) #create BAI column header using interval
        bai = [] #list of columns containing the width data we want to use to calculate BAI
        for x in np.arange(b_lower,(b_upper + b_interval), b_interval): # loop through columns w/in range we want
            xx = "{0}_w{1}".format(tl_name,format(x, f".{2}f")) #set up column name
            bai += [xx]
        blist = []
        for i in bai:
            for ii in df_all.columns:
                if i in ii:
                    blist += [ii]
        ids = []
        bais = []
        imgs = []
        for i,j in enumerate(blist[:-1]):
            jj = blist[i+1]
            for w, W, hh,anid,img in zip(df_all[j],df_all[jj], df_all[tl_name],df_all['Image_ID'],df_all['Image']):
                ph = float(b_interval)/float(100)
                h = float(hh)*ph
                sa1 = (float(1)/float(2))*(w+W)*h
                ids += [anid]
                bais += [sa1]
                imgs += [img]
        d = {'Image_ID':ids, bai_name:bais, 'Image':imgs}
        df = pd.DataFrame(data = d)

        cls = df.columns.tolist()
        grBy = ['Image_ID','Image']
        groups = [x for x in cls if x not in grBy]
        df1 = df.groupby(['Image_ID','Image'])[groups].apply(lambda x: x.astype(float).sum()).reset_index()
        dft = pd.merge(df_all[['Image_ID','Image',tl_name]],df1,on = ['Image_ID','Image'])
        dft[bai_name] = (dft[bai_name]/((dft[tl_name]*((b_upper-b_lower)/float(100)))**2))*100
        dft = dft.drop([tl_name],axis=1)
        return dft

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        #set window title
        self.setWindowTitle("CollatriX Home ({0})".format(cx_version))

        #set sizing of window
        D = self.screen().availableGeometry()
        self.move(0,0)
        self.resize( int(.4*D.width()), int(.2*D.height()) )
        self.setWindowState(self.windowState() & ~QtCore.Qt.WindowState.WindowMinimized
                            | QtCore.Qt.WindowState.WindowActive)
        self.activateWindow()

        #layout grid settings
        grid_layout = QGridLayout()
        grid_layout.setColumnMinimumWidth(0, 1) #column 0
        grid_layout.setColumnMinimumWidth(1, 1) #column 1
        grid_layout.setRowMinimumHeight(0, 1) # row 0
        grid_layout.setRowMinimumHeight(1, 1) #row 1
        grid_layout.setRowMinimumHeight(2, 1) # row 2
        grid_layout.setRowMinimumHeight(3, 1) # row 3
        grid_layout.setRowMinimumHeight(4, 1) # row 3

        #create labels and buttons
        welcome_label = QLabel("Welcome to the CollatriX home page!\nfrom here click on the tool you'd like use")
        welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setBold(True)
        welcome_label.setFont(font)

        manual_label = QLabel("Click here to see our online manual")
        manual = QPushButton("Manual",self)
        manual.clicked.connect(lambda: webbrowser.open('https://github.com/cbirdferrer/collatrix/files/12324107/CollatriX_v2_BETA_manual_230811.pdf'))

        spacer1 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        spacer2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        spacer3 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        spacer4 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        # Create instances of your window classes
        self.lidarwrangle_window = lidarwranglerWindow()
        self.lidar_window = lidarvideoWindow()
        self.lidarmatch_window = lidarmatchWindow()
        self.lidarimage_window = lidarimageWindow()
        self.collate_window = collateWindow()
        self.bodycond_window = bodycondWindow()
        
        # WRANGLE SECTION
        wrangle_label = QLabel("Start here by wrangling your LiDAR data")
        wrangle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        wrangle_label.setFont(font)
        button0_label = QLabel("This tool will collate together\nall your LiDAR data into one clean csv")
        button0 = QPushButton("Wrangle LiDAR data",self)
        button0.clicked.connect(self.show_lidarwrangle_window)

        # VIDEO SECTION
        video_label = QLabel("Use these tools if you record video during flight")
        video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        video_label.setFont(font)
        button1_label = QLabel("This tool will match up the LiDAR data with\nevery second in your videos")
        button1 = QPushButton("Pull LiDAR Data for videos", self)
        button1.clicked.connect(self.show_lidar_window)

        button1x_label = QLabel("This tool will then merge the video aligned\nLiDAR data with extracted snapshots")
        button1x = QPushButton("Merge LiDAR Data from videos",self)
        button1x.clicked.connect(self.show_lidarmatch_window)

        # IMAGE SECTION
        image_label = QLabel("Use this tool if you record images during flight")
        image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        image_label.setFont(font)
        button1y_label = QLabel("This tool will merge your LiDAR data\nwill images taken during flight")
        button1y = QPushButton("Pull/Merge LiDAR Data for images",self)
        button1y.clicked.connect(self.show_lidarimage_window)

        # COLLATE SECTION
        collate_label = QLabel("Now collate your measurements!")
        collate_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        collate_label.setFont(font)
        button2_label = QLabel("This tool collates your\nMorphoMetriX outputs")
        button2 = QPushButton("Collate MMX Outputs", self)
        button2.clicked.connect(self.show_collate_window)
        
        # BODY COND SECTION
        bodycond_label = QLabel("Calculate body condition metrics")
        bodycond_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bodycond_label.setFont(font)
        button3_label = QLabel("This tool to calculates several\ncetacean body condition metrics")
        button3 = QPushButton("Calculate Body Condition Metrics", self)
        button3.clicked.connect(self.show_bodycond_window)

        self.exit = QPushButton("Exit", self)
        self.exit.clicked.connect(self.close_application)
        
        #add labels and buttons to grid layout
        grid_layout.addWidget(welcome_label,0,0,1,4)
        grid_layout.addWidget(manual_label,1,2,1,1)
        grid_layout.addWidget(manual,1,1,1,1)
        grid_layout.addItem(spacer1, 2, 0,1,4)

        grid_layout.addWidget(wrangle_label,3,1,1,2)
        grid_layout.addWidget(button0_label,4,2,1,1)
        grid_layout.addWidget(button0,4,1,1,1)
        grid_layout.addItem(spacer2, 5, 0,1,4)

        grid_layout.addWidget(video_label,6,0,1,2)
        grid_layout.addWidget(button1_label,7,1,1,1)
        grid_layout.addWidget(button1,7,0,1,1)
        grid_layout.addWidget(button1x_label,8,1,1,1)
        grid_layout.addWidget(button1x,8,0,1,1)

        grid_layout.addWidget(image_label,6,2,1,2)
        grid_layout.addWidget(button1y_label,7,3,1,1)
        grid_layout.addWidget(button1y,7,2,1,1)
        grid_layout.addItem(spacer3, 9, 0,1,4)

        grid_layout.addWidget(collate_label,10,1,1,2)
        grid_layout.addWidget(button2_label,11,2,1,1)
        grid_layout.addWidget(button2, 11, 1,1,1)

        grid_layout.addWidget(bodycond_label,12,1,1,2)
        grid_layout.addWidget(button3_label,13,2,1,1)
        grid_layout.addWidget(button3, 13, 1,1,1)
        grid_layout.addItem(spacer4, 14, 0,1,4)   

        grid_layout.addWidget(self.exit,15,0,1,4)

        central_widget = QWidget(self)
        central_widget.setLayout(grid_layout)
        self.setCentralWidget(central_widget)

    def show_lidarwrangle_window(self):
        self.lidarwrangle_window.show()

    def show_lidar_window(self):
        self.lidar_window.show()

    def show_lidarmatch_window(self):
        self.lidarmatch_window.show()

    def show_lidarimage_window(self):
        self.lidarimage_window.show()

    def show_collate_window(self):
        self.collate_window.show()

    def show_bodycond_window(self):
        self.bodycond_window.show()

    def close_application(self):
        choice = QMessageBox.question(self, 'exit', "Exit program?",
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if choice == QMessageBox.StandardButton.Yes:
            QApplication.quit() # Quit applications
        else:
            pass

# Program crash hook for error logging
def except_hook(exc_type, exc_value, exc_tb):
    tb = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    dialog = QMessageBox()
    dialog.setIcon(QMessageBox.Icon.Critical)
    dialog.setWindowTitle("Error")
    dialog.setText("Error: Crash caught, save details to file.")
    dialog.setDetailedText(tb)
    dialog.setStandardButtons(QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Cancel)
    ret = dialog.exec()   # Show dialog box
    if ret == QMessageBox.StandardButton.Save:
        outpath = QFileDialog().getExistingDirectory(dialog,'Select a directory')
        if(outpath):
            outpath = os.path.join(outpath,"{0}_CollatriXCrashlog.txt".format(str(date.today())))
            with open(outpath, "w") as file:
                file.write("System: " + platform.system() + '\n')
                file.write("OS: " + os.name + '\n')
                file.write("Python Version: " + platform.python_version() + '\n')
                file.write("Python Implementation: " + platform.python_implementation() + '\n')
                file.write("Release: " + platform.release() + '\n')
                file.write("Version: " + platform.version() + '\n')
                file.write("Machine: " + platform.machine() + '\n')
                file.write("Processor: " + platform.processor() + '\n')
                file.write("Current Working Directory" + os.getcwd() + '\n')
                file.write("CollatriX {0}".format(cx_version) + '\n'+ '\n')
                file.write(tb)

def main():
    sys.excepthook = except_hook
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec()
    sys.exit(0)

if __name__ == '__main__':
    main()
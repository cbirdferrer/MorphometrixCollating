#---------------------------------------------------------------
#__main__.py
#this script collates measurements from individual csv outputs of
#the morphometriX GUI
#the csvs can be saved either all in one folder or within each individual
#animals folder.
#this version includes a safety net that recalculates the measurement using
#accurate altitude and focal lengths that the user must provie in csvs.
# this version uses PyQt5 instead of easygui (used in v2.0)
#created by: Clara Bird (clara.birdferrer#gmail.com), March 2020
#----------------------------------------------------------------

#import modules
import pandas as pd
import numpy as np
import os, sys
import math
from PyQt5 import QtCore
from PyQt5.QtWidgets import QApplication, QWidget, QInputDialog, QLineEdit, QFileDialog, QMessageBox, QLabel, QVBoxLayout
from PyQt5.QtGui import QIcon

#import functions
from collatrix_functions import anydup
from collatrix_functions import readfile
from collatrix_functions import fheader
from collatrix_functions import collate
from collatrix_functions import df_formatting

class App(QWidget):

    def __init__(self):
        super().__init__()
        self.title = 'close box to end script'
        self.left = 10
        self.top = 10
        self.width = 640
        self.height = 480
        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        self.show()

        #add message box with link to github documentation
        msgBox = QMessageBox()
        msgBox.setWindowTitle("For detailed input info click link below")
        msgBox.setTextFormat(QtCore.Qt.RichText)
        msgBox.setText('<a href = "https://github.com/cbirdferrer/collatrix#inputs">CLICK HERE</a> for detailed input instructions, \n then click on OK button to continue')
        x = msgBox.exec_()

        #do you want the Animal ID to be assigned based on the name of the folder
        items = ('yes', 'no')
        anFold, okPressed = QInputDialog.getItem(self,"Input #1", "Do you want the Animal ID to be assigned based on the name of the folder? \n yes or no",items,0,False)
        if okPressed and anFold:
            print("{0} Animal ID in folder name".format(anFold))

        #ask if they want safey net
        items = ('yes', 'no')
        safety, okPressed = QInputDialog.getItem(self,"Input #2", "Do you want to use the safety? \n Yes or No?",items,0,False)
        if okPressed and safety:
            print("{0} safety".format(safety))
        #if safety yes, ask for file
        if safety == 'yes':
            options = QFileDialog.Options()
            options |= QFileDialog.DontUseNativeDialog
            safe_csv, _ = QFileDialog.getOpenFileName(self,"2.1 Safety File: Image list with altitudes and other information.", "","All Files (*);;csv files (*.csv)", options=options)
            print("safety csv = {0}".format(safe_csv))
        elif safety == 'no':
            pass

        #animal id list?
        items = ('no','yes')
        idchoice, okPressed = QInputDialog.getItem(self, "Input #3", "Do you want output to only contain certain individuals? \n Yes or No?",items,0,False)
        if idchoice and okPressed:
            print("{0} subset list".format(idchoice))
        if idchoice == 'yes':
            options = QFileDialog.Options()
            options |= QFileDialog.DontUseNativeDialog
            idsCSV, _ = QFileDialog.getOpenFileName(self,"3.1 File containing ID list", "","All Files (*);;csv files (*.csv)", options=options)
            if idsCSV:
                print("ID list file = {0}".format(idsCSV))
        elif idchoice == 'no':
            pass

        #ask for name of output
        outname, okPressed = QInputDialog.getText(self, "Input #4", "Prefix for output file",QLineEdit.Normal,"")

        #import safety csv if safety selected
        if safety == 'yes':
            dfList = pd.read_csv(safe_csv, sep = ",")
            dfList = dfList.dropna(how="all",axis='rows').reset_index()
            df_L = dfList.groupby('Image').first().reset_index()
            df_L['Image'] = [x.strip() for x in df_L['Image']]
        elif safety == 'no':
            df_L = "no safety"

        #get folders
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        GUIfold = QFileDialog.getExistingDirectory(None, "Input 5. Folder containing MorphoMetriX outputs",options=options)
        saveFold = QFileDialog.getExistingDirectory(None,"Input 6. Folder where output should be saved",options = options)
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog


        #make lists
        #for csvs
        csvs_all = []
        csvs = []
        not_mmx = []
        #for measurements
        measurements = []
        nonPercMeas = []

        #walk through all folders in GUI folder and collect all csvs
        for root,dirs,files in os.walk(GUIfold):
            csvs_all += [os.path.join(root,f) for f in files if f.endswith('.csv')]
        #make sure the csvs are morphometrix outputs by checking first row
        csvs += [c for c in csvs_all if 'Image ID' in pd.read_csv(c,nrows=1,header=None)[0].tolist()]
        #make list of all csvs that were not morphometrix csvs to tell user
        not_mmx += [x for x in csvs if x not in csvs_all]
        print("these csvs were not morphometrix outputs: {0}".format(not_mmx))

        #check for csvs that (for whatever reason) hit an error when being read in.
        #makes a list of those csvs for users to examine
        badcsvs = []
        for f in csvs:
            try:
                temp=pd.read_csv(f,sep='^',header=None,prefix='X',engine = 'python',quoting=3, na_values = ['""','"']) #read in csv as one column
            except:
                print(f)
                badcsvs += [f]
                pass
        badcsvs = set(badcsvs)
        csvs = [x for x in csvs if x not in badcsvs]

        #put together dataframe of inputs and error csvs to output
        if safety == 'yes':
            message = "Animal ID from folder name?: {0} \n\nThe safety file was: {1}\n\n\nThese csvs were not morphometrix outputs:{2}\n\nThese csvs could not be read in: {3}".format(anFold, safe_csv, not_mmx, badcsvs)
        elif safety == 'no':
            message = "Animal ID from folder name?: {0} \n\nSafety not used\n\n\nThese csvs were not morphometrix outputs:{1}\n\nThese csvs could not be read in: {2}".format(anFold, not_mmx, badcsvs)

        mess = pd.DataFrame(data={'Processing Notes':message},index=[1])
        mess_out = os.path.join(saveFold,"{0}_processing_notes.txt".format(outname))
        mess.to_csv(mess_out)

        #set up list of constants
        constants = ['Image ID', 'Image Path', 'Focal Length', 'Altitude', 'Pixel Dimension']

        #run the collate function, get collated csv
        df_allx, df_allx_pixc = collate(csvs,constants,measurements,nonPercMeas,df_L,safety,anFold) #run collating function

        #now we group by ID and image just incase multiple images were measured for the same animal
        #this would combine those measurements (it's why I replaced nans with 0)
        df_all1 = df_formatting(df_allx)
        df_all1_pc = df_formatting(df_allx_pixc)

        #output to csvs
        outcsv = os.path.join(saveFold,"{0}_allIDs.csv".format(outname))
        df_all1.to_csv(outcsv,sep = ',',index_label = 'IX')

        outcsv_pc = os.path.join(saveFold,"{0}_PixelCount.csv".format(outname))
        df_all1_pc.to_csv(outcsv_pc,sep = ',',index_label = 'IX')

        if idchoice == 'yes':
            df_ids = pd.read_csv(idsCSV,sep = ',') #read in id csv
            idList = df_ids['Animal_ID'].tolist() #make list of IDs
            df_allID = df_all1[df_all1['Animal_ID'].isin(idList)] #subset full dataframe to just those IDs

            outidcsv = os.path.join(saveFold,"{0}_IDS.csv".format(outname))
            df_allID.to_csv(outidcsv,sep = ',',index_label = 'IX')
        elif idchoice == 'no':
            pass
        print(df_all1)
        print("done, close GUI window to end script")
if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())

# -*- coding: utf-8 -*-
"""
Created on Tue Aug 28 14:46:36 2018

@author: afico
This script runs the following processes:
1 - checks settlement datasets for schema inconsistencies
"""



#* Set up initial variables *#
date = 'Aug_15_2018' # date is subject to change

# ------------------------------------------- Defining Variables ------------------------------------------- #

# importing libraries
import arcpy, datetime, os
from arcpy import env
env.overwriteOutput = True
startTime = datetime.now()

# folder variables
mainFolder = r'<computer folder path>\All_POI_'+date
wrkFolder = os.path.join(mainFolder,'completed')
stateList = os.listdir(wrkFolder)
stateList.sort()


# ------------------------------------------- Script Begins ------------------------------------------- #    
for state in stateList:
    print('Processing: '+state)
    folderPath = os.path.join(wrkFolder,state)
    scratchGDB = os.path.join(folderPath,'scratch.gdb')
    setGDB = os.path.join(folderPath,'settlements.gdb')
    setFC = os.path.join(setGDB,'Human_Settlements_Settlement_Points')
    wardFC = os.path.join(folderPath,'wards_processed.gdb','wards_boundaries')
    if arcpy.Exists(setFC):
        checkList = ['wardcode_X','wardcode_Y'] # subject to change based on headers present in settlement csv files
        fList = [f.name for f in arcpy.ListFields(setFC)]
        for f in fList:
            if f in checkList:
                print(state) # state settlement csv files are manuall corrected

# ------------------------------------------- Script Ends ------------------------------------------- #
print('Script Complete')
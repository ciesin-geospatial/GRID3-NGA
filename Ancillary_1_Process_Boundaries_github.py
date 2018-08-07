# -*- coding: utf-8 -*-
"""
Created on Mon Jul 16 14:43:38 2018

@author: afico
For questions please contact: afico@ciesin.columbia.edu

This script runs the following processes:
1. Attaches state attibutes to LGA boundaries
2. Attaches LGA attibutes and state attibutes to ward boundaries
3. Seperates the ward boundaries by state 

Note - This script was written using Spyder (Python 3.6) and works on folder naming conventions and will need to be modified to fit the users folder paths
"""

### import necessary libraries ###
import arcpy, datetime, os
from arcpy import env
from datetime import datetime
env.overwriteOutput = True 
start = datetime.now()

def process_boundaries(folder):
    statePath = os.path.join(mainFolder,folder)  ## defines full folder path 
    boundaryPath = os.path.join(statePath,'boundaries.gdb')
      
    if not arcpy.Exists(boundaryPath):
        arcpy.CreateFileGDB_management(statePath,'boundaries.gdb')
        print('      Created GDB')

    arcpy.MakeFeatureLayer_management(wardBoundaries,folder+'_wardLyr')
    lyr = folder+'_wardLyr'
    
    if '_' in folder: ## Must change "_" to spaces to match values in attribute field
        stateName = folder.replace('_'," ")
        print('      Changed '+folder+' to '+stateName)
    else:
        stateName = folder
        
    print('      Selecting '+stateName+' now..')    
    arcpy.SelectLayerByAttribute_management(lyr,'NEW_SELECTION',"statename ='"+stateName+"'")
    
    ## Validate number of rows that were selected
    checkCount = int(arcpy.GetCount_management(wardBoundaries).getOutput(0))
    if checkCount <1:
        print('     !!!!Check selection!!!!!')
    
    arcpy.FeatureClassToFeatureClass_conversion(lyr,boundaryPath,'wards_boundaries')
    arcpy.SelectLayerByAttribute_management(lyr,'CLEAR_SELECTION')
    print('      3 - Export Wards by state')

##########################################################################################################

### set up initial variables ### 
mainFolder = '<\POIs_and_Administrative_Boundary_Data>' # Full path of main folder required
boundaryGDB = os.path.join(mainFolder,'1_boundaries','boundaries.gdb')
lgaBoundaries = os.path.join(boundaryGDB,'lga_boundaries')
stateBoundaries =  os.path.join(boundaryGDB,'state_boundaries')
wardBoundaries =  os.path.join(boundaryGDB,'wards_boundaries')

# Step 1: Nest boundary admin information in feature classes

''' First attach state admin info to LGA boundaries '''
arcpy.AddField_management(lgaBoundaries,'statename','TEXT')
arcpy.MakeFeatureLayer_management(lgaBoundaries,'lga_lyr')
arcpy.AddJoin_management('lga_lyr','statecode',stateBoundaries,'statecode')
arcpy.CalculateField_management('lga_lyr','statename','!state_boundaries.statename!','PYTHON')
arcpy.RemoveJoin_management('lga_lyr')

''' Validate that all rows joined '''
arcpy.SelectLayerByAttribute_management('lga_lyr','NEW_SELECTION','statename IS NULL')
checkCount = str(arcpy.GetCount_management('lga_lyr').getOutput(0)) 
print('      1 - Added state admin informtaion to LGAs. Need to check '+checkCount+' rows')
arcpy.SelectLayerByAttribute_management('lga_lyr','CLEAR_SELECTION')


''' Then attach LGA and state admin info to ward boundaries '''
arcpy.AddField_management(wardBoundaries,'lganame','TEXT')
arcpy.AddField_management(wardBoundaries,'statecode','TEXT')
arcpy.AddField_management(wardBoundaries,'statename','TEXT')

arcpy.MakeFeatureLayer_management(wardBoundaries,'ward_lyr')
arcpy.AddJoin_management('ward_lyr','lgacode',lgaBoundaries,'lgacode')

arcpy.CalculateField_management('ward_lyr','lganame','!lga_boundaries.lganame!','PYTHON')
arcpy.CalculateField_management('ward_lyr','statecode','!lga_boundaries.statecode!','PYTHON')
arcpy.CalculateField_management('ward_lyr','statename','!lga_boundaries.statename!','PYTHON')
arcpy.RemoveJoin_management('ward_lyr')


''' Validate that all rows joined '''
arcpy.SelectLayerByAttribute_management('ward_lyr','NEW_SELECTION','lganame IS NULL')
checkCount = str(arcpy.GetCount_management('ward_lyr').getOutput(0)) 
print('      2 - Added state and LGA admin informtaion to Wards. Need to check '+checkCount+' rows')
arcpy.SelectLayerByAttribute_management('ward_lyr','CLEAR_SELECTION')


# Step 2: Export wards by state using process_boundaries function
os.chdir(mainFolder)
subFolders = os.listdir(mainFolder)
subFolders.sort()
for folder in subFolders:
    if '1_' in folder or '2_' in folder:
        pass
    else:
        print('      Processing '+folder+ ' now..')
        process_boundaries(folder)

    
print('      Script Complete: '+str(datetime.now()-start))


    
        


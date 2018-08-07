# -*- coding: utf-8 -*-
"""
Created on Tue Jul 31 08:47:21 2018

@author: afico
For questions please contact: afico@ciesin.columbia.edu

This script runs the following processes:
1. Creates working geodatabases for future processing 
2. Checks each POI csv for latitutde and longitude fields
3. Converts each POI csv into a feature class
4. Checks to make sure all rows in the csv were converted over
5. Adds a "poi_type" field to the feature class

Note - This script was written using Spyder (Python 3.6) and works on folder naming conventions and will need to be modified to fit the users folder paths. 

"""

''' import necessary libraries '''
import arcpy, datetime, os, csv
from arcpy import env
from datetime import datetime
env.overwriteOutput = True


''' set up initial variables ''' 
startTime = datetime.now()
mainFolder = '<\POIs_and_Administrative_Boundary_Data>' # Full path of main folder required
os.chdir(mainFolder)
subFolders = os.listdir(mainFolder)
subFolders.sort()
stateCount = 0 # used to count number of files processed 

## Processing begins here.... 
for folder in subFolders:
    ## define full path of the subfolder
    folderPath = os.path.join(mainFolder,folder) 
    
    if '1_' in folder or '2_' in folder:  ##skip folders that are not applicable
        pass
   
    else:
        stateCount += 1
        print('Processing '+folder+' now...')      
        fileList = os.listdir(folder)  

## Step 1: Create geodatabases in each state folder
        if not arcpy.Exists(os.path.join(folderPath,'poi.gdb')):
            arcpy.CreateFileGDB_management(folderPath,'poi.gdb')
        
            
        if not arcpy.Exists(os.path.join(folderPath,'scratch.gdb')):
            arcpy.CreateFileGDB_management(folderPath,'scratch.gdb')    
        
        ## define scratch gdb
        scratchPath = os.path.join(folderPath,'scratch.gdb')  
        ## define poi gdb
        gdbPath = os.path.join(folderPath,'poi.gdb')  
        
## Step 2: Convert csv's to point events using lat/long     
        for file in fileList:                 
            if file.endswith('.csv'): 
                print('  Processing '+file+' now..')
                
                # define full path of the file
                csvPath = os.path.join(folderPath,file) 
                               
                # Validate that there is a lat/long field in each csv
                with open(csvPath,"r") as csvFile:  
                    reader = csv.reader(csvFile)
                    headers = next(reader)                    
                    headerCount = 0               
                    rowCount = sum(1 for row in reader)  # Used to validate that all rows were converted to points
                    if '_y' in headers and '_x' in headers:
                        headerCount +=2
            
                if headerCount==2:                                       
                    try: ## Convert the csv to a geodatabase table
                        # Set up variables
                        inTable = csvPath
                        x_coords = "_x"
                        y_coords = "_y"
                        lyr = folder+file[:-4]+'_lyr'
                        spRef = arcpy.SpatialReference(4326)  ## sets the spatial reference to WGS 1984
                        
                        # Convert geodatabase table to a event layer
                        arcpy.MakeXYEventLayer_management(inTable,x_coords,y_coords,lyr,spRef)
                        
                        # Validate that all rows were converted 
                        lyrCount = int(arcpy.GetCount_management(lyr).getOutput(0))
                        if rowCount != lyrCount:
                            print('      !!!!!'+str(rowCount-lyrCount)+' WERE NOT CREATED - CHECK '+file[:-4]+'!!!!!')
                        
                        # Convert event layer to feature class
                        outFC = os.path.join(gdbPath,file[:-4])
                        arcpy.FeatureClassToFeatureClass_conversion(lyr,gdbPath,file[:-4])
                        print('      1 - '+file+' was converted to a feature class')
                        
                        
                        # Add a POI Type field to new poi feature class
                        arcpy.AddField_management(outFC,'poi_type','TEXT')
                        arcpy.CalculateField_management(outFC,'poi_type',"'"+file[:-4]+"'","PYTHON")
                        print('      2 - '+file[:-4]+' type field was added')                                                                    
                    except Exception as err:
                        print("      !!!!!"+err.args[0]+'!!!!!')
                        
                else:
                    print('      !!!!!MUST CHECK '+file[:-4]+' MISSING COORD COLUMN!!!!!')

print('Script Complete @ '+str(datetime.now()-startTime)+'. Processed '+stateCount+' states.')
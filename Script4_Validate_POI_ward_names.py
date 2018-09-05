# -*- coding: utf-8 -*-
"""
Created on Tue Jul 31 09:24:15 2018

@author: afico
This script runs the following processes:
1 - Spatially joins ward boundaries and point of interest point features 
2 - Checks point of interest wardcodes against ward boundary wardcodes
"""

#* Set up initial variables *#
# variables are subject to change
date = 'Aug_15_2018' 
poi_idField = 'FID'
ward_idField = 'id'

# ------------------------------------------- Defining Variables ------------------------------------------- #

# importing libraries
import arcpy, datetime, os
from arcpy import env
from datetime import datetime
env.overwriteOutput = True
startTime = datetime.now()


# folder variables
mainFolder = r'<computer folder path>\All_POI_'+date
wrkFolder = os.path.join(mainFolder,'completed')
stateList = os.listdir(wrkFolder)
stateList.sort()

# dictionaries, lists, and counts
mergeList =[]


# folders and geodatabases to capture errors
errorFolder = os.path.join(mainFolder,'errorFolder')
if not os.path.exists(errorFolder):
    os.makedirs(errorFolder) 

errorsGDB = os.path.join(errorFolder,'errors.gdb') 
if not arcpy.Exists(errorsGDB):
    arcpy.CreateFileGDB_management(errorFolder,'errors')


# ------------------------------------------- Script Begins ------------------------------------------- #
for state in stateList:
    print('Processing '+state+' now...')

    ## Set up important variables
    folderPath = os.path.join(wrkFolder,state) 
    wardsFC = os.path.join(folderPath,'wards_processed.gdb','wards_boundaries')
    scratchGDB = os.path.join(folderPath,'scratch.gdb')
    poiGDB = os.path.join(folderPath,'poi.gdb')
    

    ##  Spatially join the wards polygons and poi points
    env.workspace = poiGDB
    poiList = arcpy.ListFeatureClasses() 
    poiList.sort()
                    
    for poi in poiList:
        print('      Starting '+poi+' now.')
        
        # Change names of poi attributes to not match ward polygon attributes           
        oldfList = [
                'wardname',
                'wardcode',
                'lganame',
                'lgacode',
                'statecode',
                'statename'
                ]
        newfList = [
                'poi_wardname',
                'poi_wardcode',
                'poi_lganame',
                'poi_lgacode',
                'poi_statecode',
                'poi_statename',
                ]
        fieldList = [f.name for f in arcpy.ListFields(poi)]
        for f in fieldList:
            if f in oldfList:
                arcpy.AlterField_management(poi,f,newfList[oldfList.index(f)])   
        
        # Run spatial join 
        spOut = os.path.join(scratchGDB,poi+'_spjoin')
        if not arcpy.Exists(spOut):
            arcpy.SpatialJoin_analysis(poi,wardsFC,spOut,'JOIN_ONE_TO_MANY')  
            print('      1 - Created spatial join layer')
        
        # Collect spatial join outputs in a list            
        mergeList.append(spOut) 

# ------------------------------------------- Creating Error Outputs ------------------------------------------- #
           
## ERROR OUTPUT 1 ----- for poi's that are outside spatial extent of specified ward
spatialErrors = os.path.join(errorsGDB,'poi_spatial_anomalies_'+date)
arcpy.Merge_management(mergeList,spatialErrors)

# Clean up
fList = [
        'poi_wardcode',
        'poi_wardname',
        poi_idField,
        'poi_lganame',
        'poi_lgacode',
        'poi_statecode',
        'poi_statename',
        'wardname',
        'wardcode',
        'lganame',
        'lgacode',
        'statename',
        ward_idField,
        'poi_file_name'
        ]

for f in arcpy.ListFields(spatialErrors):
    if f.name in fList or f.required:
        pass
    else:
        arcpy.DeleteField_management(spatialErrors,f.name)

# Add error flagging fields
arcpy.AddField_management(spatialErrors,'poi_outside_ward','TEXT')
arcpy.AddField_management(spatialErrors,'poi_outside_lga','TEXT')

# Add errors to feature class      
with arcpy.da.UpdateCursor(spatialErrors,['poi_wardcode','poi_lgacode','wardcode','lgacode','poi_outside_ward','poi_outside_lga']) as cursor: 
    for row in cursor:
        if str(row[0]) == str(row[2]) and str(row[1]) == str(row[3]):
            cursor.deleteRow()
        else:
            if str(row[0]) != str(row[2]):
                row[4] = 'True'
            if row[4] is None:
                row[4] = 'False'
            if str(row[1]) != str(row[3]):
                row[5] = 'True'    
            if row[5] is None:
                row[5] = 'False'
            if str(row[5]) =='True' and str(row[4]) == 'False':
                print('Need to check output - point is inside the correct ward, but outside the LGA')
            cursor.updateRow(row)
print('Created error output file for pois out of bounds')            


# ------------------------------------------- Clean up POI features ------------------------------------------- #
for state in stateList:
    print('Changing '+state+' field names now...')

    ## Set up important variables
    folderPath = os.path.join(wrkFolder,state) 
    poiGDB = os.path.join(folderPath,'poi.gdb')
    env.workspace = poiGDB
    poiList = arcpy.ListFeatureClasses() 
    poiList.sort()
                    
    for poi in poiList:
        # Convert poi field names back to original names 
        newfList = [
                'wardname',
                'wardcode',
                'lganame',
                'lgacode',
                'statecode',
                'statename'
                ]
        oldfList = [
                'poi_wardname',
                'poi_wardcode',
                'poi_lganame',
                'poi_lgacode',
                'poi_statecode',
                'poi_statename',
                ]
        fieldList = [f.name for f in arcpy.ListFields(poi)]
        for f in fieldList:
            if f in oldfList:
                arcpy.AlterField_management(poi,f,newfList[oldfList.index(f)])   

# ------------------------------------------- Script Ends ------------------------------------------- #
print('Script Complete @ '+str(datetime.now()-startTime))
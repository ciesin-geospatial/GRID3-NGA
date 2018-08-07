# -*- coding: utf-8 -*-
"""
Created on Tue Jul 31 09:24:15 2018

@author: afico
For questions please contact: afico@ciesin.columbia.edu

This script runs the following processes:
1. Spatially joins point points with ward polygons
2. Creates an error feature class were poi point admin names do not match ward polygon admin names

Note - This script was written using Spyder (Python 3.6) and works on folder naming conventions and will need to be modified to fit the users folder paths. 

"""

''' import necessary libraries '''
import arcpy, datetime, os
from arcpy import env
from datetime import datetime
env.overwriteOutput = True


startTime = datetime.now()
''' set up initial variables ''' 
mainFolder = '<\POIs_and_Administrative_Boundary_Data>' # Full path of main folder required
delFolder = os.path.join(mainFolder,'2_Deliverables')
outputGDB = os.path.join(delFolder,'outputs.gdb')


os.chdir(mainFolder)
subFolders = os.listdir(mainFolder)
subFolders.sort()
stateCount = 0

mergeList =[]
wardsList = []

for state in subFolders:
    ## Skip folders that shouldn't be looped through
    if '1_' in state or '2_' in state: 
        pass
    else:
        print('Processing '+state+' now...')
        stateCount +=1
        ## Set up important variables
        folderPath = os.path.join(mainFolder,state) 
        wardsFC = os.path.join(folderPath,'boundaries.gdb','wards_boundaries')
        scratchGDB = os.path.join(folderPath,'scratch.gdb')
        poiGDB = os.path.join(folderPath,'poi.gdb')
        
        # Collect list of ward feature classes by state (used during spatial join)
        wardsList.append(wardsFC)

## Step 1: Spatially join the wards polygons and poi points
        env.workspace = poiGDB
        poiList = arcpy.ListFeatureClasses() 
        poiList.sort()
                        
        for poi in poiList:
            print('      Starting '+poi+' now.')
            
            # Change names of poi attributes to not match ward polygon attributes (prevents confusion after spatial join)            
            oldfList = [
                    'wardcode',
                    'lganame',
                    'statename',
                    'globalid'
                    ]
            newfList = [
                    'poi_wardcode',
                    'poi_lganame',
                    'poi_statename',
                    'poi_globalid'
                    ]
            fieldList = [f.name for f in arcpy.ListFields(poi)]
            for f in fieldList:
                if f in oldfList:
                    arcpy.AlterField_management(poi,f,newfList[oldfList.index(f)])   
            
            # Run spatial join                    
            spOut = os.path.join(scratchGDB,poi+'_spjoin')
            arcpy.SpatialJoin_analysis(poi,wardsFC,spOut,'JOIN_ONE_TO_MANY')  
            print('      1 - Created spatial join layer')
            
            # Collect spatial join outputs in a list            
            mergeList.append(spOut) 

           
## Step 2: Create a feature class of error features where admin names do not match 
poiErrors_2 = os.path.join(outputGDB,'poiErrors_2')
arcpy.Merge_management(mergeList,poiErrors_2)

# Clean up
keepList = [
        'OBJECTID',
        'Shape',
        'poi_type',
        'poiname',
        'poi_wardcode',
        'poi_globalid',
        'poi_lganame',
        'poi_statename',
        'wardname',
        'wardcode',
        'lganame',
        'statename',
        'globalid'
        ]
poiErrors_2Fields = [f.name for f in arcpy.ListFields(poiErrors_2)]
for f in poiErrors_2Fields:
    if f not in keepList:
        arcpy.DeleteField_management(poiErrors_2,f)

# Add error flagging fields
arcpy.AddField_management(poiErrors_2,'poi_outside_ward','TEXT')
arcpy.AddField_management(poiErrors_2,'poi_outside_lga','TEXT')

# Add errors to feature class      
with arcpy.da.UpdateCursor(poiErrors_2,['poi_wardcode','poi_lganame','wardcode','lganame','poi_outside_ward','poi_outside_lga']) as cursor: 
    for row in cursor:
        if row[0] == row[2] and row[1] == row[3]:
            cursor.deleteRow()
        else:
            if row[0] != row[2]:
                row[4] = 'True'
            if row[4] is None:
                row[4] = 'False'
            if row[1] != row[3]:
                row[5] = 'True'    
            if row[5] is None:
                row[5] = 'False'
            if row[5] =='True' and row[4] == 'False':
                print('Needs to check output')
            cursor.updateRow(row)
print('      3 - Created error output file for pois out of bounds')            

print('Script Complete @ '+str(datetime.now()-startTime)+'. Processing '+stateCount+' states.')
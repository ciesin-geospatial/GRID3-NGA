# -*- coding: utf-8 -*-
"""
Created on Tue Jul 31 09:03:13 2018

@author: afico
For questions please contact: afico@ciesin.columbia.edu

This script runs the following processes:
1. Validates GUBID values within POI feature classes
2. Creates uniqueID field for internal processing purposes
3. Creates consistent POI name fields
4. Valids POI feature class coordinates
5. Creates an output feature class that contains checks for invalid coordinates and duplicate GUBIDs

Note - This script was written using Spyder (Python 3.6) and works on folder naming conventions and will need to be modified to fit the users folder paths. 

"""


''' import necessary libraries '''
import arcpy, datetime, os
from arcpy import env
from datetime import datetime
env.overwriteOutput = True


''' set up initial variables ''' 
start = datetime.now()
mainFolder = '<\POIs_and_Administrative_Boundary_Data>' # Full path of main folder required
outputGDB = os.path.join(mainFolder,'2_Deliverables\outputs.gdb')
os.chdir(mainFolder)
subFolders = os.listdir(mainFolder)
subFolders.sort()

## Set up variables used to validate datasets
stateCount = 0
invalidList = []
POIidDict = {}
uniqueidDict = {}
outputList = []


## Processing begins here.... 
for folder in subFolders:
    folderPath = os.path.join(mainFolder,folder) ## define full path of the subfolder
    
    if '1_' in folder or '2_' in folder:  ##skip folders that are not applicable
        pass
    else:
        stateCount += 1
        print('Processing '+folder+' now...')      
             
        ## define scratch gdb
        scratchPath = os.path.join(folderPath,'scratch.gdb')  
        ## define poi gdb
        gdbPath = os.path.join(folderPath,'poi.gdb')  
            
## Step 1: Collect GUBIDs
        env.workspace = gdbPath
        poiList = arcpy.ListFeatureClasses()
        poiList.sort()                                   
        print('   1 - Calculating uniqueIDs and collecting invalid coordinates for '+folder) 
        for poi in poiList:
            # Collect all poi feature classes in a list
            outputList.append(os.path.join(gdbPath,poi))  
            
            # Collect all GUBIDs (used for validation)
            with arcpy.da.SearchCursor(poi,['globalid']) as cursor:
                for row in cursor:
                    if row[0] in POIidDict:                       
                        POIidDict[row[0]] += 1                                         
                    else:
                        POIidDict[row[0]] = 1

## Step 2: Create uniqueID field and change POI name field (manual work was done to determine POI name field)
            # Set up variables
            if 'health' in poi:
                code = 'health_'
                nameField = 'primary_name'
                
            if 'market' in poi:
                code = 'market_'
                nameField = 'market_name'
                
            if 'school' in poi:
                code = 'school_'
                nameField = 'name'

            if 'settlement' in poi:
                code = 'settlement_'
                nameField = 'settlementname'
           
            # Create a universally unique identifier to be used in additional processing (For internal processing purposes only)
            arcpy.AddField_management(poi,'uniqueID','TEXT')
            arcpy.CalculateField_management(poi,'uniqueID',"'"+code+"' + str(!statename!)+'_'+ str(!wardcode!)+'_'+str(!OBJECTID!)",'PYTHON')
            
            
            # Create consistent POI name fields (always for easier merging of the datasets)
            arcpy.AlterField_management(poi,nameField,'poi_name')
            
            # Collect all uniqueIDs in a dictionary and determine if there are duplicates (used for internal validation)
            with arcpy.da.SearchCursor(poi,['uniqueID']) as cursor:
                for row in cursor:
                    if row[0] in uniqueidDict:                        
                        uniqueidDict[row[0]][0] += 1
                        uniqueidDict[row[0]] = uniqueidDict[row[0]] + [folder+'_'+poi]                                          
                    else:
                        uniqueidDict[row[0]] = [1, folder+'_'+poi]
            print('      Created uniqueID field, changed POI name field')
## Step 3: Collect invalid coordinates
            invalidCount = 0
            with arcpy.da.SearchCursor(poi,['uniqueID','_x','_y']) as curosr:
                for row in curosr:
                    if row[1] == 0 or row[2] == 0:
                        invalidList.append(row[0])                                      
            if invalidCount >1:
                print('      !!!! Found '+str(invalidCount)+' invalid rows in '+folder+' '+poi)
            else:
                print('      No invalid coordinates were found')
                
## Step 4: Merge all POI feature classes together and add error fields
outmerge = os.path.join(outputGDB,'poiErrors_1')
arcpy.Merge_management(outputList,outmerge)
arcpy.AddField_management(outmerge,'duplicate_GUBID','TEXT')
arcpy.AddField_management(outmerge,'invalid_coordinates','TEXT')

#flag errors and delete features that don't need to be checked
with arcpy.da.UpdateCursor(outmerge,['globalid','uniqueID','duplicate_GUBID','invalid_coordinates']) as cursor:
    for row in cursor:
        if POIidDict[row[0]]>1: # Flag rows that contain duplicate poi ids
            row[2] = 'True'
        else: 
            row[2] = 'False'
        if row[1] in invalidList: # Flag rows that contain invalid coordinates
            row[3] = 'True' 
        else: 
            row[3] = 'False'
        cursor.updateRow(row)   
        
        if POIidDict[row[0]]==1 and row[1] not in invalidList: ## Remove rows that are not in either check list
            cursor.deleteRow()
print('      Created error output feature class')

## Step 5: Clean up 
keepList = [
        'OBJECTID',
        'Shape',
        'duplicate_GUBID',
        'invalid_coordinates',
        'poi_type',
        'poi_name',
        'wardcode',
        'globalid',
        'lganame',
        'statename'
        ]

fieldList = [f.name for f in arcpy.ListFields(outmerge)]
for field in fieldList:
    if field not in keepList:
        arcpy.DeleteField_management(outmerge,field)
            
## Step 6: Internal Validation - Check uniqueID field for duplicates
for key in uniqueidDict:
    value = uniqueidDict[key]
    if value[0] >1:
        print('      !!!!! Must Check '+ key+ ' found in '+str(value[0])+' feature classes: '+" & ".join(value[1:])+' !!!!!')


print('Script processed '+str(stateCount)+ ' Folders in '+ str(datetime.now()-start))



 
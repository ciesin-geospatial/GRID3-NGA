# -*- coding: utf-8 -*-
"""
Created on Tue Aug 28 11:07:30 2018

@author: afico
This script does the following processing:
1 - Produces a spatial join between the settlement points and the wards
2 - Creates an error ouput file of settlements points whose ward value is different than the ward the point is spatially located in
3 - Creates an error ouput file of setlement points that have duplicate names in the same ward (i.e. same primary name with no alternative name)
"""

#* Set up initial variables *#
# variables are subject to change
date = 'Aug_15_2018' 
poi_idField = 'FID'
ward_idField = 'id'
sett_idField = 'FID'

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


# List variables to capture errors 
errorFolder = os.path.join(mainFolder,'errorFolder')
if not os.path.exists(errorFolder):
    os.makedirs(errorFolder) 

errorsGDB = os.path.join(errorFolder,'errors.gdb') 
if not arcpy.Exists(errorsGDB):
    arcpy.CreateFileGDB_management(errorFolder,'errors')

# dictionaries, lists, and counts
spOutList = []
setList = []
nameDict = {}

# ------------------------------------------- Script Begins ------------------------------------------- #    
for state in stateList:
    print('Processing: '+state)
    folderPath = os.path.join(wrkFolder,state)
    scratchGDB = os.path.join(folderPath,'scratch.gdb')
    setGDB = os.path.join(folderPath,'settlements.gdb')
    setFC = os.path.join(setGDB,'Human_Settlements_Settlement_Points')
    wardFC = os.path.join(folderPath,'wards_processed.gdb','wards_boundaries')
    
    if arcpy.Exists(setFC):
        setList.append(setFC)
        
        # Change names of settlement point attributes to not match ward polygon attributes (prevents confusion after spatial join)            
        oldfList = [
                'set_wardname',
                'set_wardcode',
                'set_lganame',
                'set_lgacode',
                'set_statecode',
                'set_statename'
                ]
        newfList = [
                'settlement_wardname',
                'settlement_wardcode',
                'settlement_lganame',
                'settlement_lgacode',
                'settlement_statecode',
                'settlement_statename',
                ]
        fieldList = [f.name for f in arcpy.ListFields(setFC)]
        for f in fieldList:
            if f in oldfList:
                arcpy.AlterField_management(setFC,f,newfList[oldfList.index(f)])   
        
        # Run spatial join 
        spOut = os.path.join(scratchGDB,os.path.basename(setFC+'_spjoin'))
        if not arcpy.Exists(spOut):
            arcpy.SpatialJoin_analysis(setFC,wardFC,spOut,'JOIN_ONE_TO_MANY')  
            print('      Created spatial join layer')
    
        # Collect spatial join outputs in a list            
        spOutList.append(spOut) 
        
        # put field names back (clean up) 
        newfList = [
                'wardname',
                'wardcode',
                'lganame',
                'lgacode',
                'statecode',
                'statename'
                ]
        oldfList = [
                'settlement_wardname',
                'settlement_wardcode',
                'settlement_lganame',
                'settlement_lgacode',
                'settlement_statecode',
                'settlement_statename',
                ]
        fieldList = [f.name for f in arcpy.ListFields(setFC)]
        for f in fieldList:
            if f in oldfList:
                arcpy.AlterField_management(setFC,f,newfList[oldfList.index(f)])   

    else:
        print('      Settlement layer does not exist')
        


# ------------------------------------------- Creating Error Outputs ------------------------------------------- #
           
## ERROR OUTPUT 1 ----- for settlements that are outside spatial extent of specified ward   
spatialFC = (os.path.join(errorsGDB,'settlement_spatial_anomalies_'+date))
arcpy.Merge_management(spOutList,spatialFC)

# Add error flagging fields
arcpy.AddField_management(spatialFC,'settlement_outside_ward','TEXT')
arcpy.AddField_management(spatialFC,'settlement_outside_lga','TEXT')

# Add errors to feature class      
with arcpy.da.UpdateCursor(spatialFC,['settlement_wardcode','settlement_lgacode','wardcode','lgacode','settlement_outside_ward','settlement_outside_lga']) as cursor: 
    for row in cursor:
        if str(row[0]) == str(row[2]) and str(row[1]) == str(row[3]):
            cursor.deleteRow()
        else:
            if str(row[0]) != str(row[2]):
                row[4] = 'True'
            if row[4] is None:
                row[4] = 'False'
            if str(row[1])!= str(row[3]):
                row[5] = 'True'    
            if row[5] is None:
                row[5] = 'False'
            if str(row[5]) =='True' and str(row[4]) == 'False':
                print('Need to check output - point is inside the correct ward, but outside the LGA')
            cursor.updateRow(row)
            
 # Clean up fields left over from boundaries           
keepList = [
        'FID',
        'settlementname',
        'settlementname_alt',
        'settlement_wardname',
        'settlement_wardcode',
        'ssettlement_lganame',
        'settlement_lgacode',
        'settlement_statecode',
        'settlement_statename',        
        'settlement_outside_ward',
        'settlement_outside_lga',
        'wardname',
        'wardcode',
        'lganame',
        'lgacode',
        'statecode',
        'statename'
        ]
      
for f in arcpy.ListFields(spatialFC):
    if f.name in keepList or f.required:
        pass
    else:
        arcpy.DeleteField_management(spatialFC,f.name)


print('Created error output file for pois out of bounds')      

## ERROR OUTPUT 2 ----- for settlement points that have the same primary name in the same ward and no alternative name
duplicateFC = (os.path.join(errorsGDB,'settlements_with_duplicate_names_in_same_ward_'+date))
arcpy.Merge_management(setList,duplicateFC)

# Add error flagging fields
arcpy.AddField_management(duplicateFC,'duplicate_settlement','TEXT')

# Add concatindate field to check names
arcpy.AddField_management(duplicateFC,'temp_concatinated_name','Text')
with arcpy.da.UpdateCursor(duplicateFC,['temp_concatinated_name','wardcode','settlementname','settlementname_alt']) as cursor:
    for row in cursor:
        row[0] = "_".join(["NULL" if r is None or r == "NA" else r for r in row[1:]])
        cursor.updateRow(row)
            
# Add errors to feature class      
with arcpy.da.SearchCursor(duplicateFC,['temp_concatinated_name','duplicate_settlement']) as cursor: 
    for row in cursor:
        if row[0] in nameDict:
            nameDict[row[0]] += 1
            
        else:
            nameDict[row[0]] = 1
            
with arcpy.da.UpdateCursor(duplicateFC,['temp_concatinated_name','duplicate_settlement']) as cursor: 
    for row in cursor:
        if nameDict[row[0]] >1:
            row[1] = 'True'
            cursor.updateRow(row)
        else:
            cursor.deleteRow()

arcpy.DeleteField_management(duplicateFC,'temp_concatinated_name')
print('Create error output for duplicate settlement names')


# ------------------------------------------- Script Ends ------------------------------------------- #
print('Script Complete @ '+str(datetime.now()-startTime))

    

# -*- coding: utf-8 -*-
"""
Created on Mon Jul 16 14:43:38 2018

@author: afico
This script runs the following processes:
1. Creates a feature class copy of the originally downloaded ward boundaries
2. Checks for duplicate ids and invalid geometry and non-alphanumeric codes
"""
#* Set up initial variables *#
# variables are subject to change
date = 'Aug_15_2018' 
poi_idField = 'FID'
ward_idField = 'id'

# ------------------------------------------- Defining Variables ------------------------------------------- #
# importing libraries
import arcpy, datetime, os
import pandas as pd
from arcpy import env
from datetime import datetime
env.overwriteOutput = True 
start = datetime.now()

# folder variables
mainFolder = r'<computer folder path>\All_POI_'+date
wrkFolder = os.path.join(mainFolder,'completed')
stateCount = 0
stateList = os.listdir(wrkFolder)
stateList.sort()

# dictionaries, lists, and counts
wardsList =[]
idDict = {}
geomDict = {}
duplicateCount = 0

# folders and geodatabases to capture errors
errorFolder = os.path.join(mainFolder,'errorFolder')
if not os.path.exists(errorFolder):
    os.makedirs(errorFolder)
errorFile = os.path.join(errorFolder,'ward_boundaries_invalid_geometries_'+date+'.csv')
statusFile = os.path.join(errorFolder,'wards_missing_status_field_'+date+'.csv')
    
errorsGDB = os.path.join(errorFolder,'errors.gdb') 
if not arcpy.Exists(errorsGDB):
    arcpy.CreateFileGDB_management(errorFolder,'errors')


# ------------------------------------------- Defining Functions ------------------------------------------- #
def process_boundaries(state):

    if not arcpy.Exists(boundaryPath):
        arcpy.CreateFileGDB_management(statePath,'wards_processed.gdb')
        print('      1- Created GDB')
    
    rawWards = os.path.join(statePath,'Administrative_Boundaries_Ward_Administrative_Boundary','Administrative_Boundaries_Ward_Administrative_Boundary.shp')
    if not arcpy.Exists(rawWards):
        print('      CHECK-- '+state+' doesnt not contain ward boundaries')
    else:
        arcpy.FeatureClassToFeatureClass_conversion(rawWards,boundaryPath,'wards_boundaries')    
        print('      2- Wards feature class was created')



def errorChecks(state,wardsList,duplicateCount):
## 1
    # Check geometry of ward boundaries
    errorCount = 0
    wardsFC = os.path.join(boundaryPath,'wards_boundaries')
    wardsList += [wardsFC]

    # Check that ward boundaries have valid shape area values
    with arcpy.da.SearchCursor(wardsFC,[ward_idField,'statename','lganame','wardname','Shape_Area','Shape_length']) as cursor:
        for row in cursor:
            if row[4] ==0:
                errorCount +=1 
                geomDict[row[0]] = row[1:]   
    print('      3- There are '+str(errorCount)+' features without valid shape areas')

## 2
    # Check for duplicate ID values 
    with arcpy.da.SearchCursor(wardsFC,[ward_idField]) as cursor:
        for row in cursor:
            if row[0] in idDict:
                idDict[row[0]][0] += 1
                duplicateCount +=1
            else:
               idDict[row[0]] = [1]
  
        
# ------------------------------------------- Script Begins ------------------------------------------- #
            
for state in stateList:
    statePath = os.path.join(wrkFolder,state)  
    boundaryPath = os.path.join(statePath,'wards_processed.gdb')
    stateCount +=1
    print('Processing '+state+ ' now..')
    process_boundaries(state)
    errorChecks(state,wardsList,duplicateCount)


# ------------------------------------------- Creating Error Outputs ------------------------------------------- #
    
## ERROR OUTPUT 1 ------ for the duplicate id values ##
errorsFC = os.path.join(errorsGDB,'wards_duplicate_ids_'+date)
arcpy.Merge_management(wardsList,errorsFC)
fList = [
        ward_idField,
        'lgacode',
        'lganame',
        'wardname',
        'wardcode',
        'statecode',
        'statename'
        ]

for f in arcpy.ListFields(errorsFC):
    if f.name in fList or f.required:
        pass
    else:
        arcpy.DeleteField_management(errorsFC,f.name)

arcpy.AddField_management(errorsFC,'duplicate_id')
with arcpy.da.UpdateCursor(errorsFC,[ward_idField,'duplicate_id']) as cursor:
    for row in cursor:
        if idDict[row[0]][0] ==1:
            cursor.deleteRow()
        else:
            row[1] = 'True'
            cursor.updateRow(row)            
print('Boundaries Errors output was created, No. of duplicates: '+str(duplicateCount))


## ERROR OUTPUT 2 ----- for invalid geometries ##
df = pd.DataFrame.from_dict(geomDict,orient='index')
df.index.names = ['id']
df.columns = ['statename',
              'lganame',
              'wardname',
              'Shape_Area',
              'Shape_length']

df.to_csv(errorFile) 
print('Geometry errors output was created')


## ERROR OUTPUT 3 ----- for wards with non-alphanumeric codes ##
alphaMerge = os.path.join(errorsGDB,'wards_nonalphanumeric_codes_'+date)
arcpy.Merge_management(wardsList,alphaMerge)

fList = [
        ward_idField,
        'lgacode',
        'lganame',
        'wardname',
        'wardcode',
        'statecode',
        'statename'
        ]

for f in arcpy.ListFields(alphaMerge):
    if f.name in fList or f.required:
        pass
    else:
        arcpy.DeleteField_management(alphaMerge,f.name)

arcpy.AddField_management(alphaMerge,'wardcode_format_anomalies','TEXT')
with arcpy.da.UpdateCursor(alphaMerge,['wardcode','wardcode_format_anomalies']) as cursor:
    for row in cursor:
        if not row[0][0].isalpha():
            row[1] = 'True'
            cursor.updateRow(row)
        else:
           cursor.deleteRow()
print('Alphanumeric ID errors output was created')


## ERROR OUTPUT 4.1 ----- for wards missing a 'status' column ##
statusList =[]
statusDict = {}

for ward in wardsList:
    state = [state for state in stateList if state in ward]
    fList = arcpy.ListFields(ward,'*status*')
    if len(fList)==0:
        statusDict[state[0]] = 'ward missing status field'
    else:
        statusList += [ward]    
    
df = pd.DataFrame.from_dict(statusDict,orient='index')
df.index.names = ['state']
df.columns = ['error']
df.to_csv(statusFile) 

print('Created csv for state names that are missing a "Status" field the ward boundaries')

## ERROR OUTPUT 4.2 ----- for wards missing 'status' values ##
if len(statusList)!=0:
    
    statusMerge = os.path.join(errorsGDB,'wards_without_status_value_'+date)     
    arcpy.Merge_management(statusList,statusMerge)
    
    fList = [
            ward_idField,
            'lgacode',
            'lganame',
            'wardname',
            'wardcode',
            'statecode',
            'statename',
            'status'
            ]
    for f in arcpy.ListFields(statusMerge):
        if f.name in fList or f.required:
            pass
        else:
            arcpy.DeleteField_management(statusMerge,f.name)
    
    arcpy.AddField_management(statusMerge,'status_missing','TEXT')
    with arcpy.da.UpdateCursor(statusMerge,['status','status_missing']) as cursor:
        for row in cursor:
            if row[0] is None:
                row[1] = 'True'
                cursor.updateRow(row)
            else:
               cursor.deleteRow()
    print('Status errors output was created')
    
else: 
    print('No ward boundaries contain a status field')


# ------------------------------------------- Script Ends ------------------------------------------- #
print('Script Complete: '+str(datetime.now()-start)+' '+str(stateCount)+' states were processed')


    
        

# -*- coding: utf-8 -*-
"""
Created on Tue Jul 31 09:40:15 2018

@author: afico
This script runs the following processes:
1. Uses the spatial join feature classes created in Check#2 to collect POI point counts by wards
2. Creates an output feature class of wards where wards do not contain at least one POI point
3. Creates a CSV of population estimates per ward and POI counts per ward
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
import pandas as pd
from datetime import datetime
env.overwriteOutput = True
startTime = datetime.now()

# folder variables
mainFolder = r'<computer folder path\All_POI_'+date
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

countFile = os.path.join(errorFolder,'poi_counts_and_population_statistics_by_wards_'+date+'.csv')

# dictionaries, lists, and counts
pDict = {}
wList = []

# ------------------------------------------- Script Begins ------------------------------------------- #
for state in stateList: 
    print('Processing '+state+' now...')

    ## Set up variables
    folderPath = os.path.join(wrkFolder,state) 
    wardsFC = os.path.join(folderPath,'wards_processed.gdb','wards_boundaries')
    poiGDB = os.path.join(folderPath,'poi.gdb')        
    scratchGDB = os.path.join(folderPath,'scratch.gdb')
    
    # Collect list of ward feature classes 
    wList.append(wardsFC)
    
## Step 1: Collect ward attributes in a dictionary
    with arcpy.da.SearchCursor(wardsFC,[ward_idField,'statecode','statename','lgacode','lganame','wardname','wardcode','GPW4_popcounts_2015','GPW4_popcounts_UNadjusted_2015']) as cursor:
        for row in cursor:
            pDict[row[0]] = list(row[1:]) + 4*[0]

## Step 2: Add POI counts into the dictionary
    env.workspace = scratchGDB
    fcList = arcpy.ListFeatureClasses('*spjoin*')
    for fc in fcList:
        place = None
        if 'Educational' in fc:
            place = 9
        if 'Commerce' in fc:
            place = 10
        if 'Pharmaceutical' in fc:
            place = 11
        
        with arcpy.da.SearchCursor(fc,[ward_idField,'wardcode']) as cursor:
            for row in cursor:              
                if row[1] is None:
                    pass
                else:
                    if place is not None:
                        pDict[row[0]][place]  += 1
                        pDict[row[0]][8] += 1
                    else:
                        pDict[row[0]][8] += 1
                        
            print('      1 - Collected POI counts for '+ os.path.basename(fc))
        
 # ------------------------------------------- Creating Error Outputs ------------------------------------------- #    
       
## ERROR OUTPUT 1 ----- for features where ward,lga, and state boundaries do not contain at least 1 poi 
poiCountError = os.path.join(errorsGDB,'poi_count_anomalies_'+date)
arcpy.Merge_management(wList,poiCountError)


# Clean up
keepList = [
        ward_idField,
        'lgacode',
        'wardname',
        'wardcode',
        'lganame',
        'statecode',
        'statename'
        ]

for f in arcpy.ListFields(poiCountError):
    if f.name in keepList or f.required:
        pass
    else:
        arcpy.DeleteField_management(poiCountError,f.name)

# Add fields to flag errors 
poiList = ['Schools','Markets','Health_Facilities']

for poi in poiList:
    arcpy.AddField_management(poiCountError,'zero_count_'+poi,'TEXT')

# Add errors to fields and clean up
with arcpy.da.UpdateCursor(poiCountError,[ward_idField]+['zero_count_'+poi for poi in poiList]) as cursor:
    for row in cursor:
        counts = pDict[row[0]][9:]
        truefalse = [str(c < 1) for c in counts]
        if truefalse == 3*['False']:
            cursor.deleteRow()
        else:
            row[1:] = truefalse
            cursor.updateRow(row)
print('Created output of errors..')    

## ERROR OUTPUT 2 ----- a csv with population and poi count data by wards 
df = pd.DataFrame.from_dict(pDict,orient='index')
df.index.names = ['id']
df.columns = [
        'statecode',
        'statename',
        'lgacode',
        'lganame',
        'wardname',
        'wardcode',
        'GPW4_popcounts_2015',
        'GPWpopcount_UNAdjusted_2015',
        'total_count',
        'schools_count',
        'markets_count',
        'health_facilities_count',
        ]
df.to_csv(countFile)
print('Created csv with population and poi count data')

# ------------------------------------------- Script Ends ------------------------------------------- #
print('Script complete @'+str(datetime.now()-startTime))


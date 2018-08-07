# -*- coding: utf-8 -*-
"""
Created on Tue Jul 31 09:40:15 2018

@author: afico
For questions please contact: afico@ciesin.columbia.edu

This script runs the following processes:
1. Uses the spatial join feature classes created in Check#2 to collect POI point counts by wards
2. Creates an output feature class of wards where wards do not contain at least one POI point
3. Creates a CSV of population estimates per ward and POI counts per ward

Note - This script was written using Spyder (Python 3.6) and works on folder naming conventions and will need to be modified to fit the users folder paths. 

"""

''' import necessary libraries '''
import arcpy, datetime, os
from arcpy import env
import pandas as pd
from datetime import datetime
env.overwriteOutput = True


startTime = datetime.now()
''' set up initial variables ''' 
mainFolder = '<\POIs_and_Administrative_Boundary_Data>' # Full path of main folder required
delFolder = os.path.join(mainFolder,'2_Deliverables')
countFile = os.path.join(delFolder,'POI_counts_validation_8.7.2018.csv')
outputGDB = os.path.join(delFolder,'outputs.gdb')


os.chdir(mainFolder)
subFolders = os.listdir(mainFolder)
subFolders.sort()
stateCount = 0

poiDict = {}
wardsList = []

for state in subFolders: ## Note: The folder names all follow the same convetion - they are the name of the state
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
        
## Step 1: Collect ward attributes in a dictionary
        with arcpy.da.SearchCursor(wardsFC,['globalid','lgacode','wardname','wardcode','lganame','statecode','statename','GPW4_popcounts_2015','GPW4_popcounts_UNadjusted_2015']) as cursor:
            for row in cursor:
                poiDict[row[0]] = list(row[1:]) + 4*[0]

## Step 2: Add POI counts into the dictionary
        env.workspace = scratchGDB
        fcList = arcpy.ListFeatureClasses('*spjoin*')
        for fc in fcList:
            if 'health' in fc:
                place = 8
            if 'market' in fc:
                place = 9
            if 'school' in fc:
                place = 10
            
            with arcpy.da.SearchCursor(fc,['globalid','Join_Count']) as cursor:
                for row in cursor:
                    if row[0] in poiDict:
                        poiDict[row[0]][place]  += row[1]
            print('      Collected POI counts for '+ os.path.basename(fc))
            
            
## Step 3: Create a feature class of error features where ward,lga, and state boundaries do not contain at least 1 poi 
poiErrors_3 = os.path.join(outputGDB,'poiErrors_3')
#arcpy.Merge_management(wardsList,poiErrors_3)


# Clean up
keepList = [
        'OBJECTID',
        'Shape',
        'Shape_Length',
        'Shape_Area',
        'globalid',
        'lgacode',
        'wardname',
        'wardcode',
        'lganame',
        'id',
        'statecode',
        'statename'
        ]

poiErrors_3FieldList = [f.name for f in arcpy.ListFields(poiErrors_3)]
for f in poiErrors_3FieldList:
    if f in keepList:
        pass
    else:
        arcpy.DeleteField_management(poiErrors_3,f)


# Add fields to flag errors 
countList = ['health_facilities','markets','schools']
for poi in countList:
    if 'health_facilities' in poi:
        place = 8
    if 'markets' in poi:
        place = 9
    if 'schools' in poi:
        place = 10
        
    arcpy.AddField_management(poiErrors_3,'zero_count_'+poi,'TEXT')

# Add errors to fields
    with arcpy.da.UpdateCursor(poiErrors_3,['globalid','zero_count_'+poi]) as cursor:
        for row in cursor:
            if row[0] is None or poiDict[row[0]][place]>=1:
                pass
            else: 
                row[1] = 'True'
                cursor.updateRow(row)
 # Clean up               
with arcpy.da.UpdateCursor(poiErrors_3,['zero_count_health_facilities','zero_count_markets','zero_count_schools']) as cursor:
    for row in cursor:
        if row[0] is None and row[1] is None and row[2] is None:
            cursor.deleteRow()
        else:
            if row[0] is None:
                row[0] = 'False'
            if row[1] is None:
                row[1] = 'False'
            if row[2] is None:
                row[2] = 'False'
            cursor.updateRow(row)
          
print('      2 - Created output of errors..')    

## Step 4: Create a csv with population and poi count data by wards 
df = pd.DataFrame.from_dict(poiDict,orient='index')
df.index.names = ['globalid']
df.columns = [
        'lgacode',
        'wardname',
        'wardcode',
        'lganame',
        'statecode',
        'statename',
        'GPW4_popcounts_2015',
        'GPWpopcount_UNAdjusted_2015',
        'health_facility_count',
        'markets_count',
        'schools_count',
        'settlements_count'
        ]

df.to_csv(countFile)
print('      3 - Created csv with population and poin count data')



print('Script complete @'+str(datetime.now()-startTime)+'. Processed ' +str(stateCount)+' states.')


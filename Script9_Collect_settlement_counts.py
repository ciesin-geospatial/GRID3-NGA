# -*- coding: utf-8 -*-
"""
Created on Wed Aug 29 20:38:40 2018

@author: afico

This script does the following processing:
1 - Collects various types of counts from the settlement point data and exports it to a csv file 
2 - Collects a count of settlements in each bua, ssa, and hamlet polygon 
3 - Collects a count of bua, ssa, and hamlets by state.
 """

#* Set up initial variables *#
# variables are subject to change
date = 'Aug_15_2018' 

# ------------------------------------------- Defining Variables ------------------------------------------- #

# importing libraries
import arcpy, datetime, os
from arcpy import env
import pandas as pd
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
    
settCountCSV = os.path.join(errorFolder,'settlement_counts_by_state_'+date+'.csv')
polyCountCSV = os.path.join(errorFolder,'settlement_counts_by_settlement_polygon'+date+'.csv')

errorsGDB = os.path.join(errorFolder,'errors.gdb') 
if not arcpy.Exists(errorsGDB):
    arcpy.CreateFileGDB_management(errorFolder,'errors')
    
scratchFolder = os.path.join(mainFolder,'scratch')
if not os.path.exists(scratchFolder):
    os.makedirs(scratchFolder)

mainscratchGDB = os.path.join(scratchFolder,'scratch.gdb')
if not arcpy.Exists(mainscratchGDB):
    arcpy.CreateFileGDB_management(scratchFolder,'scratch')
    
allsetFC = os.path.join(mainscratchGDB,'all_settlements')

settlyrGDB = os.path.join(scratchFolder,'settlyrs.gdb')
if not arcpy.Exists(settlyrGDB):
    arcpy.CreateFileGDB_management(scratchFolder,'settlyrs')


# dictionaries, lists, and counts
setList = []
countDict = {}
stateboundList = []
setCountDict = {}


# ------------------------------------------- Script Begins ------------------------------------------- #    

## Step 1:
# Collect settlement counts by state
with arcpy.da.SearchCursor(allsetFC,['statename','statecode','settlementname','settlementname_alt']) as cursor:
     for row in cursor:
         # Collect count of settlements with primary names that are not computer names
         if row[2] is not None:
             if row[2][0].isalpha() and row[2] != 'NA':
                 if row[0] in countDict:
                     countDict[row[0]][1] += 1
                 else: 
                     countDict[row[0]] = [row[1]] + [1] + [0]*4
                     
         # Collect count of settlement with alternative names that are not computer  names
         if row[3] is not None:
             if row[3][0].isalpha() and row[3] != 'NA':
                 if row[0] in countDict:
                     countDict[row[0]][2] += 1
                 else: 
                     countDict[row[0]] = [row[1]] + [0] + [1]+ [0]*3
                     
         # Collect count of settlements with primary names that are computer names 
         if row[2] is not None:
             if not row[2][0].isalpha() and row[2] != 'NA':
                 if row[0] in countDict:
                     countDict[row[0]][3] += 1
                 else: 
                     countDict[row[0]] = [row[1]] + [0] + [0] + [1] + [0]*2

         # Collect count of settlements with alternative names that are computer names 
         if row[3] is not None:
             if not row[3][0].isalpha() and row[3] != 'NA':
                 if row[0] in countDict:
                     countDict[row[0]][4] += 1
                 else: 
                     countDict[row[0]] = [row[1]] + [0] + [0] + [0] + [1] + [0]

         # Collect count of settlements with primary names or alternative names that are NULL
         if row[2] is None or row[3] is None or row[3] == 'NA':
             if row[0] in countDict:
                 countDict[row[0]][5] += 1
             else: 
                 countDict[row[0]] = [row[1]] + [0] + [0] + [0] + [0] + [1]
                 
## Step 2: 
# Create necessary feature classes
for state in stateList:
    folderPath = os.path.join(wrkFolder,state)
    scratchGDB = os.path.join(folderPath,'scratch.gdb')
    wardFC = os.path.join(folderPath,'wards_processed.gdb','wards_boundaries')    
    # Dissolve ward boundries to state level
    stateFC = os.path.join(scratchGDB,'state_boundaries')
    if not arcpy.Exists(stateFC):
        arcpy.Dissolve_management(wardFC,stateFC,['statecode','statename'])
        print('Dissolved ward boundaries to state level for {}'.format(state))   
    stateboundList.append(stateFC)
    
#Merge all dissolved state boundaries together
allstateFC = os.path.join(mainscratchGDB,'state_boundaries')
if not arcpy.Exists(allstateFC):
    arcpy.Merge_management(stateboundList,allstateFC)
    print('Created state level feature class')
    

## Step 3: Collecting bua, ssa, and hamlet counts per state AND collection settlement counts per bua, ssa, and hamlet 
# Set up dictionary to collect settlement polygon counts
with arcpy.da.SearchCursor(allstateFC,['statecode']) as cursor:
    for row in cursor:
        setCountDict[row[0]] = [0]*3

env.workspace = settlyrGDB
fcList = arcpy.ListFeatureClasses()
for fc in fcList:
    polyCountDict ={}
    
    if 'bua' in fc:
        print(fc)
        place = 0
    if 'ssa' in fc:
        print(fc)
        place = 1
    if 'hamlet' in fc:
        print(fc)
        place = 2
        
    # Intersect the settlements polygons with the state boundaries to collect counts        
    intOut = os.path.join(mainscratchGDB,fc+'_state_intersect')
    if not arcpy.Exists(intOut):
        arcpy.Intersect_analysis([allstateFC,fc],intOut)
        print('Created intersect')
    else:
        print('intersect already exists.')
    
    with arcpy.da.SearchCursor(intOut,['statecode']) as cursor:
        for row in cursor:
            if row[0] in setCountDict:
                setCountDict[row[0]][place] += 1
    print('Collected counts by state code for settlement polygons.')
    
   
    # Collect settlement count per bua, ssa, and hamlet    
    with arcpy.da.SearchCursor(intOut,['statecode','statename',fc+'_id']) as cursor:
        for row in cursor:
            polyCountDict[row[2]] = list(row) + [0]
            
    setLyr = os.path.join(mainscratchGDB,'settlement_'+fc+'_spjoin')    
    with arcpy.da.SearchCursor(setLyr,['statecode','statename',fc+'_id']) as cursor:
        for row in cursor:
            if row[2] is not None:
                if row[2] in polyCountDict:
                    polyCountDict[row[2]][-1] +=1
                else:
                    polyCountDict[row[2]] = list(row) + [1]

# ------------------------------------------- Creating Error Outputs ------------------------------------------- #    

    ## OUTPUT 1 ----- for settlement counts per bua, ssa, and hamlet 
    countFC = os.path.join(errorsGDB,'settlement_'+fc+'_count')
    arcpy.FeatureClassToFeatureClass_conversion(fc,errorsGDB,'settlement_'+fc+'_count')
    addFields = ['statecode','statename','settlement_count']
    for field in addFields:
        arcpy.AddField_management(countFC,field,'TEXT')
           
    with arcpy.da.UpdateCursor(countFC,['statecode','statename',fc+'_id','settlement_count']) as cursor:
        for row in cursor:
            if row[2] in polyCountDict:
                row = polyCountDict[row[2]]
                cursor.updateRow(row)
            else:
                row[3] = 0
        for row in cursor:
            if row[3] is None:
                row[3] = 'NA'
                cursor.updateRow(row)
    print('Created  output file for settlement count.')    
        
                       
##  OUTPUT 2 ----- for counts of settlement names by state
df = pd.DataFrame.from_dict(countDict,orient='index')
df.index.names = ['statename']
df.columns = ['statecode','primary_names_count','alternative_names_count','primary_computer_names','alternative_computer_names_count','NULL_primary_alternative_name_count']
df.to_csv(settCountCSV) 
print('Created settlement count output')

## OUTPUT 3 ----- for counts of bua, ssa, and has by state
errorFC = os.path.join(errorsGDB,'settlement_polygons_count_by_state_'+date)
arcpy.FeatureClassToFeatureClass_conversion(allstateFC,errorsGDB,'settlement_polygons_count_by_state')
addFields = ['bua_count','ssa_count','hamlet_count']
for field in addFields:
    arcpy.AddField_management(errorFC,field,'LONG')

with arcpy.da.UpdateCursor(errorFC,['statecode','bua_count','ssa_count','hamlet_count']) as cursor:
    for row in cursor:
        if row[0] in setCountDict:
            row[1:] = setCountDict[row[0]]
            cursor.updateRow(row)
    
print('Created bua, ssa, and ham count feature class')    
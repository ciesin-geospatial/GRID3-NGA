# -*- coding: utf-8 -*-
"""
Created on Mon Jul 30 13:23:55 2018

@author: afico
For questions please contact: afico@ciesin.columbia.edu

This script runs the following processes:
1. Merges all settlement points from different states together
2. Merges all wards boundaries from different states together 
3. Spatially joins the merged settlement points with the merged ward boundaries 
4. Determines total number of settlements and total number of named settlemltns
5. Produces a polygon feature class of ward boundaries with attributes for named settlement count, total settlement count, proportion of settlemtns named, flagged features that are below the threshold, and flagged features with no settlements

Note - This script was written using Spyder (Python 3.6) and works on folder naming conventions and will need to be modified to fit the users folder paths. 
"""


import arcpy, os
from arcpy import env
env.overwriteOutput = True


## Identify folders, gdbs, and feature classes
buaFC = '<\bua>' # Requires full path of BUA feature class
ssaFC = '<\ssa>'# Requires full path of SSA feature class
mainFolder = '<\POIs_and_Administrative_Boundary_Data>' # Requires full path of main folder
wardsFC = os.path.join(mainFolder,'1_boundaries','boundaries.gdb','wards_boundaries')
outputGDB = os.path.join(mainFolder,'2_Deliverables','outputs.gdb') 

fcList = []
errorDict={}

os.chdir(mainFolder)
subFolders = os.listdir(mainFolder)
subFolders.sort()

for folder in subFolders:
    folderPath = os.path.join(mainFolder,folder) ## define full path of the subfolder
    
    if '1_' in folder or '2_' in folder:  ##skip folders that are not applicable
        pass
    else:
        print(folder)
        
        poiGDB = os.path.join(folderPath,'poi.gdb')
        settlementFC = os.path.join(poiGDB,'settlements')
        if arcpy.Exists(settlementFC):
            # Collect a list of all the settlement feature classes
            fcList.append(settlementFC)
        else: 
            print(' !!!!! Settlement feature class for '+folder+' does not exists !!!!!')

## Merge all all settlements together 
settFC = os.path.join(outputGDB,'temp_settlements_merge')
arcpy.Merge_management(fcList,settFC)
print('Created a merged settlement feature class')

## Create a copy of the ward boundaries to serve as the error ouput
settlementErrors_2 = os.path.join(outputGDB,'settlementErrors_2')
arcpy.CopyFeatures_management(wardsFC,settlementErrors_2)

# Add errors fields
addintFields = ['total_settlements','total_named_settlements'] ## Count fields

for field in addintFields:
    arcpy.AddField_management(settlementErrors_2,field,'SHORT')

arcpy.AddField_management(settlementErrors_2,'prop_named_settlements','FLOAT') # Proportion field

addtextFields = [
        'settlementCount_below_threshold',
        'no_settlement_in_ward'
        ] ## True/False fields

for field in addtextFields:
    arcpy.AddField_management(settlementErrors_2,field,'TEXT')
print('Added error fields')

# Spatially join the wards with the merged settlement layer 
outFC = os.path.join(outputGDB,'settlementErrors_temp')
arcpy.SpatialJoin_analysis(settFC,wardsFC,outFC,'JOIN_ONE_TO_MANY','KEEP_ALL')

## Cleaning spatial join feature class
altFields = ['wardcode_1','id_1','lganame_1','statename_1','globalid_1']
for field in altFields:
    newName = 'wards_'+field[:-2]
    arcpy.AlterField_management(outFC,field,newName)
print('Cleaned field names')

## Search through the spatial join feature class to find errors
errorCountDict = {}
with arcpy.da.SearchCursor(outFC,['wards_globalid','poi_name','uniqueID']) as cursor:
    for row in cursor:
         #Collect total number of settlements per ward and total number of named settlements
        if row[0] in errorCountDict:
            errorCountDict[row[0]][0] += 1
            if row[1] is not None:
                errorCountDict[row[0]][1] +=1
            
        else:
            if row[1] is not None:
                errorCountDict[row[0]] = [1,1]
            else:
                errorCountDict[row[0]] = [1,0]

## Populate settlementErrors_2 with counts and proportion
with arcpy.da.UpdateCursor(settlementErrors_2,['globalid','total_settlements','total_named_settlements','prop_named_settlements','settlementCount_below_threshold','no_settlement_in_ward']) as cursor:
    for row in cursor:
        if row[0] in errorCountDict:
            row[1] = errorCountDict[row[0]][0]
            row[2] = errorCountDict[row[0]][1]
            row[3] = row[2]/row[1]
            row[4] = 'True'
            row[5] = 'False'
        else:
            row[5] = 'True'
        cursor.updateRow(row)
print('Calculated counts and proportions in error feature class')


## Additional Clean UP
deleteFields = ['amapcode','ogc_fid','timestamp','source','urban']
fieldList = [f.name for f in arcpy.ListFields(settlementErrors_2)]
for f in fieldList:
    if f in deleteFields:
        arcpy.DeleteField_management(settlementErrors_2,f)


delList = [outFC,settFC]
for fc in delList:
    arcpy.Delete_management(fc)
        
print('Script Complete!')
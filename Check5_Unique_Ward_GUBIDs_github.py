# -*- coding: utf-8 -*-
"""
Created on Fri Jul 27 13:18:37 2018

@author: afico
For questions please contact: afico@ciesin.columbia.edu

This script checks to make sure all ward globalids (GUBIDS) are universally unique
Note - This script was written using Spyder (Python 3.6)


"""

import arcpy, os
from arcpy import env
env.overwriteOutput = True

# Set up Folders
wardsFC = '</wards_boundaries>' ## Full path of ward boundary feature class is required
outputsGDB = '<\outputs.gdb>' ## Full path of an ouput geodatabase is required
gubidDict = {}

# Create the output to work with
errorFC = os.path.join(outputsGDB,'boundaryErrors_1')
arcpy.CopyFeatures_management(wardsFC,errorFC)

keepFields = [
        'OBJECTID',
        'Shape',
        'Shape_Length',
        'id',
        'Shape_Area',
        'globalid',
        'lgacode',
        'wardname',
        'wardcode',
        'statecode',
        'statename'
        ]

fList = [f.name for f in arcpy.ListFields(errorFC)]
for f in fList:
    if f not in keepFields:
        arcpy.DeleteField_management(errorFC,f)

# Add flag field
arcpy.AddField_management(errorFC,'duplicate_GUBID','TEXT')

with arcpy.da.SearchCursor(errorFC,['globalid']) as cursor:
    for row in cursor:
        if row[0] in gubidDict:
            gubidDict[row[0]][0] += 1
        else:
           gubidDict[row[0]] = [1]
           
with arcpy.da.UpdateCursor(errorFC,['globalid','duplicate_GUBID']) as cursor:
    for row in cursor:
        if gubidDict[row[0]][0] ==1:
            cursor.deleteRow()
        else:
            row[1] = 'True'
            cursor.updateRow(row)
            
             
           
    
print('Sript Complete!')


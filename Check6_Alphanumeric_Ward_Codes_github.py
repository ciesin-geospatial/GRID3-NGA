# -*- coding: utf-8 -*-
"""
Created on Fri Jul 27 10:44:16 2018

@author: afico
For questions please contact: afico@ciesin.columbia.edu

This script checks to make sure all ward codes contain an alphanumeric code 
Note - This script was written using Spyder (Python 3.6)
"""
import arcpy, os
from arcpy import env
env.overwriteOutput = True

# Set up Folders
wardsFC = '</wards_boundaries>' ## Full path of ward boundary feature class is required
outputsGDB = '<\outputs.gdb>' ## Full path of an ouput geodatabase is required

# Create the output to work with
errorFC = os.path.join(outputsGDB,'boundaryErrors_2')
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
arcpy.AddField_management(errorFC,'wardcode_format_error','TEXT')

with arcpy.da.UpdateCursor(errorFC,['wardcode','wardcode_format_error']) as cursor:
    for row in cursor:
        if not row[0][0].isalpha():
            row[1] = 'True'
            cursor.updateRow(row)
        else:
           cursor.deleteRow()

print('Sript Complete!')
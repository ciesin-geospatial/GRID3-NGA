# -*- coding: utf-8 -*-
"""
Created on Fri Jul 27 13:48:47 2018

@author: afico
For questions please contact: afico@ciesin.columbia.edu

This script checks to make sure each settlement name is unique within the confines of it's ward boundary
Note - This script was written using Spyder (Python 3.6) and works on folder naming conventions and will need to be modified to fit the users folder paths. 

"""


''' import necessary libraries '''
import arcpy, datetime, os, csv
from arcpy import env
from datetime import datetime
env.overwriteOutput = True


''' set up initial variables ''' 
start = datetime.now()
mainFolder = '<\POIs_and_Administrative_Boundary_Data>' ## Full path of main folder is required
outputGDB = os.path.join(mainFolder,'2_Deliverables','outputs.gdb')


os.chdir(mainFolder)
subFolders = os.listdir(mainFolder)
subFolders.sort()


fcList = [] ## To caputre feature classes where names will be checked
nameDict = {} ## To capture names

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
            print('!!!! The settlement feature class for '+folder+' does not exists !!!!')
        
        
setError_1 = os.path.join(outputGDB,'settlmentErrors_1')
arcpy.Merge_management(fcList,setError_1)
arcpy.AddField_management(setError_1,'duplicate_settlement','TEXT')
print('Created output feature class')

# Create a temporary field that concatenates wardcode and lgacode
arcpy.AddField_management(setError_1,'concat_name',"TEXT")
arcpy.CalculateField_management(setError_1,'concat_name',"!poi_name!+'_'+ !wardcode!")
print('Added temporary name field')

# Check to see if there are any duplicates 
with arcpy.da.SearchCursor(setError_1,['concat_name']) as cursor:
    for row in cursor:
        if row[0] in nameDict:
            nameDict[row[0]][0] += 1
        else:
           nameDict[row[0]] = [1]
                      
print('Captured duplicate names')
# If there are duplicates flag them 

with arcpy.da.UpdateCursor(setError_1,['concat_name','duplicate_settlement']) as cursor:
    for row in cursor:
        if nameDict[row[0]][0] ==1:
            cursor.deleteRow()
        else:
            row[1] = 'True'
            cursor.updateRow(row)
            

print('Flagged duplicates in output feature class')

fieldList = [f.name for f in arcpy.ListFields(setError_1)]

keepList = [
        'OBJECTID',
        'Shape',
        'id',
        'poi_name',
        'settlementid',
        'wardcode',
        'globalid',
        'lganame',
        'statename',
        'duplicate_settlement'
        ]

for field in fieldList:
    if field not in keepList:
        arcpy.DeleteField_management(setError_1,field)
print('Deleted fields not needed')

print('Script Complete!')

        


        
        
        

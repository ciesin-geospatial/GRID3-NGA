# -*- coding: utf-8 -*-
"""
Created on Fri Jul 27 15:49:46 2018

@author: afico
For questions please contact: afico@ciesin.columbia.edu

This script runs the following processes:
1. Merges all settlement points together into one feature class
2. Spatially joines settlement points to BUA and SSA polygons
3. Creates an output feature class of only BUA and SSA polygons that do not contain any settlement points 

Note - This script was written using Spyder (Python 3.6) and works on folder naming conventions and will need to be modified to fit the users folder paths. 
"""

import arcpy, os
from arcpy import env
env.overwriteOutput = True


## Identify folders, gdbs, and feature classes
buaFC = '<\bua>' # Requires full path of BUA feature class
ssaFC = '<\ssa>'# Requires full path of SSA feature class
mainFolder = '<\POIs_and_Administrative_Boundary_Data>' # Requires full path of main folder
outputGDB = os.path.join(mainFolder,'2_Deliverables','outputs.gdb') 

boundaryList = [buaFC,ssaFC]
fcList = []

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


for boundary in boundaryList:
    errors = 0
    b = os.path.basename(boundary)
    print('Processing '+b+' now')
    
    ## Spatial join settlements to the boundary
    outFC = os.path.join(outputGDB,b+'Errors_1')
    arcpy.SpatialJoin_analysis(boundary,settFC,outFC,'JOIN_ONE_TO_MANY','KEEP_ALL')
    print('Created spatial join')
    ## Check the spatial join for SSAs with no settlement name or a machine name add flag to error field
    arcpy.AddField_management(outFC,'no_settlement','TEXT')
    
    with arcpy.da.UpdateCursor(outFC,['poi_name','no_settlement']) as cursor:
        for row in cursor:
            if row[0] is not None:             
                if not row[0][0].isalpha:  ## need to fix this to include (does not contain any alphabetic letters)
                    row[1] = 'True'
                    cursor.updateRow(row)
                    errors +=1
                else:
                    cursor.deleteRow()
    
            else:
                row[1] = 'True'
                cursor.updateRow(row)
                errors +=1
    
    print('Calculated errors for polygons: '+str(errors))
    
    # clean up output 
    delFields = [
            'TARGET_FID',
            'JOIN_FID',
            'uniqueID',
            'primary_',
            'source',
            'timestamp',
            'editor',
            '_x',
            '_y',
            '_z',
            'poi_type'
            ]
    
    fList = [f.name for f in arcpy.ListFields(outFC)]
    for f in fList:
        if f in delFields:
            arcpy.DeleteField_management(outFC,f)
    


# Delete temporary file
arcpy.Delete_management(settFC)
print('Script Complete!')

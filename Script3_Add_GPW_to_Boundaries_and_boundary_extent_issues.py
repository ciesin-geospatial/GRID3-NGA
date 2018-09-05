# -*- coding: utf-8 -*-
"""
Created on Mon Jul 16 13:15:21 2018

@author: afico
This script runs the following processes:
1 - Adds GPWv4.1 2015 population data to the ward boundaries
2 - Checks ward boundaries that are outisde the Nigeria country boundary
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
from arcpy.sa import *
arcpy.CheckOutExtension("Spatial")
from datetime import datetime
env.overwriteOutput = True
startTime = datetime.now()

# folder variables
mainFolder = r'<computer folder path>\All_POI_'+date
wrkFolder = os.path.join(mainFolder,'completed')
stateList = os.listdir(wrkFolder)
stateList.sort()
clipFC = r'<computer folder path>\nga_admbnda_adm0_osgof_20161215.shp'

# dictionaries, lists, and counts
wardsList =[]
extentErrorList = []

# Create a scratch folder and geodatabase to work in
scratch = os.path.join(mainFolder,'scratch')
if not os.path.exists(scratch):
    os.makedirs(scratch)

fishnetGDB = os.path.join(scratch,'fishnet.gdb')
if not arcpy.Exists(fishnetGDB):
    arcpy.CreateFileGDB_management(scratch,'fishnet.gdb')
    
# folders and geodatabases to capture errors
errorFolder = os.path.join(mainFolder,'errorFolder')
if not os.path.exists(errorFolder):
    os.makedirs(errorFolder)    
    
errorsGDB = os.path.join(errorFolder,'errors.gdb') 
if not arcpy.Exists(errorsGDB):
    arcpy.CreateFileGDB_management(errorFolder,'errors')


# ------------------------------------------- Script Begins - Creating Fishnet ------------------------------------------- #
    
## Step 0: Create a fishnet and add pop data
rGDB = r'<computer folder path>\gpwv4_10_tifs.gdb'
env.workspace = rGDB
rList = [os.path.join(rGDB,r) for r in arcpy.ListRasters('*','ALL')]
template = r'<computer folder path>\nga_gpw_v4_popcount_2015'
arcpy.env.cellSize = template

## Setup parameters for fishnet
xcellSize = arcpy.GetRasterProperties_management(template,'CELLSIZEX')
cellSizeWidth = xcellSize.getOutput(0)
ycellSize = arcpy.GetRasterProperties_management(template,'CELLSIZEY')
cellSizeHeight = ycellSize.getOutput(0)

outFishnet = os.path.join(fishnetGDB,'NGA_fishnet')
if not arcpy.Exists(outFishnet):       
    arcpy.CreateFishnet_management(outFishnet, origin_coord="2.675 4.25000000386", y_axis_coord="2.675 14.25000000386", cell_width=xcellSize, cell_height=ycellSize, number_rows="", number_columns="", corner_coord="14.6999999999993 13.9000000038595", labels="NO_LABELS", template=template, geometry_type="POLYGON")
    arcpy.AddField_management(outFishnet,'UBID','LONG')
    arcpy.CalculateField_management(outFishnet,'UBID','!OID!','PYTHON') ## Added a uniqueID to the fishnet
    print('      0 - Fishnet created')

# Add GPW population estimates to fishnet 
fishPoints = os.path.join(fishnetGDB,'NGA_fishnet_points')
if not arcpy.Exists(fishPoints):
    arcpy.FeatureToPoint_management(outFishnet,fishPoints,"CENTROID")
    print('      0 - Turned fishnet into points')

# Extract raster cell values to fishnet points
for r in rList:
    gpwPoints = os.path.join(fishnetGDB,os.path.basename(r)+'_points')
    if not arcpy.Exists(gpwPoints):
        arcpy.gp.ExtractValuesToPoints_sa(fishPoints,r,gpwPoints,"","ALL")
        print('      0 - Extracted raster values to point for '+os.path.basename(r))
        
        arcpy.AddField_management(outFishnet,os.path.basename(r),'DOUBLE')
        arcpy.MakeFeatureLayer_management(outFishnet,os.path.basename(r)+'_lyr')
        arcpy.AddJoin_management(os.path.basename(r)+'_lyr','UBID', gpwPoints,'UBID')
        arcpy.CalculateField_management(os.path.basename(r)+'_lyr', os.path.basename(r),"!"+os.path.basename(r)+'_points'+".RASTERVALU!")
        arcpy.RemoveJoin_management(os.path.basename(r)+'_lyr')
        print('      0 - Attached pop values')

# Project fishnet to mollweide and add new area field
fishPRJ = os.path.join(fishnetGDB,'fishnet_mollweide')
outcoord = "PROJCS['World_Mollweide',GEOGCS['GCS_WGS_1984',DATUM['D_WGS_1984',SPHEROID['WGS_1984',6378137.0,298.257223563]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]],PROJECTION['Mollweide'],PARAMETER['False_Easting',0.0],PARAMETER['False_Northing',0.0],PARAMETER['Central_Meridian',0.0],UNIT['Meter',1.0]]"
if not arcpy.Exists(fishPRJ):
    arcpy.Project_management(outFishnet,fishPRJ,outcoord)
    print('      0 - Projected fishnet to Mollweide')    
    
    arcpy.AddField_management(fishPRJ,'Area_km','DOUBLE')
    arcpy.CalculateField_management(fishPRJ,'Area_km','!shape.area@SQUAREKILOMETERS!',"PYTHON")
    print('      0 - Calculated new area')    

# ------------------------------------------- Ward Boundary Processing Begins ------------------------------------------- #
for state in stateList:
    folderPath = os.path.join(wrkFolder,state)
    print('Processing '+state+' now...')
    
    boundaryGDB = os.path.join(folderPath,'wards_processed.gdb')
    scratchGDB = os.path.join(folderPath,'scratch.gdb')
    
    if not arcpy.Exists(scratchGDB):
        arcpy.CreateFileGDB_management(folderPath,'scratch.gdb')

# Step 1
    # Project boundary to equal area projection        
    wardFC = os.path.join(boundaryGDB,'wards_boundaries')
    wardPRJ = os.path.join(scratchGDB,'wards_boundaries_mollweide')
    outcoord = "PROJCS['World_Mollweide',GEOGCS['GCS_WGS_1984',DATUM['D_WGS_1984',SPHEROID['WGS_1984',6378137.0,298.257223563]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]],PROJECTION['Mollweide'],PARAMETER['False_Easting',0.0],PARAMETER['False_Northing',0.0],PARAMETER['Central_Meridian',0.0],UNIT['Meter',1.0]]"
    arcpy.Project_management(wardFC, wardPRJ, outcoord)
    print('      1 - Projected wards to mollweide')

# Step 2
    # Intersect the boundaries and the fishnet
    intFC = os.path.join(scratchGDB,'intersect')
    arcpy.Intersect_analysis([wardPRJ,fishPRJ],intFC)
    print('      2 - Intersected fishnet and wards')
    
# Step 3
    # Add new area field to intersect FC
    arcpy.AddField_management(intFC,'new_Areakm','DOUBLE')
    arcpy.CalculateField_management(intFC,'new_areakm','!shape.area@SQUAREKILOMETERS!','PYTHON')
    print('      3 - Calculate square kilometers on intersected FC')

# Step 4
    # Build a dictionary to calculate new pop counts 
    popDict = {}

    #compile a list of all the ward feature classes to create an error output for wards that are outside of NGA
    wardsList.append(wardFC)
    
    with arcpy.da.SearchCursor(intFC,[ward_idField,'nga_gpw_v4_popcount_adjusted_2015_unwpp','nga_gpw_v4_popcount_2015','Area_km','new_Areakm']) as cursor:
        for row in cursor:
            if row[1] is None and row[2] is None and row[0]:
                extentErrorList.append(row[0])
            else:
                if row[0] in popDict:
                    popDict[row[0]][0] += row[1]*row[4]/row[3]
                    popDict[row[0]][1] += row[2]*row[4]/row[3]          
                else:
                    popDict[row[0]] = [row[1]*row[4]/row[3],row[2]*row[4]/row[3]]
    print('      4 - Created dictionary')
    
# Step 5
    # Use dictionary to add population data to boundaries 
    arcpy.AddField_management(wardFC,'GPW4_popcounts_2015','DOUBLE')
    arcpy.AddField_management(wardFC,'GPW4_popcounts_UNadjusted_2015','DOUBLE')
    print('      5 - Added pop fields to wards')

    count = 0
    with arcpy.da.UpdateCursor(wardFC,[ward_idField,'GPW4_popcounts_2015','GPW4_popcounts_UNadjusted_2015']) as cursor:
        for row in cursor:
            if row[0] in popDict:
                row[1:] = popDict[row[0]]
                cursor.updateRow(row)
                
            else:
                count +=1
    print('      '+str(count)+' did not attach')
    
# ------------------------------------------- Creating Error Outputs ------------------------------------------- #

## ERROR OUTPUT 1 ----- for wards that extent outside of the Nigeria country boundary
errorFCtemp = os.path.join(errorsGDB,'wards_boundaries_extent_anomalies_temp'+date)
arcpy.Merge_management(wardsList,errorFCtemp)
arcpy.AddField_management(errorFCtemp,'ward_extent_anomalies','TEXT')
with arcpy.da.UpdateCursor(errorFCtemp,[ward_idField,'ward_extent_anomalies']) as cursor:
    for row in cursor:
        if row[0] not in extentErrorList:
            cursor.deleteRow()
        else:
            row[1] = 'True'
            cursor.updateRow(row)
            
errorFC = os.path.join(errorsGDB,'wards_boundaries_extent_anomalies_'+date)
arcpy.Erase_analysis(errorFCtemp,clipFC,errorFC)

keepList = [
        'id',
        'wardcode',
        'wardname',
        'statecode',
        'statename',
        'lgacode',
        'lganame',
        'ward_extent_error'
        ]

for f in arcpy.ListFields(errorFC):
    if f.name in keepList or f.required:
        pass
    else:
        arcpy.DeleteField_management(errorFC,f.name)

arcpy.Delete_management(errorFCtemp)
print('Created output for ward boundary extent errors')

# ------------------------------------------- Script Ends ------------------------------------------- #
print('Script Complete after: '+str(datetime.now()-startTime))
        
                   

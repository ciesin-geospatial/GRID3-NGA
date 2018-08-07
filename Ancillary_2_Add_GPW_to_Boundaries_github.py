# -*- coding: utf-8 -*-
"""
Created on Mon Jul 16 13:15:21 2018

@author: afico
For questions please contact: afico@ciesin.columbia.edu

## This script adds GPW population estimates to ward boundaries by state
Note - This script was written using Spyder (Python 3.6) and works on folder naming conventions and will need to be modified to fit the users folder paths. 
Additionally, it uses 2 GPW v4.10 population rasters (2015 Population Count & 2015 UN WPP-Adjusted Population Count) that can be downloaded here: http://sedac.ciesin.columbia.edu/data/collection/gpw-v4/sets/browse
"""

''' import necessary libraries '''
import arcpy, datetime, os
from arcpy import env
from datetime import datetime
env.overwriteOutput = True

startTime = datetime.now()

### set up initial variables ###
mainFolder = '<\POIs_and_Administrative_Boundary_Data>' # Full path of main folder required
boundaries = os.path.join(mainFolder,'1_boundaries','boundaries.gdb')
fishnetGDB = os.path.join(mainFolder,'1_boundaries','fishnets.gdb')
arcpy.CheckOutExtension("Spatial")


## Step 0: Create a fishnet and add pop data
gpwGDB = '\GPW_Population_Rasters.gdb>'
env.workspace = gpwGDB
gpwList = [os.path.join(gpwGDB,data) for data in arcpy.ListFeatureClasses()]

template = '<\gpw_v4_popcount_2015.tiff>' #This template is used to capture the extent needed for the fishnet and is the GPWv4.10 population count 2015 raster

''' Setup parameters for fishnet '''
xcellSize = arcpy.GetRasterProperties_management(template,'CELLSIZEX')
cellSizeWidth = xcellSize.getOutput(0)
ycellSize = arcpy.GetRasterProperties_management(template,'CELLSIZEY')
cellSizeHeight = ycellSize.getOutput(0)

''' Set environment raster analysis cell size '''
arcpy.env.cellSize = template

outFishnet = os.path.join(fishnetGDB,'fishnet')
arcpy.CreateFishnet_management(outFishnet,"","",cellSizeWidth,cellSizeHeight,"","","","NO_LABELS",template,"POLYGON")
arcpy.AddField_management(outFishnet,'UBID','LONG')
arcpy.CalculateField_management(outFishnet,'UBID','!OBJECTID!','PYTHON') ## Added a uniqueID to the fishnet
print('      0 - Fishnet created')

''' Add GPW pop data to fishnet '''
outPoints = os.path.join(fishnetGDB,'fishnet_points')
arcpy.FeatureToPoint_management(outFishnet,outPoints,"CENTROID")
print('      0 - Turned fishnet into points')

''' Extract raster cell values to fishnet points '''
for data in gpwList:
    gpwPoints = os.path.join(fishnetGDB,os.path.basename(data)+'_points')
    arcpy.ExtractValuesToPoints(outPoints,data,gpwPoints,"","ALL")
    print('      0 - Extracted raster values to point for '+os.path.basename(data))
    
    arcpy.AddField_management(outFishnet,os.path.basename(data),'DOUBLE')
    arcpy.MakeFeatureLayer_management(outFishnet,os.path.basename(data)+'_lyr')
    arcpy.AddJoin_management(os.path.basename(data)+'lyr','UBID', gpwPoints,'UBID')
    arcpy.CalculateField_management(os.path.basename(data)+'_lyr', os.path.basename(data),"!"+os.path.basename(data)+".RASTERVALU!")
    arcpy.RemoveJoin_management(os.path.basename(data)+'_lyr')
    print('      0 - Attached pop values')

''' Project fishnet to mollweide and add new area field '''
prjectFC = os.path.join(fishnetGDB,'fishnet_mollweide')
outcoord = "PROJCS['World_Mollweide',GEOGCS['GCS_WGS_1984',DATUM['D_WGS_1984',SPHEROID['WGS_1984',6378137.0,298.257223563]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]],PROJECTION['Mollweide'],PARAMETER['False_Easting',0.0],PARAMETER['False_Northing',0.0],PARAMETER['Central_Meridian',0.0],UNIT['Meter',1.0]]"
arcpy.Project_management(outFishnet,prjectFC,outcoord)
print('      0 - Projected fishnet to Mollweide')    

arcpy.AddField_management(prjectFC,'Area_km','DOUBLE')
arcpy.CalculateField_managemenet(prjectFC,'Area_km','!shape.area@SQUAREKILOMETERS!',"PYTHON")
print('      0 - Calculated new area')    

fishnet = prjectFC

''' Start adding GPW data to wards '''
os.chdir(mainFolder)
subFolders = os.listdir(mainFolder)
subFolders.sort()

for state in subFolders:
    folderPath = os.path.join(mainFolder,state) ## define full path of state folders

    
    if '1_' in state: ## skip boundary folder
        pass
    else:
        print('Processing '+state+' now...')
        boundaryGDB = os.path.join(mainFolder,state,'boundaries.gdb')
        scratchGDB = os.path.join(mainFolder,state,'scratch.gdb')

# Step 1
        # Project boundary to equal area projection        
        inFC = os.path.join(boundaryGDB,'wards_boundaries')
        outFC = os.path.join(scratchGDB,'wards_boundaries_mollweide')
        outcoord = "PROJCS['World_Mollweide',GEOGCS['GCS_WGS_1984',DATUM['D_WGS_1984',SPHEROID['WGS_1984',6378137.0,298.257223563]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]],PROJECTION['Mollweide'],PARAMETER['False_Easting',0.0],PARAMETER['False_Northing',0.0],PARAMETER['Central_Meridian',0.0],UNIT['Meter',1.0]]"
        arcpy.Project_management(inFC, outFC, outcoord)
        print('      1 - Projected wards to mollweide')

# Step 2
        # Intersect the boundaries and the fishnet
        intFC = os.path.join(scratchGDB,'intersect')
        arcpy.Intersect_analysis([outFC,fishnet],intFC)
        print('      2 - Intersected fishnet and wards')
        
# Step 3
        # Add new area field to intersect FC
        arcpy.AddField_management(intFC,'new_Areakm','DOUBLE')
        arcpy.CalculateField_management(intFC,'new_areakm','!shape.area@SQUAREKILOMETERS!','PYTHON')
        print('      3 - Calculate square kilometers on intersected FC')

# Step 4
        # Build a dictionary to calculate new pop counts 
        popDict = {}
        with arcpy.da.SearchCursor(intFC,['globalid','gpw4_popcount_2015','gpw4_popcount_adjusted_2015','Area_km','new_Areakm']) as cursor:
            for row in cursor:
                if row[0] in popDict:
                    popDict[row[0]][0] += row[1]*row[4]/row[3]
                    popDict[row[0]][1] += row[2]*row[4]/row[3]
                    
                else:
                    popDict[row[0]] = [row[1]*row[4]/row[3],row[2]*row[4]/row[3]]
        print('      4 - Created dictionary')
        
# Step 5
        # Use dictionary to add population data to boundaries 
        wardFC = os.path.join(boundaryGDB,'wards_boundaries')
        arcpy.AddField_management(wardFC,'GPW4_popcounts_2015','DOUBLE')
        arcpy.AddField_management(wardFC,'GPW4_popcounts_UNadjusted_2015','DOUBLE')
        print('      5 - Added pop fields to wards')

        count = 0
        with arcpy.da.UpdateCursor(wardFC,['globalid','GPW4_popcounts_2015','GPW4_popcounts_UNadjusted_2015']) as cursor:
            for row in cursor:
                if row[0] in popDict:
                    row[1:] = popDict[row[0]]
                    cursor.updateRow(row)
                    
                else:
                    count +=1
        print('      '+str(count)+' did not attach')


print('      Script Complete after: '+str(datetime.now()-startTime))
        
                   

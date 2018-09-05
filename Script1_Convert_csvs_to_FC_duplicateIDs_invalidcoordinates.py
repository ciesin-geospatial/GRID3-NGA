# -*- coding: utf-8 -*-
"""
Created on Tue Jul 31 08:47:21 2018

@author: afico

This script runs the following processes:
1. Creates working geodatabases for future processing 
2. Checks each POI csv for latitutde and longitude fields
3. Converts each POI csv into a feature class
4. Checks to make sure all rows in the csv were converted over
5. Adds a "poi_type" field to the feature class

"""

#* Set up initial variables *#
# variables are subject to change
date = 'Aug_15_2018' 
poi_idField = 'FID'
ward_idField = 'id'


# ------------------------------------------- Defining Variables ------------------------------------------- #

# import Libraries
import arcpy, datetime, os, re, csv
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

# dictionaries, lists, and counts
eDict ={}
invalidList = []
POIidDict = {}
uniqueidDict = {}
outputList = []
idErrorDict = {}
stateCount = 0 

# folders and geodatabases to capture errors
errorFolder = os.path.join(mainFolder,'errorFolder')
if not os.path.exists(errorFolder):
    os.makedirs(errorFolder)

coordCSV = os.path.join(errorFolder,'poi_coordinate_field_anomalies_'+date+'.csv')    
idCSV = os.path.join(errorFolder,'poi_id_field_anomalies_'+date+'.csv')    

errorsGDB = os.path.join(errorFolder,'errors.gdb') 
if not arcpy.Exists(errorsGDB):
    arcpy.CreateFileGDB_management(errorFolder,'errors')
    

# ------------------------------------------- Defining Functions ------------------------------------------- #
def convert(state):
    
    # Convert csv's to feature classes  
    csvList = [file for file in os.listdir(folderPath) if file.endswith('.csv') and 'Human_Settlements_Settlement_Points' not in file]
       
    csvList.sort()
    for file in csvList:  
        csvPath = os.path.join(folderPath,file)                
        # replace all invalid characters 
        poiName = re.sub('[^a-zA-Z0-9_.]', '', file[:-4])
        poiName = poiName.replace('__','_')
        
        if not arcpy.Exists(os.path.join(gdbPath,poiName)):
            print('      Converting: '+poiName)             
                                    
            # Check for latitude and longitude fields
            with open(csvPath,"r") as csvFile:  
                reader = csv.reader(csvFile)
                headers = next(reader)                    
                headerCount = 0               
                rowCount = sum(1 for row in reader)  
    
                if 'latitude' in headers and 'longitude' in headers:
                    headerCount +=2
                else: 
                    print('      !Error - check coordinates!')
                    key = state+'_'+file[:-4]
                    eDict[key] = [state,file[:-4],'coordinate field name is inconsistent'] 
                        
                # Check for id field     
                if poi_idField not in headers:
                    key = state+'_'+file[:-4]
                    idErrorDict[key] = [state,file[:-4],'id field name is inconsistent']
                    print('      !Error - check id field!')
                    
                                    
            # Process csv's with lat/long fields
            if headerCount==2 and poi_idField in headers:                                       
                try: 
    
                    inTable = csvPath
                    x_coords = "longitude"
                    y_coords = "latitude"
                    lyr = state+file[:-4]+'_lyr'
                    spRef = arcpy.SpatialReference(4326)  
                    
                    # Convert geodatabase table to a event layer
                    arcpy.MakeXYEventLayer_management(inTable,x_coords,y_coords,lyr,spRef)
                    
                    # Validate that all rows were converted 
                    lyrCount = int(arcpy.GetCount_management(lyr).getOutput(0))
                    if rowCount != lyrCount:
                        print('      !!!!!'+str(rowCount-lyrCount)+' WERE NOT CREATED - CHECK '+poiName+'!!!!!')
                    
                    # Convert event layer to feature class
                    poiFC = os.path.join(gdbPath,poiName)
                    arcpy.FeatureClassToFeatureClass_conversion(lyr,gdbPath,poiName)              
                    # Add a POI Type field to new poi feature class
                    arcpy.AddField_management(poiFC,'poi_file_name','TEXT')
                    arcpy.CalculateField_management(poiFC,'poi_file_name',"'"+poiName+"'","PYTHON")
                    
                    
    
                except Exception as err:
                    print("      !!!!!"+err.args[0]+'!!!!!')               
            else:
                print('      Conversion was incomplete')      
        else:
            print('      '+poiName+' already exists..')


def idCheck(state):
        
        env.workspace = gdbPath
        poiList = arcpy.ListFeatureClasses()
        poiList.sort()                                   
        for poi in poiList:
            # Collect all poi feature classes in a list
            outputList.append(os.path.join(gdbPath,poi))  
            
            # Check for duplicate ids
            with arcpy.da.SearchCursor(poi,[poi_idField]) as cursor:
                for row in cursor:
                    if row[0] in POIidDict:                       
                        POIidDict[row[0]] += 1                                         
                    else:
                        POIidDict[row[0]] = 1

            # Create a universally unique identifier for internal use and fix white spaces in values
            fList = ['statecode','statename','wardname','lganame','statecode','wardcode','lgacode']
            f2List = [f.name for f in arcpy.ListFields(poi,'String')]
            for f in f2List:
                if f in fList:
                    arcpy.CalculateField_management(poi,f,'!'+f+'!.replace(" ","")','PYTHON')
                            
            arcpy.AddField_management(poi,'uniqueID','TEXT')
            arcpy.CalculateField_management(poi,'uniqueID',"'"+poi+"'+'_'+ str(!statecode!)+'_'+str(!lgacode!)+'_'+str(!wardcode!)+'_'+str(!OBJECTID!)",'PYTHON')
            
            # Collect all uniqueIDs in a dictionary and determine if there are duplicates (used for internal validation)
            with arcpy.da.SearchCursor(poi,['uniqueID']) as cursor:
                for row in cursor:
                    if row[0] in uniqueidDict:                        
                        uniqueidDict[row[0]][0] += 1
                        uniqueidDict[row[0]] = uniqueidDict[row[0]] + [state+'_'+poi]                                          
                    else:
                        uniqueidDict[row[0]] = [1, state+'_'+poi]
           
            # Check for invalid coordinates
            invalidCount = 0
            with arcpy.da.SearchCursor(poi,['uniqueID','latitude','longitude']) as cursor:
                for row in cursor:
                    if row[1] == 0 or row[2] == 0:
                        invalidList.append(row[0])                                      
            if invalidCount >1:
                print('!!!! Found '+str(invalidCount)+' invalid rows in '+state+' '+poi)
            
            # Clean up poi feature classes
            keepList = [
                    poi_idField,
                    'poi_file_name',
                    'wardname',
                    'wardcode',
                    'lgacode',
                    'lganame',
                    'statename',
                    'statecode',
                    'uniqueID'
                    ]
            for f in arcpy.ListFields(poi):
                if f.name in keepList or f.required:
                    pass
                else:
                    arcpy.DeleteField_management(poi,f.name)
      
# ------------------------------------------- Script Begins ------------------------------------------- #
for state in stateList:    
    ## define full path of the subfolder
    folderPath = os.path.join(wrkFolder,state)     
    stateCount += 1
    print('Processing '+state+' now...')
        
    ## Step 1: Create geodatabases in each state folder if they don't already exist
    if not arcpy.Exists(os.path.join(folderPath,'poi.gdb')):
        arcpy.CreateFileGDB_management(folderPath,'poi.gdb')
            
    if not arcpy.Exists(os.path.join(folderPath,'scratch.gdb')):
        arcpy.CreateFileGDB_management(folderPath,'scratch.gdb')    
    
    scratchPath = os.path.join(folderPath,'scratch.gdb')  
    gdbPath = os.path.join(folderPath,'poi.gdb')  

    convert(state)      
    idCheck(state)


# ------------------------------------------- Creating Error Outputs ------------------------------------------- #
    
## ERROR OUTPUT 1 ----- for duplicate ids and invalid coordinates (0,0)
mergedFC = os.path.join(errorsGDB,'poi_id_and_coordinate_anomalies_'+date)
arcpy.Merge_management(outputList,mergedFC)
arcpy.AddField_management(mergedFC,'duplicate_id','TEXT')
arcpy.AddField_management(mergedFC,'invalid_coordinates','TEXT')
print('Merged all poi feature classes')

with arcpy.da.UpdateCursor(mergedFC,[poi_idField,'uniqueID','duplicate_id','invalid_coordinates']) as cursor:
    for row in cursor:
        if POIidDict[row[0]]>1: # Flag rows that contain duplicate poi ids
            row[2] = 'True'
        else: 
            row[2] = 'False'
        if row[1] in invalidList: # Flag rows that contain invalid coordinates
            row[3] = 'True' 
        else: 
            row[3] = 'False'
        cursor.updateRow(row)   
        
        if POIidDict[row[0]]==1 and row[1] not in invalidList: ## Remove rows that are not in either check list
            cursor.deleteRow()
arcpy.DeleteField_management(mergedFC,'uniqueID')
print('Created error output feature class of duplicate ids')


## ERROR OUTPUT 2 ----- for poi csvs missing coordinate fields (or have inconsistent schema)
if len(eDict) !=0:
    df = pd.DataFrame.from_dict(eDict,orient='index')
    df.index.names = ['id']
    df.columns = ['state','file','anomaly']
    df.to_csv(coordCSV) 
    print('Created csv with poi files that have inconsistent coordinate schemas (or missing field all together)')
else:
    print('No issues with coordinate schema were found')


## ERROR OUTPUT 3 ----- for pois missing an id field (or inconsistent schema)
if len(idErrorDict) !=0:
    df = pd.DataFrame.from_dict(idErrorDict,orient='index')
    df.index.names = ['id']
    df.columns = ['state','file','anomaly']
    df.to_csv(idCSV) 
    print('Created csv for pois with inconsistent, or missing, id field names')
else:
    print('No issues with id field schema were found')
                
## Internal Validation - Check uniqueID field for duplicates
for key in uniqueidDict:
    value = uniqueidDict[key]
    if value[0] >1:
        print('!!!!! Must Check '+ key+ ' found in '+str(value[0])+' feature classes: '+" & ".join(value[1:])+' !!!!!')

# ------------------------------------------- Script Ends ------------------------------------------- #
print('Script Complete @ '+str(datetime.now()-startTime)+'. Processed '+str(stateCount)+' states.')





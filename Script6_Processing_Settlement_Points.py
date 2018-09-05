# -*- coding: utf-8 -*-
"""
Created on Tue Aug 23 09:24:15 2018

@author: afico

This script runs the following processes:
1. Checks for latitude, longitude, and id columns within settlement csvs and produces error files if not found
2. Converts the settlement csv files to point feature classes
3. Eliminates white space from settlement point attribute tables
"""


#* Set up initial variables *#
# variables are subject to change
date = 'Aug_15_2018' 
poi_idField = 'FID'
ward_idField = 'id'
sett_idField = 'FID'

# ------------------------------------------- Defining Variables ------------------------------------------- #

# importing libraries
import arcpy, datetime, os, csv, re
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

scratchFolder = os.path.join(mainFolder,'scratch')
if not arcpy.Exists(scratchFolder):
    os.mkdir(scratchFolder)

scratchGDB = os.path.join(scratchFolder,'scratch.gdb')
if not arcpy.Exists(scratchGDB):
    arcpy.CreateFileGDB_management(scratchFolder,'scratch')


# List variables to capture errors 
errorFolder = os.path.join(mainFolder,'errorFolder')
if not os.path.exists(errorFolder):
    os.makedirs(errorFolder) 

errorsGDB = os.path.join(errorFolder,'errors.gdb') 
if not arcpy.Exists(errorsGDB):
    arcpy.CreateFileGDB_management(errorFolder,'errors')

missingCSV = os.path.join(errorFolder,'states_missing_settlement_file_'+date+'.csv')
coordCSV = os.path.join(errorFolder,'settlements_with_coordinate_issues_'+date+'.csv')


# dictionaries, lists, and counts
coordDict = {}
missingDict = {}

    
# ------------------------------------------- Defining Functions ------------------------------------------- #    

def settlements(state):
    csvname = os.path.basename(setCSV)[:-4]
    filename = re.sub('[^a-zA-Z0-9_.]', '', csvname)
    filename = csvname.replace('__','_')

    with open(setCSV,"r") as csvFile:  
        reader = csv.reader(csvFile)
        headers = next(reader)                    
        rowCount = sum(1 for row in reader)  
            
    if 'latitude' in headers and 'longitude' in headers:
        try: 

            inTable = setCSV
            x_coords = "longitude"
            y_coords = "latitude"
            lyr = state+'_'+filename+'_lyr'
            spRef = arcpy.SpatialReference(4326)  
            
            # Convert geodatabase table to a event layer
            arcpy.MakeXYEventLayer_management(inTable,x_coords,y_coords,lyr,spRef)
            
            # Validate that all rows were converted 
            lyrCount = int(arcpy.GetCount_management(lyr).getOutput(0))
            if rowCount != lyrCount:
                print('      !!!!!'+str(rowCount-lyrCount)+' WERE NOT CREATED - CHECK '+filename+'!!!!!')
            
            # Convert event layer to feature class
            arcpy.FeatureClassToFeatureClass_conversion(lyr,setGDB,filename)
            settFC = os.path.join(setGDB,filename)
                       
            print('1 - Created settlement Feature class')
            
            # Clean up
            fList = arcpy.ListFields(settFC)
            for f in fList:
                if f.name not in headers and not f.required:
                    arcpy.DeleteField_management(settFC,f.name)
            
        except Exception as err:
            print("      !!!!!"+err.args[0]+'!!!!!')               
            
        
    else: 
        print('      !Error - for coordinate column!')
        key = state+'_'+os.path.basename(setCSV)[:-4]
        coordDict[key] = [state,os.path.basename(setCSV)[:-4],'coordinate field name is inconsistent'] 
        

def fix_whitespace(state):
        env.workspace = setGDB
        fcList = arcpy.ListFeatureClasses()
        # Fix white space in all settlement point attributes
        fList = ['settlementname','settlementname_alt','statecode','statename','wardname','lganame','statecode','wardcode','lgacode']
        f2List = [f.name for f in arcpy.ListFields(fcList[0],'String')]
        for f in f2List:
            if f in fList:
                arcpy.CalculateField_management(fcList[0],f,'!'+f+'!.replace(" ","")','PYTHON')
        print('2 - Fixed whitespace')
                


# ------------------------------------------- Script Begins ------------------------------------------- #    
for state in stateList:
    print('Processing: '+state)
    folderPath = os.path.join(wrkFolder,state)
    setCSV = os.path.join(folderPath,'Human_Settlements_Settlement_Points.csv')
    setGDB = os.path.join(folderPath,'settlements.gdb')
    
    if not arcpy.Exists(setGDB):
        arcpy.CreateFileGDB_management(folderPath,'settlements')
    #run functions depending on the avaliable file type    
    if arcpy.Exists(setCSV):
        settlements(state)  
        fix_whitespace(state)
    else: 
        missingDict[state] = 'State missing settlement file'
        print(' !!!! CHECK - '+state+': missing settlements file')
      
        

# ------------------------------------------- Creating Error Outputs ------------------------------------------- #

## ERROR OUTPUT 1 ----- for settlemts missing coordinate fields (or have inconsistent schema)
if len(missingDict)!=0:
    df = pd.DataFrame.from_dict(missingDict,orient='index')
    df.index.names = ['state']
    df.columns = ['error']
    df.to_csv(missingCSV) 
    print('Created csv of state names that are missing settlement files')
else:
    print('All states contain settlement files.')      

## ERROR OUTPUT 2 ----- for settlemts missing coordinate fields (or have inconsistent schema)
if len(coordDict)!=0:
    df = pd.DataFrame.from_dict(coordDict,orient='index')
    df.index.names = ['id']
    df.columns = ['state','file','error']
    df.to_csv(coordCSV) 
    print('Created csv with settlement files that are inconsistent with schema (or missing field all together)')
else:
    print('No coordinate errors found.')           

# ------------------------------------------- Script Ends ------------------------------------------- #
print('Script Complete @ '+str(datetime.now()-startTime))


        
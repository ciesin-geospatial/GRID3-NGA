# -*- coding: utf-8 -*-
"""
Created on Tue Jul 31 08:47:21 2018

@author: afico

This script runs the following processes:
1 - checks all csv for schema inconsistencies  
"""

#* Set up initial variables *#
date = 'July_26_2018' # date is subject to change

# ------------------------------------------- Defining Variables ------------------------------------------- #

# import Libraries
import datetime, os, csv
from arcpy import env
import pandas as pd
from datetime import datetime
startTime = datetime.now()

# folder variables
mainFolder = r'<computer folder path>\All_POI_'+date
wrkFolder = os.path.join(mainFolder,'completed')
stateList = os.listdir(wrkFolder)
stateList.sort()

# dictionaries, lists, and counts
headerDict = {}

# folders and geodatabases to capture errors
errorFolder = os.path.join(mainFolder,'errorFolder')
if not os.path.exists(errorFolder):
    os.makedirs(errorFolder)

headerCSV = os.path.join(errorFolder,'files_with_column_header_inconsistencies_'+date+'.csv')    
  
# ------------------------------------------- Script Begins ------------------------------------------- #
for state in stateList:    
    ## define full path of the subfolder
    folderPath = os.path.join(wrkFolder,state)     
    print('Processing '+state+' now...')
        
    csvList = [file for file in os.listdir(folderPath) if file.endswith('.csv')]
    schemaList = ['globalid','latitude','longitude','wardcode','statecode','lgacode','wardname','statename','lganame'] # these fields are subject to change
    for file in csvList:  
        csvPath = os.path.join(folderPath,file)  
                  
        with open(csvPath,"r") as csvFile:  
            
            reader = csv.reader(csvFile)
            headers = next(reader)      
            
            for schema in schemaList:
                if schema not in headers:
                    print('{} contains schema issues for {}.'.format(state,file))
                    key = state+'_'+file
                    if key in headerDict:
                        headerDict[key] = headerDict[key] + [schema] 
                    else: 
                        headerDict[key] = [state,file,schema]


# ------------------------------------------- Creating Error Outputs ------------------------------------------- #

 ## ERROR OUTPUT 3 ----- for csv's missing an id field (or inconsistent schema)
if len(headerDict) !=0:
    df = pd.DataFrame.from_dict(headerDict,orient='index')
    df.index.names = ['id']
    df.to_csv(headerCSV) 
    print('Created csv for pois with inconsistent, or missing, id field names')
else:
    print('No issues with id field schema were found')
                
# ------------------------------------------- Script Ends ------------------------------------------- #
print('Script Complete @ '+str(datetime.now()-startTime))
   
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
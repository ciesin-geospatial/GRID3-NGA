# -*- coding: utf-8 -*-
"""
Created on Fri Aug 24 08:26:15 2018

@author: afico
This script runs the following processing:
1 - Changes headers names in csvs to match schema 
"""
#* Set up initial variables *#
date = 'Aug_15_2018' # date is subject to change

# ------------------------------------------- Defining Variables ------------------------------------------- #

# import Libraries
import os
import pandas as pd


# folder variables
mainFolder = r'<computer folder path>\All_POI_'+date
wrkFolder = os.path.join(mainFolder,'completed')
stateList = os.listdir(wrkFolder)
stateList.sort()

# ------------------------------------------- Script Begins ------------------------------------------- #
# the progessing in this script is subject to change based on the headers present in the csv files.
for state in stateList:
    if 'Jigawa' in state:
        stateFolder = os.path.join(wrkFolder,state)
        print('Processing: '+state)
        fList = [os.path.join(stateFolder,f) for f in os.listdir(stateFolder) if f.endswith('.csv') and 'Educational' in f] 
        
        for f in fList:
            print(os.path.basename(f))
            df = pd.read_csv(f)
            headers = list(df.head(0))
    
            for header in headers:
                if 'properties' in header:
                    new = header[11:]
                    df.rename(columns={header:new}, inplace = True)            
                       
                    if new == 'y':
                        new4 = 'latitude'
                        df.rename(columns={new:new4},inplace = True)
                        
                    if new == 'x':
                        new5 = 'longitude'
                        df.rename(columns={new:new5},inplace = True)
                if 'id' in header:
                    df.rename(columns={'id':'FID'}, inplace = True)
                    
 # ------------------------------------------- Creating Error Outputs ------------------------------------------- #
                   
            newHeaders2 = list(df.head(0))                                           
            df2 = pd.DataFrame.to_csv(df,index = True)
            df.index.names = ['temp_column']
            df.columns = newHeaders2
            df.to_csv(f) 
            print('Changed headers in csv')
                 
                
# ------------------------------------------- Script Ends ------------------------------------------- #
print('Script Complete')
   
    
    
    
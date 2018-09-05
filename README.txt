## Alyssa Fico 
## 09/04/2018

#Notes about the scripts and how to use them 

Scripts are listed in the order in which they should be run:
------------------------------------------------------------

SCRIPT W: Check header names in point of interest csv files
This script checks for schema issues in each csv prior to any processing. It creates an output file that contains all csv files (by state) that do not follow a specified schema. 

SCRIPT X: Change header names in point of interest csv files
This script checks for specified headers in specific csv files. It then changes the header names to match the correct schema. 

SCRIPT Z: Check header names in settlement csv files
This script checks for specified headers in specific csv files. Header names are then manually changed.

SCRIPT 1: Converts csv files to feature classes
This script converts the csv files to feature classes. It checks for duplicate IDs and invalid coordinates.

SCRIPT 2: Processing ward boundaries 
This script checks the 'Status' field in each ward boundary dataset. It also checks for duplicate IDs, invalid geometry, and non-alphanumeric wardcodes

SCRIPT 3: Add population estimates to the ward boundaries
This script adds GPWv4.1 2015 population data to the ward boundaries. It then creates an output of all ward boundaries that extent outside the Nigeria country boundary. 

SCRIPT 4: Checks the spatial location of point of interest features 
This script checks that the ward each point of interest feature specified in the attribute table matches the ward the point of interest is spatially located in. 

SCRIPT 5: Checks the point of interest count
A csv file is produced of point of interest counts within each ward and an error file is produced that contains all wards that do not have at least one health facility, school, or market

SCRIPT 6: Processing settlement points
This script checks for latitude and longitude columns in settlement point csv files then converts them to feature classes.

SCRIPT 7: Checks the spatial location of settlement points
This script checks that the ward each settlement feature specified in the attribute table matches the ward the point of interest is spatially located in. 


SCRIPT 8: In progress

SCRIPT 9: Collects a settlement point count
This script collects a count of the number of settlements in bua, ssa, and hamlet polygons. It also creates a csv of counts of settlement name types (computer, NULL, and noncomputer) 




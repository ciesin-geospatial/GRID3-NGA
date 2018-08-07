## Alyssa Fico 
## 7/31/2018

#Notes about the scripts and how to use them 

Scripts are listed in the order in which they should be run:
------------------------------------------------------------
Check1.1
Converts the point of interest csvs into feature classes, creates working geodatabases and keeps everything seperated by state. Requires that all data be in seperated into "State" folders housed within a "Main" folder. This script also produces a "uniqueID" value (for internal processing only) for each POI feature which should be used during all processes as GUBIDs might contain duplicates.

Ancillary1
Since administative levels are provided as 3 seperate features (state,lga, and wards). This script attaches state and LGA information onto the ward boundaries using the provided 'codes'. First, state attributes must be added to the LGA dataset then the LGA attributes are attached to the wards - since there is no way to attach state to wards directly.  The wards dataset is then broken up by state and exported to the "State" folder created in script 1.1.

Check5
This script validates that all ward GUBIDs are universally unique. It creates an output that contains only wards with duplicate GUIBIDs.

Check1.2
Takes the outputs from script 1.1 and makes sure all POI GUBIDs are unique universally (not just within the feature class itself but also among the entire collection) It then checks to make sure there are valid coordinates within each feature class (i.e. no 0,0 coords). An output is produced, that contains ALL POI features with errors (e.g.nonError features are removed, all POI feature classes are merged into one "error dataset") with two error fields that flag features with duplicate GUBIDs and invalid coordinates. 

Check2
Uses outputs from check1.1 to validate the POI 'wardname' field against the 'wardname' field in the ward boundaries. Creates an output with ALL POI features that do not have ward names that match those in the ward boundaries. 

Ancillary2
This script takes the ward boundaries produced in Ancillary1 and adds GPW population estimates by ward. 

Check3 and Check4: This script takes the outputs from Ancillary1/Ancillary2 and Check1.1 to collect a count of POI per ward and produce a CSV that contains that counts and population estimates per ward. In addition to the CSV, an output polygon is produced of only wards that contain either no schools, health facility, or markets. 

Check6: This script checks to make sure all ward codes with the ward boundaries from Ancillary1/Ancillary2 are alphanumerical. There should not be any 'machine produced placeholders' present as values. An output is produced containing all ward features that contain non-alphanumerical wardcodes. 

Check9: This script checks that each settlement name within a ward is unique. Although settlement names can be duplicated across adminsitrative boundaries, they should be unique within the confides of their adminsitative level. An output is produced that contains ALL settlement points that have duplicate names within the same ward. 

Check10: This scripts check that BUA and SSA polygons (from ORNL) have at least one named settlement point. 'machine produced placeholders' do not count. Two outputs are produced, one of BUA polygons and one of SSA polygons. Both outputs only contains features that do not have any named settlements. 

Check11.1 This script uses the wards from Ancillary1/Ancillary2 and the settlements from Check1.1 to determine the proportion of named settlements within each ward boundry.  The total count of settlements and the total count of named settlements (names that are NOT 'machine produced placeholders') are also produced. A polygon feature class of the ward boundaries with this information is produced. In addition, a field for "no settlements within wards" is added and marked "True" for any feature that does not contain at least one settlement point. 






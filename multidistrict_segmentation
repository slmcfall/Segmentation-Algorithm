#-------------------------------------------------------------------------------
# Name:        multidistrict_segmentation
# Author:      Edward Abrahams and Sean McFall
#
# Created:     10/04/2015
# Copyright:   (c) erabrahams 2015
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import arcpy, random_segmentation
arcpy.env.overwriteOutput = 1
arcpy.env.workspace = "in_memory"

all_parcels = "all_parcels_lyr"
districts = "group_districts_lyr"
parcels = "group_parcels_lyr"
curDistrict = "cur_district_lyr"

# Instructions:
#    - Create shapefile of the districts you wish to analyze.
#    - Use this and the shapefile containing all parcels (script will perform clip on these)
#      as the inputs for the script.
#    - Input desired number of map iterations that will be created for each district.

# Accounts for directories containing whitespace
def treatDirectory(directory):
    if " " in directory:
        raise Exception("Directory path cannot contain space!")
    directory += "\\"
    return directory

def main():
    directory = arcpy.GetParameterAsText(0)
    parcelsInput = arcpy.GetParameterAsText(1)
    group_districts = arcpy.GetParameterAsText(2)
    subsect_field = arcpy.GetParameterAsText(3)
    pop_field = arcpy.GetParameterAsText(4)
    iterations = int(arcpy.GetParameterAsText(5))
    rngSeed = int(arcpy.GetParameterAsText(6))

    directory = treatDirectory(directory)

    arcpy.MakeFeatureLayer_management(parcelsInput, all_parcels)
    arcpy.MakeFeatureLayer_management(group_districts, districts)

    arcpy.AddMessage("\nClipping relevant parcels...")
    arcpy.Clip_analysis(all_parcels, districts, parcels)

    arcpy.AddMessage("\nBeginning processing loop.")
    group = arcpy.da.SearchCursor(group_districts, ["LEAID", subsect_field])

    errorLog = open(directory + "errorLog.txt", "w")
    for district in group:
        arcpy.AddMessage("-----------------------------")
        arcpy.AddMessage("Processing District: " + district[0])

        arcpy.FeatureClassToFeatureClass_conversion(parcels, arcpy.env.workspace, curDistrict, "GEOID10_1 = '{id}'".format(id = district[0]))

        curDistrictParcels = directory + "District_" + district[0] + ".shp"
        arcpy.Clip_analysis(parcels, curDistrict, curDistrictParcels)

        arcpy.AddMessage("Creating subdivision maps...")
        random_segmentation.subdivideDistrict(curDistrictParcels, pop_field, district[1], iterations, rngSeed)

        errors = random_segmentation.getErrors()
        errorLog.write(errors + "\n")

    errorLog.close()

main()

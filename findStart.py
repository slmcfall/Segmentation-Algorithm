#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      erabrahams
#
# Created:     05/02/2015
# Copyright:   (c) erabrahams 2015
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import arcpy

fileInput = arcpy.GetParameterAsText(0)
bndLine = arcpy.GetParameterAsText(1)
parcels = "parcels_lyr"
bndLayer = "bound_lyr"

def centroidPosition(row):
    x = row.getValue("Centroid_X")
    y = row.getValue("Centroid_Y")
    return abs(x) + abs(y)

arcpy.MakeFeatureLayer_management(fileInput, parcels)
arcpy.MakeFeatureLayer_management(bndLine, bndLayer)
arcpy.SelectLayerByLocation_management(parcels, "INTERSECT", bndLayer, "", "NEW_SELECTION")

cursor = arcpy.SearchCursor(parcels)
"""for line in cursor:
    arcpy.AddMessage(line.getValue("NAME"))"""

high = 0
highNdx = 0
coord = 0

for row in cursor:
    coord = centroidPosition(row)
    arcpy.AddMessage("Index = " + str(row.getValue("FID")) + ", coord = " + str(coord))
    if (coord > high):
        high = coord
        highNdx = row.getValue("FID")
    arcpy.AddMessage("curHigh = " + str(high))

arcpy.AddMessage("Starting position is shape number " + str(highNdx) + " with value " + str(high))








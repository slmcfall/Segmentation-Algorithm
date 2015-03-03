#-------------------------------------------------------------------------------
# Name:        Segmentaion Algorithm
# Purpose:
#
# Author:      erabrahams and slmcfall
#
# Created:     30/01/2015
# Copyright:   (c) erabrahams 2015
#-------------------------------------------------------------------------------

import arcpy
arcpy.env.overwriteOutput = 1

fileInput = arcpy.GetParameterAsText(0)
#totalSubsects = arcpy.GetParameterAsText(1)
totalSubsects = 1
totalTracts = 0
totalPop = 0

""" Calculate total population """
# cursor is a one time thing..
rows = arcpy.SearchCursor(fileInput, "", "", "", "")
for row in rows:
    totalPop += row.getValue('TOTAL')
    totalTracts += 1

# output total population and number of tracts
arcpy.AddMessage("Number of Kids: " + str(totalPop))
arcpy.AddMessage("Number of Tracts" + str(totalTracts))

""" Calculate centroids """
arcpy.AddField_management(fileInput,"Centroid_X","DOUBLE")
arcpy.AddField_management(fileInput,"Centroid_Y","DOUBLE")

arcpy.CalculateField_management(fileInput,"Centroid_X",
                                "!SHAPE.CENTROID.X!","Python_9.3")
arcpy.CalculateField_management(fileInput,"Centroid_Y",
                                "!SHAPE.CENTROID.Y!","Python_9.3")

"""
2. Get input for:
    a. Subsections
    b. Number of Parcels
    c. Total student population
3. Calculate kids/subsection = T
"""

currentSubsect = 0
while (currentSubsect < totalSubsects):

    """ Create bounding line G """
    boundline = arcpy.GetParameterAsText(1)
    #boundline = "boundline"
    dissolve = "dissolve"

    # Process: Dissolve
    arcpy.Dissolve_management(fileInput, dissolve, "", "", "MULTI_PART", "DISSOLVE_LINES")

    # Process: Polygon To Line
    arcpy.PolygonToLine_management(dissolve, boundline, "IDENTIFY_NEIGHBORS")

    # Output test
    mxd = arcpy.mapping.MapDocument("CURRENT")
    data_frame = arcpy.mapping.ListDataFrames(mxd, "*")[0]
    add_layer = arcpy.mapping.Layer(boundline)
    arcpy.mapping.AddLayer(data_frame,add_layer)

    # Remove intermediate files from memory
    arcpy.Delete_management(dissolve)

"""
    2. Find all bounding polygons, create list bndPoly
    3. Determine starting point based on our value for 'Southwestmost-ness'"""

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

"""
    Divide sections starting with startPoly
    While bndPoly != null:
        1. Calculate distance to all other polygons (dist[], queue would be good here)
        2. Sort dist[] in reverse order (lowest first)
        3. If subVal < T:
            Add from dist[] in order:
            if subVal + dist[curPoly] <= T:
                a. Add curPoly
                b. Flag added polygon
            else:
                if lastOver is False:
                    a. Add curPoly
                    b. Flag added polygon
                    c. lastOver = True
                else:
                    Do not add.
                    lastOver = False
        4. Once all polygons added, create bound for new subsection poly
        5. Set startPoly as next lowest distance (will cause null pointer on last runthrough)"""




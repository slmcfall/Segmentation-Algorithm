#-------------------------------------------------------------------------------
# Name:        Segmentaion Algorithm
# Purpose:
#
# Author:      erabrahams and slmcfall
#
# Created:     30/01/2015
# Copyright:   (c) erabrahams 2015, prestige worldwide
#-------------------------------------------------------------------------------

import arcpy
arcpy.env.overwriteOutput = 1
arcpy.env.workspace = "E:\Research\segmentation\Tests"

""" Parameters """
fileInput = arcpy.GetParameterAsText(0)
#totalSubsects = arcpy.GetParameterAsText(1)
totalSubsects = 1
totalTracts = 0
totalPop = 0


""" BEGIN SCRIPT """


""" 1. Calculate centroids """
# appends the column to the table
arcpy.AddField_management(fileInput,"Centroid_X","DOUBLE")
arcpy.AddField_management(fileInput,"Centroid_Y","DOUBLE")

# calculates the centroid values
arcpy.CalculateField_management(fileInput,"Centroid_X",
                                "!SHAPE.CENTROID.X!","Python_9.3")
arcpy.CalculateField_management(fileInput,"Centroid_Y",
                                "!SHAPE.CENTROID.Y!","Python_9.3")

""" 2. Calculate inputs """
# cursor is a one time thing..
rows = arcpy.SearchCursor(fileInput, "", "", "", "")
for row in rows:
    totalPop += row.getValue('TOTAL')
    totalTracts += 1

# print total population, number of tracts, subsections
arcpy.AddMessage("Number of Kids: " + str(totalPop))
arcpy.AddMessage("Number of Tracts" + str(totalTracts))
arcpy.AddMessage("Number of Subsections" + str(totalSubsects))

""" 3. Calculate T, kids/subsection """
kidsPerSS = totalPop/totalTracts

""" 4. Algorithm """
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

""" Distance to Other Polygons """

# original tract file to points
polyToPoint = arcpy.FeatureToPoint_management(fileinput, "fToShape.shp", "CENTROID")
# essentially a Select By Attribute step, creates new shapefile
startPoint = arcpy.FeatureClassToFeatureClass_conversion(polyToPoint, arcpy.env.workspace, "start.shp", "FID = 82")
# creates table with distances from origin/outermost point to all other centroids of original tract file
dist2Points = arcpy.PointDistance_analysis(startPoint, polyToPoint, "distances.dbf")

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




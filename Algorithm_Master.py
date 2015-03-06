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
arcpy.env.workspace = "in_memory"

""" Parameters """
fileInput = arcpy.GetParameterAsText(0)
#totalSubsects = arcpy.GetParameterAsText(1)
totalSubsects = 1
totalTracts = 0
totalPop = 0

parcelDict = {} # Master dictionary to hold parcel attributes
boundList = [] # To hold indices of bounding parcels.
toDistance = [] # List for distances from curPoint to other points

centroids = "centroids"
boundline = arcpy.GetParameterAsText(1)
#boundline = "boundline"
dissolve = "dissolve"

parcels = "parcels_lyr"        # Layer for all parcels
bndlineLayer = "bound_lyr"   # Layer for boundline
parcelPoints = "parcel_pnts" # Point features to perform distance calcs
curShape = "select_shape"
curParcel = "select_layer"
curPoint = "select_pnts"

distance = "dists" # A table that will hold point distances

# Calculate the "farthest distance" to the NE or SW.
def centroidPosition(row):
    x = row[2]
    y = row[3]
    return abs(x) + abs(y)

""" BEGIN SCRIPT """


""" 1. Calculate centroids """
# Append the column to the table
arcpy.AddField_management(fileInput,"Centroid_X","DOUBLE")
arcpy.AddField_management(fileInput,"Centroid_Y","DOUBLE")

# Calculate the centroid values
arcpy.CalculateField_management(fileInput,"Centroid_X",
                                "!SHAPE.CENTROID.X!","Python_9.3")
arcpy.CalculateField_management(fileInput,"Centroid_Y",
                                "!SHAPE.CENTROID.Y!","Python_9.3")

# Create point shapefile for centroids
arcpy.FeatureToPoint_management(fileInput, centroids, "CENTROID")

""" 2. Calculate inputs """
# cursor is a one time thing..
rows = arcpy.da.SearchCursor(fileInput, "TOTAL")
for row in rows:
    totalPop += row[0]
    totalTracts += 1

# print total population, number of tracts, subsections
arcpy.AddMessage("Number of Kids: " + str(totalPop))
arcpy.AddMessage("Number of Tracts: " + str(totalTracts))
arcpy.AddMessage("Number of Subsections: " + str(totalSubsects))

""" 3. Calculate T, kids/subsection """
kidsPerSS = totalPop/totalSubsects

""" 4. Algorithm """
currentSubsect = 0
while (currentSubsect < totalSubsects):

    """ Create bounding line G """
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


    """Find all bounding polygons, create list bndPoly.
       Determine starting point based on our value for 'Southwestmost-ness'"""

    # Create layers for parcels and boundline; find intersection
    arcpy.MakeFeatureLayer_management(fileInput, parcels)
    arcpy.MakeFeatureLayer_management(boundline, bndlineLayer)
    arcpy.SelectLayerByLocation_management(parcels, "INTERSECT", bndlineLayer, "", "NEW_SELECTION")

    # Create searchCursor to access attributes. ID = 0, Name = 1, X = 2, Y = 3.
    cursor = arcpy.da.SearchCursor(parcels, ["FID","NAME10","CENTROID_X","CENTROID_Y"])
    #for line in cursor:
    #    arcpy.AddMessage(line[1])
    #cursor.reset()

    # Iterate through boundary polygons to find the starting (farthest) parcel, and
    # create a queue of bound-poly indices. Furthermore, initialize master dict.
    high = 0
    highNdx = 0
    coord = 0
    for row in cursor:
        parcelDict[row[0]] = [None, None]
        coord = centroidPosition(row)
        boundList.append(row[0])
        arcpy.AddMessage("Index = " + str(row[0]) + ", coord = " + str(coord))
        if (coord > high):
            high = coord
            highNdx = row[0]
        arcpy.AddMessage("curHigh = " + str(high))

    arcpy.AddMessage("Starting position is shape number " + str(highNdx) + " with value " + str(high))

    # Grab starting polygon, export as new shape/layer
    curNdx = highNdx
    arcpy.FeatureClassToFeatureClass_conversion(parcels, arcpy.env.workspace, curShape, "FID = " + str(curNdx))
    arcpy.MakeFeatureLayer_management(curShape, curParcel)

    """ Distance to Other Polygons """

    # Select starting centroid, and find distance to all other centroids.
    arcpy.FeatureClassToFeatureClass_conversion(centroids, arcpy.env.workspace, curPoint, "FID = " + str(curNdx))
    arcpy.PointDistance_analysis(curPoint, centroids, distance)

    toDistance = []
    dists = arcpy.da.SearchCursor(distance, ["NEAR_FID","DISTANCE"])
    for row in dists:
        arcpy.AddMessage("Dist_To: " + str(row[0]) + " = " + str(row[1]))
        toDistance.append([row[1], row[0]])
    toDistance.sort()

    arcpy.AddMessage("\n")
    for i in toDistance:
        arcpy.AddMessage(i)

    currentSubsect += 1

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




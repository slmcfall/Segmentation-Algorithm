#-------------------------------------------------------------------------------
# Name:        Segmentaion Algorithm
# Purpose:
#
# Author:      erabrahams and slmcfall
#
# Created:     05/04/2015
#-------------------------------------------------------------------------------

import arcpy
arcpy.env.overwriteOutput = 1
arcpy.env.workspace = "in_memory"

# ---------- Parameters ---------- #

fileInput = arcpy.GetParameterAsText(0)

parcelDict = {} # Master dictionary to hold parcel attributes key is ID = (pop, subsect)
boundList = [] # To hold indices of bounding parcels.

centroids = "V:\erabrahams\\test_files\\test_centroids_all.shp"
#centroids = "centroids"
boundline = "V:\erabrahams\\test_files\\boundline_test.shp"
#boundline = "boundline"
dissolve = "V:\erabrahams\\test_files\dissolve_test.shp"
#dissolve = "dissolve"

parcels = "V:\erabrahams\\test_files\parcel_test.shp"
#parcels = "parcels_lyr"        # Layer for all parcels
bndlineLayer = "bound_lyr"   # Layer for boundline
parcelPoints = "parcel_pnts" # Point features to perform distance calcs
curShape = "select_shape"
curParcel = "select_layer"
curPoint = "select_pnts"
startPoint = "select_pnts_layer"

distance = "V:\erabrahams\\test_files\distance_test.dbf"
#distance = "dists" # A table that will hold point distances


# --------- Small Helper Functions --------- #

# Calculate "far-ness"
def centroidPosition(x, y):
    return abs(x) + abs(y)

def getNextParcel(toDistance):
    try:
        nextParcel = toDistance.pop(0)
        if nextParcel in boundList:
            boundList.remove(nextParcel)
        #arcpy.AddMessage("Next parcel is {ID}, with distance {dist}, subsection {sub}." .format(ID = nextParcel[1], dist = nextParcel[0], sub = nextParcel[3]))
        return nextParcel
    except IndexError:
        return None

# Find starting parceel for the next subsection. Picks closest bounding parcel
# to original starting parcel that is not yet in a subsection.
def findNextStart(toDistance):
    arcpy.AddMessage("boundlist: " + str(len(boundList)))
    for parcel in toDistance:
        ndx = parcel[1]
        if ndx in boundList:
            if parcelDict[ndx][0] == 0:
                boundList.remove(ndx)
                #arcpy.AddMessage("Next start chosen: {parc}, Dist to = {distance}" .format(parc = parcel[1], distance = parcel[0]))
                return parcel
                arcpy.AddMessage("boundlist: " + str(len(boundList)))
            else:
                boundList.remove(ndx)
    return None

# Intialize dictionary entries with (subsect = 0, population)
def dictInit():
    arcpy.MakeFeatureLayer_management(fileInput, parcels)
    dictInit = arcpy.da.SearchCursor(parcels, ["FID", "TOTAL"])
    for parcel in dictInit:
        parcelDict[parcel[0]] = [0, parcel[1]]

# --------- Workhorse Functions --------- #

def calculateCentroids():
    # Append the column to the table
    arcpy.AddField_management(fileInput,"Centroid_X","DOUBLE")
    arcpy.AddField_management(fileInput,"Centroid_Y","DOUBLE")

    # Calculate the centroid values
    arcpy.CalculateField_management(fileInput,"Centroid_X", "!SHAPE.CENTROID.X!","Python_9.3")
    arcpy.CalculateField_management(fileInput,"Centroid_Y", "!SHAPE.CENTROID.Y!","Python_9.3")

    # Create point shapefile for centroids
    arcpy.FeatureToPoint_management(fileInput, centroids, "CENTROID")

# Create layers for parcels and boundline; find intersection
def getBounds():
    arcpy.SelectLayerByAttribute_management(parcels, "NEW_SELECTION", "Subsection = 0")
    arcpy.Dissolve_management(parcels, dissolve, "", "", "MULTI_PART", "DISSOLVE_LINES")

    arcpy.PolygonToLine_management(dissolve, boundline, "IDENTIFY_NEIGHBORS")
    arcpy.MakeFeatureLayer_management(boundline, bndlineLayer)
    arcpy.SelectLayerByLocation_management(parcels, "INTERSECT", bndlineLayer, "", "NEW_SELECTION")

def findStart():
    boundary = arcpy.da.SearchCursor(parcels, ["FID","Centroid_X","Centroid_Y"]) # ID = 0, X = 1, Y = 2.

    # Iterate through boundary polygons to find the starting (farthest) parcel, and
    # create a queue of bound-poly indices. Furthermore, initialize master dict.
    high = 0
    highNdx = 0
    coord = 0

    for parcel in boundary:
        if parcelDict[parcel[0]][0] == 0:
            coord = centroidPosition(parcel[1], parcel[2])
            boundList.append(parcel[0])
            if (coord > high):
                high = coord
                highNdx = parcel[0]
        #arcpy.AddMessage("curHigh = " + str(high))

    #arcpy.AddMessage("Starting position is shape number " + str(highNdx) + " with value " + str(high) + "\n")

    # Grab starting polygon, export as new shape/layer, clear selection on
    # parcels; there is now a list of bounding parcels.
    curNdx = highNdx
    arcpy.FeatureClassToFeatureClass_conversion(parcels, arcpy.env.workspace, curShape, ' "FID" = ' + str(curNdx))
    arcpy.MakeFeatureLayer_management(curShape, curParcel)
    arcpy.SelectLayerByAttribute_management(parcels, "CLEAR_SELECTION")

    return curNdx

# Select starting centroid, and find distance to all other centroids.
def getDistanceToOthers(curNdx):
    #curPoint ="V:\erabrahams\\test_files\RANDOM.shp"
    #arcpy.AddMessage("CurNdx = {x}" .format(x = curNdx))

    arcpy.FeatureClassToFeatureClass_conversion(centroids, arcpy.env.workspace, curPoint, 'FID = {ndx}' .format(ndx = curNdx))

    #row = arcpy.da.SearchCursor(curPoint, ["ORIG_FID", "TOTAL"])
    #for val in row:
    #    arcpy.AddMessage("Val = " + str(val[0]) + " " + str(val[1]))

    arcpy.PointDistance_analysis(curPoint, centroids, distance)

    toDistance = []
    dists = arcpy.da.SearchCursor(distance, ["NEAR_FID","DISTANCE"])

    for row in dists:
        if parcelDict[row[0]][0] == 0:
            toDistance.append([row[1], row[0]])

    toDistance.sort()
    return toDistance


# ---------- MAIN ---------- #
def main():
    totalSubsects = int(arcpy.GetParameterAsText(1))
    totalPop = 0
    totalTracts = 0

    popfile = arcpy.da.SearchCursor(fileInput, "TOTAL")
    for parcel in popfile:
        totalPop += parcel[0]
        totalTracts += 1

    # Calculate T
    maxSubPop = totalPop/totalSubsects

    # Field will eventually hold subsect ID
    arcpy.AddField_management(fileInput, "Subsection", "SHORT")
    arcpy.CalculateField_management(fileInput, "Subsection", '0')

    # Print totals and number of subsections
    arcpy.AddMessage("Number of Children: " + str(totalPop))
    arcpy.AddMessage("Number of Tracts: " + str(totalTracts))
    arcpy.AddMessage("Number of Subsections: " + str(totalSubsects))
    arcpy.AddMessage("Max Subsection Population: " + str(maxSubPop) + "\n")

    # Initialize the subsection loop.
    dictInit()
    calculateCentroids()
    getBounds()
    curNdx = findStart()
    toDistance = getDistanceToOthers(curNdx)

    currentSubsect = 1
    lastSubsectSmall = False
    while (currentSubsect < totalSubsects):
        arcpy.AddMessage("Creating subsection " + str(currentSubsect) + "...")

        # When current boundList is exhausted, create a new inner bound.
        if len(boundList) == 0:
            arcpy.AddMessage("Boundlist exhausted, creating new boundline.")
            getBounds()
            curNdx = findStart()
            toDistance = getDistanceToOthers(curNdx)
            curPop = parcelDict[curNdx][1]

        # Otherwise, initialize the next starting point.
        else:
            curParcel = findNextStart(toDistance)
            curNdx = curParcel[1]
            curPop = parcelDict[curNdx][1]
            toDistance = getDistanceToOthers(curNdx)

        # Initialize loop
        subPop = 0

        # Populate nearby parcels with the current subsection ID.
        # First assign will be the starting parcel with a dist of 0.
        # lastSubsectSmall is a boolean check to alternate which subsections are "overpopulated" to maintain balance.
        while (subPop + curPop < maxSubPop) and curParcel is not None:
            arcpy.SelectLayerByAttribute_management(parcels, "NEW_SELECTION", "FID = " + str(curNdx))
            arcpy.CalculateField_management(parcels, "Subsection", currentSubsect, "Python_9.3")
            arcpy.SelectLayerByAttribute_management(parcels, "CLEAR_SELECTION")

            parcelDict[curNdx][0] = currentSubsect
            subPop += curPop
            if curNdx in boundList:
                boundList.remove(curNdx)

            curParcel = getNextParcel(toDistance)
            if curParcel is not None:
                curNdx = curParcel[1]
                curPop = parcelDict[curNdx][1]

        if curParcel is None:
            arcpy.AddMessage("Current parcel is None, for some reason...")

        # OVERfill the current subsection if last one was smaller than the threshold.
        arcpy.AddMessage("Last subsect was small: {sma}" .format(sma = lastSubsectSmall))

        if lastSubsectSmall:
            arcpy.AddMessage("Adding another parcel.")
            arcpy.SelectLayerByAttribute_management(parcels, "NEW_SELECTION", "FID = " + str(curNdx))
            arcpy.CalculateField_management(parcels, "Subsection", currentSubsect, "Python_9.3")
            arcpy.SelectLayerByAttribute_management(parcels, "CLEAR_SELECTION")

            parcelDict[curNdx][0] = currentSubsect
            subPop += curPop
            if curNdx in boundList:
                boundList.remove(curNdx)

            curParcel = getNextParcel(toDistance)
            if curParcel is not None:
                curNdx = curParcel[1]
                curPop = parcelDict[curNdx][1]

            lastSubsectSmall = False

        else:
            arcpy.AddMessage("Setting switch to True")
            lastSubsectSmall = True

        arcpy.AddMessage("Current population is {cur}, limit is {max}.\n" .format(cur = subPop, max = maxSubPop))
        currentSubsect += 1

    # For last subsection, grab all parcels not yet assigned.
    arcpy.SelectLayerByAttribute_management(parcels, "NEW_SELECTION", "Subsection = 0")
    arcpy.CalculateField_management(parcels, "Subsection", currentSubsect, "Python_9.3")
    arcpy.SelectLayerByAttribute_management(parcels, "CLEAR_SELECTION")

#arcpy.SelectLayerByAttribute_management(parcels, "NEW_SELECTION", "FID = " + str(curNdx))
#arcpy.CalculateField_management(parcels, "Subsection", currentSubsect, "Python_9.3")
#arcpy.SelectLayerByAttribute_management(parcels, "CLEAR_SELECTION")

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
main()




#-------------------------------------------------------------------------------
# Name:        Segmentaion Algorithm
# Purpose:
#
# Author:      erabrahams and slmcfall
#
# Created:     05/04/2015
#-------------------------------------------------------------------------------

import arcpy, time
arcpy.env.overwriteOutput = 1
arcpy.env.workspace = "in_memory"

# ---------- Parameters ---------- #

parcelDict = {} # Master dictionary to hold parcel attributes key is ID = (pop, subsect)
#boundList = [] # To hold indices of bounding parcels.

centroidPoints = "V:\erabrahams\\test_files\\centroidPoints.shp"
centroids = "V:\erabrahams\\test_files\\centroids.shp"

#centroids = "centroids"
#boundline = "V:\erabrahams\\test_files\\boundline_test.shp"
#boundline = "boundline"
dissolve = "V:\erabrahams\\test_files\dissolve.shp"
#dissolve = "dissolve"

parcels = "V:\erabrahams\\test_files\parcels.shp"
#parcels = "parcels_lyr"        # Layer for all parcels
#bndlineLayer = "bound_lyr"   # Layer for boundline
#parcelPoints = "parcel_pnts" # Point features to perform distance calcs

curPoint = "curPoint"

distance = "V:\erabrahams\\test_files\distance_test.dbf"
distance = "dist" # A table that will hold point distances


# --------- Small Helper Functions --------- #

# Calculate "far-ness"
def centroidPosition(x, y):
    return abs(x) + abs(y)

def mapInit(fileInput):
    arcpy.MakeFeatureLayer_management(fileInput, parcels)

# Intialize dictionary entries with (subsect = 0, population)
def dictInit():
    dictInit = arcpy.da.SearchCursor(parcels, ["FID", "TOTAL"])
    for parcel in dictInit:
        parcelDict[parcel[0]] = [0, parcel[1]]

def updateSubsections():
    subsectCursor = arcpy.da.UpdateCursor(parcels, ["FID", "Subsection"])
    for parcel in subsectCursor:
        if parcel[1] == 0:
            parcel[1] = parcelDict[parcel[0]][0]
            subsectCursor.updateRow(parcel)

def getNextParcel(toDistance, boundList):
    try:
        nextParcel = toDistance.pop(0)
        if nextParcel in boundList:
            boundList.remove(nextParcel)
        return nextParcel
    except IndexError:
        return None

# Find starting parceel for the next subsection. Picks closest bounding parcel
# to original starting parcel that is not yet in a subsection.
def findNextStart(toDistance, boundList):
    for parcel in toDistance:
        ndx = parcel[1]
        if ndx in boundList:
            if parcelDict[ndx][0] == 0:
                boundList.remove(ndx)
                return parcel[1]
            else:
                boundList.remove(ndx)
    return None


# --------- Workhorse Functions --------- #

def calculateCentroids(fileInput):
    arcpy.AddMessage("Calculating centroids...")

    arcpy.FeatureToPoint_management(fileInput, centroidPoints, "CENTROID")
    arcpy.MakeFeatureLayer_management(centroidPoints, centroids)

# Create layers for parcels and boundline; find intersection
def getBounds():
    arcpy.AddMessage("\t\tDetermining bound parcels...")

    #updateSubsections()

    arcpy.SelectLayerByAttribute_management(parcels, "NEW_SELECTION", '"Subsection" = 0')
    arcpy.Dissolve_management(parcels, dissolve, "", "", "MULTI_PART", "DISSOLVE_LINES")

    #arcpy.PolygonToLine_management(dissolve, boundline, "IDENTIFY_NEIGHBORS")
    #arcpy.MakeFeatureLayer_management(boundline, bndlineLayer)

    arcpy.SelectLayerByLocation_management(parcels, "BOUNDARY_TOUCHES", dissolve, "", "NEW_SELECTION")

# Iterate through boundary polygons to find the starting (farthest) parcel, and create a list of bound-poly indices.
def findStart():
    arcpy.AddMessage("\tFinding starting parcel...")

    getBounds()    # Select bounding parcels
    boundList = []

    high, highNdx, coord = 0, 0, 0
    boundary = arcpy.da.SearchCursor(parcels, ["FID", "SHAPE@XY"])
    for parcel in boundary:
        if parcelDict[parcel[0]][0] == 0:
            coord = centroidPosition(parcel[1][0], parcel[1][1])
            boundList.append(parcel[0])
            if (coord > high):
                high = coord
                highNdx = parcel[0]

    #arcpy.AddMessage("Starting position is shape number " + str(highNdx) + " with value " + str(high) + "\n")

    # Grab starting polygon, export as new shape/layer, clear selection on
    # parcels; there is now a list of bounding parcels.
    curNdx = highNdx
    #curShape = "select_shape"
    #curParcel = "select_layer"

    #arcpy.FeatureClassToFeatureClass_conversion(parcels, arcpy.env.workspace, curShape, ' "FID" = ' + str(curNdx))
    #arcpy.MakeFeatureLayer_management(curShape, curParcel)
    arcpy.SelectLayerByAttribute_management(parcels, "CLEAR_SELECTION")

    return curNdx, boundList

# Select starting centroid, and find distance to all other centroids.
def getDistanceToOthers(curNdx):
    arcpy.AddMessage("\tCalculating distances...")

    arcpy.FeatureClassToFeatureClass_conversion(centroids, arcpy.env.workspace, curPoint, '"FID" = {ndx}'.format(ndx = curNdx))
    arcpy.PointDistance_analysis(curPoint, centroids, distance)

    toDistance = []
    dists = arcpy.da.SearchCursor(distance, ["NEAR_FID","DISTANCE"])

    for row in dists:
        if parcelDict[row[0]][0] == 0:
            toDistance.append([row[1], row[0]])

    toDistance.sort()
    return toDistance


# ---------- Main function body ---------- #
def makeDistricts(fileInput, totalSubsects):
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
    arcpy.AddMessage("\nNumber of Children: " + str(totalPop))
    arcpy.AddMessage("Number of Tracts: " + str(totalTracts))
    arcpy.AddMessage("Number of Subsections: " + str(totalSubsects))
    arcpy.AddMessage("Max Subsection Population: " + str(maxSubPop) + "\n")

    # Initialize the subsection loop.
    mapInit(fileInput)
    calculateCentroids(fileInput)
    dictInit()

    boundList = []
    currentSubsect = 1
    lastSubsectSmall = False
    while (currentSubsect < totalSubsects):
        arcpy.AddMessage("Creating subsection {num}..." .format(num = currentSubsect))

        # When current boundList is exhausted, create a new inner bound.
        if len(boundList) == 0:
            arcpy.AddMessage("\tBoundlist empty, creating new boundline.")

            curNdx, boundList = findStart()
            curPop = parcelDict[curNdx][1]

            toDistance = getDistanceToOthers(curNdx)
            curParcel = findNextStart(toDistance, boundList)  # Assign curParcel and remove start from lists.


        # Otherwise, initialize the next starting point.
        else:
            startNdx = findNextStart(toDistance, boundList)
            toDistance = getDistanceToOthers(startNdx)

            curParcel = getNextParcel(toDistance, boundList)
            curNdx = curParcel[1]
            curPop = parcelDict[curNdx][1]

        # Initialize loop
        subPop = 0
        arcpy.AddMessage("\tAdding parcels...")

        # Populate nearby parcels with the current subsection ID.
        # First assign will be the starting parcel with a dist of 0.
        # lastSubsectSmall is a boolean check to alternate which subsections are "overpopulated" to maintain balance.
        while ((subPop + curPop) < maxSubPop) and curParcel is not None:

            parcelDict[curNdx][0] = currentSubsect
            subPop += curPop
            if curNdx in boundList:
                boundList.remove(curNdx)

            curParcel = getNextParcel(toDistance, boundList)
            if curParcel is not None:
                curNdx = curParcel[1]
                curPop = parcelDict[curNdx][1]

        # OVERfill the current subsection if last one was smaller than the threshold.
        # + (totalPop/totalTracts)
        if lastSubsectSmall:
            while subPop < maxSubPop:
                parcelDict[curNdx][0] = currentSubsect
                subPop += curPop
                if curNdx in boundList:
                    boundList.remove(curNdx)

                curParcel = getNextParcel(toDistance, boundList)
                if curParcel is not None:
                    curNdx = curParcel[1]
                    curPop = parcelDict[curNdx][1]

            lastSubsectSmall = False

        else:
            lastSubsectSmall = True

        arcpy.AddMessage("Subsection {num} created.\n" .format(num = currentSubsect))
        updateSubsections()
        arcpy.RefreshActiveView()
        currentSubsect += 1

    # For last subsection, grab all parcels not yet assigned.
    arcpy.AddMessage("Creating subsection {num} by adding remaining parcels..." .format(num = currentSubsect))

    #arcpy.SelectLayerByAttribute_management(parcels, "NEW_SELECTION", "Subsection = 0")
    #arcpy.CalculateField_management(parcels, "Subsection", currentSubsect, "Python_9.3")
    #arcpy.SelectLayerByAttribute_management(parcels, "CLEAR_SELECTION")

    for parcel in parcelDict.values():
        if parcel[0] == 0:
            parcel[0] = currentSubsect

    arcpy.AddMessage("Subsection {num} created.\n" .format(num = currentSubsect))

    arcpy.AddMessage("Updating subsections...\n")
    updateSubsections()
    arcpy.RefreshActiveView()

def main():
    fileInput = arcpy.GetParameterAsText(0)
    subsections = int(arcpy.GetParameterAsText(1))
    makeDistricts(fileInput, subsections)

main()




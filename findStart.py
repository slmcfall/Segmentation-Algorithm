#-------------------------------------------------------------------------------
# Name:        findStart
# Purpose:
#
# Author:      erabrahams
#
# Created:     05/02/2015
# Copyright:   (c) erabrahams 2015
#-------------------------------------------------------------------------------

import arcpy
arcpy.env.workspace = "in_memory"

fileInput = arcpy.GetParameterAsText(0)
bndLine = arcpy.GetParameterAsText(1)

parcels = "parcels_lyr"        # Layer for all parcels
bnd_line_layer = "bound_lyr"   # Layer for boundline
curShape = "tract"
cur_parcel = "cur_layer"
parcelPoints = "parcel_pnts" # Point features to perform distance calcs
curPoints = "cur_pnts"

boundList = [] # To hold indices of bounding parcels.
distance = "dists" # A table that will hold point distances

# Calculate the "farthest distance" to the NE or SW.
def centroidPosition(row):
    x = row[2]
    y = row[3]
    return abs(x) + abs(y)

# Create layers for parcels and boundline; find intersection
arcpy.MakeFeatureLayer_management(fileInput, parcels)
arcpy.MakeFeatureLayer_management(bndLine, bnd_line_layer)
arcpy.SelectLayerByLocation_management(parcels, "INTERSECT", bnd_line_layer, "", "NEW_SELECTION")

# Create searchCursor to access attributes. ID = 0, Name = 1, X = 2, Y = 3.
cursor = arcpy.da.SearchCursor(parcels, ["FID","NAME10","CENTROID_X","CENTROID_Y"])
for line in cursor:
    arcpy.AddMessage(line[1])
cursor.reset()

# Iterate through boundary polygons to find the starting (farthest) parcel, and
# create a queue of bound-poly indices.
high = 0
highNdx = 0
coord = 0
for row in cursor:
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
arcpy.SelectLayerByAttribute_management(parcels, "NEW_SELECTION", ' "FID" =  ' + str(curNdx))
arcpy.CopyFeatures_management(parcels,curShape)
arcpy.MakeFeatureLayer_management(curShape, cur_parcel)
arcpy.SelectLayerByAttribute_management(parcels, "CLEAR_SELECTION")

# Create centroid points and find distances
for ndx in parcels:
    arcpy.Point()

"""mxd = arcpy.mapping.MapDocument("CURRENT")
data_frame = arcpy.mapping.ListDataFrames(mxd, "*")[0]

add_layer = arcpy.mapping.Layer(parcels)
arcpy.mapping.AddLayer(data_frame,add_layer)
add_layer = arcpy.mapping.Layer(cur_parcel)
arcpy.mapping.AddLayer(data_frame,add_layer)"""






#-------------------------------------------------------------------------------
# Name:        Segmentaion Algorithm - Plan
# Purpose:
#
# Author:      erabrahams
#
# Created:     30/01/2015
# Copyright:   (c) erabrahams 2015
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import arcpy


fileInput = arcpy.GetParameterAsText(0)
subSects = arcpy.GetParameterAsText(1)
tracts = 0
totalPop = 0

#calculate total population
"""for tract in fileInput:
    ##get pop val, += to totalPop"""

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

While curSubsection < desiredSubsection:

    1. Create bounding line G
    # Local variables:
    bounds_test_shp = Regional_Counties
    boundline_test_shp = bounds_test_shp

    # Process: Dissolve
    arcpy.Dissolve_management(Regional_Counties, bounds_test_shp, "", "", "MULTI_PART", "DISSOLVE_LINES")

    # Process: Polygon To Line
    arcpy.PolygonToLine_management(bounds_test_shp, boundline_test_shp, "IDENTIFY_NEIGHBORS")



    2. Find all bounding polygons, create list bndPoly
    3. Determine starting point based on our value for "Southwestmost-ness"

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




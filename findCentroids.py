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

arcpy.AddField_management(fileInput,"Centroid_X","DOUBLE")
arcpy.AddField_management(fileInput,"Centroid_Y","DOUBLE")

arcpy.CalculateField_management(fileInput,"Centroid_X",
                                "!SHAPE.CENTROID.X!","Python_9.3")
arcpy.CalculateField_management(fileInput,"Centroid_Y",
                                "!SHAPE.CENTROID.Y!","Python_9.3")

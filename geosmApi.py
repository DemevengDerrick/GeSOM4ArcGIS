# import the HTTP request module : requests
import requests
#import json
import arcpy
# overwrite any existing output name
arcpy.env.overwriteOutput = True

#-------------------------------------------------------------------------------Tool parameters----------------------------------------------------------------------------
location = arcpy.GetParameterAsText(0)
theme = arcpy.GetParameterAsText(1)
layer = arcpy.GetParameterAsText(2)
outputFolder = arcpy.GetParameterAsText(3)
outputFcName = arcpy.GetParameterAsText(4)
#location = "togo"
#id_themes = arcpy.GetParameterAsText(1)
#id_objects = arcpy.GetParameterAsText(2)


#arcpy.env.wprkspace = r"D:\Penn State\GEOG485\final_project"
#spatial reference
sr = arcpy.SpatialReference(4326)
#----------------------------------------------------------------------------------------Get themes ------------------------------------------------------------------
# def a funtion that return a list of all themes in the catalogue
def themes(location):
    themeTable = {}
    subthemTable = {}
    nameMaping = {}
    response = requests.get("https://api.geosm.org/api/v1/" + location +"/themes")
    # check the connection status
    if response.status_code == 200:
        # check the content-type and make sure it is application/json
        if response.headers['content-type']=="application/json":
            # Get the body of the request as a json
            jsonResponse = response.json()
            # get the themes of the json response
            themes = jsonResponse['themes']
            # loop through the theme and get the table of correspondance between names of themes and thiers ids
            for theme in themes:
                themeTable[theme['name_theme']] = theme['id_theme']
                subThemes = theme['sub_themes']
                # get the sub-themes
                for subTheme in subThemes:
                    layers = subTheme['layers']
                    for layer in layers:
                        nameMaping[layer['id']] = layer['name']
                        # check if a theme exist already and create it if not
                        if theme['id_theme'] not in subthemTable:
                            subthemTable[theme['id_theme']] =[layer['id']]
                        else:
                            subthemTable[theme['id_theme']].append(layer['id'])
                            
        else:
            arcpy.AddMessage("The content type is not 'Apllication/json'")
            return []
    else:
        arcpy.AddMessage("Connection problem occured. status :" + response.status_code)
        return []
    
    return [themeTable, subthemTable, nameMaping]

#theme = themes("senegal")[0]
#
#id_theme = themes("uganda")[0][theme]
#
#layers = themes("uganda")[1][id_theme]


#arcpy.AddMessage(themes)

#print(theme)

# ------------------------------------------------------------------------------Get data from API---------------------------------------------------------------------
# funtion to query data in a particular location
def data(location, id_theme, id_object):
    #request to API
    #print('https://api.geosm.org/api/v1/'+location+'?'+'id_theme='+str(id_theme)+'&id='+id_object+"'")
    response = requests.get('https://api.geosm.org/api/v1/'+location+'?'+'id_theme='+str(id_theme)+'&id='+id_object)
    # check the connection status
    if response.status_code == 200:
        # check the content-type and make sure it is application/json
        if response.headers['content-type']=="application/json":
            # Get the body of the request as a json
            #json response
            jsonResponse = response.json()
            #return json dictionary
            return jsonResponse
        else:
            arcpy.AddMessage("The content-type is not 'application/json'")
            return []
    else:
        arcpy.AddMessage("Connection problem occured. status :" + response.status_code)
        return[]

# data() call

# -----------------------------------------------------------------------------Create point features -----------------------------------------------------------------
#outputName = "points.shp"
def createPoint(data, outputFolder, outputName, sr):
    # coordinate list
    row_data = []
    # loop through the data and append it to the row_data list
    for point in data:
        name = point['properties']['name']
        amenity = point['properties']['amenity']
        coordinates = point['geometry']['coordinates']
        
        if name == None:
            if amenity == None:
                name = ""
                amenity = ""
                row_data.append(((coordinates[0], coordinates[1]),amenity,name))
            else:
                name = ""
                row_data.append(((coordinates[0], coordinates[1]),amenity,name))
        elif amenity == None:
            if name == None:
                name = ""
                amenity = ""
                row_data.append(((coordinates[0], coordinates[1]),amenity,name))
            else:
                amenity = ""
                row_data.append(((coordinates[0], coordinates[1]),amenity,name))
        else:
            row_data.append(((coordinates[0], coordinates[1]),amenity,name))
        #point['geometry']['type'])
        #print(point['properties']['amenity'])
        #print(point['properties']['name'])
        
    #print(coords)
    # create a point feature class
    shp = arcpy.CreateFeatureclass_management(outputFolder, outputName,"POINT","","","",sr)
    # add an amenity field
    arcpy.management.AddField(shp,'amenity','TEXT',255,"","","","NULLABLE")
    # add a name field
    arcpy.management.AddField(shp,'Name','TEXT',255,"","","","NULLABLE")
    # create an insert cursor on the feature and add data
    with arcpy.da.InsertCursor(shp,("SHAPE@XY", 'amenity', 'Name')) as cursor:
        # loop through the data and add to the cursor
        for row in row_data:
            # check for null values
            #print(type(row[2]))
            cursor.insertRow(row)
            
    addLayerToMap(shp)
    
    del cursor
    
#createPoint(data, outputName)
#---------------------------------------------------------------------- Create line feature -----------------------------------------------------------------------------
#print(data)
def createPolyline(data, outputFolder, outputName, sr):
    row_data = []
    
    for point in data:
        
        name = point['properties']['name']
        amenity = point['properties']['amenity']
        coordinates = point['geometry']['coordinates']
        
        vertices = []
        
        for coord in coordinates:
            vertices.append((coord[0],coord[1]))
        
        if name == None:
            if amenity == None:
                name = ""
                amenity = ""
                row_data.append((vertices,amenity,name))
            else:
                name = ""
                row_data.append((vertices,amenity,name))
        elif amenity == None:
            if name == None:
                name = ""
                amenity = ""
                row_data.append((vertices,amenity,name))
            else:
                amenity = ""
                row_data.append((vertices,amenity,name))
        else:
            row_data.append((vertices,amenity,name))
    
    #print(row_data[0])
        
    shp = arcpy.CreateFeatureclass_management(outputFolder, outputName,"POLYLINE","","","",sr)
    # add an amenity field
    arcpy.management.AddField(shp,'amenity','TEXT',255,"","","","NULLABLE")
    # add a name field
    arcpy.management.AddField(shp,'Name','TEXT',255,"","","","NULLABLE")
    # create an insert cursor on the feature and add data
    with arcpy.da.InsertCursor(shp,("SHAPE@","amenity", "Name")) as cursor:
        # loop through the data and add to the cursor
        for row in row_data:
            # check for null values
            #print(type(row[2]))
            #print(row[2])
            cursor.insertRow((row[0],row[1],row[2]))
            
    addLayerToMap(shp)
    
    del cursor

#createPolyline(data, outputName)  
#------------------------------------------------------------------Create polygones --------------------------------------------------------------------------------------

def createPolygon(data, outputFolder, outputName, sr):

    row_data = []
    for point in data:
        
        name = point['properties']['name']
        amenity = point['properties']['amenity']
        coordinates = point['geometry']['coordinates']
        geomType = point['geometry']['type']
        
        if geomType == 'Polygon':
            
            #pt = arcpy.Point()
            #array = arcpy.Array()
            
            for coord in coordinates:
                pt = arcpy.Point()
                array = arcpy.Array()
                for cor in coord:

                    pt.X = float(cor[0])
                    pt.Y = float(cor[1])
                    array.add(pt)
    
                polygon = arcpy.Polygon(array)
                        #print(cor)
                
                if name == None:
                    if amenity == None:
                        name = ""
                        amenity = ""
                        row_data.append((polygon,amenity,name))
                    else:
                        name = ""
                        row_data.append((polygon,amenity,name))
                elif amenity == None:
                    if name == None:
                        name = ""
                        amenity = ""
                        row_data.append((polygon,amenity,name))
                    else:
                        amenity = ""
                        row_data.append((polygon,amenity,name))
                else:
                    row_data.append((polygon,amenity,name))
                
        elif geomType == 'MultiPolygon':
            
#            pt = arcpy.Point()
#            array = arcpy.Array()
            
            for coord in coordinates:
                pt = arcpy.Point()
                array = arcpy.Array()
                for cor in coord:
                    for c in cor:
                        pt.X = float(c[0])
                        pt.Y = float(c[1])
                        array.add(pt)
    
                polygon = arcpy.Polygon(array)
                        #print(cor)
                
                if name == None:
                    if amenity == None:
                        name = ""
                        amenity = ""
                        row_data.append((polygon,amenity,name))
                    else:
                        name = ""
                        row_data.append((polygon,amenity,name))
                elif amenity == None:
                    if name == None:
                        name = ""
                        amenity = ""
                        row_data.append((polygon,amenity,name))
                    else:
                        amenity = ""
                        row_data.append((polygon,amenity,name))
                else:
                    row_data.append((polygon,amenity,name))
    
    shp = arcpy.CreateFeatureclass_management(outputFolder, outputName,"POLYGON","","","",sr)
    # add an amenity field
    arcpy.management.AddField(shp,'amenity','TEXT',255,"","","","NULLABLE")
    # add a name field
    arcpy.management.AddField(shp,'Name','TEXT',255,"","","","NULLABLE")
    # loop through the data and add to the cursor
    with arcpy.da.InsertCursor(shp,("SHAPE@","amenity", "Name")) as cursor:
            # loop through the data and add to the cursor
            for row in row_data:
                # check for null values
                cursor.insertRow((row))
                
    addLayerToMap(shp)
    
    del cursor
    
#createPolygon(data)
#
#arcpy.AddMessage("Sucessfully executed :)")
#-----------------------------------------------------------------------------Add Feature to CURRENT Map---------------------------------------------------------------
def addLayerToMap(feature):
    aprx = arcpy.mp.ArcGISProject("CURRENT")
    m =  aprx.listMaps()[0]
    m.addDataFromPath(feature)

#-----------------------------------------------------------------------------Execution--------------------------------------------------------------------------------
countryDict = {"South Africa":'afs', "Burkina-Faso":'bfa',"Cameroon":'cameroun',
               "Ivory Coast":'ci', "Ethiopia":'ethiopia', "Ghana":'ghana', "Kenya":'kenya',
               "Libya":'libya', "Madagascar":'madagascar', "Mali":'mali', "Morocco":'maroc',
               "Niger":'niger', "Nigeria":'nigeria', "Uganda":'uganda', "DRC":'rdc',
               "Rwanda":'rwanda', "Senegal":'senegal', "Tanzania":'tanzania', "Togo":'togo',
               "Zambia":'zambia', "Zimbabwe":'zimbabwe'}

location = countryDict[location]

id_theme = themes(location)[0][theme]

subtheme = themes(location)[2]

for key, value in subtheme.items():
    if layer == value:
        lyr = key
        
#arcpy.AddMessage(id_theme)
#arcpy.AddMessage(lyr)
        
data = data(location, id_theme, lyr)
arcpy.AddMessage(data)

if len(data) != 0:
    if len(data['results']['data']['features']) != 0:
        
        data = data['results']['data']['features']
        #print(data)
        
        for feature in data:
            geomType = feature['geometry']['type']
            arcpy.AddMessage('Geometry Type = '+geomType)
            #print(geomType)
        
        if geomType == 'Point':
            
            createPoint(data, outputFolder, outputFcName, sr)
        
        elif geomType == 'LineString':
            
            createPolyline(data, outputFolder, outputFcName, sr)
        
        else:
            
            createPolygon(data, outputFolder, outputFcName, sr)
            
        arcpy.AddMessage("Sucessfully processed")
    else:
        arcpy.AddMessage('No data found')
else:
    arcpy.AddMessage('No data found')

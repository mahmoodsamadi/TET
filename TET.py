import arcpy
import sys, string, os
from arcpy.sa import *

arcpy.env.overwriteOutput = True

inputdem = arcpy.GetParameterAsText(0)
outputDIR = arcpy.GetParameterAsText(1)
convalue = arcpy.GetParameterAsText(2)
TE_threshold = float(arcpy.GetParameterAsText(3))
simplify = "false"

distance = 30000.0
arcpy.env.workspace = outputDIR

inputlines_raw = os.path.join(outputDIR, 'inputlines.shp')
inputlines = os.path.join(outputDIR, 'inputlines_m.shp')



for dir in ['rasters','reservoirs','temp']:
	try:
		os.makedirs(os.path.join(outputDIR, dir))
	except:
		pass


#mydef############################################################################
def my_fields(table, wildcard=None, fieldtype=None):
    fields = arcpy.ListFields(table, wildcard, fieldtype)
    nameList = []
    for field in fields:
        nameList.append(field.name)
    return nameList

#mydef############################################################################
def my_addfield(inFeatures, fieldname, type="n"):
	types={"s":"TEXT","n":"DOUBLE"}
	if fieldname in my_fields(inFeatures):
		return False
	else:
		arcpy.AddField_management(inFeatures, fieldname, types[type])
		return True


#mydef############################################################################
def my_field2list(infc,field):
	list = []
	for row in arcpy.da.SearchCursor(infc, [field]):
		list.append(row[0])
	return list


def my_field2dic(infc,key_field,value_field):
	mydic = {}
	for row in arcpy.da.SearchCursor(infc, [key_field,value_field]):
		mydic.setdefault(row[0], []).append(row[1])
	return mydic





sp1 = "PROJCS['Iranlambert',GEOGCS['GCS_WGS_1984',DATUM['D_WGS_1984',SPHEROID['WGS_1984',6378137.0,298.257223563]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]],PROJECTION['Lambert_Conformal_Conic'],PARAMETER['False_Easting',0.0],PARAMETER['False_Northing',0.0],PARAMETER['Central_Meridian',54.0],PARAMETER['Standard_Parallel_1',30.0],PARAMETER['Standard_Parallel_2',36.0],PARAMETER['Scale_Factor',1.0],PARAMETER['Latitude_Of_Origin',24.0],UNIT['Meter',1.0]]"
sp2 = "PROJCS['Iran_lambert_my',GEOGCS['GCS_WGS_1984',DATUM['D_WGS_1984',SPHEROID['WGS_1984',6378137.0,298.257223563]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]],PROJECTION['Lambert_Conformal_Conic'],PARAMETER['False_Easting',2000000.0],PARAMETER['False_Northing',40000.0],PARAMETER['Central_Meridian',54.0],PARAMETER['Standard_Parallel_1',30.0],PARAMETER['Standard_Parallel_2',36.0],PARAMETER['Scale_Factor',1.0],PARAMETER['Latitude_Of_Origin',24.0],UNIT['Meter',1.0]]"
sp3 = arcpy.SpatialReference(32639)
sp4 = arcpy.SpatialReference(4326)
def area_(fc):
	area = 0
	#for row in arcpy.da.SearchCursor(fc, ["OID@", "SHAPE@AREA"], spatial_reference=sp1):
	for row in arcpy.da.SearchCursor(fc, ["OID@", "SHAPE@AREA"]):
		area += row[1]
	return area



def updater(shp, fieldnames =["FID","start"],values =[1,"22t"]):
	with arcpy.da.UpdateCursor(shp,fieldnames) as cursor:
		for row in cursor:
			if row[0] == values[0]:
				row[1] = values[1]
				cursor.updateRow(row)
#end def############
try:
	demfill = Fill(inputdem)
except:
	arcpy.env.parallelProcessingFactor = "90"
	demfill = Fill(inputdem)





outFlowDirection = FlowDirection(demfill, "FORCE", "")
outFlowDirection.save(outputDIR + "\\rasters\\f_DIRECTION")
inFlowDirection = outputDIR + "\\rasters\\f_DIRECTION"

outFlowAccumulation = FlowAccumulation(outFlowDirection, "", "INTEGER")
outFlowAccumulation.save(outputDIR + "\\rasters\\f_Accumul")

vall = outFlowAccumulation > int(convalue)
streams = Con(vall , 1, "")
streams.save(outputDIR + "\\rasters\\river")

outStreamOrder = StreamOrder(streams, outFlowDirection, "STRAHLER")
outStreamOrder.save(outputDIR + "\\rasters\\inputlines")


if simplify == "true":
  simplifying = "SIMPLIFY"
else:
  simplifying = "NO_SIMPLIFY"

StreamToFeature(outStreamOrder, outFlowDirection, inputlines_raw, simplifying)
#arcpy.Project_management(inputlines_raw, inputlines, out_coordinate_system)
inputlines = inputlines_raw


#end river############

tin = os.path.join(outputDIR, 'rasters\\tin')
outName_point = '_point.shp'
outName_temp = 'temp\\temp.shp'
outName_temp = os.path.join(outputDIR, outName_temp)
contour_temp1 = os.path.join(outputDIR, 'temp\\contour_temp.shp')
contour_temp_pol1 = os.path.join(outputDIR, 'temp\\contour_temp_pol.shp')
outwtrshd = os.path.join(outputDIR, 'rasters\\outwtrshd')
outwtrshd_poly1 = os.path.join(outputDIR, 'temp\\outwtrshd_poly.shp')
contour_poly1 = os.path.join(outputDIR, 'temp\\contour_poly.shp')
result_poly1 = os.path.join(outputDIR, 'temp\\result_poly.shp')
result_poly_single1 = os.path.join(outputDIR, 'temp\\result_poly_single.shp')
fc = os.path.join(outputDIR, 'temp\\z.shp')



arcpy.RasterTin_3d(inputdem,tin,"1","#","1")


point_file = os.path.join(outputDIR, outName_point)
arcpy.CreateFeatureclass_management(outputDIR, outName_point, "POINT", "", "DISABLED", "DISABLED", inputlines)

my_addfield(point_file, 'orderno', type="n")
my_addfield(point_file, 'unique_id', type="n")
my_addfield(point_file, 'basin_area', type="n")
my_addfield(point_file, 'dam_area', type="n")
my_addfield(point_file, 'TE', type="n")


#for row in arcpy.da.SearchCursor(inputlines, ["SHAPE@","GRID_CODE"], spatial_reference=out_coordinate_system):
for row in arcpy.da.SearchCursor(inputlines, ["SHAPE@","GRID_CODE"]):
  line_geom = row[0]
  length = float(line_geom.length)
  count = distance
  while count <= length:

    #if count != distance:	# skip first vertex
    point = line_geom.positionAlongLine(count, False)
    cursor = arcpy.da.InsertCursor(point_file, ("SHAPE@","orderno"))
    cursor.insertRow((point,row[1]))
    del cursor
    count += distance


arcpy.CalculateField_management(point_file,"unique_id","!FID!","PYTHON_9.3","#")

inRasterList = [[inputdem, "myrasterv"]]
ExtractMultiValuesToPoints(point_file, inRasterList, "BILINEAR")

raster_list = []
field = ["myrasterv"]
with arcpy.da.SearchCursor(point_file,field) as cursor:
		for row in cursor:
			raster_list.append(row[0])

########	end point creation









arcpy.AddMessage(raster_list)




previous_area = 0.0
mydic = {}
fidinfo = {}

orders = list(set(my_field2list(point_file, 'orderno')))
arcpy.AddMessage('%s%s'%('list of point orders: ',orders))

number_of_all = len(my_field2list(point_file, 'orderno'))
noo = 0


alll = []
last_merged_dam = ''
last_dam = ''
merged = os.path.join(outputDIR, 'temp\\merged.shp')

arcpy.AddMessage('------start looping all points-------')
for order in sorted(orders):
	order_shp_file = os.path.join(outputDIR, 'temp\\ord_%s.shp'%int(order))
	arcpy.AddMessage('%s%s'%('order: ', order))
	arcpy.Select_analysis(point_file, order_shp_file, "\"orderno\" = %s"%order)

	with arcpy.da.SearchCursor(order_shp_file,["SHAPE@","unique_id", 'orderno']) as cursor:
	   for row in cursor:
		noo +=1
		arcpy.AddMessage("-"*15)
		arcpy.AddMessage("%s/%s"%(noo,number_of_all))
		unique_id = int(row[1])
		contour_poly = contour_poly1.replace(".shp","_%s.shp"%unique_id)
		outwtrshd_poly = outwtrshd_poly1.replace(".shp","_%s.shp"%unique_id)
		result_poly = result_poly1.replace(".shp","_%s.shp"%unique_id)
		result_poly_single = result_poly_single1.replace(".shp","_%s.shp"%unique_id)

		#arcpy.AddMessage(raster_list[unique_id])
		arcpy.Select_analysis(point_file, outName_temp, "\"FID\" = %s"%unique_id)

		contour = Con( Raster(inputdem) < raster_list[unique_id] + 5, 1)
		arcpy.RasterToPolygon_conversion(contour, contour_poly, "NO_SIMPLIFY","VALUE")

		outWatershed = Watershed(inFlowDirection, outName_temp,"myrasterv")
		outWatershed.save(outwtrshd)
		arcpy.RasterToPolygon_conversion(outwtrshd, outwtrshd_poly, "NO_SIMPLIFY","VALUE")

		arcpy.Clip_analysis(outwtrshd_poly, contour_poly, result_poly)
		arcpy.MultipartToSinglepart_management(result_poly,result_poly_single)

		mem_point = arcpy.MakeFeatureLayer_management(result_poly_single, "parcel_lyr")
		Selection = arcpy.SelectLayerByLocation_management(mem_point, "INTERSECT", outName_temp, "", "NEW_SELECTION")
		fc = os.path.join(outputDIR, 'reservoirs\\%s_.shp'%unique_id)
		fc_t = os.path.join(outputDIR, 'temp\\tt_.shp')
		tttt = os.path.join(outputDIR, 'temp\\tttt.shp')
		alll.append(fc)

		arcpy.CopyFeatures_management(mem_point, fc_t)
		arcpy.Delete_management(mem_point)


		if last_dam == '':
			arcpy.CopyFeatures_management(fc_t, fc)
			arcpy.CopyFeatures_management(fc_t, merged)
		else:
			arcpy.CopyFeatures_management(merged,tttt)
			arcpy.Erase_analysis(fc_t,merged,fc,'#')
			arcpy.Merge_management([tttt,fc], merged)

################
		my_addfield(fc, 'dam_top_h', type="n")
		updater(fc, fieldnames =["FID","dam_top_h"],values =[0,raster_list[unique_id] + 5])


		#arcpy.PolygonVolume_3d(tin,fc,"GRIDCODE","BELOW","Voluq","SAreq","0")
		arcpy.PolygonVolume_3d(tin,fc,"dam_top_h","BELOW","Voluq","SAreq","0")

		dam_volume = my_field2list(fc,"Voluq")
		if dam_volume == []:
			dam_volume = [0]
		arcpy.AddMessage('%s%s'%('dam_volume: ', dam_volume))

		marea = area_(outwtrshd_poly)

		
		mem_point = arcpy.MakeFeatureLayer_management(point_file, "parcel_lyr")
		Selection = arcpy.SelectLayerByLocation_management(mem_point, "WITHIN", outwtrshd_poly, "", "NEW_SELECTION")
		selectedfc = os.path.join(outputDIR, 'temp\\selected_%s.shp'%int(unique_id))
		arcpy.CopyFeatures_management(mem_point, selectedfc)
		arcpy.Delete_management(mem_point)
		previous_area = sum(my_field2list(selectedfc, 'basin_area'))
		D = 0.1
		W = (float(marea) / 1000000.0) - previous_area
		C =  float(dam_volume[0])
		arcpy.AddMessage('%s%s, path: %s'%('area: ', float(marea), outwtrshd_poly))
		if W ==0:
			TE = 0.0
		else:
			TE = 100.0 * (1.0 - (1.0 / (1.0 + (0.0021*0.1*(C/W)))))
		if TE > TE_threshold:
			updater(point_file, fieldnames =["unique_id","basin_area"],values =[row[1],W])
			arcpy.AddMessage("this point is ok")
			previous_area = W

		#arcpy.AddMessage(TE)

		mydic[unique_id] = {'W':W,'C':C,'TE':TE}
		arcpy.AddMessage(mydic[unique_id])


		updater(point_file, fieldnames =["unique_id","TE"],values =[row[1],TE])
		updater(point_file, fieldnames =["unique_id","dam_area"],values =[row[1],C])


OK_dams = os.path.join(outputDIR, 'OK_dams.shp')
all_dam_poly = os.path.join(outputDIR, 'all_dams_poly.shp')

arcpy.Select_analysis(point_file, OK_dams, "\"basin_area\" > 0")

alll = []
for x in range(number_of_all):
	alll.append(os.path.join(outputDIR, 'reservoirs\\%s_.shp'%x))

arcpy.Merge_management(alll, all_dam_poly)

mem_point = arcpy.MakeFeatureLayer_management(all_dam_poly, "parcel_lyr")
Selection = arcpy.SelectLayerByLocation_management(mem_point, "INTERSECT", OK_dams, "", "NEW_SELECTION")
fc = os.path.join(outputDIR, 'OK_dams_poly.shp')
arcpy.CopyFeatures_management(mem_point, fc)
arcpy.Delete_management(mem_point)

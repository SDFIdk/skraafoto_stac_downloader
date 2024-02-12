import os, time
import requests
import json
import time

results_folder = 'C:/Temp/skraafoto_stack_api_results'
save_copy_as_shp = False ## Requires install of geopandas. Can be either False or Ture
save_copy_as_gpkg = False ## Requires install of geopandas. Can be either False or Ture

token = 'fda85a3e152879320b575898f0be683d'

year = [2017]  ### Can be more than one year.. [2017, 2019, 2021, 2023]
direction = ['east'] ### Can be more than one direction. Options are ['nadir','north','south','east','west']
### Polygon area to seach for images. Use following coordinates for entire DK: [120000.0,5900000.0],[120000.0,6500000.0],[1000000.0,6500000.0],[1000000.0,5900000.0],[120000.0,5900000.0] -- Be awere, that the first set of coordinates, must match the last. The polygons does not have to be an exact square.
roi_coordinates = '[722000.0,6165800.0],[722000.0,6175800.0],[743000.0,6175800.0],[743000.0,6165800.0],[722000.0,6165800.0]'

limit = 1000

def generate_base_urls(token, year, direction, roi_coordinates,limit):
    urls = []
    params = []
    for aar in year:
        for dir in direction:
            urls.append('https://api.dataforsyningen.dk/rest/skraafoto_api/v1.0/search?filter={"and":[{"eq": [ { "property": "direction" }, "'+dir+'" ] },{"eq": [ { "property": "collection" }, "skraafotos'+str(aar)+'" ] },{"intersects":[{"property":"geometry"},{"type":"Polygon","coordinates":[['+roi_coordinates+']]}]}]}&filter-lang=cql-json&filter-crs=http://www.opengis.net/def/crs/EPSG/0/25832&crs=http://www.opengis.net/def/crs/EPSG/0/25832&token='+token+'&limit='+str(limit))
            params.append([aar,dir])
    return urls, params


def download_metadata(results_folder, save_copy_as_shp, save_copy_as_gpkg, year, direction, roi_coordinates, limit):
    current_time_seconds = time.time()
    timestamp_folder = time.strftime("%Y%m%d_%H%M%S", time.localtime(current_time_seconds))
    results_folder = f'{results_folder}/{timestamp_folder}_results'

    if not os.path.exists(results_folder):
        os.makedirs(results_folder)
    
    with open(f"{results_folder}/download_parameters.txt", "w") as parameter_file:
        parameter_file.write(f"Parameters used for download\nresults_folder: {results_folder}\nsave_copy_as_shp: {save_copy_as_shp}\nsave_copy_as_gpkg: {save_copy_as_gpkg}\ntoken: {token}\nyear: {year}\ndirection: {direction}\nroi_coordinates: {roi_coordinates}\nlimit: {limit}\n")
    
    cnt=1
    urls, params = generate_base_urls(token, year, direction, roi_coordinates, limit)
    print()
    for elm in urls:
        all_features = []
        #print(elm)
        cnt_fetched = 0
        next_link = elm
        while next_link:
            # Make the API request
            response = requests.get(next_link)

            if response.status_code == 200:
                data = response.json()

                context = data.get("context", [])
                tot_number = context.get("matched")
                cnt_fetched+= context.get("returned")
                
                features = data.get("features", [])
                all_features.extend(features)
                
                next_link = None
                links = data.get("links", [])
                for link in links:
                    if link.get("rel") == "next":
                        next_link = link.get("href")
                        break
                print (f'Fetching features in year {params[cnt-1][0]} for direction {params[cnt-1][1]} ({cnt}/{len(urls)}). Currently at {round(cnt_fetched/tot_number*100,2)}% for this year and direction',end='\r')
        # Define the CRS for EPSG:25832
        crs = {
            "type": "name",
            "properties": {
                "name": "urn:ogc:def:crs:EPSG::25832"
            }
        }

        # Save all features with CRS to a GeoJSON file
        feature_collection = {
            "type": "FeatureCollection",
            "features": all_features,
            "crs": crs
        }
        
        print ()
        print ('Saving results to footprint file in resutls folder')

        geojson_out = f"{results_folder}/footprints_{params[cnt-1][0]}_{params[cnt-1][1]}.geojson"

        with open(geojson_out, "w") as geojson_file:
            json.dump(feature_collection, geojson_file, indent=2)

        if save_copy_as_shp == True:
            print ('Saving results as .shp file')
            try:
                import geopandas as gpd

                gdf = gpd.read_file(geojson_out)
                gdf = gdf.set_crs('epsg:25832',allow_override=True)
                shp_folder = f'{results_folder}/shp_footprints_{params[cnt-1][0]}_{params[cnt-1][1]}'
                if not os.path.exists(shp_folder):
                    os.makedirs(shp_folder)
                gdf.to_file(f'{shp_folder}/footprints_{params[cnt-1][0]}_{params[cnt-1][1]}.shp')
            except Exception as e:
                print ()
                print ('error converting to .shp')
                print (e)
        
        if save_copy_as_gpkg == True:
            print ('Saving results as .gpkg file')
            try:
                import geopandas as gpd

                gdf = gpd.read_file(geojson_out)
                gdf.crs = 'epsg:25832'
                gpkg_folder = f'{results_folder}/gpkg_footprints_{params[cnt-1][0]}_{params[cnt-1][1]}'
                if not os.path.exists(gpkg_folder):
                    os.makedirs(gpkg_folder)
                gdf.to_file(f'{gpkg_folder}/footprints_{params[cnt-1][0]}_{params[cnt-1][1]}.gpkg', driver='GPKG')
            except Exception as e:
                print ()
                print ('error converting to .gpkg')
                print (e)
        cnt+=1
        
download_metadata(results_folder, save_copy_as_shp, save_copy_as_gpkg, year, direction, roi_coordinates, limit)

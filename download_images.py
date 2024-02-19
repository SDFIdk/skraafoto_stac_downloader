import requests, json, os

#### This script requires that you have downloaded a geojson file containing the images to be downloaded:
geojson_file = 'C:/Temp/skraafoto_stack_api_results/20240212_162201_results/footprints_2017_east.geojson'
make_simple_georeference_of_image = True
destination_folder = f'{os.path.dirname(geojson_file)}/images_{os.path.basename(geojson_file).split(".")[0]}'

def download_tif_file(url, destination):
    response = requests.get(url)
    
    if response.status_code == 200:
        with open(destination, 'wb') as file:
            file.write(response.content)
        print(f"Downloaded successfully to {destination}")
    else:
        print(f"Failed to download. Status code: {response.status_code}")

def georeference_tiff(input_tiff_path, X0, Y0, pixel_size_x, pixel_size_y):
    from osgeo import gdal, osr
    # Open the input TIFF file
    input_dataset = gdal.Open(input_tiff_path, gdal.GA_Update)

    # Set the geotransform and spatial reference (EPSG:25832)
    geotransform = (X0, pixel_size_x, 0, Y0, 0, -pixel_size_y)
    input_dataset.SetGeoTransform(geotransform)

    # Set the spatial reference to EPSG:25832
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(4326)
    input_dataset.SetProjection(srs.ExportToWkt())

    # Close the dataset
    input_dataset = None

def download_images(geojson_file,destination_folder):
    if not os.path.exists(destination_folder):
        os.makedirs(destination_folder)
    
    with open(geojson_file, 'r') as file:
        geojson_data = json.load(file)

        for feature in geojson_data['features']:
            asset_data_url = feature['properties']['asset:data']
            file_name = f"{feature['id']}.tif"
            destination_path = f"{destination_folder}/{file_name}"

            download_tif_file(asset_data_url, destination_path)
            if make_simple_georeference_of_image == True:
                
                ppo_x, ppo_y = feature['properties']["pers:interior_orientation"]["principal_point_offset"]
                sensor_cols, sensor_rows = feature['properties']["pers:interior_orientation"]["sensor_array_dimensions"]
                pixel_size = feature['properties']["pers:interior_orientation"]["pixel_spacing"][0]

                x0 = sensor_cols * 0.5 + ppo_x / pixel_size
                y0 = sensor_rows * 0.5 + ppo_y / pixel_size

                print (str(x0))
                print (str(y0))

                georeference_tiff(destination_path, x0, y0, pixel_size, pixel_size)



download_images(geojson_file, destination_folder)


"""

# Example usage
input_tiff_path = 'input.tif'
output_tiff_path = 'output_georeferenced.tif'

# Example coordinates and pixel sizes (replace with your actual values)
X0 = 100000  # X-coordinate of the lower-left corner
Y0 = 500000  # Y-coordinate of the lower-left corner
pixel_size_x = 10  # Pixel size in the x direction
pixel_size_y = 10  # Pixel size in the y direction

georeference_tiff_with_coords(input_tiff_path, output_tiff_path, X0, Y0, pixel_size_x, pixel_size_y)
"""
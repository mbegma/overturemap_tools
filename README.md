# overturemap_tools
Tool for work with overture maps data
--

## [Download data](#download-data)    
#### module: download_data.py   
    
#### Parameters:   
- --dbname: The name of the duckdb database where the data will be downloaded;
- --xmin: Bbox minimum x-coordinate for downloading by bbox;
- --xmax: Bbox maximum x-coordinate for downloading by bbox;
- --ymin: Bbox minimum y-coordinate for downloading by bbox;
- --ymax: Bbox maximum y-coordinate for downloading by bbox;
- --lreg: Short Name of local region (like RU-MOW);
- --country: Country Short Name (like RU);   
    
`xmin`, `xmax`, `ymin`, `ymax` are used to download data from the 
following themes (download by bounding box):
- base
- places
- transportation
- buildings

`lreg`, `country` are used to download data from the 
following themes (download by attribute definition):
- divisions  

> Sample:   
> ```batch
> python download_data.py --dbname ru-moscow.duckdb --xmin 37.573214 --xmax 37.662821 --ymin 55.725876 --ymax 55.775533 --lreg RU-MOW --country RU
> ```
    
## [Export data](#export-data)    
#### module: export_data.py 
   
#### Parameters:   
- --dbname: The name of the duckdb database where the data will be downloaded;
- --output_dir: Directory in which to save exported files; 
- --tables: List of tables to export (separated by spaces)
- --is_wm: An indication that spatial data needs to be reprojected from WGS-84(EPSG:4326) to WebMercator (EPSG:3857)
- --format: The format in which the data must be obtained (currently only the GPKG)

--dbname ru-iva-s.duckdb --output_dir D:\PyProjects\overturemaps\output\tmp\iva-s-wm --is_wm --tables base_bathymetry base_infrastructure base_land base_land_cover base_land_use base_water buildings_building buildings_building_part divisions_division divisions_division_area divisions_division_boundary places_place transportation_connector transportation_segment
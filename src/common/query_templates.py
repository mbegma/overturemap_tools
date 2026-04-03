# -*- coding:utf-8 -*-
# -----------------------------------------------------
# Project Name: overturemaps
# Name: query_templates
# Filename: query_templates.py
# Author: mbegma
# Create data: 12.03.2026
# Description: 
#            
# Copyright: (c) mbegma, 2026
# History: 
#        - 12.03.2026: start of development
# -----------------------------------------------------
from src.config import config

QUERY_GET_REGIONS_NAMES = f"""
SELECT 
    names.primary as name, region 
FROM 
    read_parquet('s3://{config.S3STORE_BUCKET}/release/{{{{ release }}}}/theme=divisions/type=division/*.parquet') 
WHERE 
    subtype = 'region' and country = '{{{{ country }}}}' ORDER BY name;
"""

QUERY_CREATE_SPATIAL_INDEX = """
CREATE INDEX geom_{{ table_name }}_idx ON {{ table_name }} USING RTREE ({{ geometry_field_name }});
"""

QUERY_DOWNLOAD_BY_BBOX = f"""
CREATE OR REPLACE TABLE {{{{ table }}}} AS (
SELECT * 
FROM 
read_parquet('s3://{config.S3STORE_BUCKET}/release/{{{{ release }}}}/theme={{{{ theme }}}}/type={{{{ type }}}}/*.parquet') 
WHERE 
bbox.xmin BETWEEN {{{{ x_min }}}} AND {{{{ x_max }}}} AND bbox.ymin BETWEEN {{{{ y_min }}}} AND {{{{ y_max }}}});
"""

QUERY_DOWNLOAD_BY_REGION_AND_COUNTRY = f"""
CREATE OR REPLACE TABLE {{{{ table }}}} AS (
SELECT *   
FROM 
read_parquet('s3://{config.S3STORE_BUCKET}/release/{{{{ release}}}}/theme={{{{ theme }}}}/type={{{{ type }}}}/*.parquet') 
WHERE region = '{{{{ local_region }}}}' and country = '{{{{ country }}}}');
"""

QUERY_DATA_COUNT = "SELECT COUNT(*) as count FROM {{ table_name }};"
QUERY_DATA_GEOM_NOT_VALID = "SELECT COUNT(*) as count FROM {{ table_name }} WHERE not ST_IsValid(geometry);"
QUERY_DATA_GEOM_TYPE_COUNT = """
SELECT DISTINCT ST_GeometryType(geometry) as geom_type, COUNT(*) as count 
FROM {{ table_name }} GROUP BY geom_type ORDER BY count DESC;
"""

PNT_GEOM = "'POINT', 'MULTIPOINT'"
LIN_GEOM = "'LINESTRING', 'MULTILINESTRING'"
POL_GEOM = "'POLYGON', 'MULTIPOLYGON'"
SR_WGS84 = 'EPSG:4326'
SR_WM = 'EPSG:3857'

QUERY_EXPORT_BASE_LAND = f"""
COPY(
	SELECT 
		id,
		{{% if is_wm %}}ST_Transform(geometry, '{SR_WGS84}', '{SR_WM}', true) as geometry,{{% else %}}geometry,{{% endif %}} 
		names.primary as name, subtype, "class", 
		CAST(source_tags AS JSON) as source_tags, 
		level, surface, elevation, 
		CAST(sources AS JSON) as sources
	FROM {{{{ table_name }}}} 
	WHERE ST_GeometryType(geometry) in ({{% if geom == 'pnt' %}}{PNT_GEOM}{{% elif geom == 'lin' %}}{LIN_GEOM}{{% else %}}{POL_GEOM}{{% endif %}}) 
) TO '{{{{ file_name }}}}' 
WITH (FORMAT GDAL, DRIVER '{{{{ driver }}}}', LAYER_NAME '{{{{ layer_name }}}}', 
SRS{{% if is_wm %}} '{SR_WM}', {{% else %}} '{SR_WGS84}', {{% endif %}} 
LAYER_CREATION_OPTIONS 'WRITE_BBOX=YES');
"""

QUERY_EXPORT_BASE_LAND_USE = f"""
COPY(
	SELECT 
		id,
		{{% if is_wm %}}ST_Transform(geometry, '{SR_WGS84}', '{SR_WM}', true) as geometry,{{% else %}}geometry,{{% endif %}} 
		names.primary as name, level, 
		CAST(source_tags AS JSON) as source_tags, 
		subtype, "class", elevation, surface, 
		CAST(sources AS JSON) as sources
	FROM {{{{ table_name }}}} 
	WHERE ST_GeometryType(geometry) in ({{% if geom == 'pnt' %}}{PNT_GEOM}{{% elif geom == 'lin' %}}{LIN_GEOM}{{% else %}}{POL_GEOM}{{% endif %}}) 
) TO '{{{{ file_name }}}}' 
WITH (FORMAT GDAL, DRIVER '{{{{ driver }}}}', LAYER_NAME '{{{{ layer_name }}}}', 
SRS{{% if is_wm %}} '{SR_WM}', {{% else %}} '{SR_WGS84}', {{% endif %}} 
LAYER_CREATION_OPTIONS 'WRITE_BBOX=YES');
"""

QUERY_EXPORT_BASE_INFRASTRUCTURE = f"""
COPY(
	SELECT 
		id,
		{{% if is_wm %}}ST_Transform(geometry, '{SR_WGS84}', '{SR_WM}', true) as geometry,{{% else %}}geometry,{{% endif %}} 
		names.primary as name, "level", 
		CAST(source_tags AS JSON) as source_tags, 
		subtype, "class", height, surface, 
		CAST(sources AS JSON) as sources
	FROM {{{{ table_name }}}} 
	WHERE ST_GeometryType(geometry) in ({{% if geom == 'pnt' %}}{PNT_GEOM}{{% elif geom == 'lin' %}}{LIN_GEOM}{{% else %}}{POL_GEOM}{{% endif %}}) 
) TO '{{{{ file_name }}}}' 
WITH (FORMAT GDAL, DRIVER '{{{{ driver }}}}', LAYER_NAME '{{{{ layer_name }}}}', 
SRS{{% if is_wm %}} '{SR_WM}', {{% else %}} '{SR_WGS84}', {{% endif %}}
LAYER_CREATION_OPTIONS 'WRITE_BBOX=YES');
"""

QUERY_EXPORT_BASE_LAND_COVER = f"""
COPY(
	SELECT 
		id,
		{{% if is_wm %}}ST_Transform(geometry, '{SR_WGS84}', '{SR_WM}', true) as geometry,{{% else %}}geometry,{{% endif %}} 
		subtype,  
		CAST(cartography AS JSON) as cartography, 
		CAST(sources AS JSON) as sources
	FROM {{{{ table_name }}}} 
	WHERE ST_GeometryType(geometry) in ({{% if geom == 'pnt' %}}{PNT_GEOM}{{% elif geom == 'lin' %}}{LIN_GEOM}{{% else %}}{POL_GEOM}{{% endif %}}) 
) TO '{{{{ file_name }}}}' 
WITH (FORMAT GDAL, DRIVER '{{{{ driver }}}}', LAYER_NAME '{{{{ layer_name }}}}', 
SRS{{% if is_wm %}} '{SR_WM}', {{% else %}} '{SR_WGS84}', {{% endif %}}
LAYER_CREATION_OPTIONS 'WRITE_BBOX=YES');
"""

QUERY_EXPORT_BASE_WATER = f"""
COPY(
	SELECT 
		id,
		{{% if is_wm %}}ST_Transform(geometry, '{SR_WGS84}', '{SR_WM}', true) as geometry,{{% else %}}geometry,{{% endif %}}
		names.primary as name, subtype, "class", CAST(source_tags AS JSON) as source_tags, 
		level, is_intermittent, is_salt, 
		CAST(sources AS JSON) as sources
	FROM {{{{ table_name }}}} 
	WHERE ST_GeometryType(geometry) in ({{% if geom == 'pnt' %}}{PNT_GEOM}{{% elif geom == 'lin' %}}{LIN_GEOM}{{% else %}}{POL_GEOM}{{% endif %}}) 
) TO '{{{{ file_name }}}}' 
WITH (FORMAT GDAL, DRIVER '{{{{ driver }}}}', LAYER_NAME '{{{{ layer_name }}}}', 
SRS{{% if is_wm %}} '{SR_WM}', {{% else %}} '{SR_WGS84}', {{% endif %}}
LAYER_CREATION_OPTIONS 'WRITE_BBOX=YES');
"""

QUERY_EXPORT_PLACES_PLACE = f"""
COPY(
	SELECT 
		id,
		{{% if is_wm %}}ST_Transform(geometry, '{SR_WGS84}', '{SR_WM}', true) as geometry,{{% else %}}geometry,{{% endif %}} 
		categories.primary as categories, CAST(categories.alternate AS JSON) as alt_categories, 
		confidence, CAST(brand AS JSON) as brand, CAST(addresses AS JSON) as addresses, 
		names.primary as name, basic_category, taxonomy.primary as taxonomy, 
		CAST(taxonomy.hierarchy as JSON) as taxonomy_hierarchy, 
		CAST(sources AS JSON) as sources  
	FROM {{{{ table_name }}}} 
	WHERE ST_GeometryType(geometry) in ({{% if geom == 'pnt' %}}{PNT_GEOM}{{% elif geom == 'lin' %}}{LIN_GEOM}{{% else %}}{POL_GEOM}{{% endif %}}) 
) TO '{{{{ file_name }}}}' 
WITH (FORMAT GDAL, DRIVER '{{{{ driver }}}}', LAYER_NAME '{{{{ layer_name }}}}', 
SRS{{% if is_wm %}} '{SR_WM}', {{% else %}} '{SR_WGS84}', {{% endif %}}
LAYER_CREATION_OPTIONS 'WRITE_BBOX=YES');
"""

QUERY_EXPORT_BUILDINGS_BUILDING = f"""
COPY(
	SELECT 
		id,
		{{% if is_wm %}}ST_Transform(geometry, '{SR_WGS84}', '{SR_WM}', true) as geometry,{{% else %}}geometry,{{% endif %}} 
		names.primary as name, "level", height, min_height, is_underground, num_floors, num_floors_underground,	
		min_floor, subtype, "class", facade_color, facade_material, 
		roof_material, roof_shape, roof_direction, roof_orientation, roof_color, roof_height, 
		has_parts,
		CAST(sources AS JSON) as sources  
	FROM {{{{ table_name }}}} 
	WHERE ST_GeometryType(geometry) in ({{% if geom == 'pnt' %}}{PNT_GEOM}{{% elif geom == 'lin' %}}{LIN_GEOM}{{% else %}}{POL_GEOM}{{% endif %}}) 
) TO '{{{{ file_name }}}}' 
WITH (FORMAT GDAL, DRIVER '{{{{ driver }}}}', LAYER_NAME '{{{{ layer_name }}}}', 
SRS{{% if is_wm %}} '{SR_WM}', {{% else %}} '{SR_WGS84}', {{% endif %}}
LAYER_CREATION_OPTIONS 'WRITE_BBOX=YES');
"""

QUERY_EXPORT_BUILDINGS_BUILDING_PART = f"""
COPY(
	SELECT 
		id,
		{{% if is_wm %}}ST_Transform(geometry, '{SR_WGS84}', '{SR_WM}', true) as geometry,{{% else %}}geometry,{{% endif %}} 
		names.primary as name, height, min_height, is_underground, num_floors, num_floors_underground, min_floor, 
		facade_color, facade_material,
		roof_material, roof_shape, roof_direction, roof_orientation, roof_color, roof_height,  
		"level", building_id, 
		CAST(sources AS JSON) as sources  
	FROM {{{{ table_name }}}} 
	WHERE ST_GeometryType(geometry) in ({{% if geom == 'pnt' %}}{PNT_GEOM}{{% elif geom == 'lin' %}}{LIN_GEOM}{{% else %}}{POL_GEOM}{{% endif %}}) 
) TO '{{{{ file_name }}}}' 
WITH (FORMAT GDAL, DRIVER '{{{{ driver }}}}', LAYER_NAME '{{{{ layer_name }}}}', 
SRS{{% if is_wm %}} '{SR_WM}', {{% else %}} '{SR_WGS84}', {{% endif %}}
LAYER_CREATION_OPTIONS 'WRITE_BBOX=YES');
"""

QUERY_EXPORT_TRANSPORTATION_SEGMENT = f"""
COPY(
	SELECT 
		id,
		{{% if is_wm %}}ST_Transform(geometry, '{SR_WGS84}', '{SR_WM}', true) as geometry,{{% else %}}geometry,{{% endif %}} 
		names.primary as name, 
		subtype, "class", subclass, CAST(subclass_rules AS JSON) as subclass_rules, 
		CAST(road_surface AS JSON) as road_surface, 
		CAST(connectors AS JSON) as connectors, CAST(road_flags AS JSON) as road_flags, 
		CAST(rail_flags AS JSON) as rail_flags, CAST(width_rules AS JSON) as width_rules, 
		CAST(level_rules AS JSON) as level_rules, 
		CAST(access_restrictions AS JSON) as access_restrictions, 
		CAST(speed_limits AS JSON) as speed_limits, 
		CAST(prohibited_transitions AS JSON) as prohibited_transitions,
		CAST(routes AS JSON) as routes,
		CAST(destinations AS JSON) as destinations, 
		CAST(sources AS JSON) as sources
	FROM {{{{ table_name }}}} 
	WHERE ST_GeometryType(geometry) in ({{% if geom == 'pnt' %}}{PNT_GEOM}{{% elif geom == 'lin' %}}{LIN_GEOM}{{% else %}}{POL_GEOM}{{% endif %}}) 
) TO '{{{{ file_name }}}}' 
WITH (FORMAT GDAL, DRIVER '{{{{ driver }}}}', LAYER_NAME '{{{{ layer_name }}}}', 
SRS{{% if is_wm %}} '{SR_WM}', {{% else %}} '{SR_WGS84}', {{% endif %}}
LAYER_CREATION_OPTIONS 'WRITE_BBOX=YES');
"""

QUERY_EXPORT_TRANSPORTATION_CONNECTOR = f"""
COPY(
	SELECT 
		id,
		{{% if is_wm %}}ST_Transform(geometry, '{SR_WGS84}', '{SR_WM}', true) as geometry,{{% else %}}geometry,{{% endif %}} 
		CAST(sources AS JSON) as sources  
	FROM {{{{ table_name }}}} 
	WHERE ST_GeometryType(geometry) in ({{% if geom == 'pnt' %}}{PNT_GEOM}{{% elif geom == 'lin' %}}{LIN_GEOM}{{% else %}}{POL_GEOM}{{% endif %}}) 
) TO '{{{{ file_name }}}}' 
WITH (FORMAT GDAL, DRIVER '{{{{ driver }}}}', LAYER_NAME '{{{{ layer_name }}}}', 
SRS{{% if is_wm %}} '{SR_WM}', {{% else %}} '{SR_WGS84}', {{% endif %}}
LAYER_CREATION_OPTIONS 'WRITE_BBOX=YES');
"""

QUERY_EXPORT_DIVISIONS_AREA = f"""
COPY(
	SELECT 
		id,
		{{% if is_wm %}}ST_Transform(geometry, '{SR_WGS84}', '{SR_WM}', true) as geometry,{{% else %}}geometry,{{% endif %}}
		country, subtype, admin_level, "class", names.primary as name, 
		is_land, is_territorial, region, division_id, 
		CAST(sources AS JSON) as sources 
	FROM {{{{ table_name }}}} 
	WHERE ST_GeometryType(geometry) in ({{% if geom == 'pnt' %}}{PNT_GEOM}{{% elif geom == 'lin' %}}{LIN_GEOM}{{% else %}}{POL_GEOM}{{% endif %}}) 
) TO '{{{{ file_name }}}}' 
WITH (FORMAT GDAL, DRIVER '{{{{ driver }}}}', LAYER_NAME '{{{{ layer_name }}}}', 
SRS{{% if is_wm %}} '{SR_WM}', {{% else %}} '{SR_WGS84}', {{% endif %}}
LAYER_CREATION_OPTIONS 'WRITE_BBOX=YES');
"""

QUERY_EXPORT_DIVISIONS_BOUNDARY = f"""
COPY(
	SELECT 
		id,
		{{% if is_wm %}}ST_Transform(geometry, '{SR_WGS84}', '{SR_WM}', true) as geometry,{{% else %}}geometry,{{% endif %}}
		CAST(division_ids AS JSON) as division_ids, 
		subtype, admin_level, "class", is_disputed, is_land, is_territorial, country, region, 
		CAST(sources AS JSON) as sources
	FROM {{{{ table_name }}}} 
	WHERE ST_GeometryType(geometry) in ({{% if geom == 'pnt' %}}{PNT_GEOM}{{% elif geom == 'lin' %}}{LIN_GEOM}{{% else %}}{POL_GEOM}{{% endif %}}) 
) TO '{{{{ file_name }}}}' 
WITH (FORMAT GDAL, DRIVER '{{{{ driver }}}}', LAYER_NAME '{{{{ layer_name }}}}', 
SRS{{% if is_wm %}} '{SR_WM}', {{% else %}} '{SR_WGS84}', {{% endif %}}
LAYER_CREATION_OPTIONS 'WRITE_BBOX=YES');
"""

QUERY_EXPORT_DIVISIONS_DIVISION = f"""
COPY(
	SELECT 
		id,
		{{% if is_wm %}}ST_Transform(geometry, '{SR_WGS84}', '{SR_WM}', true) as geometry,{{% else %}}geometry,{{% endif %}}
		country, region, subtype, admin_level, "class", names.primary as name, 
		CAST(local_type AS JSON) as local_type, CAST(hierarchies AS JSON) as hierarchies, 
		parent_division_id, population, 
		CAST(capital_division_ids AS JSON) as capital_division_ids, 
		CAST(capital_of_divisions AS JSON) as capital_of_divisions,	
		CAST(cartography AS JSON) as cartography, 
		CAST(sources AS JSON) as sources
	FROM {{{{ table_name }}}} 
	WHERE ST_GeometryType(geometry) in ({{% if geom == 'pnt' %}}{PNT_GEOM}{{% elif geom == 'lin' %}}{LIN_GEOM}{{% else %}}{POL_GEOM}{{% endif %}}) 
) TO '{{{{ file_name }}}}' 
WITH (FORMAT GDAL, DRIVER '{{{{ driver }}}}', LAYER_NAME '{{{{ layer_name }}}}', 
SRS{{% if is_wm %}} '{SR_WM}', {{% else %}} '{SR_WGS84}', {{% endif %}}
LAYER_CREATION_OPTIONS 'WRITE_BBOX=YES');
"""

def main():
    pass


if __name__ == "__main__":
    main()

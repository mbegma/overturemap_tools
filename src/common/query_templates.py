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
# _query = f"CREATE INDEX geom_{table_name}_idx ON {table_name} USING RTREE ({geometry_field_name});"
QUERY_CREATE_SPATIAL_INDEX = "CREATE INDEX geom_{{ table_name }}_idx ON {{ table_name }} USING RTREE ({{ geometry_field_name }});"

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

QUERY_DATA_COUNT = "SELECT count(*) as count FROM {{ table_name }};"
QUERY_DATA_GEOM_NOT_VALID = "SELECT count(*) as count FROM {{ table_name }} where not ST_IsValid(geometry);"
QUERY_DATA_GEOM_TYPE_COUNT = """
SELECT DISTINCT ST_GeometryType(geometry) as geom_type, COUNT(*) as count 
FROM {{ table_name }} GROUP BY geom_type ORDER BY count DESC;
"""

# region DIVISION
QUERY_DIVISION_AREA_TEMPLATE = f"""
CREATE OR REPLACE TABLE {{{{ table }}}} AS (
SELECT id, geometry, bbox, country, subtype, class, names.primary, is_land, is_territorial, region, division_id   
FROM read_parquet('s3://{config.S3STORE_BUCKET}/release/{{{{ release}}}}/theme=divisions/type=division_area/*.parquet') 
WHERE region = '{{{{ local_region }}}}' and country = 'RU');
"""
QUERY_DIVISION_BOUNDARY = f"""
CREATE OR REPLACE TABLE {{{{ table }}}} AS (
SELECT id, geometry, bbox, country, subtype, class, is_land, is_territorial, region, division_ids, 
list_value(division_ids)[1][1] as division_id_1, list_value(division_ids)[1][2] as division_id_2   
FROM read_parquet('s3://{config.S3STORE_BUCKET}/release/{{{{ release }}}}/theme=divisions/type=division_boundary/*.parquet') 
WHERE region = '{{{{ local_region }}}}' and country = 'RU');
"""
QUERY_DIVISION = f"""
CREATE OR REPLACE TABLE {{{{ table }}}} AS (
SELECT id, geometry, bbox, country, cartography.prominence as cartography_prominence, 
subtype, class, names.primary as name, region, hierarchies, parent_division_id, population, 
capital_division_ids, capital_of_divisions 
FROM read_parquet('s3://{config.S3STORE_BUCKET}/release/{{{{ release }}}}/theme=divisions/type=division/*.parquet') 
WHERE region = '{{{{ local_region }}}}' and country = 'RU');
"""
# endregion

# region BASE
QUERY_BASE_LAND_TEMPLATE = f"""
CREATE OR REPLACE TABLE {{{{ table }}}} AS (
SELECT id, geometry, bbox, level, subtype, class, names.primary as name, elevation 
FROM read_parquet('s3://{config.S3STORE_BUCKET}/release/{{{{ release }}}}/theme=base/type=land/*.parquet') 
WHERE bbox.xmin BETWEEN {{{{ x_min }}}} AND {{{{ x_max }}}} AND bbox.ymin BETWEEN {{{{ y_min }}}} AND {{{{ y_max }}}});
"""
QUERY_BASE_LAND_USE_TEMPLATE = f"""
CREATE OR REPLACE TABLE {{{{ table }}}} AS (
SELECT id, geometry, bbox, level, subtype, class, surface, names.primary as name, elevation 
FROM read_parquet('s3://{config.S3STORE_BUCKET}/release/{{{{ release }}}}/theme=base/type=land_use/*.parquet') 
WHERE bbox.xmin BETWEEN {{{{ x_min }}}} AND {{{{ x_max }}}} AND bbox.ymin BETWEEN {{{{ y_min }}}} AND {{{{ y_max }}}});
"""
QUERY_BASE_INFRASTRUCTURE_TEMPLATE = f"""
CREATE OR REPLACE TABLE {{{{ table }}}} AS (
SELECT id, geometry, bbox, level, subtype, class, height, surface, names.primary as name, CAST(source_tags AS JSON) as source_tags 
FROM read_parquet('s3://{config.S3STORE_BUCKET}/release/{{{{ release }}}}/theme=base/type=infrastructure/*.parquet') 
WHERE bbox.xmin BETWEEN {{{{ x_min }}}} AND {{{{ x_max }}}} AND bbox.ymin BETWEEN {{{{ y_min }}}} AND {{{{ y_max }}}});
"""
QUERY_BASE_LAND_COVER_TEMPLATE = f"""
CREATE OR REPLACE TABLE {{{{ table }}}} AS (
SELECT id, geometry, bbox, CAST(cartography AS JSON) as cartography, subtype  
FROM read_parquet('s3://{config.S3STORE_BUCKET}/release/{{{{ release }}}}/theme=base/type=land_cover/*.parquet') 
WHERE bbox.xmin BETWEEN {{{{ x_min }}}} AND {{{{ x_max }}}} AND bbox.ymin BETWEEN {{{{ y_min }}}} AND {{{{ y_max }}}});
"""
QUERY_BASE_WATER_TEMPLATE = f"""
CREATE OR REPLACE TABLE {{{{ table }}}} AS (
SELECT id, geometry, bbox, subtype, class, names.primary as name, CAST(source_tags AS JSON) as source_tags, is_salt, is_intermittent    
FROM read_parquet('s3://{config.S3STORE_BUCKET}/release/{{{{ release }}}}/theme=base/type=water/*.parquet') 
WHERE bbox.xmin BETWEEN {{{{ x_min }}}} AND {{{{ x_max }}}} AND bbox.ymin BETWEEN {{{{ y_min }}}} AND {{{{ y_max }}}});
"""
# endregion

# region PLACES
QUERY_PLACES_PLACE_TEMPLATE = f"""
CREATE OR REPLACE TABLE {{{{ table }}}} AS (
SELECT id, geometry, bbox, names.primary as name, categories.primary as categories, basic_category, 
taxonomy.primary as taxonomy, confidence, operating_status, CAST(addresses AS JSON) as addresses    
FROM read_parquet('s3://{config.S3STORE_BUCKET}/release/{{{{ release }}}}/theme=places/type=place/*.parquet') 
WHERE bbox.xmin BETWEEN {{{{ x_min }}}} AND {{{{ x_max }}}} AND bbox.ymin BETWEEN {{{{ y_min }}}} AND {{{{ y_max }}}});
"""
# endregion

# region TRANSPORTATION
QUERY_TRANSPORTATION_SEGMENT_TEMPLATE = f"""
CREATE OR REPLACE TABLE {{{{ table }}}} AS (
SELECT id, geometry, bbox, subtype, class, names.primary as name, routes, subclass_rules   
FROM read_parquet('s3://{config.S3STORE_BUCKET}/release/{{{{ release }}}}/theme=transportation/type=segment/*.parquet') 
WHERE bbox.xmin BETWEEN {{{{ x_min }}}} AND {{{{ x_max }}}} AND bbox.ymin BETWEEN {{{{ y_min }}}} AND {{{{ y_max }}}});
"""
QUERY_TRANSPORTATION_CONNECTOR_TEMPLATE = f"""
CREATE OR REPLACE TABLE {{{{ table }}}} AS (
SELECT id, geometry, bbox   
FROM read_parquet('s3://{config.S3STORE_BUCKET}/release/{{{{ release }}}}/theme=transportation/type=connector/*.parquet') 
WHERE bbox.xmin BETWEEN {{{{ x_min }}}} AND {{{{ x_max }}}} AND bbox.ymin BETWEEN {{{{ y_min }}}} AND {{{{ y_max }}}});
"""
# endregion

# region BUILDINGS
QUERY_BUILDINGS_BUILDING_TEMPLATE = f"""
CREATE OR REPLACE TABLE {{{{ table }}}} AS (
SELECT id, geometry, bbox, level, subtype, class, height, names, has_parts, is_underground, 
num_floors, num_floors_underground, min_height, min_floor, facade_color, facade_material, roof_material, roof_shape, roof_direction, roof_orientation, roof_color, roof_height   
FROM read_parquet('s3://{config.S3STORE_BUCKET}/release/{{{{ release }}}}/theme=buildings/type=building/*') 
WHERE bbox.xmin BETWEEN {{{{ x_min }}}} AND {{{{ x_max }}}} AND bbox.ymin BETWEEN {{{{ y_min }}}} AND {{{{ y_max }}}});
"""
QUERY_BUILDINGS_BUILDING_PART_TEMPLATE = f"""
CREATE OR REPLACE TABLE {{{{ table }}}} AS (
SELECT id, geometry, bbox, level, height, names, is_underground, 
num_floors, num_floors_underground, min_height, min_floor, facade_color, facade_material, roof_material, roof_shape, roof_direction, roof_orientation, roof_color, roof_height, building_id   
FROM read_parquet('s3://{config.S3STORE_BUCKET}/release/{{{{ release }}}}/theme=buildings/type=building_part/*') 
WHERE bbox.xmin BETWEEN {{{{ x_min }}}} AND {{{{ x_max }}}} AND bbox.ymin BETWEEN {{{{ y_min }}}} AND {{{{ y_max }}}});
"""

# endregion



def main():
    pass


if __name__ == "__main__":
    main()

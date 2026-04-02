# -*- coding:utf-8 -*-
# -----------------------------------------------------
# Project Name: overturemaps
# Name: download_data
# Filename: download_data.py
# Author: mbegma
# Create data: 26.03.2026
# Description: 
#            
# Copyright: (c) mbegma, 2026
# History: 
#        - 26.03.2026: start of development
# -----------------------------------------------------
import argparse
import logging
from src.config import config
from src.common import create_logger_ext, get_log_filename
from src.common import LOG_HDL_CNSL, LOG_HDL_FILE, LOG_FMT
from src.common import utilities as u
from src.classes import DownloadCore
from src.common import query_templates


log = create_logger_ext(logger_name=config.LOGGER_NAME,
                        logger_file_name=get_log_filename(config.LOG_DIR, 'download'),
                        logger_handler_type_dict={
                            LOG_HDL_FILE: {"level": logging.DEBUG, "format": LOG_FMT['extra_1']},
                            LOG_HDL_CNSL: {"level": logging.DEBUG, "format": LOG_FMT['detailed']}
                        })
log.info(f"Hello from logger {log.name}!")


def main():
    log.info(f"Start process to download Overture Maps data...")
    parser = argparse.ArgumentParser(description='Download Overture Map data tool')
    parser.add_argument('--dbname', type=str, help='DuckDB name')
    parser.add_argument('--xmin', type=float, help='BBox Xmin')
    parser.add_argument('--xmax', type=float, help='BBox Xmax')
    parser.add_argument('--ymin', type=float, help='BBox Ymin')
    parser.add_argument('--ymax', type=float, help='BBox Ymax')
    parser.add_argument('--lreg', type=str, help='Short Name of local region')
    parser.add_argument('--country', type=str, help='country Short Name')

    args = parser.parse_args()

    if args.dbname is None:
        log.error(f"Database name not specified, please specify dbname parameter")
        return

    log.info(f"BBox: {args.xmin}, {args.xmax}, {args.ymin}, {args.ymax}")
    log.info(f"Local Region Name: {args.lreg}")
    core = DownloadCore(class_logger=log)
    core.set_parameters(
        {
            'x_min': args.xmin,
            'x_max': args.xmax,
            'y_min': args.ymin,
            'y_max': args.ymax,
            'db_name': args.dbname,
            'local_region': args.lreg,
            'country': args.country
        }
    )
    releases = core.fetch_releases_from_s3()
    log.info(f"Last release: {releases['latest']}")
    log.info(f"Releases: {releases['releases']}")
    _table_region_list = [
        {'name': config.TBL_NAME_DIVISION, 'template': query_templates.QUERY_DOWNLOAD_BY_REGION_AND_COUNTRY},
        {'name': config.TBL_NAME_DIVISION_BOUNDARY, 'template': query_templates.QUERY_DOWNLOAD_BY_REGION_AND_COUNTRY},
        {'name': config.TBL_NAME_DIVISION_AREA, 'template': query_templates.QUERY_DOWNLOAD_BY_REGION_AND_COUNTRY},
    ]
    log.info(f"Start to download data by Region into: {', '.join([x['name'] for x in _table_region_list])}")
    if core.download_data(_table_region_list, is_bbox=False):
        log.info(f"Data by Region downloaded successfully")
    else:
        log.error(f"Errors while downloading data by Region: {core.get_last_error()}")

    _table_bbox_list = [
            {'name': config.TBL_NAME_BASE_LAND, 'template': query_templates.QUERY_DOWNLOAD_BY_BBOX},
            {'name': config.TBL_NAME_BASE_LAND_USE, 'template': query_templates.QUERY_DOWNLOAD_BY_BBOX},
            {'name': config.TBL_NAME_BASE_INFRASTRUCTURE, 'template': query_templates.QUERY_DOWNLOAD_BY_BBOX},
            {'name': config.TBL_NAME_BASE_LAND_COVER, 'template': query_templates.QUERY_DOWNLOAD_BY_BBOX},
            {'name': config.TBL_NAME_BASE_WATER, 'template': query_templates.QUERY_DOWNLOAD_BY_BBOX},
            {'name': config.TBL_NAME_PLACES_PLACE, 'template': query_templates.QUERY_DOWNLOAD_BY_BBOX},
            {'name': config.TBL_NAME_TRANSPORTATION_SEGMENT, 'template': query_templates.QUERY_DOWNLOAD_BY_BBOX},
            {'name': config.TBL_NAME_TRANSPORTATION_CONNECTOR, 'template': query_templates.QUERY_DOWNLOAD_BY_BBOX},
            {'name': config.TBL_NAME_BUILDINGS_BUILDING, 'template': query_templates.QUERY_DOWNLOAD_BY_BBOX},
            {'name': config.TBL_NAME_BUILDINGS_BUILDING_PART, 'template': query_templates.QUERY_DOWNLOAD_BY_BBOX}
        ]
    log.info(f"Start to download data by BBox into: {', '.join([x['name'] for x in _table_bbox_list])}")
    if core.download_data(_table_bbox_list):
        log.info(f"Data by BBox downloaded successfully")
    else:
        log.error(f"Errors while downloading data by BBox: {core.get_last_error()}")

    for _ in core.downloaded_data_info.table_info_list:
        log.info(f"{u.tab(2)}table: {_.name}")
        log.info(f"{u.tab(4)}count: {_.count} | non valid geometry: {_.not_valid_geom}")
        log.info(f"{u.tab(4)}geometry type count: {', '.join([f'{q[0]}: {q[1]}' for q in _.geom_type_count])}")
    log.info(f"Process to download Overture Maps data finished")

if __name__ == "__main__":
    main()

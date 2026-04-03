# -*- coding:utf-8 -*-
# -----------------------------------------------------
# Project Name:
# Name: config
# Filename: config.py
# Author: mbegma
# Create data: 09.02.2022
# Description: 
# Copyright: (c) Дата+, 2022 - 2023
# -----------------------------------------------------
from os import sep, path, makedirs
import configparser
from pathlib import Path
import json

ROOT_DIR = Path(__file__).parents[2]
RESOURCE_DIR = ROOT_DIR / "resources"

config_file = ROOT_DIR / "settings" / "settings.ini"
config = configparser.ConfigParser()  # создаём объект парсера
if len(config.read(config_file, encoding="utf-8")) == 0:  # читаем конфиг
    raise Exception(f"ini file is not present in script directory")



def create_dir(directory):
    if not Path(directory).exists():
        Path(directory).mkdir(parents=True)
    # if not path.exists(directory):
    #     makedirs(directory)


class Config(object):
    # region CONST
    IS_DEBUG = config.getboolean("TOOL", "is_debug")
    IS_LOGGING = config.getboolean("TOOL", "is_logging")
    LOGGER_NAME = "overture_map"
    # endregion

    # region DIR
    MAIN_DIR = config["WORKSPACE"]["main_dir"]
    create_dir(MAIN_DIR)

    LOG_DIR = config['WORKSPACE']['log_dir_name']
    create_dir(LOG_DIR)

    OUTPUT_DIR = config['WORKSPACE']['output_dir_name']
    create_dir(OUTPUT_DIR)

    DB_DIR = config['DB']['db_dirs']
    create_dir(DB_DIR)
    # endregion

    S3STORE_BUCKET = config["S3STORE"]["bucket"] # overturemaps-us-west-2
    S3STORE_REGION = config["S3STORE"]["region"] # us-west-2

    TBL_NAME_DIVISIONS_AREA = config["TABLE_NAMES"]["division_area"]
    TBL_NAME_DIVISIONS_BOUNDARY = config["TABLE_NAMES"]["division_boundary"]
    TBL_NAME_DIVISIONS_DIVISION = config["TABLE_NAMES"]["division"]

    TBL_NAME_BASE_LAND = config["TABLE_NAMES"]["base_land"]
    TBL_NAME_BASE_LAND_USE = config["TABLE_NAMES"]["base_land_use"]
    TBL_NAME_BASE_INFRASTRUCTURE = config["TABLE_NAMES"]["base_infrastructure"]
    TBL_NAME_BASE_LAND_COVER = config["TABLE_NAMES"]["base_land_cover"]
    TBL_NAME_BASE_WATER = config["TABLE_NAMES"]["base_water"]

    TBL_NAME_PLACES_PLACE = config["TABLE_NAMES"]["places_place"]

    TBL_NAME_TRANSPORTATION_SEGMENT = config["TABLE_NAMES"]["transportation_segment"]
    TBL_NAME_TRANSPORTATION_CONNECTOR = config["TABLE_NAMES"]["transportation_connector"]

    TBL_NAME_BUILDINGS_BUILDING = config["TABLE_NAMES"]["buildings_building"]
    TBL_NAME_BUILDINGS_BUILDING_PART = config["TABLE_NAMES"]["buildings_building_part"]

    TABLE_TO_THEME = {
        'base_land': {'theme': 'base', 'type': 'land'},
        'base_land_use': {'theme': 'base', 'type': 'land_use'},
        'base_infrastructure': {'theme': 'base', 'type': 'infrastructure'},
        'base_land_cover': {'theme': 'base', 'type': 'land_cover'},
        'base_water': {'theme': 'base', 'type': 'water'},
        'places_place': {'theme': 'places', 'type': 'place'},
        'transportation_segment': {'theme': 'transportation', 'type': 'segment'},
        'transportation_connector': {'theme': 'transportation', 'type': 'connector'},
        'buildings_building': {'theme': 'buildings', 'type': 'building'},
        'buildings_building_part': {'theme': 'buildings', 'type': 'building_part'},
        'divisions_division': {'theme': 'divisions', 'type': 'division'},
        'divisions_division_boundary': {'theme': 'divisions', 'type': 'division_boundary'},
        'divisions_division_area': {'theme': 'divisions', 'type': 'division_area'},
    }

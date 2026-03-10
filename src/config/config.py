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

    S3STORE_BUCKET = config["S3STORE"]["bucket"]
    S3STORE_REGION = config["S3STORE"]["region"]

    TBL_NAME_DIVISION_AREA = config["TABLE_NAMES"]["division_area"]
    TBL_NAME_DIVISION_BOUNDARY = config["TABLE_NAMES"]["division_boundary"]
    TBL_NAME_DIVISION = config["TABLE_NAMES"]["division"]

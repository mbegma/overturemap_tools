# -*- coding:utf-8 -*-
# -----------------------------------------------------
# Project Name: overturemaps
# Name: ExportCore
# Filename: export_core.py
# Author: mbegma
# Create data: 02.04.2026
# Description: 
#            
# Copyright: (c) mbegma, 2026
# History: 
#        - 02.04.2026: start of development
# -----------------------------------------------------
import logging
from typing import List

from pathlib import Path
# from datetime import datetime
from src.config import config
from src.common import utilities as u
import duckdb
from jinja2 import Template
from src.common import query_templates
from src.common import EXPORT_FORMAT


class ExportCore:
    _ver = "1.0.0"
    def __init__(self, class_logger=None, **kwargs):
        self.log = class_logger or logging.getLogger(config.LOGGER_NAME)
        self.log.info(f"Hello, from {self.__class__.__name__} version: {self._ver}")
        self.error = None

        self.db_name = kwargs.get("dbname", "")
        self.output_dir = kwargs.get("output_dir", None)
        self.tables = kwargs.get("tables", [])
        self.is_wm = kwargs.get("is_wm", False)
        self.format = kwargs.get("format", "GPKG")


    def get_last_error(self):
        return self.error

    def _set_info(self, info):
        self.log.info(info)

    def _set_error(self, info):
        self.error = info
        self.log.error(info)

    def set_parameters(self, parameters: dict):
        self.log.debug(parameters)
        self.db_name = parameters.get("db_name", "")
        self.output_dir = parameters.get("output_dir", None)
        self.tables = parameters.get("tables", [])
        self.is_wm = parameters.get("is_wm", False)
        self.format = parameters.get("format", "GPKG")
        if self.db_name == "":
            if Path(self.db_name).suffix == "":
                self.db_name = f"{self.db_name}.duckdb"
        else:
            self._set_error(f"Database name not specified")

        if len(self.tables) == 0:
            self.tables = self._get_db_tables_name(db_name=self.db_name)
        else:
            self.tables = list(self.tables)

    def _get_db_tables_name(self, db_name: str) -> List[str]:
        """
        The function gets the name of all tables in the specified database.
        :param db_name: name of the database (without full path);
        :return: list of table names or empty list;
        """
        self.log.debug(f"{u.tab()}get tables name in {db_name} ...")
        try:
            with duckdb.connect(Path(config.DB_DIR) / db_name) as con:
                ret = con.sql("SHOW TABLES;").fetchall()
            return [str(t[0]) for t in ret]
        except Exception as e:
            self._set_error(str(e.args))
            return []




def main():
    # region local log
    log = logging.getLogger(config.LOGGER_NAME)
    log.setLevel(logging.DEBUG)
    log_formatter = logging.Formatter("%(asctime)s.%(msecs)03d |"
                                      " %(module)s:%(lineno)d\t%(levelname)s\t%(message)s",
                                      u"%m-%d %H:%M:%S")
    log_handler = logging.StreamHandler()
    log_handler.setFormatter(log_formatter)
    log.addHandler(log_handler)
    # log_file_name = f"debug_log_{datetime.today():%Y-%m-%d_%H_%M_%S}.log"
    # file_log_handler = logging.FileHandler(filename=f'{config.LOG_DIR}{sep}{log_file_name}', mode='a', encoding='utf-8')
    # file_log_handler.setFormatter(log_formatter)
    # log.addHandler(file_log_handler)
    log.info(f"Started {__name__}")
    # endregion

    params = {
        "db_name": "ru-iva-s",
        "output_dir": r"D:\PyProjects\overturemaps\output\tmp",
        "tables": ['base_land', 'base_water', 'places_place'],
        "is_wm": False,
        "format": EXPORT_FORMAT[0] # GPKG
    }
    try:
        cl = ExportCore(class_logger=log)

        ret = cl._get_db_tables_name(db_name="ru-iva-s.duckdb")
        print(ret)

        cl.set_parameters(params)
    except Exception as e:
        log.error(str(e.args))

if __name__ == "__main__":
    main()

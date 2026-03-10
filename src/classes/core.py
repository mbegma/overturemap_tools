# -*- coding:utf-8 -*-
# -----------------------------------------------------
# Project Name: overturemaps
# Name: core
# Filename: core.py
# Author: mbegma
# Create data: 25.02.2026
# Description: 
#            
# Copyright: (c) mbegma, 2026
# History: 
#        - 25.02.2026: start of development
# -----------------------------------------------------
import logging
from obstore.store import S3Store
# import json
from os import sep, path, makedirs
# from datetime import datetime
from src.config import config
from src.common import utilities as u
import duckdb


class Core:
    _ver = "1.0.0"
    def __init__(self, class_logger=None, **kwargs):
        self.log = class_logger or logging.getLogger(config.LOGGER_NAME)
        self.log.info(f"Hello, from {self.__class__.__name__} version: {self._ver}")
        self.error = None

        self.releases = {}
        self.x_min = 0.0
        self.x_max = 0.0
        self.y_min = 0.0
        self.y_max = 0.0
        self.db_name = "test_01.duckdb"
        self.local_region = ''
        # self.gdb = kwargs.get('gdb', None)
        # self.result_gdb = None

    def get_last_error(self):
        return self.error

    def _set_info(self, info):
        self.log.info(info)

    def _set_error(self, info):
        self.error = info
        self.log.error(info)

    def set_parameters(self, parameters: dict):
        self.log.debug(parameters)
        self.x_min = parameters.get("x_min", 0.0)
        self.x_max = parameters.get("x_max", 0.0)
        self.y_min = parameters.get("y_min", 0.0)
        self.y_max = parameters.get("y_max", 0.0)
        self.local_region = parameters.get("local_region", "")
        self.db_name = parameters.get("db_name", "test_01.duckdb")
        filename, file_extension = path.splitext(self.db_name)
        if file_extension == "":
            self.db_name = f"{filename}.duckdb"

    def fetch_releases_from_s3(self) -> dict:
        _output = {}
        _store = S3Store("overturemaps-us-west-2",
                         region="us-west-2",
                         skip_signature=True)

        _releases = _store.list_with_delimiter("release/")
        for idx, release in enumerate(sorted(_releases.get("common_prefixes"), reverse=True)):
            _path = release.split("/")[1]
            if idx == 0:
                _output["latest"] = _path
                _output["releases"] = []
            _output["releases"].append(_path)

            self.log.debug(f"{release} | {_path}")
        self.releases = _output
        return _output

    def get_regions_name(self) -> list:
        self.log.debug(f"get regions names ...")
        _query = f"""
            SELECT id, bbox, names.primary as name, region 
            FROM read_parquet('s3://{config.S3STORE_BUCKET}/release/{self.releases['latest']}/theme=divisions/type=division/*.parquet') 
            WHERE subtype = 'region' and country = 'RU' ORDER BY name;
        """
        with duckdb.connect(f"{config.DB_DIR}{sep}{self.db_name}") as con:
            _val = con.sql(_query).fetchall()

        return [f"{x[2]}: {x[3]}" for x in _val] if _val is not None else []

    def download_local_region_data(self, local_region) -> bool:
        self.log.info(f"Downloading local region data to {self.db_name} for region {local_region} ...")
        _query_division_area = f"""
        CREATE OR REPLACE TABLE {config.TBL_NAME_DIVISION_AREA} AS (
        SELECT id, geometry, bbox, country, subtype, class, names.primary, is_land, is_territorial, region, division_id   
        FROM read_parquet('s3://{config.S3STORE_BUCKET}/release/{self.releases['latest']}/theme=divisions/type=division_area/*.parquet') 
        WHERE region = '{local_region}' and country = 'RU');
        """
        _query_division_boundary = f"""
        CREATE OR REPLACE TABLE {config.TBL_NAME_DIVISION_BOUNDARY} AS (
        SELECT id, geometry, bbox, country, subtype, class, is_land, is_territorial, region, division_ids, 
        list_value(division_ids)[1][1] as division_id_1, list_value(division_ids)[1][2] as division_id_2   
        FROM read_parquet('s3://{config.S3STORE_BUCKET}/release/{self.releases['latest']}/theme=divisions/type=division_boundary/*.parquet') 
        WHERE region = '{local_region}' and country = 'RU');
        """
        _query_division = f"""
        CREATE OR REPLACE TABLE {config.TBL_NAME_DIVISION} AS (
        SELECT id, geometry, bbox, country, cartography.prominence as cartography_prominence, 
        subtype, class, names.primary as name, region, hierarchies, parent_division_id, population, 
        capital_division_ids, capital_of_divisions 
        FROM read_parquet('s3://{config.S3STORE_BUCKET}/release/{self.releases['latest']}/theme=divisions/type=division/*.parquet') 
        WHERE region = '{local_region}' and country = 'RU');
        """
        try:
            with duckdb.connect(f"{config.DB_DIR}{sep}{self.db_name}") as con:
                con.sql("INSTALL SPATIAL;")
                con.sql("LOAD SPATIAL;")
                con.sql("INSTALL httpfs;")
                con.sql("LOAD httpfs;")

                self.log.debug(f"download <{config.TBL_NAME_DIVISION_AREA}> for {local_region}")
                con.sql(_query_division_area)
                self.log.debug(f"download - OK")

                self.log.debug(f"download <{config.TBL_NAME_DIVISION_BOUNDARY}> for {local_region}")
                con.sql(_query_division_boundary)
                self.log.debug(f"download - OK")

                self.log.debug(f"download <{config.TBL_NAME_DIVISION}> for {local_region}")
                con.sql(_query_division)
                self.log.debug(f"download - OK")
            return True
        except Exception as e:
            self._set_error(str(e.args))
            return False

    def download_data(self):
        self.log.info(f"Downloading data to {self.db_name} ...")
        with duckdb.connect(f"{config.DB_DIR}{sep}{self.db_name}") as conn:
            ...
        # with duckdb.connect("file.db") as con:
        #     con.sql("CREATE TABLE test (i INTEGER)")
        #     con.sql("INSERT INTO test VALUES (42)")
        #     con.table("test").show()
        #     # the context manager closes the connection automatically

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
    cl = Core(class_logger=log)
    releases = cl.fetch_releases_from_s3()
    log.debug(f"{releases}")
    _regions_names = cl.get_regions_name()
    log.debug(f"{_regions_names}")

if __name__ == "__main__":
    main()

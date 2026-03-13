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
from jinja2 import Template
from src.common import query_templates


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
        self.stat = {
            'divisions': [],
            'base': [],
            'places': [],
            'transportation': [],
            'buildings': []
        }

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

    def _create_spatial_index(self, table_name: str, geometry_field_name: str= 'geometry') -> bool:
        self.log.debug(f"{u.tab()}create spatial index for {table_name} ...")
        # CREATE INDEX geom_division_area_idx ON division_area USING RTREE (geometry);
        # _query = f"CREATE INDEX geom_{table_name}_idx ON {table_name} USING RTREE ({geometry_field_name});"
        _query = Template(query_templates.QUERY_CREATE_SPATIAL_INDEX).render(
            table_name=table_name,
            geometry_field_name=geometry_field_name,
        )
        try:
            with duckdb.connect(f"{config.DB_DIR}{sep}{self.db_name}") as con:
                con.sql(_query)

            return True
        except Exception as e:
            self._set_error(str(e.args))
            return False

    def _download_data_by_bbox(self, table_list: list) -> bool:
        self.log.debug(f"download data ...")
        try:
            with duckdb.connect(f"{config.DB_DIR}{sep}{self.db_name}") as con:
                con.sql("INSTALL SPATIAL;")
                con.sql("LOAD SPATIAL;")
                con.sql("INSTALL httpfs;")
                con.sql("LOAD httpfs;")
                for _table in table_list:
                    self.log.debug(f"{u.tab()}download data into <{_table['name']}> ...")
                    _query = Template(_table['template']).render(
                        table=_table['name'],
                        release=self.releases['latest'],
                        x_min=self.x_min, x_max=self.x_max,
                        y_min=self.y_min, y_max=self.y_max
                    )
                    con.sql(_query)
                    self.log.debug(f"{u.tab()}data to <{_table['name']}> downloaded successfully")
                    self._create_spatial_index(_table['name'])
                self.log.debug(f"{u.tab()}download - OK")
            return True
        except Exception as e:
            self._set_error(str(e.args))
            return False

    # region CORE
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

    def get_regions_short_name(self) -> list:
        """
        Получение списка сокращений названий субъектов РФ.
        Далее по ним запрашивается информация о границах и территории
        :return: список сокращенных имен
        """
        self.log.debug(f"get regions names ...")
        _query = f"""
            SELECT id, bbox, names.primary as name, region 
            FROM read_parquet('s3://{config.S3STORE_BUCKET}/release/{self.releases['latest']}/theme=divisions/type=division/*.parquet') 
            WHERE subtype = 'region' and country = 'RU' ORDER BY name;
        """
        try:
            with duckdb.connect(f"{config.DB_DIR}{sep}{self.db_name}") as con:
                _val = con.sql(_query).fetchall()

            return [f"{x[2]}: {x[3]}" for x in _val] if _val is not None else []
        except Exception as e:
            self._set_error(str(e.args))
            return []
    # endregion

    # region DIVISIONS
    def download_local_divisions_data(self, local_region: str) -> bool:
        """
        Получение данных из темы divisions (границы, территории, точки) по РФ, с учетом субъекта
        :param local_region: сокращенное название субъекта РФ
        :return: True/False
        """
        self.log.info(f"Downloading local region data into {self.db_name} for region {local_region} ...")
        _divisions_tables_list = [
            {'name': config.TBL_NAME_DIVISION_AREA, 'template': query_templates.QUERY_DIVISION_AREA_TEMPLATE},
            {'name': config.TBL_NAME_DIVISION_BOUNDARY, 'template': query_templates.QUERY_DIVISION_BOUNDARY},
            {'name': config.TBL_NAME_DIVISION, 'template': query_templates.QUERY_DIVISION}
        ]
        try:
            with duckdb.connect(f"{config.DB_DIR}{sep}{self.db_name}") as con:
                con.sql("INSTALL SPATIAL;")
                con.sql("LOAD SPATIAL;")
                con.sql("INSTALL httpfs;")
                con.sql("LOAD httpfs;")
                for _table in _divisions_tables_list:
                    self.log.debug(f"download data into <{_table['name']}> for {local_region}")
                    _query = Template(_table['template']).render(
                        table=_table['name'],
                        release=self.releases['latest'],
                        local_region=local_region
                    )
                    con.sql(_query)
                    self.log.debug(f"data to {_table['name']}> for {local_region} downloaded successfully")
                    self._create_spatial_index(_table['name'])
                self.log.debug(f"download - OK")
            return True
        except Exception as e:
            self._set_error(str(e.args))
            return False

    def create_local_divisions_spatial_indexes(self):
        for _type in [config.TBL_NAME_DIVISION, config.TBL_NAME_DIVISION_BOUNDARY, config.TBL_NAME_DIVISION_AREA]:
            if self._create_spatial_index(_type):
                self.log.debug(f"{u.tab()}create spatial index for {_type} - OK")
            else:
                self.log.debug(f"{u.tab()}create spatial index for {_type} - Failed")

    def get_local_divisions_data_stat(self) -> bool:
        """
        Получение статистики
        -- Вывод статистики по уровням административного деления
        SELECT subtype as admin_level, COUNT(*) as count FROM division GROUP BY subtype ORDER BY count DESC;
        SELECT subtype as admin_level, COUNT(*) as count FROM division_area GROUP BY subtype ORDER BY count DESC;
        SELECT subtype as admin_level, COUNT(*) as count FROM division_boundary GROUP BY subtype ORDER BY count DESC;
        :return: True/False
        """
        self.log.debug(f"getting local divisions data statistic ...")
        try:
            with duckdb.connect(f"{config.DB_DIR}{sep}{self.db_name}") as con:
                for _type in [config.TBL_NAME_DIVISION, config.TBL_NAME_DIVISION_BOUNDARY, config.TBL_NAME_DIVISION_AREA]:
                    _query = f"SELECT subtype as admin_level, COUNT(*) as count FROM {_type} GROUP BY subtype ORDER BY count DESC;"
                    _val = con.sql(_query).fetchall()
                    # _obj = {'type': _type, 'values': [{'admin_level': x[0], 'count': x[1]} for x in _val]}
                    # self.stat['divisions'].append({_type: [{'admin_level': x[0], 'count': x[1]} for x in _val]})
                    self.stat['divisions'].append(
                        {
                            'type': _type,
                            'values': [{'admin_level': x[0], 'count': x[1]} for x in _val]
                        }
                    )
                return True
        except Exception as e:
            self._set_error(str(e.args))
            return False
    # endregion

    # region BASE
    def download_local_base_data(self, local_region: str) -> bool:
        self.log.info(f"Downloading BASE local region data into {self.db_name} for region {local_region} ...")

        _base_tables_list = [
            {'name': config.TBL_NAME_BASE_LAND, 'template': query_templates.QUERY_BASE_LAND_TEMPLATE},
            {'name': config.TBL_NAME_BASE_LAND_USE, 'template': query_templates.QUERY_BASE_LAND_USE_TEMPLATE},
            {'name': config.TBL_NAME_BASE_INFRASTRUCTURE, 'template': query_templates.QUERY_BASE_INFRASTRUCTURE_TEMPLATE},
            {'name': config.TBL_NAME_BASE_LAND_COVER, 'template': query_templates.QUERY_BASE_LAND_COVER_TEMPLATE},
            {'name': config.TBL_NAME_BASE_WATER, 'template': query_templates.QUERY_BASE_WATER_TEMPLATE}
        ]
        try:
            with duckdb.connect(f"{config.DB_DIR}{sep}{self.db_name}") as con:
                con.sql("INSTALL SPATIAL;")
                con.sql("LOAD SPATIAL;")
                con.sql("INSTALL httpfs;")
                con.sql("LOAD httpfs;")
                for _base in _base_tables_list:
                    self.log.debug(f"download data into <{_base['name']}> for {local_region}")
                    _query = Template(_base['template']).render(
                        table=_base['name'],
                        release=self.releases['latest'],
                        x_min=self.x_min, x_max=self.x_max,
                        y_min=self.y_min, y_max=self.y_max
                    )
                    con.sql(_query)
                    self.log.debug(f"data to {_base['name']}> for {local_region} downloaded successfully")
                    self._create_spatial_index(_base['name'])
                self.log.debug(f"download - OK")
            return True
        except Exception as e:
            self._set_error(str(e.args))
            return False
    # endregion

    # region PLACES
    def download_local_places_data(self) -> bool:
        """
        Получение данных из темы places
        :return: True/False
        """
        self.log.info(f"Downloading local PLACES data into {self.db_name} ...")
        _places_tables_list = [
            {'name': config.TBL_NAME_PLACES_PLACE, 'template': query_templates.QUERY_PLACES_PLACE_TEMPLATE}
        ]
        if self._download_data_by_bbox(_places_tables_list):
            self._set_info(f"local PLACES data downloaded successfully")
            return True
        else:
            self._set_error(f"local PLACES data downloaded failed: {self.get_last_error()}")
            return False

    # endregion

    # region TRANSPORTATION
    def download_local_transportation_data(self) -> bool:
        """
        Получение данных из темы transportation
        :return: True/False
        """
        self.log.info(f"Downloading local TRANSPORTATION data into {self.db_name} ...")
        _tables_list = [
            {'name': config.TBL_NAME_TRANSPORTATION_SEGMENT,
             'template': query_templates.QUERY_TRANSPORTATION_SEGMENT_TEMPLATE},
            {'name': config.TBL_NAME_TRANSPORTATION_CONNECTOR,
             'template': query_templates.QUERY_TRANSPORTATION_CONNECTOR_TEMPLATE}
        ]
        if self._download_data_by_bbox(_tables_list):
            self._set_info(f"local TRANSPORTATION data downloaded successfully")
            return True
        else:
            self._set_error(f"local TRANSPORTATION data downloaded failed: {self.get_last_error()}")
            return False
    # endregion

    # region BUILDINGS
    def download_local_buildings_data(self) -> bool:
        """
        Получение данных из темы BUILDINGS
        :return: True/False
        """
        self.log.info(f"Downloading local BUILDINGS data into {self.db_name} ...")
        _tables_list = [
            {'name': config.TBL_NAME_BUILDINGS_BUILDING,
             'template': query_templates.QUERY_BUILDINGS_BUILDING_TEMPLATE},
            {'name': config.TBL_NAME_BUILDINGS_BUILDING_PART,
             'template': query_templates.QUERY_BUILDINGS_BUILDING_PART_TEMPLATE}
        ]
        if self._download_data_by_bbox(_tables_list):
            self._set_info(f"local BUILDINGS data downloaded successfully")
            return True
        else:
            self._set_error(f"local BUILDINGS data downloaded failed: {self.get_last_error()}")
            return False
    # endregion


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

    _local_reg = "RU-IVA"
    cl.set_parameters(
        {
            'x_min': 41.298079,
            'x_max': 41.500639,
            'y_min': 56.799198,
            'y_max': 56.900203,
            'db_name': 'test_01',
            'local_region': _local_reg
        }
    )


    releases = cl.fetch_releases_from_s3()
    log.debug(f"{releases}")

    # _regions_names = cl.get_regions_short_name()
    # log.debug(f"{_regions_names}")


    # if cl.download_local_divisions_data(_local_reg):
    #     log.debug(f"data downloaded successfully for {_local_reg}")
    # else:
    #     log.error(f"data for {_local_reg} download failed: {cl.get_last_error()}")

    # ret = cl.get_local_divisions_data_stat()
    # print(cl.stat)

    # ret = cl.download_local_base_data(_local_reg)
    # print(ret)

    ret = cl.download_local_places_data()
    ret = cl.download_local_transportation_data()
    ret = cl.download_local_buildings_data()
    print(ret)

if __name__ == "__main__":
    main()

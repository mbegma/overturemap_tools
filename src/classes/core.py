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
from typing import List

from obstore.store import S3Store
# import json
from os import sep, path, makedirs
# from datetime import datetime
from src.config import config
from src.common import utilities as u
import duckdb
from jinja2 import Template
from src.common import query_templates
from dataclasses import dataclass, field


@dataclass
class TableInfo:
    name: str = field(default_factory=str)
    count: int = field(default_factory=int)
    not_valid_geom: int = field(default_factory=int)
    geom_type_count: list = field(default_factory=list)

@dataclass
class TableInfoList:
    table_info_list: List[TableInfo] = field(default_factory=list)


class Core:
    _ver = "1.0.0"
    def __init__(self, class_logger=None, **kwargs):
        self.log = class_logger or logging.getLogger(config.LOGGER_NAME)
        self.log.info(f"Hello, from {self.__class__.__name__} version: {self._ver}")
        self.error = None
        self.downloaded_data_info = TableInfoList()

        self.releases = {}
        self.x_min = 0.0
        self.x_max = 0.0
        self.y_min = 0.0
        self.y_max = 0.0
        self.db_name = "test_01.duckdb"
        self.country = 'RU'
        self.local_region = ''


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
        self.country = parameters.get("country", "RU")
        self.db_name = parameters.get("db_name", "test_01.duckdb")
        filename, file_extension = path.splitext(self.db_name)
        if file_extension == "":
            self.db_name = f"{filename}.duckdb"
        self.downloaded_data_info.table_info_list.clear()

    def _create_spatial_index(self, table_name: str, geometry_field_name: str= 'geometry') -> bool:
        """
        Function for creating a spatial index
        :param table_name: table name;
        :param geometry_field_name: name of the geometry field;
        :return: True/False
        """
        self.log.debug(f"{u.tab()}create spatial index for {table_name} ...")
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

    @u.time_of_function
    def _get_downloaded_data_info(self, table_name: str) -> bool:
        self.log.debug(f"{u.tab()}get information about {table_name} ...")
        _table_info = TableInfo(name=table_name)
        _table_list = [
            {'num': 1, 'name': 'Total records count', 'query': query_templates.QUERY_DATA_COUNT},
            {'num': 2, 'name': 'Count of Not valid Geometry', 'query': query_templates.QUERY_DATA_GEOM_NOT_VALID},
            {'num': 3, 'name': 'Count by Geometry Type', 'query': query_templates.QUERY_DATA_GEOM_TYPE_COUNT},
        ]
        try:
            with duckdb.connect(f"{config.DB_DIR}{sep}{self.db_name}") as con:
                con.sql("LOAD SPATIAL;")
                for _table in _table_list:
                    _query = Template(_table['query']).render(table_name=table_name)
                    _val = con.sql(_query).fetchall()
                    if _table['num'] == 1:
                        try:
                            _table_info.count = _val[0][0]
                        except IndexError:
                            _table_info.count = 0
                    elif _table['num'] == 2:
                        try:
                            _table_info.not_valid_geom = _val[0][0]
                        except IndexError:
                            _table_info.not_valid_geom = 0
                    elif _table['num'] == 3:
                        _table_info.geom_type_count = _val
            self.downloaded_data_info.table_info_list.append(_table_info)
            return True
        except Exception as e:
            self._set_error(str(e.args))
            return False

    # region CORE
    def fetch_releases_from_s3(self) -> dict:
        """
        Function to get the latest release and previous releases
        :return: dict with structure {'latest': <str>, 'releases': [<str>]}
        """
        _output = {}
        _store = S3Store(config.S3STORE_BUCKET,
                         region=config.S3STORE_REGION,
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

    def get_regions_short_name(self, country: str='RU') -> list:
        """
        A function that gets a list of abbreviated names of subjects (regions) of a country.
        :return: list of abbreviated names or empty list
        """
        self.log.debug(f"get regions names for {country} ...")
        _query = Template(query_templates.QUERY_GET_REGIONS_NAMES).render(
            release=self.releases['latest'],
            country=self.country
        )
        try:
            with duckdb.connect(f"{config.DB_DIR}{sep}{self.db_name}") as con:
                _val = con.sql(_query).fetchall()

            return [f"{x[0]}: {x[1]}" for x in _val] if _val is not None else []
        except Exception as e:
            self._set_error(str(e.args))
            return []

    @u.time_of_function
    def download_data(self, params_list: list, is_bbox: bool=True) -> bool:
        """
        A function that downloads data from s3 geoparquet file to a database table specified by a parameter.
        :param params_list: list of objects, like {'name': <name table>, 'template': <template query name>}>
        :param is_bbox: a switch that determines the condition by which to make a data request (bbox or region)
        :return: True/False (error description in get_last_error() function
        """
        self.log.debug(f"download data ...")
        try:
            with duckdb.connect(f"{config.DB_DIR}{sep}{self.db_name}") as con:
                con.sql("INSTALL SPATIAL;")
                con.sql("LOAD SPATIAL;")
                con.sql("INSTALL httpfs;")
                con.sql("LOAD httpfs;")
                for _table in params_list:
                    self.log.debug(f"{u.tab()}download data into <{_table['name']}> ...")
                    _theme = config.TABLE_TO_THEME.get(_table['name'], None)
                    if _theme is None:
                        self._set_error(f"{u.tab()}theme for <{_table['name']}> not found")
                        continue
                    if is_bbox:
                        _query = Template(_table['template']).render(
                            table=_table['name'],
                            release=self.releases['latest'],
                            theme=_theme['theme'], type=_theme['type'],
                            x_min=self.x_min, x_max=self.x_max,
                            y_min=self.y_min, y_max=self.y_max
                        )
                    else:
                        _query = Template(_table['template']).render(
                            table=_table['name'],
                            release=self.releases['latest'],
                            theme=_theme['theme'], type=_theme['type'],
                            local_region=self.local_region,
                            country=self.country
                        )
                    con.sql(_query)
                    self.log.debug(f"{u.tab()}data to <{_table['name']}> downloaded successfully")
                    self._create_spatial_index(_table['name'])
                    self._get_downloaded_data_info(_table['name'])
                self.log.debug(f"{u.tab()}download - OK")
            return True
        except Exception as e:
            self._set_error(str(e.args))
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
    # 41.298079,56.799198,41.500639,56.900203 - Шуя
    _local_reg = "RU-IVA"
    cl.set_parameters(
        {
            'x_min': 41.298079,
            'x_max': 41.500639,
            'y_min': 56.799198,
            'y_max': 56.900203,
            'db_name': 'ru-iva-s.duckdb',
            'local_region': _local_reg,
            'country': 'RU'
        }
    )
    # Ульяновская обл.: RU-ULY 45.756,52.4625,50.4058,54.9617
    # _local_reg = "RU-ULY"
    # cl.set_parameters(
    #     {
    #         'x_min': 45.756,
    #         'x_max': 52.4625,
    #         'y_min': 51.44,
    #         'y_max': 54.9617,
    #         'db_name': 'ru_uly.duckdb',
    #         'local_region': _local_reg
    #     }
    # )

    # Башкортостан: RU-BA  53.12,51.44,60.29,56.73
    # _local_reg = "RU-BA"
    # cl.set_parameters(
    #     {
    #         'x_min': 53.12,
    #         'x_max': 60.29,
    #         'y_min': 51.44,
    #         'y_max': 56.73,
    #         'db_name': 'ru_ba.duckdb',
    #         'local_region': _local_reg
    #     }
    # )

    releases = cl.fetch_releases_from_s3()
    log.debug(f"{releases}")

    _regions_names = cl.get_regions_short_name()
    log.debug(f"{_regions_names}")

    ret = cl._get_downloaded_data_info('base_land')
    if ret:
        print(cl.downloaded_data_info.table_info_list)
    else:
        print(cl.get_last_error())

    print(ret)

if __name__ == "__main__":
    main()

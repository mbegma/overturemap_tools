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
import threading

from pathlib import Path


from src.config import config
from src.common import utilities as u
import duckdb
from jinja2 import Template
from src.common import query_templates
from src.common import EXPORT_FORMAT

TABLES = {
    config.TBL_NAME_BASE_LAND: {
        "template": query_templates.QUERY_EXPORT_BASE_LAND,
        "geom": ['pnt', 'lin', 'pol']
    },
    config.TBL_NAME_BASE_LAND_USE: {
        "template": query_templates.QUERY_EXPORT_BASE_LAND_USE,
        "geom": ['pnt', 'lin', 'pol']
    },
    config.TBL_NAME_BASE_LAND_COVER: {
        "template": query_templates.QUERY_EXPORT_BASE_LAND_COVER,
        "geom": ['pnt', 'lin', 'pol']
    },
    config.TBL_NAME_BASE_INFRASTRUCTURE: {
        "template": query_templates.QUERY_EXPORT_BASE_INFRASTRUCTURE,
        "geom": ['pnt', 'lin', 'pol']
    },
    config.TBL_NAME_BASE_WATER: {
        "template": query_templates.QUERY_EXPORT_BASE_WATER,
        "geom": ['pnt', 'lin', 'pol']
    },
    config.TBL_NAME_BASE_BATHYMETRY: {
        "template": query_templates.QUERY_EXPORT_BASE_BATHYMETRY,
        "geom": ['pol']
    },
    config.TBL_NAME_PLACES_PLACE: {
        "template": query_templates.QUERY_EXPORT_PLACES_PLACE,
        "geom": ['pnt']
    },
    config.TBL_NAME_BUILDINGS_BUILDING: {
        "template": query_templates.QUERY_EXPORT_BUILDINGS_BUILDING,
        "geom": ['pol']
    },
    config.TBL_NAME_BUILDINGS_BUILDING_PART: {
        "template": query_templates.QUERY_EXPORT_BUILDINGS_BUILDING_PART,
        "geom": ['pol']
    },
    config.TBL_NAME_TRANSPORTATION_SEGMENT: {
        "template": query_templates.QUERY_EXPORT_TRANSPORTATION_SEGMENT,
        "geom": ['pnt', 'lin', 'pol']
    },
    config.TBL_NAME_TRANSPORTATION_CONNECTOR: {
        "template": query_templates.QUERY_EXPORT_TRANSPORTATION_CONNECTOR,
        "geom": ['pnt', 'lin', 'pol']
    },
    config.TBL_NAME_DIVISIONS_AREA: {
        "template": query_templates.QUERY_EXPORT_DIVISIONS_AREA,
        "geom": ['pol']
    },
    config.TBL_NAME_DIVISIONS_BOUNDARY: {
        "template": query_templates.QUERY_EXPORT_DIVISIONS_BOUNDARY,
        "geom": ['lin']
    },
    config.TBL_NAME_DIVISIONS_DIVISION: {
        "template": query_templates.QUERY_EXPORT_DIVISIONS_DIVISION,
        "geom": ['pnt']
    },
}

class ExportCore:
    _ver = "1.0.0"
    def __init__(self, class_logger=None, **kwargs):
        self.log = class_logger or logging.getLogger(config.LOGGER_NAME)
        self.log.info(f"Hello, from {self.__class__.__name__} version: {self._ver}")
        self.error = None
        self._lock = threading.Lock()

        self.db_name = kwargs.get("dbname", "")
        self.output_dir: str = kwargs.get("output_dir", "")
        self.tables_list = kwargs.get("tables", [])
        self.is_wm = kwargs.get("is_wm", False)
        self.format = kwargs.get("format", "GPKG")

    def get_last_error(self):
        return self.error

    def _set_info(self, info):
        with self._lock:
            self.log.info(info)

    def _set_error(self, info):
        with self._lock:
            self.error = info
            self.log.error(info)

    def set_parameters(self, parameters: dict):
        self.log.debug(parameters)
        self.db_name = parameters.get("db_name", "")
        self.output_dir = parameters.get("output_dir", "")
        self.tables_list = parameters.get("tables", [])
        self.is_wm = parameters.get("is_wm", False)
        self.format = parameters.get("format", "GPKG")

        if self.db_name != "":
            if Path(self.db_name).suffix == "":
                self.db_name = f"{self.db_name}.duckdb"
        else:
            self._set_error(f"Database name not specified")

        if len(self.tables_list) == 0:
            self.tables_list = self._get_db_tables_name(db_name=self.db_name)
        else:
            self.tables_list = list(self.tables_list)

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

    def _create_output_file_name(self, table_name: str, geometry_type: str) -> str:
        _extension = '.gpkg' if self.format == 'GPKG' else '.geojson'
        if geometry_type == 'lin':
            _postfix = '_lin'
        elif geometry_type == 'pol':
            _postfix = '_pol'
        else:
            _postfix = '_pnt'
        return f"{table_name}{_postfix}{_extension}"

    def _export_table(self, table_name: str) -> bool:
        self.log.debug(f"{u.tab()}export data from <{table_name}> ...")
        if not table_name in TABLES.keys():
            self._set_error(f"Table {table_name} not found in processed tables.")
            return False
        _table = TABLES[table_name]
        try:
            with duckdb.connect(Path(config.DB_DIR) / self.db_name) as con:
                # con.sql("INSTALL SPATIAL;")
                con.sql("LOAD SPATIAL;")
                # con.sql("INSTALL json;")
                con.sql("LOAD json;")
                for geom in _table['geom']:
                    _file_name = self._create_output_file_name(table_name, geom)
                    self.log.debug(f"{u.tab(2)}export {geom.upper()} data from <{table_name}> to {_file_name} ...")
                    _query = Template(_table['template']).render(
                        is_wm=self.is_wm,
                        table_name=table_name,
                        geom=geom,
                        file_name= Path(self.output_dir) / _file_name,
                        driver='GPKG' if self.format == 'GPKG' else 'GeoJSON',
                        layer_name=Path(_file_name).stem,
                    )
                    self.log.debug(f"{u.tab(2)}sql query: {_query}")
                    ret_val = con.sql(_query)
                    self.log.debug(f"{u.tab(2)}sql result: {ret_val}")
                    self.log.debug(f"{u.tab(2)}export {geom.upper()} data from <{table_name}> "
                                   f"to {_file_name} successfully finished")
                self.log.debug(f"{u.tab()}export table {table_name} successfully finished")
            return True
        except Exception as e:
            self._set_error(str(e.args))
            return False

    @u.time_of_function
    def export_data(self) -> bool:
        if self.error:
            return False

        if len(self.tables_list) == 0:
            self._set_error("No tables specified for export.")
            return False

        errors = []
        threads = []
        results_lock = threading.Lock()

        def export_table_thread(thread_table_name: str):
            """Вспомогательная функция для экспорта таблицы в отдельном потоке"""
            if self._export_table(table_name=thread_table_name):
                self._set_info(f"The {thread_table_name} table export was successful.")
            else:
                error_msg = f"Error exporting table {thread_table_name}. Error: {self.get_last_error()}"
                with results_lock:
                    errors.append(error_msg)
                self._set_error(error_msg)

        try:
            # Создаем и запускаем потоки для каждой таблицы
            for table_name in self.tables_list:
                thread = threading.Thread(target=export_table_thread, args=(table_name,), daemon=False)
                threads.append(thread)
                thread.start()

            # Ожидаем завершения всех потоков
            for thread in threads:
                thread.join()

            # Возвращаем результат
            if errors:
                self._set_error(f"Export completed with errors: {'; '.join(errors)}")
                return False

            self._set_info("All tables exported successfully.")
            return True

        except Exception as e:
            self._set_error(str(e.args))
            return False

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
        "tables": ['base_water'],
        "is_wm": True,
        "format": EXPORT_FORMAT[0] # GPKG
    }
    try:
        cl = ExportCore(class_logger=log)

        # ret = cl._get_db_tables_name(db_name="ru-iva-s.duckdb")


        cl.set_parameters(params)
        ret = cl.export_data()
        print(ret)
    except Exception as e:
        log.error(str(e.args))

if __name__ == "__main__":
    main()

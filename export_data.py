# -*- coding:utf-8 -*-
# -----------------------------------------------------
# Project Name: overturemaps
# Name: export_data
# Filename: export_data.py
# Author: mbegma
# Create data: 02.04.2026
# Description: 
#            
# Copyright: (c) mbegma, 2026
# History: 
#        - 02.04.2026: start of development
# -----------------------------------------------------
import argparse
import logging
from pathlib import Path
from src.config import config
from src.common import create_logger_ext, get_log_filename
from src.common import LOG_HDL_CNSL, LOG_HDL_FILE, LOG_FMT
from src.common import EXPORT_FORMAT
from src.classes import ExportCore

log = create_logger_ext(logger_name=config.LOGGER_NAME,
                        logger_file_name=get_log_filename(config.LOG_DIR, 'export'),
                        logger_handler_type_dict={
                            LOG_HDL_FILE: {"level": logging.DEBUG, "format": LOG_FMT['extra_1']},
                            LOG_HDL_CNSL: {"level": logging.INFO, "format": LOG_FMT['detailed']}
                        })
log.info(f"Hello from logger {log.name}!")


def main():
    log.info(f"Start process to export Overture Maps data...")
    parser = argparse.ArgumentParser(description='Export Overture Map data tool', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--dbname', type=str, help='DuckDB name')
    parser.add_argument('--output_dir', type=str, help='Output directory')
    parser.add_argument('--tables', nargs='+', help='List of tables')
    parser.add_argument('--is_wm', action="store_true", help='Reproject data into the WebMercator coordinate system')
    parser.add_argument('--format', type=str, default='GPKG', help='Export data format')

    args = parser.parse_args()

    if args.dbname is None:
        log.error(f"Database name not specified, please specify dbname parameter")
        return

    _db_filename = Path(config.DB_DIR) / args.dbname

    if not _db_filename.exists():
        log.error(f"Database file {_db_filename} not exist in {config.DB_DIR}, "
                  f"please specify dbname parameter or db_dirs parameter in settings")
        return

    if args.output_dir is None:
        log.error(f"Output directory not specified, please specify output_dir parameter")
        return

    if not Path(args.output_dir).exists():
        Path(args.output_dir).mkdir(parents=True)
        log.debug(f"Created output directory {args.output_dir}")

    if args.format not in EXPORT_FORMAT:
        log.error(f"Format not supported: {args.format}")
        return

    log.info('-'*60)
    log.info(f"DuckDB name: {_db_filename}")
    log.info(f"Output directory {args.output_dir}")
    log.info(f"Tables: {args.tables}")
    log.info(f"Reproject data to Web Mercator: {args.is_wm}")
    log.info(f"Export data to format: {args.format}")
    log.info('-' * 60)

    export_class = ExportCore(class_logger=log)
    export_class.set_parameters(
        {
            'db_name': args.dbname,
            'output_dir': args.output_dir,
            'tables': args.tables,
            'is_wm': args.is_wm,
            'format': args.format
        }
    )

    if export_class.export_data():
        log.info(f"Export Overture Maps data - OK")
    else:
        log.error(f"Export Overture Maps data - Fail: {export_class.get_last_error()}")

    log.info(f"Process to export Overture Maps data finished")


if __name__ == "__main__":
    main()

# -*- coding:utf-8 -*-
# -----------------------------------------------------
# Project Name:
# Name: __init__.py
# Filename: __init__.py
# Author: mbegma
# Create data: 23.01.2023
# Description: 
# Copyright: (c) mbegma, 2024
# -----------------------------------------------------
from src.common.consts import RET_CODE_OK, RET_CODE_ERROR
from src.common.consts import SR_WEB_MERCATOR, SR_WGS84, SR_EQUIDISTANT_CONIC
from src.common.consts import EMPTY_POLYGON, EMPTY_POINT, EMPTY_LINE
# from src.common.consts import DIVISION_AREA_TBL, DIVISION_BOUNDARY_TBL, DIVISION

from src.common.custom_logger import get_log_filename, create_logger_ext, get_logger_random_name
from src.common.custom_logger import LOG_HDL_CNSL, LOG_HDL_ROT_FILE, LOG_HDL_FILE, LOG_FMT

from src.common import utilities
from src.common import query_templates






# -*- coding:utf-8 -*-
# -----------------------------------------------------
# Project Name: overturemaps
# Name: main
# Filename: main.py
# Author: mbegma
# Create data: 11.02.2026
# Description: 
#            
# Copyright: (c) mbegma, 2026
# History: 
#        - 11.02.2026: start of development
# -----------------------------------------------------
from sys import argv, exit
import os
import logging
from src.config import config
from src.common import create_logger_ext, get_log_filename
from src.common import LOG_HDL_CNSL, LOG_HDL_FILE, LOG_FMT
from src.common import utilities as u
from src.classes import Core
from colorama import init, Fore, Style
init()


log = create_logger_ext(logger_name=config.LOGGER_NAME,
                        logger_file_name=get_log_filename(config.LOG_DIR),
                        logger_handler_type_dict={
                            LOG_HDL_FILE: {"level": logging.DEBUG, "format": LOG_FMT['extra_1']},
                            LOG_HDL_CNSL: {"level": logging.DEBUG, "format": LOG_FMT['detailed']}
                        })
log.info(f"Hello from logger {log.name}!")

core = Core(class_logger=log)

class OrderProcessor:
    def __init__(self):
        self.handlers = {
            "0": self._action_0,
            "1": self._action_1,
            "2": self._action_2,
        }

    def process_execute(self, status):
        handler = self.handlers.get(status, self._handle_unknown)
        return handler()

    def _handle_unknown(self):
        log.warning(f"Unknown command")

    def _set_header(self, title_text: str, subtitle_text: str = '', clear: bool = True):
        if clear:
            os.system('cls' if os.name == 'nt' else 'clear')
        print("-" * 75)
        print(Fore.LIGHTBLUE_EX + Style.BRIGHT + f"{u.tab(2)}{title_text}" + Fore.RESET + Style.RESET_ALL)
        print(" ")
        # print(" " * 10 + "-" * 45)
        print(Fore.LIGHTYELLOW_EX + f"{u.tab(2)}{subtitle_text}" + Fore.RESET)
        print("-" * 75)
        input("Нажмите [Enter] для продолжения")

    def _action_0(self):
        print(Fore.LIGHTBLUE_EX + Style.BRIGHT + f"Вы действительно хотите прекратить работу (Y/N)?" + Fore.RESET + Style.RESET_ALL)
        # self._s0et_header('Вы действительно хотите прекратить работу (Y/N)?')
        if input("Y/N: ").strip().upper() == 'Y':
            return True
        else:
            return False

    def _action_1(self):
        self._set_header('1. Получение информации о релизах')
        _releases = core.fetch_releases_from_s3()

        if len(_releases) != 0:
            log.info("Получение информации о релизах - OK")
            print("Получение информации о релизах - OK")
            print(f"Релизы: {_releases}")
            return True
        else:
            log.error(f"Получение информации о релизах - Fail: {core.get_last_error()}")
            print(f"Получение информации о релизах - Fail: {core.get_last_error()}")
            return False

    def _action_2(self):
        self._set_header('2. Получение информации о регионах РФ (RU)')
        _regions = core.get_regions_name()

        if len(_regions) != 0:
            log.info("Получение информации о регионах РФ (RU) - OK")
            print("Получение информации о регионах РФ (RU) - OK")
            print(f"Регионы ({len(_regions)}): ")
            for _ in _regions:
                print(f"{u.tab(2)}{_}")
            _local_reg = input("Укажите необходимый регион: ").strip()
            log.debug(f"выбранный регион: {_local_reg}")
            if core.download_local_region_data(_local_reg):
                log.debug(f"data downloaded successfully for {_local_reg}")
                # запросить статистическую информацию о данных
            else:
                log.error(f"data for {_local_reg} download failed")
            return True
        else:
            log.error(f"Получение информации о регионах РФ - Fail: {core.get_last_error()}")
            print(f"Получение информации о регионах РФ - Fail: {core.get_last_error()}")
            return False


def _print_menu():
    os.system('cls' if os.name == 'nt' else 'clear')
    print("-"*75)
    print(Fore.LIGHTBLUE_EX + Style.BRIGHT + f"{u.tab(2)}Инструменты для подготовки")
    print(f"{u.tab()}данных Overture Maps (https://overturemaps.org/)")
    print(Fore.GREEN + f"{u.tab(2)}       ИГИТ, 2026")
    print(Fore.RESET + Style.RESET_ALL + "")
    print("-" * 75)

    print(" 1. Получение информации о релизах")
    print(" 2. Получение информации о регионах РФ")
    print('-'*75)
    print(" 0. Выход")
    print('-' * 75)


def main():
    # if len(argv) > 1:
    #     log.debug(Fore.GREEN + f"параметр: {argv[1]}" + Fore.RESET)
    #     _dalgan_gdb = argv[1]
    # else:
    #     log.error(Fore.RED + f"Не указан параметр" + Fore.RESET)
    #     exit()

    log.info(f"начало процесса подготовки данных ...")
    # 37.900113, 55.849313, 38.051175, 55.950173 - Щелково
    # 41.298079,56.799198,41.500639,56.900203 - Шуя
    _x_min = 0.0
    _x_max = 0.0
    _y_min = 0.0
    _y_max = 0.0
    _db_name = 'test_01'
    _region = ''
    core.set_parameters(
        {
            'x_min': _x_min,
            'x_max': _x_max,
            'y_min': _y_min,
            'y_max': _y_max,
            'db_name': _db_name,
            'local_region': _region
        }
    )
    processor = OrderProcessor()
    while True:
        _print_menu()
        option = input("Выберите: ").strip()
        result = processor.process_execute(option)
        if option == "0" and result:
            exit()

        input("Нажмите [Enter] для продолжения")



if __name__ == "__main__":
    main()

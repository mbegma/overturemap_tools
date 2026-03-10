# -*- coding:utf-8 -*-
# -----------------------------------------------------
# Project Name:
# Name: utilities
# Filename: utilities.py
# Author: mbegma
# Create data: 09.02.2022
# Description: 
# Copyright: (c) mbegma, 2024
# -----------------------------------------------------
import random
import string
import time
import math
from os import sep, path, makedirs
from uuid import uuid4
import logging
from src.config import config


# local_log = logging.getLogger(__name__)
local_log = logging.getLogger(config.LOGGER_NAME)


def time_of_function(function):
    def wrapped(*args, **kwargs):
        start_time = time.time()
        res = function(*args, **kwargs)
        est_time = time.time() - start_time
        if est_time < 300:
            msg = f"{function.__name__} running: {est_time:.4f} sec."
        else:
            msg = f"{function.__name__} running: more then {est_time / 60:.4f} min. ({est_time} sec.)"
        print(msg)
        local_log.debug(msg)
        return res

    return wrapped


def tab(n:int=1):
    return "\t" * n


def random_string(size=8, chars=string.ascii_lowercase):
    """
    Функция генерирует случайную строку длинной size из chars
    :param size: длинна сгенерированной строки
    :param chars: последовательность символов из которых происходит генерация
    :return: строка
    """
    return ''.join(random.choice(chars) for _ in range(size))


def get_guid_format(upper_format=True):
    """
    Функция формирует строку GUID со скобками
    :param upper_format: признак генерации в upper case
    :return: '{GUID}'
    """
    if upper_format:
        return '{{{0}}}'.format(uuid4()).upper()
    else:
        return '{{{0}}}'.format(uuid4()).lower()


def save_to_file(file_name, data) -> bool:
    try:
        with open(file_name, 'w') as f:
            if isinstance(data, list):
                for item in data:
                    f.write('{0}\n'.format(item))
            else:
                f.write('{0}\n'.format(data))
        return True
    except Exception as e:
        local_log.error(str(e.args))
        return False


def main():
    pass


if __name__ == "__main__":
    main()

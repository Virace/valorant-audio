# -*- coding: utf-8 -*-
# @Author  : Virace
# @Email   : Virace@aliyun.com
# @Site    : x-item.com
# @Software: Pycharm
# @Create  : 2022/8/16 0:15
# @Update  : 2023/10/16 22:36
# @Detail  : 通用函数

import os
import re
import shutil
import time
from collections import defaultdict

from loguru import logger


def str_get_number(s):
    """
    从字符串中提取数字
    :param s:
    :return:
    """
    i = [*filter(str.isdigit, s)]
    if i:
        return int(''.join([*i]))


def tree():
    """
    defaultdict 创建一个带默认值的dict，默认值为自身
    :return:
    """
    return defaultdict(tree)


def makedirs(path, clear=False):
    """
    如果文件夹不存在，则使用os.makedirs创建文件，存在则不处理
    :param path: 路径
    :param clear: 是否清空文件夹，创建前直接清空文件夹
    :return:
    """
    try:
        if clear and os.path.exists(path):
            shutil.rmtree(path)

        if not os.path.exists(path):
            os.makedirs(path)

    except FileExistsError as _:
        pass


def check_time(func):
    """
    获取函数执行时间
    :param func:
    :return:
    """

    def wrapper(*args, **kwargs):
        st = time.time()
        ret = func(*args, **kwargs)
        logger.debug(f'Func: {func.__module__}.{func.__name__}, Time Spent: {round(time.time() - st, 2)}')
        return ret

    return wrapper


def replace(data, repl):
    """
    替换
    :param data:
    :param repl:键值对
    :return:
    """
    for key, value in repl.items():
        data = data.replace(key, value)
    return data


def re_replace(data, repl):
    """
    正则替换
    :param data:
    :param repl: 键值对
    :return:
    """

    def replf(v):
        def temp(mobj):
            match = mobj.groups()[0]
            if match:
                return v.format(match)
            else:
                return v.replace('{}', '')

        return temp

    for key, value in repl.items():
        if '{}' in value:
            value = replf(value)
        data = re.compile(f'{key}', re.I).sub(value, data)
    return data


def confirm(text):
    """
    确认 y/n
    :return:
    """
    while True:
        logger.warning(f'\n{text} [y/n]: ')
        # i = input(f'\n{text} [y/n]: ')
        i = input('')
        if i.lower() == 'y':
            return True
        elif i.lower() == 'n':
            return False
        else:
            print('输入错误, 请重新输入.')

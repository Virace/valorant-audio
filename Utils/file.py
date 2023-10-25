# -*- coding: utf-8 -*-
# @Author  : Virace
# @Email   : Virace@aliyun.com
# @Site    : x-item.com
# @Software: Pycharm
# @Create  : 2023/10/25 22:57
# @Update  : 2023/10/26 0:35
# @Detail  : 

import hashlib
import os
import shutil
from typing import BinaryIO, Union


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


def get_file_sha256(file: Union[str, bytes, BinaryIO], chunk_size=1024):
    """
    计算文件的sha256值
    :param file: 文件路径或者文件内容.
    :param chunk_size: 读取文件的块大小
    """
    if isinstance(file, str):
        with open(file, "rb") as f:
            return get_file_sha256(f, chunk_size)

    elif isinstance(file, bytes):
        return hashlib.sha256(file).hexdigest()
    else:
        sha256 = hashlib.sha256()
        while True:
            chunk = file.read(chunk_size)
            if not chunk:
                break
            sha256.update(chunk)
        return sha256.hexdigest()


def get_file_size(filename):
    """
    获取文件大小
    """
    return os.stat(filename).st_size


def get_valorant_version(path):
    # https://github.com/Morilli/riot-manifests/blob/ebee7f7253a18898a02601ace90ed6492c7f9c6b/VALORANT.py#L7
    with open(path, "rb") as exe_file:
        data = exe_file.read()
        pattern = "++Ares-Core+release-".encode("utf-16le")
        pos = data.find(pattern) + len(pattern)
        short_version = data[pos:pos + 10].decode("utf-16le")
        pos += 10
        version = '\0'
        while '\0' in version:
            pos += 2
            version = data[pos:pos + 32].decode("utf-16le").rstrip("\x00")
        return version

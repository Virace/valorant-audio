# -*- coding: utf-8 -*-
# @Author  : Virace
# @Email   : Virace@aliyun.com
# @Site    : x-item.com
# @Software: Pycharm
# @Create  : 2023/10/26 0:39
# @Update  : 2023/10/26 13:17
# @Detail  : 

from dataclasses import dataclass


@dataclass(frozen=True)
class AudioHash:
    id: str
    event: str
    size: int
    sha256: str

    def __str__(self):
        return f"{self.id} {self.event} {self.size} {self.sha256}"

    def __repr__(self):
        return self.__str__()

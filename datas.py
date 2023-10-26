# -*- coding: utf-8 -*-
# @Author  : Virace
# @Email   : Virace@aliyun.com
# @Site    : x-item.com
# @Software: Pycharm
# @Create  : 2023/10/26 0:39
# @Update  : 2023/10/26 16:13
# @Detail  : 

from dataclasses import dataclass


@dataclass(frozen=True)
class AudioHash:
    id: str
    event: str
    size: int
    sha256: str

    def __str__(self):
        return f"Id:{self.id}, Event:{self.event}, Size:{self.size}, SHA:{self.sha256}"

    def __repr__(self):
        return self.__str__()

    def __hash__(self):
        return hash(f'{self.id}{self.event}{self.size}{self.sha256}')

    def __eq__(self, other):
        return (self.id == other.id and self.event == other.event and
                self.size == other.size and self.sha256 == other.sha256)


class ValorantAudioInfo(object):
    def __init__(self, version='', files: list[AudioHash] = None):
        self.version = version
        self.files = files or list()

    def __str__(self):
        return f"{self.version} {len(self.files)}"

    def __repr__(self):
        return self.__str__()

    def diff(self, other):
        """
        比较两个版本的文件差异
        :param other:
        :return: （新增, 删除）
        """

        # 新diff旧返回的是新增的文件
        # 旧diff新返回的是删除的文件
        a = {i for i in self.files}
        b = {i for i in other.files}
        ad = a.difference(b)
        bd = b.difference(a)

        # 07.08.00.1007528
        # 对比版本号
        # 大版本， 小版本， 0 ，修订数？
        avb, avs, _, ava = self.version.split('.')
        bvb, bvs, _, bva = other.version.split('.')

        # 偷个懒，只用修订数来判断哪个是新版本
        if float(ava) > float(bva):
            return ad, bd
        return bd, ad


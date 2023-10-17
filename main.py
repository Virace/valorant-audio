# -*- coding: utf-8 -*-
# @Author  : Virace
# @Email   : Virace@aliyun.com
# @Site    : x-item.com
# @Software: Pycharm
# @Create  : 2023/10/13 22:38
# @Update  : 2023/10/17 22:09
# @Detail  : 

import gc
import json
import os
import shutil

from UE4Parse.Assets.Objects.FGuid import FGuid
from UE4Parse.Encryption import FAESKey
from UE4Parse.PakFile.PakObjects.FPakEntry import FPakEntry
from UE4Parse.Provider import DefaultFileProvider
from UE4Parse.Versions import EUEVersion, VersionContainer
from bs4 import BeautifulSoup
from loguru import logger

from Utils import common
from config import AES_KEY, GAME_PATH, LOCALIZATION, OUTPUT_PATH, PACKAGE_PREFIX
from hook.wwiser.parser import wparser
from hook.wwiser.viewer import wdumper


# 1. 先取出{LOCALIZATION}_Audio-WindowsClient.pak，存放于临时目录
# 2. 挂载pak文件
# todo: 3. 遍历挂载目录，解析Event并取出wem


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


class ValorantAudio:
    def __init__(self, game_path=GAME_PATH, out_path=OUTPUT_PATH, aes_key=AES_KEY,
                 localization=LOCALIZATION, package_prefix=PACKAGE_PREFIX):
        """
        初始化
        :param game_path: 游戏目录
        :param out_path: 输出目录
        :param aes_key: 解密密钥
        :param localization: 语言
        :param package_prefix: 前缀
        :return:
        """
        self.game_path = game_path
        logger.info(f'游戏目录: {self.game_path}')
        self.out_path = out_path
        self.game_version = get_valorant_version(
            os.path.join(self.game_path, 'ShooterGame/Binaries/Win64/VALORANT-Win64-Shipping.exe'))

        logger.info(f'游戏版本号: {self.game_version}')
        self.aes_key = aes_key
        self.localization = localization
        self.package_prefix = package_prefix

        self.TEMP_PATH = os.path.join(self.out_path, 'temps')

        # 相关目录加入游戏版本号，为后续取差异做准备
        self.PAKS_PATH = os.path.join(self.out_path, 'paks', self.game_version)
        self.HASH_PATH = os.path.join(self.out_path, 'hashes', self.game_version)
        self.AUDIO_PATH = os.path.join(self.out_path, 'audios', self.game_version)

        common.makedirs(self.TEMP_PATH, True)
        common.makedirs(self.PAKS_PATH)
        common.makedirs(self.HASH_PATH)
        common.makedirs(self.AUDIO_PATH)

        self.audio_hash_file = os.path.join(self.HASH_PATH, 'data.json')

        self.pak_file = os.path.join(self.PAKS_PATH, f'{self.localization}_Audio-WindowsClient.pak')

        # 如果文件存在，则询问是否继续
        if os.path.exists(self.pak_file):
            if not common.confirm('目录中PAK文件已存在，是否继续？(继续则将重新解析当前版本.)'):
                raise FileExistsError(f'{self.pak_file}已存在，退出程序')

        common.makedirs(self.PAKS_PATH, True)
        self._copy_pak_file()

        logger.debug(f'pak文件: {self.pak_file}')

        self.provider = None

    def _copy_pak_file(self):
        """
        复制pak文件
        :return:
        """
        game_pak = os.path.join(self.game_path, 'ShooterGame/Content/Paks',
                                f'{self.localization}_Audio-WindowsClient.pak')

        if os.path.exists(game_pak):
            shutil.copyfile(game_pak, self.pak_file)
        else:
            raise FileNotFoundError(
                f'游戏目录下不存在{self.localization}_Audio-WindowsClient.pak，检查游戏目录是否正确')

    @classmethod
    def _get_file(cls, file: FPakEntry, raw=False):
        """
        获取文件内容
        :param file:
        :param raw:
        :return:
        """
        if raw:
            return file.get_data().base_stream
        else:
            return file.get_data().read()

    def mount_paks(self):
        """
        挂载pak文件, 返回文件列表
        :return:
        """
        aeskeys = {FGuid(0, 0, 0, 0): FAESKey(AES_KEY)}

        gc.disable()

        self.provider = DefaultFileProvider(self.PAKS_PATH, VersionContainer(EUEVersion.GAME_VALORANT))
        self.provider.initialize()
        self.provider.submit_keys(aeskeys)

        # provider.load_localization('zh-CN')

        # 因为目录中只有一个paks文件，所以取第一个
        return self.provider.files.Storage[0].files

    def get_audio_ids(self, bnk: FPakEntry):
        """
        获取音频id
        :return:
        """

        # if isinstance(bnk, bytes):
        #
        #     parser.parse_bank(name, raw=BytesIO(bnk))
        # else:
        #     # 后缀名不为bnk则报错
        #     if bnk.Name.split('.')[-1] != 'bnk':
        #         raise TypeError(f'文件{bnk.Name}不是bnk文件')
        #     # parse_bank 第一个参数如果从内存直接读取则可以给虚假值， 但只能从dumper中调用get_xml_raw，其他任何write_x 函数都会造成不可预估错误
        #     parser.parse_bank(bnk.Name, raw=bnk.get_data().base_stream)
        parser = wparser.Parser()
        parser.parse_bank(bnk.Name, raw=self._get_file(bnk, True))
        banks = parser.get_banks()

        dumper = wdumper.DumpPrinter(banks, 'none', '')
        data = dumper.get_xml_raw()

        ids = []
        soup = BeautifulSoup(data, features="lxml")
        sounds = soup.find_all('object', {'name': 'CAkSound'})
        for item in sounds:
            bank_data = item.find('object', {'name': 'AkBankSourceData'})
            stream_type = bank_data.find('field', {'name': 'StreamType'})
            sid = item.find('field', {'name': 'sourceID'})

            # if stream_type.attrs['value'] != '0':
            #     logger.debug(f'添加{sid.attrs["value"]} - {stream_type.attrs["value"]}')
            #     ids.append(sid.attrs['value'])
            # else:
            #     logger.debug(f'跳过{sid.attrs["value"]}，因为stream_type为{stream_type.attrs["value"]}')
            ids.append(sid.attrs['value'])

        return ids

    def get_audio_hash(self):
        """
        获取音频hash
        """
        result = dict()
        files = self.mount_paks()

        for name, file in files.items():

            if 'Event' in name:

                # Play_VO_Rift_LastRoundofHalfasAttackers
                # Play_HURM_Multikill_Gekko
                _, _type, _item, *_event = name.split('_')

                if _type not in result:
                    result[_type] = dict()

                if _item not in result[_type]:
                    result[_type][_item] = dict()
                _event = '_'.join(_event)

                # logger.debug(f'解析{name}')
                ids = self.get_audio_ids(file)
                logger.debug(f'解析{os.path.basename(name)}，共{len(ids)}个音频')
                if len(ids) == 0:
                    logger.warning(f'解析{os.path.basename(name)}，未找到音频')
                result[_type][_item][_event] = ids

        with open(self.audio_hash_file, 'w+', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=4)

        return result

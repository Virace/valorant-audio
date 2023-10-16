# -*- coding: utf-8 -*-
# @Author  : Virace
# @Email   : Virace@aliyun.com
# @Site    : x-item.com
# @Software: Pycharm
# @Create  : 2023/10/13 22:38
# @Update  : 2023/10/16 23:24
# @Detail  : 

import gc
import os
import shutil
import xml.etree.ElementTree as ET

from UE4Parse.Assets.Objects.FGuid import FGuid
from UE4Parse.Encryption import FAESKey
from UE4Parse.PakFile.PakObjects.FPakEntry import FPakEntry
from UE4Parse.Provider import DefaultFileProvider
from UE4Parse.Versions import EUEVersion, VersionContainer
from loguru import logger

from Utils import common
from config import AES_KEY, GAME_PATH, LOCALIZATION, OUTPUT_PATH, PACKAGE_PREFIX
from hook.wwiser.parser import wparser
from hook.wwiser.viewer import wdumper


# 1. 先取出{LOCALIZATION}_Audio-WindowsClient.pak，存放于临时目录
# todo: 2. 挂载pak文件
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
        logger.debug(f'游戏目录: {self.game_path}')
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

    def get_audio_ids_from_bnk(self, bnk: FPakEntry):
        """
        获取音频id
        :return:
        """
        # 后缀名不为bnk则报错
        if bnk.Name.split('.')[-1] != 'bnk':
            raise TypeError(f'文件{bnk.Name}不是bnk文件')

        parser = wparser.Parser()

        # parse_bank 第一个参数如果从内存直接读取则可以给虚假值， 但只能从dumper中调用get_xml_raw，其他任何write_x 函数都会造成不可预估错误
        parser.parse_bank(bnk.Name, raw=bnk.get_data().base_stream)
        banks = parser.get_banks()

        dumper = wdumper.DumpPrinter(banks, 'none', '')
        data = dumper.get_xml_raw()
        # if 'VO' not in bnk.Name:
        #     with open(os.path.join(self.TEMP_PATH, f'{os.path.basename(bnk.Name)}.xml'), 'w+', encoding='utf-8') as f:
        #         f.write(data)
        # return
        root = ET.fromstring(data)
        # 寻找name为AkMediaInformation的所有子节点
        ids = []
        for item in root.findall("./object[@name='HircChunk']/list/object[@name='CAkSound']"
                                 "/object[@name='SoundInitialValues']"):
            for sound in item.findall('*[@name="AkBankSourceData"]/*[@name="AkMediaInformation"]/*[@name="sourceID"]'):
                ids.append(sound.get('value'))

        return ids

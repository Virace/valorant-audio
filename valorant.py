# -*- coding: utf-8 -*-
# @Author  : Virace
# @Email   : Virace@aliyun.com
# @Site    : x-item.com
# @Software: Pycharm
# @Create  : 2023/10/26 13:18
# @Update  : 2023/10/26 16:56
# @Detail  : 

import json
import os
import shutil
import traceback
from concurrent.futures import ProcessPoolExecutor, as_completed

from UE4Parse.Assets.Objects.FGuid import FGuid
from UE4Parse.Encryption import FAESKey
from UE4Parse.PakFile.PakObjects.FPakEntry import FPakEntry
from UE4Parse.Provider import DefaultFileProvider
from UE4Parse.Versions import EUEVersion, VersionContainer
from bs4 import BeautifulSoup
from loguru import logger

import Utils.file
from Utils import common
from Utils.common import wem2wav
from config import AES_KEY, GAME_PATH, LOCALIZATION, OUTPUT_PATH, PACKAGE_PREFIX, VGMSTREAM_PATH
from datas import AudioHash, ValorantAudioInfo
from hook.wwiser.parser import wparser
from hook.wwiser.viewer import wdumper

from typing import Union


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
        self.game_version = Utils.file.get_valorant_version(
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

        Utils.file.makedirs(self.TEMP_PATH, True)
        Utils.file.makedirs(self.PAKS_PATH)
        Utils.file.makedirs(self.HASH_PATH)
        Utils.file.makedirs(self.AUDIO_PATH)

        self.event_hash_file = os.path.join(self.HASH_PATH, 'event.json')
        self.audio_hash_file = os.path.join(self.HASH_PATH, 'audio.json')

        self.pak_file = os.path.join(self.PAKS_PATH, f'{self.localization}_Audio-WindowsClient.pak')

        # 如果文件存在，则询问是否继续
        if os.path.exists(self.pak_file):
            if not common.confirm('目录中PAK文件已存在，是否继续？(继续则将重新解析当前版本.)'):
                raise FileExistsError(f'{self.pak_file}已存在，退出程序')

        Utils.file.makedirs(self.PAKS_PATH, True)
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
    def _get_file(cls, file: FPakEntry, stream=False):
        """
        获取文件内容
        :param file:
        :param stream:
        :return:
        """
        if stream:
            return file.get_data().base_stream
        else:
            return file.get_data().read()

    def mount_paks(self):
        """
        挂载pak文件, 返回文件列表
        :return:
        """
        aeskeys = {FGuid(0, 0, 0, 0): FAESKey(AES_KEY)}

        # gc.disable()

        self.provider = DefaultFileProvider(self.PAKS_PATH, VersionContainer(EUEVersion.GAME_VALORANT))
        self.provider.initialize()
        self.provider.submit_keys(aeskeys)

        # provider.load_localization('zh-CN')

        # 因为目录中只有一个paks文件，所以取第一个
        return self.provider.files.Storage[0].files

    def get_audio_ids(self, bnk: FPakEntry):
        """
        获取音频id
        :param bnk: bnk文件
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
            # bank_data = item.find('object', {'name': 'AkBankSourceData'})
            # stream_type = bank_data.find('field', {'name': 'StreamType'})
            sid = item.find('field', {'name': 'sourceID'})

            # if stream_type.attrs['value'] != '0':
            #     logger.debug(f'添加{sid.attrs["value"]} - {stream_type.attrs["value"]}')
            #     ids.append(sid.attrs['value'])
            # else:
            #     logger.debug(f'跳过{sid.attrs["value"]}，因为stream_type为{stream_type.attrs["value"]}')
            ids.append(sid.attrs['value'])

        logger.info(f'解析{os.path.basename(bnk.Name)}，共{len(ids)}个音频')

        # (长度, 名称) 排序
        ids.sort(key=lambda x: (len(x), x))

        return ids

    @common.check_time
    def get_audio_hash(self, files=None, save_file=False):
        """
        获取音频hash.
        :param files:
        :param save_file: 是否保存文件, 计算文件校验码时可直接保存文件(wem)
        """

        # 字典递归排序
        def sort_dict(data, key=lambda x: x[0], reverse=False):
            """
            字典递归排序, 列表不动
            :param data:
            :param key:
            :param reverse:
            :return:
            """
            if isinstance(data, dict):
                return {k: sort_dict(v, key, reverse) for k, v in
                        sorted(data.items(), key=key, reverse=reverse)}
            elif isinstance(data, list):
                return [sort_dict(v, key, reverse) for v in data]
            else:
                return data

        event_hash = dict()
        audio_hash = dict()
        if files is None:
            files = self.mount_paks()

        for name, file in files.items():

            if 'Event' in name:

                # Play_VO_Rift_LastRoundofHalfasAttackers
                # Play_HURM_Multikill_Gekko
                _, _type, _item, *_event = name.split('_')

                if _type not in event_hash:
                    event_hash[_type] = dict()

                if _item not in event_hash[_type]:
                    event_hash[_type][_item] = dict()
                _event = '_'.join(_event)

                # logger.debug(f'解析{name}')
                ids = self.get_audio_ids(file)
                logger.debug(f'解析{os.path.basename(name)}，共{len(ids)}个音频')
                if len(ids) == 0:
                    logger.warning(f'解析{os.path.basename(name)}，未找到音频')
                event_hash[_type][_item][_event] = ids

            elif 'Media' in name:
                file_raw = self._get_file(file, False)

                audio_hash[os.path.basename(name)] = dict(size=file.get_size(),
                                                          sha256=Utils.file.get_file_sha256(file_raw))
                if save_file:
                    # 减少IO
                    this_file = os.path.join(self.AUDIO_PATH, os.path.basename(file.Name))
                    with open(this_file, 'wb') as f:
                        f.write(file_raw)

        # 保存哈希值
        event_hash = sort_dict(event_hash)
        with open(self.event_hash_file, 'w+', encoding='utf-8') as f:
            json.dump({'data': event_hash, 'version': self.game_version, 'type': 'event_hash'}, f, ensure_ascii=False,
                      indent=4)

        audio_hash = sort_dict(audio_hash, key=lambda x: (len(x[0]), x[0]))
        with open(self.audio_hash_file, 'w+', encoding='utf-8') as f:
            json.dump({'data': audio_hash, 'version': self.game_version, 'type': 'audio_hash'}, f, ensure_ascii=False,
                      indent=4)

        return event_hash

    def get_audio(self, files=None):
        """
        获取音频
        :param files:
        """
        if files is None:
            files = self.mount_paks()

        # 只有转码用多线程
        with ProcessPoolExecutor(max_workers=32) as e:
            fs = dict()
            for name, file in files.items():
                if 'Event' in name:
                    continue

                filename = os.path.join(self.AUDIO_PATH, os.path.basename(file.Name))

                # 如果文件不存在或者文件大小不一致则重新写入
                if not os.path.exists(filename) or os.path.getsize(filename) != file.get_size():
                    logger.debug(f'写入{os.path.basename(file.Name)}')
                    with open(filename, 'wb') as f:
                        f.write(self._get_file(file))

                wav_file = os.path.splitext(filename)[0] + '.wav'
                if not os.path.exists(wav_file):
                    fs[e.submit(wem2wav, VGMSTREAM_PATH, filename,
                                wav_file, True)] = filename

            for f in as_completed(fs):
                try:
                    f.result()
                except Exception as exc:
                    traceback.print_exc()

    @common.check_time
    def organize_audio_files(self):
        """
        整理音频文件
        """

        if not os.path.exists(self.event_hash_file) or os.path.getsize(self.event_hash_file) == 0:
            self.get_audio_hash(save_file=True)

        with open(self.event_hash_file, 'r', encoding='utf-8') as f:
            hash_data = json.load(f)

        for _type, _items in hash_data.items():
            # 类型
            _type_path = os.path.join(self.AUDIO_PATH, _type)
            if not os.path.exists(_type_path):
                os.makedirs(_type_path)

            # VO的话为英雄名， 其他还是类型
            for _name, _events in _items.items():
                _name_path = os.path.join(_type_path, _name)
                if not os.path.exists(_name_path):
                    os.makedirs(_name_path)

                for _event, _ids in _events.items():
                    for _id in _ids:
                        src = os.path.join(self.AUDIO_PATH, f'{_id}.wav')
                        if not os.path.exists(src):
                            logger.warning(f'音频文件{_id}.wav不存在，跳过')
                            continue

                        dst = os.path.join(_name_path, f'{_event}{"-" if _event else ""}{_id}.wav')
                        # logger.info(f'{dst}')
                        shutil.move(src, dst)

    def __del__(self):
        if self.provider:
            self.provider.close()


# 根据事件和音频哈希文件读取audio_info
def get_audio_info(event_hash: Union[str, dict], audio_hash: Union[str, dict]):
    """
    根据事件和音频哈希文件读取audio_info
    :param event_hash:
    :param audio_hash:
    :return:
    """
    if isinstance(event_hash, str):
        with open(event_hash, 'r', encoding='utf-8') as f:
            event_data = json.load(f)
    elif isinstance(event_hash, dict):
        event_data = event_hash
    else:
        raise TypeError(f'event_hash类型错误，应为str或dict，当前类型为{type(event_hash)}')

    if isinstance(audio_hash, str):
        with open(audio_hash, 'r', encoding='utf-8') as f:
            audio_data = json.load(f)
    elif isinstance(audio_hash, dict):
        audio_data = audio_hash
    else:
        raise TypeError(f'event_hash类型错误，应为str或dict，当前类型为{type(event_hash)}')

    files = []
    event_version = event_data['version']
    audio_version = audio_data['version']
    if event_version != audio_version:
        logger.warning(f'事件哈希版本{event_version}与音频哈希版本{audio_version}不一致，可能会造成不可预知的错误')
        return

    audio_data = audio_data['data']

    for _type, _items in event_data['data'].items():
        for _name, _events in _items.items():
            for _event, _ids in _events.items():
                for _id in _ids:
                    event = f'{_type}-{_name}{"-" if _event else ""}{_event}'
                    if _id not in audio_data:
                        size = 0
                        sha256 = ''
                    else:
                        size = audio_data[_id]['size']
                        sha256 = audio_data[_id]['sha256']
                    _hash = AudioHash(id=_id, event=event, size=size, sha256=sha256)
                    files.append(_hash)

    return ValorantAudioInfo(version=event_version, files=files)

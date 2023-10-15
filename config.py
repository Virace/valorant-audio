# -*- coding: utf-8 -*-
# @Author  : Virace
# @Email   : Virace@aliyun.com
# @Site    : x-item.com
# @Software: Pycharm
# @Create  : 2023/10/14 14:26
# @Update  : 2023/10/15 20:46
# @Detail  : 配置文件

import os

# 解密密钥 https://discord.com/channels/637265123144237061/1090601049909362739/1090601049909362739
AES_KEY = '0x4BE71AF2459CF83899EC9DC2CB60E22AC4B3047E0211034BBABE9D174C069DD6'

# 游戏目录
GAME_PATH = ''

# 输出目录
OUTPUT_PATH = ''

# 语言 (zh_CN_Audio-WindowsClient.pak则取zh_CN)
LOCALIZATION = 'zh_CN'

# 前缀
PACKAGE_PREFIX = 'ShooterGame/Content/WwiseAudio'

# vgmstream cli程序, 用来转码, 如果不提供则默认输出为wem格式。
VGMSTREAM_PATH = ""

######################################################
#                ！！！！！！！！！！                #
#                以下配置无需手动修改                #
#                ！！！！！！！！！！                #
######################################################

# PAK 目录，每次启动会清空
PAK_PATH = os.path.join(OUTPUT_PATH, 'paks')

# 缓存目录，临时文件存放处
TEMP_PATH = os.path.join(OUTPUT_PATH, 'temps')

# 哈希目录，存放所有与 k,v 相关数据
HASH_PATH = os.path.join(OUTPUT_PATH, 'hashes')

# 音频目录，最终解包生成的音频文件都放在这
AUDIO_PATH = os.path.join(OUTPUT_PATH, 'audios')

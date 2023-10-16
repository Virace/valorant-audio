# -*- coding: utf-8 -*-
# @Author  : Virace
# @Email   : Virace@aliyun.com
# @Site    : x-item.com
# @Software: Pycharm
# @Create  : 2023/10/14 14:26
# @Update  : 2023/10/16 23:25
# @Detail  : 配置文件

# 解密密钥 https://discord.com/channels/637265123144237061/1090601049909362739/1090601049909362739
AES_KEY = '0x4BE71AF2459CF83899EC9DC2CB60E22AC4B3047E0211034BBABE9D174C069DD6'

# 游戏目录，选择游戏目录中live文件夹，该文件夹下一般有 VALORANT.exe 以及 ShooterGame文件夹 等其他文件
GAME_PATH = ''

# 输出目录
OUTPUT_PATH = ''

# 语言 (zh_CN_Audio-WindowsClient.pak则取zh_CN)
LOCALIZATION = 'zh_CN'

# 前缀
PACKAGE_PREFIX = 'ShooterGame/Content/WwiseAudio'

# vgmstream cli程序, 用来转码, 如果不提供则默认输出为wem格式。
VGMSTREAM_PATH = ""
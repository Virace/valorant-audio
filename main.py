# -*- coding: utf-8 -*-
# @Author  : Virace
# @Email   : Virace@aliyun.com
# @Site    : x-item.com
# @Software: Pycharm
# @Create  : 2023/10/13 22:38
# @Update  : 2023/11/26 20:53
# @Detail  : 

from valorant import ValorantAudio

va = ValorantAudio(
    game_path=r"游戏目录",
    out_path=r"输出目录",
    localization="zh_CN",
    package_prefix="ShooterGame/Content/WwiseAudio",
)
va.organize_audio_files()

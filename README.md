[![Python][requires-python]][python-url]
[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![MIT License][license-shield]][license-url]

<br />
<div align="center">
  <a href="https://github.com/Virace/valorant-audio">
  </a>

<h3 align="center">valorant-audio</h3>

  <p align="center">
    自动化提取并整理游戏内台词音频文件
  </p>
</div>

## 目录

- [上手指南](#上手指南)
    - [开发前的配置要求](#开发前的配置要求)
    - [使用方法](#使用方法)
    - [注意事项](#注意事项)
- [文件目录说明](#文件目录说明)
- [维护者](#维护者)
- [感谢](#感谢)
- [许可证](#许可证)

### 上手指南

###### 开发前的配置要求

1. Python 3.10
2. Poetry(非必须)

3.10是必要的，至少在2023年10月23日的时候是这样的，3.11以及3.12无法正常安装UE4Parse

###### **使用方法**

1. Clone
   ```sh
   git clone https://github.com/Virace/valorant-audio.git  --recursive
   ```
2. 安装依赖
   ```sh
   pip install -r requirements.txt
   ```
   or
   ```sh
   poetry install
   ```
3. 启动脚本
   随便创建一个文件，比如`run.py`，内容可参考`main.py`：
   ```python
   from valorant import ValorantAudio
   va = ValorantAudio()
   va.organize_audio_files()
   ```
   
4. 执行脚本
   执行前确保配置文件中游戏路径以及输出路径正确。如果你不喜欢配置文件方式执行脚本或想把此脚本作为模块使用，也可以查看**ValorantAudio**类的构造函数，是可以将相关参数直接在创建对象时传入的。
   ```python
   from valorant import ValorantAudio
   va = ValorantAudio(
        game_path=r"游戏目录",
        out_path=r"输出目录",
        localization="zh_CN",
        package_prefix="ShooterGame/Content/WwiseAudio",
    )
   va.organize_audio_files()
   ```
5. 配置文件
   三种方法可以给ValorantAudio传入参数，
       
       - 通过构造函数
       - 通过config.py文件
       - 通过环境变量
   构造函数优先级最高。 

   其中环境变量为了做出区分，加入了VAL_前缀
     ```
    VAL_ENV_ONLY
   
    VAL_GAME_PATH
    VAL_OUTPUT_PATH
    VAL_LOCALIZATION
    VAL_VGMSTREAM_PATH
    VAL_PACKAGE_PREFIX
    ```
   **VAL_ENV_ONLY** 为 True 时，会优先使用环境变量，否则会优先使用config.py。
   

 

###### 注意事项




### 文件目录说明

###### 代码目录
hook是为了让wwiser可以直接作为模块使用，就改了部分源文件。

###### 输出目录
audios、hashes、paks以及temps文件夹。

**audios**: 为提取出的音频文件 

**hashes**: 为提取出的音频文件的哈希值，用于分类

**paks**: 因为wwiser代码默认挂载文件夹下所有paks文件，所以这里将需要的复制到此文件夹下，以便提高解析速度

**temps**: 临时文件夹

### 维护者

**Virace**

- blog: [孤独的未知数](https://x-item.com)

### 感谢

- [@MinshuG](https://github.com/MinshuG/pyUE4Parse), **pyUE4Parse**
- [@bnnm](https://github.com/bnnm/wwiser), **wwiser**
- [@vgmstream](https://github.com/vgmstream/vgmstream), **vgmstream**
- [@Morilli](https://github.com/Morilli/riot-manifests), **riot-manifests**

- 以及**JetBrains**提供开发环境支持

  <a href="https://www.jetbrains.com/?from=kratos-pe" target="_blank"><img src="https://cdn.jsdelivr.net/gh/virace/kratos-pe@main/jetbrains.svg"></a>

### 许可证

[MIT](LICENSE)

<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->

[contributors-shield]: https://img.shields.io/github/contributors/Virace/valorant-audio.svg?style=for-the-badge

[contributors-url]: https://github.com/Virace/valorant-audio/graphs/contributors

[forks-shield]: https://img.shields.io/github/forks/Virace/valorant-audio.svg?style=for-the-badge

[forks-url]: https://github.com/Virace/valorant-audio/network/members

[stars-shield]: https://img.shields.io/github/stars/Virace/valorant-audio.svg?style=for-the-badge

[stars-url]: https://github.com/Virace/valorant-audio/stargazers

[issues-shield]: https://img.shields.io/github/issues/Virace/valorant-audio.svg?style=for-the-badge

[issues-url]: https://github.com/Virace/valorant-audio/issues

[license-shield]: https://img.shields.io/github/license/Virace/valorant-audio.svg?style=for-the-badge

[license-url]: https://github.com/Virace/valorant-audio/blob/master/LICENSE.txt

[python-url]: https://www.python.org/downloads/release/python-31013/

[requires-python]: https://img.shields.io/python/required-version-toml?tomlFilePath=https%3A%2F%2Fraw.githubusercontent.com%2FVirace%2Fvalorant-audio%2Fmain%2Fpyproject.toml&style=for-the-badge

[product-screenshot]: images/screenshot.png



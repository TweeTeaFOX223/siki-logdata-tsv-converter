
# siki-logdata-tsv-converter
- [siki-logdata-tsv-converter](#siki-logdata-tsv-converter)
- [基本説明](#基本説明)
- [スクリプトの機能](#スクリプトの機能)
  - [★スレッドログをTSVファイルに変換(src/main\_B\_1.py)](#スレッドログをtsvファイルに変換srcmain_b_1py)
    - [board.tsv(全掲示板のリスト)](#boardtsv全掲示板のリスト)
    - [threads.tsv(全スレッドのリスト)](#threadstsv全スレッドのリスト)
    - [posts.tsv(全レスポンスのリスト)](#poststsv全レスポンスのリスト)
    - [alldata.tsv(上3つの情報を全部結合したもの)](#alldatatsv上3つの情報を全部結合したもの)
  - [おまけ：↑のTSVファイルを分析して統計情報を出す(src/main\_B\_2.py)](#おまけのtsvファイルを分析して統計情報を出すsrcmain_b_2py)
    - [word\_frequencies.csv(各単語の出現回数)](#word_frequenciescsv各単語の出現回数)
    - [monthly\_counts\_{指定単語}.csv(指定した単語の月毎の出現回数)](#monthly_counts_指定単語csv指定した単語の月毎の出現回数)
  - [おまけ：ログファイルを直接分析して統計情報を出す(src/main\_A.py)](#おまけログファイルを直接分析して統計情報を出すsrcmain_apy)
    - [word\_freq.csv(各単語の出現回数)](#word_freqcsv各単語の出現回数)
    - [{指定単語}\_monthly.csv(指定した単語の月毎の出現回数)](#指定単語_monthlycsv指定した単語の月毎の出現回数)
- [使用する方法](#使用する方法)
  - [\[0\]：インストールが必要なもの](#0インストールが必要なもの)
  - [\[1\]：リポジトリをクローン](#1リポジトリをクローン)
  - [\[2\]：Vibratoの辞書を準備](#2vibratoの辞書を準備)
  - [\[3\]：設定ファイル(config/config.toml)に設定を書く](#3設定ファイルconfigconfigtomlに設定を書く)
  - [\[4\]：Python仮想環境の作成＆スクリプトの実行](#4python仮想環境の作成スクリプトの実行)
    - [パターンA：uvを使用(推奨)](#パターンauvを使用推奨)
    - [パターンB：venvとrequirements.txtを使用(普通)](#パターンbvenvとrequirementstxtを使用普通)
- [使用ライブラリのライセンス](#使用ライブラリのライセンス)
- [その他](#その他)
  - [`uv.lock`から`requirements.txt`を生成する方法](#uvlockからrequirementstxtを生成する方法)
  
<br>  
  
# 基本説明
手元にある汎用掲示板ビューアSikiのスレッドログ(JSONファイル)を解析、TSVファイルに変換したり統計情報を出したりすることができるPythonスクリプトです。スレッドログの統計情報を出して個人的に遊んだりテキストマイニングで分析したりすることに使えます。※私はSikiの作者様と一切関係はありません。  
https://sikiapp.net/  
  
このリポジトリを見て、「スクレイピングで収集した過去ログではなく、手元にある過去ログを対象に分析するようなものがあったらいいな」と思ったので作ってみました。  
https://github.com/GINK03/5ch-analysis  
  
Sikiは2ch互換サイトに加えて、Steamコミュニティ・Reddit・ニコニコ大百科・4chan…等にも対応しています。。それらのサイトの書き込みを分析したい時にもかなり使えるのではないかと思います。  
https://sikiapp.net/support/
  
スレッドログのTSVファイル変換機能がメインで、統計情報を出す機能はおまけです。コードは「とりあえず動く」程度のクオリティなので、無断改造やフォーク大歓迎です。同じようなものをゼロから作ってしまう方が色々と良いかもしれません。  
  
<br>  
  
| 技術項目                               | 使用しているもの                  |
| -------------------------------------- | --------------------------------- |
| プログラミング言語                     | Python 3.11                       |
| Pythonの仮想環境管理 | uv                          |
| Pythonのリンターとフォーマッター       | Ruff                        |
| プログラム作成の補助AI       | Claude 3.7 Sonnet                        |
  
<br>  
  
| 機能 | Pythonのライブラリ|  
| -------------------------------------- | --------------------------------- |
| **日本語文章の形態素解析**                     | vibrato           |
|  **TSVファイルの処理**      | Polars               |
  
<br>  
  
# スクリプトの機能

## ★スレッドログをTSVファイルに変換(src/main_B_1.py)
Sikiに保存されているスレッドログを以下の形式の4つのTSVファイルに変換します。
  
### board.tsv(全掲示板のリスト)
| title(掲示板の名前) | location(掲示板のURL) |
| ------------------ | --------------- |
| ダミー掲示板             | https://example.com/dummy/            |
  
<br>  
  
### threads.tsv(全スレッドのリスト)  
| board_location(掲示板のURL) | threadkey(スレッドの番号) | title(スレッドタイトル) | resnum(スレッドのレス数) | location(スレッドのURL)                        | thread_established(スレッドの投稿日時) |
| --------------------------- | ------------------------- | ----------------------- | ------------------------ | ---------------------------------------------- | -------------------------------------- |
| https://example.com/dummy/  | 123456                    | ～～について語るスレ    | 123                      | https://example.com/test/read.cgi/dummy/123456 | 2025-03-14 00:17:38                    |
  
<br>  
  
### posts.tsv(全レスポンスのリスト)
| thread_location(スレッドのURL)                 | post_num(レスの番号) | post_an(レスのアンカー番号、レス番号＋１) | post_mname(名前欄) | post_mail(メール欄) | post_timestamp(レスの投稿日時) | post_chars(レス本文の文字数) | post_body(レスの本文) | post_anchor_an(レスのアンカー先、複数の場合カンマ区切り) | post_ancfrom(このレスにアンカーしているレスの番号、複数の場合カンマ区切り) |
| ---------------------------------------------- | -------------------- | ----------------------------------------- | ------------------ | ------------------- | ------------------------------ | ---------------------------- | --------------------- | -------------------------------------------------------- | -------------------------------------------------------------------------- |
| https://example.com/test/read.cgi/dummy/123456 | 5                    | 6                                         | ダミー名無しさん   | sage                | 2025-03-14 00:17:38            | 10                           | あいうえおかきくけこ  | 2,3                                                      | 15,100,234                                                                 |  
  
<br>  
  
### alldata.tsv(上3つの情報を全部結合したもの)  
| board_title(掲示板の名前) | board_location(掲示板のURL) | threadkey(スレッドの番号) | thread_title(スレッドタイトル) | thread_location(スレッドのURL)                 | thread_established(スレッドの投稿日時) | thread_resnum(スレッドのレス数) | post_num(レスの番号) | post_an(レスのアンカー番号、レス番号＋１) | post_mname(名前欄) | post_mail(メール欄) | post_timestamp(レスの投稿日時) | post_chars(レス本文の文字数) | post_body(レスの本文) | post_anchor_an(レスのアンカー先、複数の場合カンマ区切り) | post_ancfrom(このレスにアンカーしているレスの番号、複数の場合カンマ区切り) |
| ------------------------- | --------------------------- | ------------------------- | ------------------------------ | ---------------------------------------------- | -------------------------------------- | ------------------------------- | -------------------- | ----------------------------------------- | ------------------ | ------------------- | ------------------------------ | ---------------------------- | --------------------- | -------------------------------------------------------- | -------------------------------------------------------------------------- |
| ダミー掲示板              | https://example.com/dummy/  | 123456                    | ～～について語るスレ           | https://example.com/test/read.cgi/dummy/123456 | 2025-03-14 00:17:38                    | 123                             | 5                    | 6                                         | ダミー名無しさん   | sage                | 2025-03-14 00:17:38            | 10                           | あいうえおかきくけこ  | 2,3                                                      | 15,100,234                                                                 |  
  
<br>  
  
## おまけ：↑のTSVファイルを分析して統計情報を出す(src/main_B_2.py)
出力したTSVファイルを解析して、統計情報を出します。
  
<br>  
  
### word_frequencies.csv(各単語の出現回数)
全てのスレッドのタイトルとレス内容について、全単語のリストと出現回数を出力します。
|単語|出現回数|  
| ------------------------- | --------------------------- |
|単語の名称|数字|
  
<br>  
  
###  monthly_counts_{指定単語}.csv(指定した単語の月毎の出現回数)
指定した単語について、全てのスレッドのタイトルとレス内容の中で、月毎に何回出現しているか出力します。

|月|出現回数|種類|
| ------------------------- | --------------------------- |--------------------------- |
|～年の～月|単語の出現回数|スレッドタイトルor レス本文|
  
<br>  
  
## おまけ：ログファイルを直接分析して統計情報を出す(src/main_A.py)  
ログファイルをそのまま解析して、統計情報を出します。
### word_freq.csv(各単語の出現回数)
全てのスレッドのタイトルとレス内容について、全単語のリストと出現回数を出力します。
| 単語       | 出現回数 |
| ---------- | -------- |
| 単語の名称 | 数字     |
  
<br>  
  
### {指定単語}_monthly.csv(指定した単語の月毎の出現回数)  
指定した単語について、全てのスレッドのタイトルとレス内容の中で、月毎に何回出現しているか出力します。

| 月         | 出現回数       | 
| ---------- | -------------- | 
| ～年の～月 | 単語の出現回数 | 
  
<br>  
  
# 使用する方法
  
<br>  
  
## [0]：インストールが必要なもの

Pythonのインストールが必須です。uvの使用は任意です（軽量・Python本体のバージョン管理が可能・簡単かつ確実な動作が可能となるので推奨です）。Ruffの使用は任意です(VSCodeでは使用する設定になっています `.vscode/settings.json`)。 →[uvとRuffのインストール＆使用方法のおすすめ記事](https://zenn.dev/turing_motors/articles/594fbef42a36ee)。

動作確認はWindows10とPowerShellとFirefoxでやりました。おそらく他のOSやターミナルでも動くと思います。

  
| インストールが必要 | 動作確認したver |
| ------------------ | --------------- |
| Python             | 3.11            |
| uv(任意)           | 0.5.4           |
  
<br>  
  
## [1]：リポジトリをクローン
ターミナルでリポジトリをクローンし、cdでディレクトリに入ってください。gitを使用しない場合はZIPでダウンロードして解凍してください。
```
git clone 
cd 
```
  
<br>  
  
## [2]：Vibratoの辞書を準備
mainA.pyとmain_B_2.pyで、Vibrato(日本語の文章を形態素解析するためのライブラリ)を使用します。Vibrato用の辞書ファイルをダウンロード＆解凍して準備する必要があります。

このスクリプトに使用しているpython-vibratoはv0.2.0(vibrato本体はv0.5.1)です。下記のリンクからv0.5.0用の辞書をダウンロードしてください。辞書の拡張子は`tar.xz`なので、Windowsなら7zip、Linuxならxzやtarを使って解凍してください。  
https://github.com/daac-tools/vibrato?tab=readme-ov-file#basic-usage  
https://github.com/daac-tools/vibrato/releases/tag/v0.5.0  
  
解凍した辞書ファイル(`.dic.zst`のファイル)は、どこか適当な場所に配置し、ファイルパスをメモしてください。設定ファイルにファイルパスを書きます(次の項目参照)。
  
<br>  
  
## [3]：設定ファイル(config/config.toml)に設定を書く
`config/config.toml`に設定を書いてください。

```toml
# Sikiのスレッドのログファイルのパスを記載してください
# https://sikiapp.net/settings/
# WindowsだとC:/Users/PC_User/AppData/Roaming/Siki/profile/logにあるはず
siki_logfile_pass = "C:/Users/PC_User/AppData/Roaming/Siki/profile/log"


# 使用するVibratoの辞書ファイルのパスを書いてください
# https://github.com/daac-tools/vibrato?tab=readme-ov-file#basic-usage
# https://github.com/daac-tools/vibrato/releases/tag/v0.5.0
vibrato_dict_pass = "./config/vibrato_dict/ipadic-mecab-2_7_0/system.dic.zst"


# ログを分析した結果を出力するディレクトリのパスを書いてください
# main_A.py(ログの直接分析)の結果の出力先
output_dir_direct_analysis = "./output_direct_analysis"
# main_B_1.py(ログのTSV変換)とmain_B_2.py(TSVの分析)の出力先
output_dir_convert_tsv = "./output_tsv"


# main_A.py(ログの直接分析)と、main_B_2.py(TSVの分析)で、
# 月毎の出現回数を調べたい単語をリスト形式で入力してください。
analyze_target_words = ["日本","りんご","ゴリラ"]
```
  
<br>  
  
## [4]：Python仮想環境の作成＆スクリプトの実行
Windows10とPowerShellの場合のコマンドです。

### パターンA：uvを使用(推奨)
仮想環境を作成します。
```
uv sync
```

スレッドログをTSVファイルに変換します。
```
uv run src/main_B_1.py
```
変換したTSVファイルを分析します。
```
uv run src/main_B_2.py
```
スレッドログを直接分析します。
```
uv run src/main_A.py
```
  
<br>  
  
### パターンB：venvとrequirements.txtを使用(普通)
仮想環境を作成します。
```
python -m venv venv
./venv/Scripts/pip.exe install -r requirements.txt
```
スレッドログをTSVファイルに変換します。
```
./venv/Scripts/python.exe src/main_B_1.py
```
変換したTSVファイルを分析します。
```
./venv/Scripts/python.exe src/main_B_2.py
```
スレッドログを直接分析します。
```
./venv/Scripts/python.exe src/main_A.py
```
  
<br>  
  
# 使用ライブラリのライセンス
pip-licensesで出力
```txt
 Name                 Version      License
 colorama             0.4.6        BSD License
 contourpy            1.3.1        BSD License
 cycler               0.12.1       BSD License
 fonttools            4.56.0       MIT License
 japanize-matplotlib  1.1.3        MIT License
 kiwisolver           1.4.8        BSD License
 matplotlib           3.10.1       Python Software Foundation License
 numpy                2.2.3        BSD License
 packaging            24.2         Apache Software License; BSD License
 pillow               11.1.0       CMU License (MIT-CMU)
 polars               1.24.0       MIT License
 pyparsing            3.2.1        MIT License
 python-dateutil      2.9.0.post0  Apache Software License; BSD License
 pytomlpp             1.0.13       MIT License
 six                  1.17.0       MIT License
 tqdm                 4.67.1       MIT License; Mozilla Public License 2.0 (MPL 2.0)
 vibrato              0.2.0        Apache Software License; MIT License 
 <!-- https://github.com/daac-tools/python-vibrato -->
 zstandard            0.23.0       BSD License
```
  
<br>  
  
# その他

 ## `uv.lock`から`requirements.txt`を生成する方法

このコマンドで生成できます。パッと検索しても書いてる記事見つからなかったので一応記載。  
```
uv export --format requirements-txt --output-file requirements.txt 
```  

公式ドキュメントより  https://docs.astral.sh/uv/reference/cli/#uv-export  
  
<br>  

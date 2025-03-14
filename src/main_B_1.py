"""
SikiのログデータをTSVファイルに変換するスクリプト
"""

import os

import pytomlpp

import mylib.logdata_convert.log_convert_tsv as log_convert

# 設定ファイルのtomlを読み込む
with open("./config/config.toml", mode="r", encoding="utf-8") as f:
    text = f.read()
config_doc = pytomlpp.loads(text)

# 処理対象のルートディレクトリ（ログフォルダ）
log_folder_path = config_doc["siki_logfile_pass"]

# csvを出力するフォルダ
output_dir: str = config_doc["output_dir_convert_tsv"]
# output先のフォルダが存在しない場合は作成する
if os.path.isdir(config_doc["output_dir_convert_tsv"]):
    pass
else:
    os.makedirs(config_doc["output_dir_convert_tsv"])


# 全データを出力するかどうかの選択
output_all_data: bool = (
    input("全データを含むファイル(alldata.tsv)も出力しますか？ (y/n): ").lower() == "y"
)

# 以前の出力をクリアするかどうか：設定ミス対策でやっぱ無しで
# clear_previous: bool = input("以前の出力結果をクリアしますか？ (y/n): ").lower() == "y"


# if clear_previous:
#     if os.path.exists(output_dir):
#         shutil.rmtree(output_dir)
#         print("以前の出力をクリアしました。")

# 処理開始
print("\n処理を開始します...")
log_convert.process_log_folder(log_folder_path, output_dir, output_all_data)

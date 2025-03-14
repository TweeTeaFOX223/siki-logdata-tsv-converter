"""
Sikiのログデータを直接分析するスクリプト
"""

import os

import pytomlpp

from mylib.text_wakatigaki.use_vibrato import VibratoTokenizer
from mylib.word_analysis.log_word_analysis import BBSLogAnalyzer

# 設定ファイルのtomlを読み込む
with open("./config/config.toml", mode="r", encoding="utf-8") as f:
    text = f.read()
print("Tomlの読込")
config_doc = pytomlpp.loads(text)

# output先のフォルダが存在しない場合は作成する
if os.path.isdir(config_doc["output_dir_direct_analysis"]):
    pass
else:
    os.makedirs(config_doc["output_dir_direct_analysis"])


# Vibratoで形態素解析＆分かち書きするやつをインスタンス化
tokenizer = VibratoTokenizer(config_doc["vibrato_dict_pass"])
# 掲示板ログの解析するやつをインスタンス化
analyzer = BBSLogAnalyzer(config_doc["siki_logfile_pass"], tokenizer)

# ログを解析
analyzer.analyze_all_logs()

# 結果を取得
top_words = analyzer.get_word_frequency(10)  # 上位10件の単語を表示
print(top_words)

# 特定の単語の月別カウントを取得
monthly_counts = analyzer.get_monthly_word_count("日本")

# 結果をエクスポート
analyzer.export_word_frequency(
    f"{config_doc['output_dir_direct_analysis']}/word_freq.csv"
)

target_words = config_doc["analyze_target_words"]

for word in target_words:
    analyzer.export_monthly_word_count(
        word, f"{config_doc['output_dir_direct_analysis']}/{word}_monthly.csv"
    )
    # グラフを作成
    analyzer.plot_monthly_word_count(
        word, f"{config_doc['output_dir_direct_analysis']}/{word}_trend.png"
    )

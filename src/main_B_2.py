"""
Sikiのログデータを変換して作成したTSVファイルを分析するスクリプト
"""

from pathlib import Path

import pytomlpp

import mylib.word_analysis.csv_word_analysis as cwa

# 自作モジュールのインポート
from mylib.text_wakatigaki.use_vibrato import VibratoTokenizer


def analyze_board_data(
    csv_dir: str, target_words: list[str], vibrato_instance: VibratoTokenizer
):
    # ファイルパスの設定
    base_dir = Path(csv_dir)
    threads_path: Path = base_dir / "threads.tsv"
    posts_path: Path = base_dir / "posts.tsv"
    output_dir: Path = base_dir / "board_analysis"

    # 出力ディレクトリを作成
    output_dir.mkdir(exist_ok=True, parents=True)

    # 分析対象の単語リスト
    if target_words is None:
        target_words: list[str] = ["コロナ", "ワクチン", "医療", "政府", "感染"]

    # テキスト分析の実行
    print(f"テキスト分析を開始: {threads_path}, {posts_path}")

    results = cwa.analyze_text(
        threads_path=str(threads_path),
        posts_path=str(posts_path),
        vibrato_instance=vibrato_instance,
        target_words=target_words,
        output_dir=str(output_dir),
        generate_graphs=True,
    )

    # 分析結果の表示
    print("分析結果の概要:")

    # 単語出現頻度の上位10件を表示
    word_freq = results["word_frequencies"]
    print("\n上位10単語の出現頻度:")
    print(word_freq.head(10))

    # 月別単語出現回数の結果を表示
    for word in target_words:
        if word in results["monthly_word_counts"]:
            print(f"\n単語「{word}」の月別出現回数:")
            monthly_data = results["monthly_word_counts"][word]
            print(monthly_data)

    print(f"\n結果は {output_dir} に保存されました")
    return results


# def analyze_custom_files(
#     threads_file, posts_file, vibrato_instance: VibratoTokenizer, custom_words=None
# ):
#     """
#     カスタムファイルとカスタム単語を使用してテキスト分析を実行する

#     Parameters:
#     -----------
#     threads_file : str
#         スレッド情報のCSVファイルパス
#     posts_file : str
#         書き込み情報のCSVファイルパス
#     custom_words : list, optional
#         分析対象とする単語のリスト

#     Returns:
#     --------
#     dict
#         分析結果
#     """
#     if custom_words is None:
#         custom_words = ["問題", "対応", "解決"]

#     # 出力ディレクトリを設定
#     output_dir = Path(f"./results/custom_analysis_{Path(threads_file).stem}")
#     output_dir.mkdir(exist_ok=True, parents=True)

#     # テキスト分析を実行
#     results = cwa.analyze_text(
#         threads_path=threads_file,
#         posts_path=posts_file,
#         vibrato_instance=vibrato_instance,
#         target_words=custom_words,
#         output_dir=str(output_dir),
#     )

#     print(f"カスタム分析が完了しました。結果は {output_dir} に保存されています。")
#     return results


if __name__ == "__main__":
    # 設定ファイルのtomlを読み込む
    with open("./config/config.toml", mode="r", encoding="utf-8") as f:
        text = f.read()
    print("Tomlの読込")
    config_doc = pytomlpp.loads(text)

    # Vibratoで形態素解析＆分かち書きするやつをインスタンス化
    tokenizer = VibratoTokenizer(config_doc["vibrato_dict_pass"])

    # デフォルトの分析を実行
    analyze_board_data(
        config_doc["output_dir_convert_tsv"],
        config_doc["analyze_target_words"],
        tokenizer,
    )

    # 例: カスタム分析の実行
    # analyze_custom_files(
    #     threads_file="./data/custom_threads.csv",
    #     posts_file="./data/custom_posts.csv",
    #     custom_words=["技術", "開発", "プログラム", "エラー"]
    # )

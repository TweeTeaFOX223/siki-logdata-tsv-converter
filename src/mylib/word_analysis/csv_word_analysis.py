import argparse
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import japanize_matplotlib
import matplotlib.pyplot as plt
import polars as pl

from ..text_wakatigaki.use_vibrato import VibratoTokenizer

japanize_matplotlib.japanize()


def tokenize_text(text: str, vibrato_instance) -> list[str]:
    """Vibratoを使用して日本語テキストを形態素解析し、単語に分割する"""
    words: list[str] = vibrato_instance.wakatigaki(text)
    return words


def count_words(texts: List[str], vibrato_instance) -> Counter:
    """テキストのリストから単語の出現頻度を計算する"""
    all_words = []
    for text in texts:
        if isinstance(text, str):
            words = tokenize_text(text, vibrato_instance)
            all_words.extend(words)

    return Counter(all_words)


def count_words_by_month(
    df: pl.DataFrame,
    date_column: str,
    text_column: str,
    target_words: List[str],
    vibrato_instance,
) -> Dict[str, Dict[str, int]]:
    """月ごとに特定の単語の出現回数を計算する"""
    # 日付列をdatetime型に変換
    df = df.with_columns(pl.col(date_column).str.to_datetime())

    # 日付がNullのレコードを除外
    df = df.filter(pl.col(date_column).is_not_null())

    # 月ごとにグループ化するための列を追加
    df = df.with_columns(pl.col(date_column).dt.strftime("%Y-%m").alias("month"))

    # 各月の各単語の出現回数を格納する辞書
    monthly_counts = {word: {} for word in target_words}

    # 月ごとに単語の出現回数を計算
    for month in df["month"].unique():
        # Noneをスキップ
        if month is None:
            continue

        month_df = df.filter(pl.col("month").is_not_null() & (pl.col("month") == month))
        texts = month_df[text_column].to_list()
        all_text = " ".join([str(text) for text in texts if isinstance(text, str)])
        words = tokenize_text(all_text, vibrato_instance)

        # 対象単語の出現回数を計算
        for word in target_words:
            monthly_counts[word][month] = words.count(word)

    return monthly_counts


def create_word_frequency_graph(
    word_counts_df: pl.DataFrame, output_dir: Path, top_n: int = 20
) -> str:
    """単語の出現頻度をグラフ化して保存する"""
    top_words = word_counts_df.slice(0, top_n)

    plt.figure(figsize=(12, 8))
    plt.barh(top_words["単語"].to_list(), top_words["出現回数"].to_list())
    plt.xlabel("出現回数")
    plt.ylabel("単語")
    plt.title(f"トップ{top_n}単語の出現頻度")
    plt.tight_layout()

    graph_file = output_dir / "top_words_frequency.png"
    plt.savefig(graph_file)
    plt.close()

    return str(graph_file)


def create_monthly_word_count_graph(
    combined_df: pl.DataFrame, word: str, output_dir: Path
) -> str:
    """月別単語出現回数をグラフ化して保存する"""
    plt.figure(figsize=(12, 6))

    # グラフ用にデータを整形（Polarsでピボット）
    pivot_data = {}
    for type_name in combined_df["種類"].unique():
        type_data = combined_df.filter(pl.col("種類") == type_name)
        for row in type_data.iter_rows():
            month, count, _ = row
            if month not in pivot_data:
                pivot_data[month] = {}
            pivot_data[month][type_name] = count

    # 月とデータ種類ごとの値を取得
    months = sorted(pivot_data.keys())
    thread_values = [pivot_data[m].get("スレッドタイトル", 0) for m in months]
    post_values = [pivot_data[m].get("書き込み内容", 0) for m in months]

    # バーグラフの作成
    x = range(len(months))
    width = 0.35
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.bar(
        [i - width / 2 for i in x],
        thread_values,
        width,
        label="スレッドタイトル",
    )
    ax.bar([i + width / 2 for i in x], post_values, width, label="書き込み内容")

    ax.set_title(f"単語「{word}」の月別出現回数")
    ax.set_xlabel("月")
    ax.set_ylabel("出現回数")
    ax.set_xticks(x)
    ax.set_xticklabels(months, rotation=45)
    ax.legend()

    plt.tight_layout()
    graph_file = output_dir / f"monthly_counts_{word}.png"
    plt.savefig(graph_file)
    plt.close()

    return str(graph_file)


def calculate_word_frequencies(
    threads_df: pl.DataFrame,
    posts_df: pl.DataFrame,
    vibrato_instance,
    thread_title_col: str,
    post_content_col: str,
) -> Tuple[pl.DataFrame, Counter]:
    """全ての書き込みとスレッドタイトルに含まれる単語の出現頻度を計算する"""
    # スレッドタイトルの処理
    thread_titles = threads_df[thread_title_col].to_list()
    thread_title_word_counts = count_words(thread_titles, vibrato_instance)

    # 書き込み内容の処理
    post_contents = posts_df[post_content_col].to_list()
    post_content_word_counts = count_words(post_contents, vibrato_instance)

    # 両方の結果を結合
    all_word_counts = thread_title_word_counts + post_content_word_counts

    # 結果をDataFrameに格納
    word_counts_data = [
        {"単語": word, "出現回数": count}
        for word, count in all_word_counts.most_common()
    ]
    word_counts_df = pl.DataFrame(word_counts_data)

    return word_counts_df, all_word_counts


def calculate_monthly_word_counts(
    threads_df: pl.DataFrame,
    posts_df: pl.DataFrame,
    target_words: List[str],
    vibrato_instance,
    thread_title_col: str,
    thread_date_col: str,
    post_content_col: str,
    post_date_col: str,
) -> Dict[str, pl.DataFrame]:
    """月別単語出現回数を計算する"""
    monthly_word_counts = {}

    # スレッドタイトルでの単語出現回数（月別）
    thread_monthly_counts = count_words_by_month(
        threads_df, thread_date_col, thread_title_col, target_words, vibrato_instance
    )

    # 書き込み内容での単語出現回数（月別）
    post_monthly_counts = count_words_by_month(
        posts_df, post_date_col, post_content_col, target_words, vibrato_instance
    )

    # 結果を辞書に格納
    for word in target_words:
        # スレッドタイトルでの出現回数
        thread_counts = thread_monthly_counts[word]
        thread_counts_data = [
            {"月": month, "出現回数": count, "種類": "スレッドタイトル"}
            for month, count in sorted(thread_counts.items())
            if month is not None
        ]
        thread_counts_df = pl.DataFrame(thread_counts_data)

        # 書き込み内容での出現回数
        post_counts = post_monthly_counts[word]
        post_counts_data = [
            {"月": month, "出現回数": count, "種類": "書き込み内容"}
            for month, count in sorted(post_counts.items())
            if month is not None
        ]
        post_counts_df = pl.DataFrame(post_counts_data)

        # 結果を結合
        combined_df = pl.concat([thread_counts_df, post_counts_df])
        monthly_word_counts[word] = combined_df

    return monthly_word_counts


def analyze_text(
    threads_path: str,
    posts_path: str,
    vibrato_instance,
    target_words: Optional[List[str]] = None,
    output_dir: str = "./output",
    generate_graphs: bool = True,
) -> Dict[str, Any]:
    """
    テキストを分析し、単語出現頻度と月別単語出現回数を計算する

    Parameters:
    -----------
    threads_path : str
        スレッド情報のCSVファイルパス
    posts_path : str
        書き込み情報のCSVファイルパス
    vibrato_instance : VibratoTokenizer
        形態素解析に使用するVibratoTokenizerのインスタンス
    target_words : list, optional
        月別で集計する対象単語のリスト
    output_dir : str, optional
        出力ディレクトリ (デフォルト: './output')
    generate_graphs : bool, optional
        グラフを生成するかどうか (デフォルト: True)

    Returns:
    --------
    dict
        分析結果を含む辞書
    """
    # 出力ディレクトリの作成
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True, parents=True)

    # CSVファイルの読み込み
    threads_df = pl.read_csv(
        threads_path,
        separator="\t",
        schema_overrides={
            "post_anc": pl.String,
            "post_anchor_an": pl.String,
            "post_ancfrom": pl.String,
        },
    )
    posts_df = pl.read_csv(
        posts_path,
        separator="\t",
        schema_overrides={
            "post_anc": pl.String,
            "post_anchor_an": pl.String,
            "post_ancfrom": pl.String,
        },
    )

    # 必要なカラムの定義
    thread_title_col = "title"
    # thread_id_col = "location"
    thread_date_col = "thread_established"

    # post_thread_id_col = "thread_location"
    post_date_col = "post_timestamp"
    post_content_col = "post_body"

    # 結果を保存する辞書を初期化
    results = {"word_frequencies": None, "monthly_word_counts": {}}

    # 1. 単語の出現頻度の計算
    word_counts_df, all_word_counts = calculate_word_frequencies(
        threads_df, posts_df, vibrato_instance, thread_title_col, post_content_col
    )

    # 結果を辞書に保存（Pandasと互換性を保つためにPandasに変換）
    # results["word_frequencies"] = word_counts_df.to_pandas()
    results["word_frequencies"] = word_counts_df

    # 結果をCSVファイルに保存
    word_counts_file = output_dir / "word_frequencies.csv"
    word_counts_df.write_csv(word_counts_file)

    # グラフを生成する場合
    if generate_graphs:
        # トップN単語の出現頻度をグラフ化
        top_n = 20
        graph_file = create_word_frequency_graph(word_counts_df, output_dir, top_n)
        results["word_frequency_graph"] = graph_file

    # 2. ユーザーが指定した単語の月別出現回数の計算
    if target_words:
        monthly_word_counts = calculate_monthly_word_counts(
            threads_df,
            posts_df,
            target_words,
            vibrato_instance,
            thread_title_col,
            thread_date_col,
            post_content_col,
            post_date_col,
        )

        # 結果を保存してグラフ作成
        for word, combined_df in monthly_word_counts.items():
            # 結果を辞書に保存（Pandasと互換性を保つためにPandasに変換）
            # results["monthly_word_counts"][word] = combined_df.to_pandas()
            results["monthly_word_counts"][word] = combined_df

            # CSVファイルに保存
            word_file = output_dir / f"monthly_counts_{word}.csv"
            combined_df.write_csv(word_file)

            # グラフを生成する場合
            if generate_graphs:
                graph_file = create_monthly_word_count_graph(
                    combined_df, word, output_dir
                )
                results["monthly_word_counts"][f"{word}_graph"] = graph_file

    return results


# コマンドラインからも実行可能なメイン関数
def main():
    parser = argparse.ArgumentParser(description="テキスト分析スクリプト")
    parser.add_argument(
        "--threads", required=True, help="スレッド情報のCSVファイルパス"
    )
    parser.add_argument("--posts", required=True, help="書き込み情報のCSVファイルパス")
    parser.add_argument(
        "--vibrato-dict", required=True, help="Vibrato辞書ファイルのパス"
    )
    parser.add_argument(
        "--target-words",
        nargs="+",
        default=[],
        help="月別で集計する対象単語（スペース区切りで複数指定可能）",
    )
    parser.add_argument("--output-dir", default="./output", help="出力ディレクトリ")
    parser.add_argument("--no-graphs", action="store_true", help="グラフを生成しない")

    args = parser.parse_args()

    # Vibratoトークナイザーを初期化
    vibrato_tokenizer = VibratoTokenizer(args.vibrato_dict)

    # 分析実行
    results = analyze_text(
        threads_path=args.threads,
        posts_path=args.posts,
        vibrato_instance=vibrato_tokenizer,
        target_words=args.target_words,
        output_dir=args.output_dir,
        generate_graphs=not args.no_graphs,
    )

    print("処理が完了しました。")
    return results


if __name__ == "__main__":
    # main()
    print("呼び出して実行してください。")

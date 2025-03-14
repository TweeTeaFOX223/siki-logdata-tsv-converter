import argparse
import json
import os
from collections import Counter
from datetime import datetime

import japanize_matplotlib
import matplotlib.pyplot as plt
import polars as pl
from tqdm import tqdm

from ..text_wakatigaki.use_vibrato import VibratoTokenizer

japanize_matplotlib.japanize()


class BBSLogAnalyzer:
    def __init__(self, log_dir: str, vibrato_tokenizer_instance: VibratoTokenizer):
        """
        電子掲示板ログ解析クラス

        Parameters:
        -----------
        log_dir : str
            ログディレクトリのパス
        """
        self.log_dir = log_dir

        # Vibratoのトークナイザを初期化
        self.vibrato_tokenizer: VibratoTokenizer = vibrato_tokenizer_instance

        self.words_counter = Counter()
        self.monthly_word_counts = {}

    def timestamp_to_yearmonth(self, timestamp):
        """UNIXタイムスタンプを'YYYY-MM'形式に変換"""
        dt = datetime.fromtimestamp(timestamp / 1000)  # ミリ秒を秒に変換
        return dt.strftime("%Y-%m")

    def analyze_board_folder(self, board_site_path, board_folder):
        """個別の掲示板フォルダを解析"""
        board_path = os.path.join(board_site_path, board_folder)
        subject_path = os.path.join(board_path, "subject.json")

        if not os.path.exists(subject_path):
            print(f"Warning: subject.json not found in {board_path}")
            return

        try:
            with open(subject_path, "r", encoding="utf-8") as f:
                subject_data = json.load(f)

            # 掲示板タイトルの解析
            if "title" in subject_data and subject_data["title"]:
                board_title = subject_data["title"]
                words: list[str] = self.vibrato_tokenizer.wakatigaki(board_title)
                self.words_counter.update(words)

            # 各スレッドの解析
            if "items" in subject_data and isinstance(subject_data["items"], list):
                for thread_info in subject_data["items"]:
                    thread_key = thread_info.get("threadkey")
                    if not thread_key:
                        continue

                    # スレッドタイトルの解析
                    thread_title = thread_info.get("title", "")
                    title_words: list[str] = self.vibrato_tokenizer.wakatigaki(
                        thread_title
                    )
                    self.words_counter.update(title_words)

                    # スレッドファイルの解析
                    thread_file = os.path.join(board_path, f"{thread_key}.json")
                    if os.path.exists(thread_file):
                        self.analyze_thread_file(thread_file)

        except Exception as e:
            print(f"Error analyzing board {board_folder}: {str(e)}")

    def analyze_thread_file(self, thread_file):
        """個別のスレッドファイルを解析"""
        try:
            with open(thread_file, "r", encoding="utf-8") as f:
                thread_data = json.load(f)

            # スレッドタイトルの解析
            if "title" in thread_data and thread_data["title"]:
                title_words = self.vibrato_tokenizer.wakatigaki(thread_data["title"])
                self.words_counter.update(title_words)

                # 月別カウントにも追加
                if "established" in thread_data and thread_data["established"]:
                    year_month = self.timestamp_to_yearmonth(thread_data["established"])
                    for word in title_words:
                        if word not in self.monthly_word_counts:
                            self.monthly_word_counts[word] = Counter()
                        self.monthly_word_counts[word][year_month] += 1

            # 各書き込みの解析
            if "thread_array" in thread_data and isinstance(
                thread_data["thread_array"], list
            ):
                for post in thread_data["thread_array"]:
                    if "body" in post and post["body"]:
                        # 書き込み本文の単語カウント
                        post_words = self.vibrato_tokenizer.wakatigaki(post["body"])
                        self.words_counter.update(post_words)

                        # 月別カウントにも追加
                        if "timestamp" in post and post["timestamp"]:
                            year_month = self.timestamp_to_yearmonth(post["timestamp"])
                            for word in post_words:
                                if word not in self.monthly_word_counts:
                                    self.monthly_word_counts[word] = Counter()
                                self.monthly_word_counts[word][year_month] += 1

        except Exception as e:
            print(f"Error analyzing thread file {thread_file}: {str(e)}")

    def analyze_all_logs(self):
        """すべてのログを解析"""
        print("ログ解析を開始します...")

        # logディレクトリ内の各掲示板サイトフォルダを処理
        for board_site in os.listdir(self.log_dir):
            board_site_path = os.path.join(self.log_dir, board_site)
            if not os.path.isdir(board_site_path):
                continue

            # 掲示板サイト内の各掲示板フォルダを処理
            for board_folder in tqdm(
                os.listdir(board_site_path), desc=f"解析中: {board_site}"
            ):
                board_folder_path = os.path.join(board_site_path, board_folder)
                if os.path.isdir(board_folder_path):
                    self.analyze_board_folder(board_site_path, board_folder)

        print("ログ解析が完了しました")

    def get_word_frequency(self, top_n=None):
        """
        単語の出現頻度を返す

        Parameters:
        -----------
        top_n : int or None
            取得する上位単語数。Noneの場合は全単語を返す

        Returns:
        --------
        list of tuple
            (単語, 出現回数) のリスト
        """
        if top_n is None:
            # 全単語を取得（降順ソート）
            return sorted(self.words_counter.items(), key=lambda x: x[1], reverse=True)
        else:
            # 上位N個の単語を取得
            return self.words_counter.most_common(top_n)

    def get_monthly_word_count(self, word):
        """指定した単語の月別出現回数を返す"""
        if word in self.monthly_word_counts:
            # 日付順にソート
            sorted_counts = sorted(self.monthly_word_counts[word].items())
            return sorted_counts
        return []

    def export_word_frequency(self, output_file, top_n=None):
        """
        単語の出現頻度をCSVファイルに出力

        Parameters:
        -----------
        output_file : str
            出力先ファイルパス
        top_n : int or None
            出力する上位単語数。Noneの場合は全単語を出力
        """
        # top_nがNoneの場合は全単語を対象にする
        most_common = self.get_word_frequency(top_n)

        # Polarsデータフレームを作成
        df = pl.DataFrame(
            {
                "単語": [word for word, _ in most_common],
                "出現回数": [count for _, count in most_common],
            }
        )

        # CSVファイルに出力
        df.write_csv(output_file)

        # 出力の詳細を表示
        word_count = len(most_common)
        if top_n is None:
            print(
                f"全単語 ({word_count}語) の頻度リストを {output_file} に出力しました"
            )
        else:
            print(
                f"単語頻度上位 {min(top_n, word_count)} 語を {output_file} に出力しました"
            )

    def export_monthly_word_count(self, word, output_file):
        """指定した単語の月別出現回数をCSVファイルに出力"""
        monthly_counts = self.get_monthly_word_count(word)
        if not monthly_counts:
            print(f"単語 '{word}' は見つかりませんでした")
            return False

        # Polarsデータフレームを作成
        df = pl.DataFrame(
            {
                "年月": [month for month, _ in monthly_counts],
                "出現回数": [count for _, count in monthly_counts],
            }
        )

        # CSVファイルに出力
        df.write_csv(output_file)
        print(f"'{word}' の月別出現回数を {output_file} に出力しました")
        return True

    def plot_monthly_word_count(self, word, output_file=None):
        """指定した単語の月別出現回数をグラフ化"""
        monthly_counts = self.get_monthly_word_count(word)
        if not monthly_counts:
            print(f"単語 '{word}' は見つかりませんでした")
            return False

        months, counts = zip(*monthly_counts)

        plt.figure(figsize=(12, 6))
        plt.bar(months, counts)
        plt.title(f"'{word}' の月別出現回数")
        plt.xlabel("年月")
        plt.ylabel("出現回数")
        plt.xticks(rotation=45)
        plt.tight_layout()

        if output_file:
            plt.savefig(output_file)
            print(f"グラフを {output_file} に保存しました")
        else:
            plt.show()
        return True


def main():
    parser = argparse.ArgumentParser(description="電子掲示板ログ解析ツール")
    parser.add_argument("log_dir", help="ログディレクトリのパス")
    parser.add_argument(
        "--top",
        type=int,
        default=100,
        help="出力する単語頻度の上位数 (デフォルト: 100)",
    )
    parser.add_argument(
        "--all-words", action="store_true", help="全単語の頻度を出力する"
    )
    parser.add_argument("--word", help="月別出現回数を調査する単語")
    parser.add_argument("--output-freq", help="単語頻度リストの出力ファイル名")
    parser.add_argument("--output-monthly", help="月別出現回数の出力ファイル名")
    parser.add_argument("--plot", help="月別出現回数のグラフ出力ファイル名")

    args = parser.parse_args()

    analyzer = BBSLogAnalyzer(args.log_dir)
    analyzer.analyze_all_logs()

    # 単語頻度リストの出力
    if args.output_freq:
        # --all-wordsフラグがある場合はNoneを渡して全単語を出力
        top_n = None if args.all_words else args.top
        analyzer.export_word_frequency(args.output_freq, top_n)
    else:
        if args.all_words:
            print("\n【全単語の出現頻度】")
            word_freq = analyzer.get_word_frequency(None)
            print(f"単語数: {len(word_freq)}")
            # 出力が多すぎるので上位20件だけ表示
            for word, count in word_freq[:20]:
                print(f"{word}: {count}")
            print("... (以下省略)")
        else:
            print(f"\n【単語出現頻度上位{args.top}】")
            for word, count in analyzer.get_word_frequency(args.top):
                print(f"{word}: {count}")

    # 月別出現回数の分析
    if args.word:
        if args.output_monthly:
            analyzer.export_monthly_word_count(args.word, args.output_monthly)
        else:
            print(f"\n【'{args.word}' の月別出現回数】")
            monthly_counts = analyzer.get_monthly_word_count(args.word)
            if monthly_counts:
                for month, count in monthly_counts:
                    print(f"{month}: {count}")
            else:
                print(f"単語 '{args.word}' は見つかりませんでした")

        # グラフの出力
        if args.plot:
            analyzer.plot_monthly_word_count(args.word, args.plot)


if __name__ == "__main__":
    # main()
    print("呼び出して実行してください。")

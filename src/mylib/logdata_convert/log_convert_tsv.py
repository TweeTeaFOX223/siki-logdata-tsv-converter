import csv
import datetime
import json
import os
import shutil
from typing import Dict, List


def convert_unix_timestamp(timestamp: int) -> str:
    """UNIXタイムスタンプを読みやすい日時形式に変換する"""
    return datetime.datetime.fromtimestamp(timestamp / 1000).strftime(
        "%Y-%m-%d %H:%M:%S"
    )


def process_board_folder(folder_path: str) -> tuple:
    """掲示板フォルダを処理し、掲示板情報、スレッド情報、投稿情報を抽出する"""
    board_info = None
    threads_info = []
    posts_info = []
    all_data = []

    # subject.jsonを処理
    subject_path = os.path.join(folder_path, "subject.json")
    if os.path.exists(subject_path):
        with open(subject_path, "r", encoding="utf-8") as f:
            subject_data = json.load(f)

            # 掲示板情報を抽出
            board_info = {
                "title": subject_data.get("title", ""),
                "location": subject_data.get("location", ""),
            }

            # スレッド情報を抽出
            for thread in subject_data.get("items", []):
                thread_key = thread.get("threadkey", "")
                thread_title = thread.get("title", "")
                thread_location = thread.get("location", "")
                thread_resnum = thread.get("resnum", 0)

                # スレッドのJSONファイルを処理
                thread_file = os.path.join(folder_path, f"{thread_key}.json")
                thread_established = None

                if os.path.exists(thread_file):
                    with open(thread_file, "r", encoding="utf-8") as tf:
                        thread_data = json.load(tf)
                        thread_established = thread_data.get("established", 0)
                        established_date = (
                            convert_unix_timestamp(thread_established)
                            if thread_established
                            else ""
                        )

                        threads_info.append(
                            {
                                "board_location": board_info["location"],
                                "threadkey": thread_key,
                                "title": thread_title,
                                "resnum": thread_resnum,
                                "location": thread_location,
                                "thread_established": established_date,
                            }
                        )

                        # 投稿情報を抽出
                        for post in thread_data.get("thread_array", []):
                            timestamp = post.get("timestamp", 0)
                            formatted_time = (
                                convert_unix_timestamp(timestamp) if timestamp else ""
                            )

                            # 返信先と返信元をカンマ区切りの文字列に変換
                            anchor_an = (
                                ",".join(map(str, post.get("anchor_an", [])))
                                if "anchor_an" in post
                                else ""
                            )
                            ancfrom = (
                                ",".join(map(str, post.get("ancfrom", [])))
                                if "ancfrom" in post
                                else ""
                            )

                            # 投稿データ（一部フィールドを除外）
                            post_data = {
                                "thread_location": thread_location,
                                "post_num": post.get("num", 0),
                                "post_an": post.get("an", 0),
                                "post_mname": post.get("mname", ""),
                                "post_mail": post.get("mail", ""),
                                "post_timestamp": formatted_time,
                                "post_chars": post.get("chars", 0),
                                "post_body": post.get("body", "").replace("\n", " "),
                                "post_anchor_an": anchor_an,
                                "post_ancfrom": ancfrom,
                            }
                            posts_info.append(post_data)

                            # 全データ用（全フィールドを含む）
                            full_data = {
                                "board_title": board_info["title"],
                                "board_location": board_info["location"],
                                "threadkey": thread_key,
                                "thread_title": thread_title,
                                "thread_location": thread_location,
                                "thread_established": established_date,
                                "thread_resnum": thread_resnum,
                                "post_num": post.get("num", 0),
                                "post_an": post.get("an", 0),
                                "post_mname": post.get("mname", ""),
                                "post_mail": post.get("mail", ""),
                                "post_timestamp": formatted_time,
                                "post_chars": post.get("chars", 0),
                                "post_body": post.get("body", "").replace("\n", " "),
                                "post_anchor_an": anchor_an,
                                "post_ancfrom": ancfrom,
                            }
                            all_data.append(full_data)

    return board_info, threads_info, posts_info, all_data


def is_board_folder(folder_path: str) -> bool:
    """指定されたフォルダが掲示板フォルダかどうかを判定する（subject.jsonの存在で判断）"""
    return os.path.exists(os.path.join(folder_path, "subject.json"))


def write_tsv_files(
    output_dir: str,
    all_boards: List[Dict],
    all_threads: List[Dict],
    all_posts: List[Dict],
    all_data: List[Dict],
    output_all_data: bool,
) -> None:
    """TSVファイルを出力する"""
    os.makedirs(output_dir, exist_ok=True)

    # 掲示板リストのTSV
    if all_boards:
        with open(
            os.path.join(output_dir, "boards.tsv"), "w", encoding="utf-8", newline=""
        ) as f:
            writer = csv.DictWriter(f, fieldnames=all_boards[0].keys(), delimiter="\t")
            writer.writeheader()
            writer.writerows(all_boards)

    # スレッドリストのTSV
    if all_threads:
        with open(
            os.path.join(output_dir, "threads.tsv"), "w", encoding="utf-8", newline=""
        ) as f:
            writer = csv.DictWriter(f, fieldnames=all_threads[0].keys(), delimiter="\t")
            writer.writeheader()
            writer.writerows(all_threads)

    # 投稿データのTSV
    if all_posts:
        with open(
            os.path.join(output_dir, "posts.tsv"), "w", encoding="utf-8", newline=""
        ) as f:
            writer = csv.DictWriter(f, fieldnames=all_posts[0].keys(), delimiter="\t")
            writer.writeheader()
            writer.writerows(all_posts)

    # 全データを含むTSV（オプション）
    if output_all_data and all_data:
        with open(
            os.path.join(output_dir, "alldata.tsv"), "w", encoding="utf-8", newline=""
        ) as f:
            writer = csv.DictWriter(f, fieldnames=all_data[0].keys(), delimiter="\t")
            writer.writeheader()
            writer.writerows(all_data)

    print(f"- 掲示板数: {len(all_boards)}")
    print(f"- スレッド数: {len(all_threads)}")
    print(f"- 投稿数: {len(all_posts)}")
    if output_all_data:
        print(f"- 全データのエントリ数: {len(all_data)}")


def process_site_folder(site_folder_path: str, output_all_data: bool = False) -> tuple:
    """掲示板サイトフォルダを処理し、そのサイト内の全掲示板の情報を抽出する"""
    site_boards = []
    site_threads = []
    site_posts = []
    site_all_data = []

    # サイトフォルダ内の各掲示板フォルダを処理
    for item_name in os.listdir(site_folder_path):
        board_folder_path = os.path.join(site_folder_path, item_name)
        if os.path.isdir(board_folder_path) and is_board_folder(board_folder_path):
            board_info, threads_info, posts_info, all_data = process_board_folder(
                board_folder_path
            )
            if board_info:
                site_boards.append(board_info)
                site_threads.extend(threads_info)
                site_posts.extend(posts_info)
                site_all_data.extend(all_data)

    # サイトフォルダごとの出力
    if site_boards:
        site_name = os.path.basename(site_folder_path)
        output_dir = os.path.join(
            os.path.dirname(site_folder_path), "output", site_name
        )
        print(f"\n処理中: {site_name}")
        write_tsv_files(
            output_dir,
            site_boards,
            site_threads,
            site_posts,
            site_all_data,
            output_all_data,
        )

    return site_boards, site_threads, site_posts, site_all_data


def process_log_folder(
    log_folder_path: str, output_dir_path: str, output_all_data: bool = False
) -> None:
    """ログフォルダ全体を処理する"""
    # サイト全体の集計用
    all_site_boards = []
    all_site_threads = []
    all_site_posts = []
    all_site_data = []

    # 各サイトフォルダを処理
    for site_name in os.listdir(log_folder_path):
        site_folder_path = os.path.join(log_folder_path, site_name)
        if os.path.isdir(site_folder_path):
            # サイトフォルダかどうかを判定（掲示板フォルダを含んでいるか）
            contains_board_folder = False
            for item_name in os.listdir(site_folder_path):
                item_path = os.path.join(site_folder_path, item_name)
                if os.path.isdir(item_path) and is_board_folder(item_path):
                    contains_board_folder = True
                    break

            if contains_board_folder:
                site_boards, site_threads, site_posts, site_all_data = (
                    process_site_folder(site_folder_path, output_all_data)
                )

                all_site_boards.extend(site_boards)
                all_site_threads.extend(site_threads)
                all_site_posts.extend(site_posts)
                all_site_data.extend(site_all_data)

    # 全サイトの集計データを出力
    if all_site_boards:
        print("\n全サイト集計データを出力中...")
        write_tsv_files(
            output_dir_path,
            all_site_boards,
            all_site_threads,
            all_site_posts,
            all_site_data,
            output_all_data,
        )

    print(f"\n変換が完了しました。結果は {output_dir_path} に保存されています。")


def main():
    # 処理対象のルートディレクトリ（ログフォルダ）
    log_folder_path = input("ログフォルダのパスを入力してください: ")

    # 全データを出力するかどうかの選択
    output_all_data = (
        input("全データを含むファイル(alldata.tsv)も出力しますか？ (y/n): ").lower()
        == "y"
    )

    # 以前の出力をクリアするかどうか
    clear_previous = input("以前の出力結果をクリアしますか？ (y/n): ").lower() == "y"

    if clear_previous:
        output_dir: str = "./output_csv"
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
            print("以前の出力をクリアしました。")

    # 処理開始
    print("\n処理を開始します...")
    process_log_folder(log_folder_path, output_all_data)


if __name__ == "__main__":
    # main()
    print("呼び出して実行してください。")

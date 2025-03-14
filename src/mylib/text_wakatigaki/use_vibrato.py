import zstandard
import vibrato
import re


class VibratoTokenizer:
    def __init__(self, vibrato_dict_pass: str):
        """使用する辞書(zst)のパスを指定して初期化"""
        zstreader = zstandard.ZstdDecompressor()

        with open(vibrato_dict_pass, "rb") as fp:
            with zstreader.stream_reader(fp) as dict_reader:
                self.tokenizer = vibrato.Vibrato(dict_reader.read())

    def wakatigaki(self, text: str) -> list[str]:
        """テキストを形態素解析して単語リストを返す"""
        if not text or not isinstance(text, str):
            return []

        # 特殊文字と半角・全角スペースを除去
        cleaned_text: str = re.sub(r"[^\w\s]", "", text)
        cleaned_text = re.sub(r"[\s　]+", " ", cleaned_text).strip()
        # 英語を全部小文字に変換する
        cleaned_text = text.lower()

        if not cleaned_text:
            return []

        # Vibratoで形態素解析
        tokens: vibrato.TokenList = self.tokenizer.tokenize(cleaned_text)
        # 表層形を取得してリストに変換
        words: list[str] = [token.surface() for token in tokens]

        return words

    def wakatigaki_ngram(self, text, num) -> list[str]:
        """
        単語リストからN-gramのリストを生成する関数

        引数:
            word_list (list[str]): 単語のリスト
            n (int): N-gramのN（何個の単語を一組にするか）

        戻り値:
            list[str]: N-gramのリスト（各N-gramは空白で結合された1つの文字列）
        """

        if num <= 0:
            raise ValueError("N must be a positive integer")

        bigram: list[str] = self.wakatigaki(text)

        if len(bigram) < num:
            return bigram

        ngrams: list[str] = []
        for i in range(len(bigram) - num + 1):
            # n個の単語を取得して結合
            one_word = "".join(bigram[i : i + num])
            ngrams.append(one_word)

        return ngrams

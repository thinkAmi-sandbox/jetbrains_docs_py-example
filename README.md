# JetBrains ドキュメント PDF 生成・結合スクリプト

このリポジトリには、JetBrains IntelliJ プラグイン開発ドキュメントを取得し、PDF に変換して、単一の PDF ファイルに結合するスクリプトが含まれています。

## 機能

1. サイトマップから URL を抽出
2. 各 URL のウェブページを取得
3. HTML コンテンツを整形
4. 個別の PDF ファイルに変換
5. 全ての PDF を 1 つのファイルに結合

## 必要条件

以下のライブラリが必要です：

- requests
- beautifulsoup4
- lxml
- xhtml2pdf
- pypdf (バージョン 5.0.0 以上)

## セットアップ

```bash
# Python 3.12.10 を使用
% mise use python@3.12.10

# プロジェクトの初期化
% uv init

# 必要なライブラリのインストール
% uv add requests beautifulsoup4 lxml xhtml2pdf pypdf
```

## 使用方法

### jb_docs.py

このスクリプトは、ドキュメントの取得から PDF 変換、結合までの全ての処理を行います。

#### 基本的な使用法

```bash
python jb_docs.py
```

これにより、デフォルトの設定でドキュメントが取得・変換・結合されます。

#### コマンドラインオプション

- `--temp-dir TEMP_DIR` - 一時的な PDF ファイル置き場 (デフォルト: `temp_pdfs`)
- `--merge` - PDF をマージする (デフォルト: True)
- `--no-merge` - PDF をマージしない
- `--output OUTPUT` - 出力 PDF ファイルのパス (デフォルト: `jetbrains_intellij_docs.pdf`)
- `--delay DELAY` - リクエスト間の遅延（秒） (デフォルト: 1.0)
- `--clean` - 処理完了後に一時ファイルを削除する

#### 使用例

##### PDF 変換のみ（マージなし）

```bash
python jb_docs.py --no-merge
```

##### カスタム出力ファイル名を指定

```bash
python jb_docs.py --output custom_jetbrains_docs.pdf
```

##### カスタム一時ディレクトリを指定

```bash
python jb_docs.py --temp-dir custom_temp_dir
```

##### リクエスト間の遅延を調整

```bash
python jb_docs.py --delay 2.0
```

##### 処理後に一時ファイルを削除

```bash
python jb_docs.py --clean
```

### main.py

このスクリプトは、ドキュメントの取得と PDF 変換のみを行います（古い実装）。

```bash
python main.py
```

### merge_docs.py

このスクリプトは、既存の PDF ファイルを結合するためのものです。

```bash
python merge_docs.py --input-dir temp_pdfs --output merged_output.pdf
```

## 注意点

1. サイトの構造に依存するため、JetBrains のサイト構造が変更された場合は `clean_html` 関数の調整が必要かもしれません。
2. 大量のページを処理する場合、処理時間が長くなる可能性があります。
3. サーバーに過度の負荷をかけないよう、リクエスト間に遅延を設定しています。

## 元の課題

> https://plugins.jetbrains.com/docs/intellij/sitemap.xml に書かれているURLにあるWebページを一つのpdfとして取得したいです。Pythonを使って作成する場合、どのような設計・スクリプトにすればよいか検討してください
>
> なお、必要と思われるライブラリはuvですでにインストール済です。pyproject.tomlを確認してください。

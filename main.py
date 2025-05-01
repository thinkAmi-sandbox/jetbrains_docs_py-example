import os
import requests
from bs4 import BeautifulSoup
from xhtml2pdf import pisa
from pypdf import PdfMerger
import tempfile
import logging
import time

# ロギング設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 定数
SITEMAP_URL = "https://plugins.jetbrains.com/docs/intellij/sitemap.xml"
OUTPUT_PDF = "jetbrains_intellij_docs.pdf"
TEMP_DIR = "temp_pdfs_bkup"
REQUEST_DELAY = 1  # サーバーに負荷をかけないための遅延（秒）


def fetch_sitemap(url):
    """
    サイトマップを取得して解析する
    """
    logger.info(f"サイトマップを取得中: {url}")
    response = requests.get(url)
    response.raise_for_status()  # エラーがあれば例外を発生

    soup = BeautifulSoup(response.content, 'lxml')
    urls = [loc.text for loc in soup.find_all('loc')]

    logger.info(f"{len(urls)}個のURLを抽出しました")
    return urls


def fetch_page_content(url):
    """
    指定されたURLからウェブページのコンテンツを取得する
    """
    logger.info(f"ページを取得中: {url}")
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except Exception as e:
        logger.error(f"ページの取得に失敗しました: {url}, エラー: {e}")
        return None


def clean_html(html_content, url):
    """
    HTMLコンテンツを整形して、PDF変換に適した形式にする
    """
    soup = BeautifulSoup(html_content, 'lxml')

    # タイトルを取得
    title = soup.title.text if soup.title else "No Title"

    # メインコンテンツを特定（サイトの構造に応じて調整が必要）
    main_content = soup.find('main') or soup.find('article') or soup.find('div', class_='content')

    if not main_content:
        logger.warning(f"メインコンテンツが見つかりませんでした: {url}")
        main_content = soup.body

    # PDF用のHTMLテンプレート
    html_template = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>{title}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            h1 {{ color: #333; }}
            a {{ color: #0066cc; }}
            img {{ max-width: 100%; height: auto; }}
            pre, code {{ background-color: #f5f5f5; padding: 5px; border-radius: 3px; }}
        </style>
    </head>
    <body>
        <h1>{title}</h1>
        <p><a href="{url}">{url}</a></p>
        <hr>
        {main_content}
    </body>
    </html>
    """

    return html_template


def html_to_pdf(html_content, output_path):
    """
    HTMLをPDFに変換する
    """
    with open(output_path, "wb") as pdf_file:
        pisa_status = pisa.CreatePDF(html_content, dest=pdf_file)

    return not pisa_status.err


def merge_pdfs(pdf_files, output_path):
    """
    複数のPDFファイルを1つに結合する
    """
    merger = PdfMerger()

    for pdf in pdf_files:
        try:
            merger.append(pdf)
        except Exception as e:
            logger.error(f"PDFの結合に失敗しました: {pdf}, エラー: {e}")

    merger.write(output_path)
    merger.close()

    logger.info(f"PDFを結合しました: {output_path}")


def main():
    # 一時ディレクトリの作成
    if not os.path.exists(TEMP_DIR):
        os.makedirs(TEMP_DIR)

    try:
        # サイトマップからURLを取得
        urls = fetch_sitemap(SITEMAP_URL)

        pdf_files = []

        # 各URLのコンテンツを取得してPDFに変換
        for i, url in enumerate(urls):
            try:
                # サーバーに負荷をかけないよう遅延を入れる
                if i > 0:
                    time.sleep(REQUEST_DELAY)

                # ウェブページを取得
                html_content = fetch_page_content(url)
                if not html_content:
                    continue

                # HTMLを整形
                clean_content = clean_html(html_content, url)

                # 一時PDFファイルのパス
                pdf_path = os.path.join(TEMP_DIR, f"page_{i}.pdf")

                # HTMLをPDFに変換
                if html_to_pdf(clean_content, pdf_path):
                    pdf_files.append(pdf_path)
                    logger.info(f"PDFに変換しました: {url} -> {pdf_path}")
                else:
                    logger.error(f"PDFへの変換に失敗しました: {url}")

            except Exception as e:
                logger.error(f"処理中にエラーが発生しました: {url}, エラー: {e}")

        # すべてのPDFを結合
        if pdf_files:
            merge_pdfs(pdf_files, OUTPUT_PDF)
            logger.info(f"すべてのドキュメントを結合しました: {OUTPUT_PDF}")
        else:
            logger.warning("結合するPDFファイルがありません")

    finally:
        # 一時ファイルのクリーンアップ（オプション）
        # for pdf in pdf_files:
        #     if os.path.exists(pdf):
        #         os.remove(pdf)
        # if os.path.exists(TEMP_DIR):
        #     os.rmdir(TEMP_DIR)
        pass


if __name__ == "__main__":
    main()

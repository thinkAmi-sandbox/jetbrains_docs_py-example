import os
import requests
import argparse
import logging
import time
from bs4 import BeautifulSoup
from xhtml2pdf import pisa
from pypdf import PdfWriter, PdfReader

# ロギング設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 定数
SITEMAP_URL = "https://plugins.jetbrains.com/docs/intellij/sitemap.xml"


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
    if not pdf_files:
        logger.warning("結合するPDFファイルがありません")
        return False
    
    logger.info(f"{len(pdf_files)}個のPDFファイルを結合します")
    
    writer = PdfWriter()
    
    success_count = 0
    for pdf in pdf_files:
        try:
            if not os.path.exists(pdf):
                logger.warning(f"ファイルが存在しません: {pdf}")
                continue
                
            # PdfWriter では append ではなく PdfReader からページを読み込んで add_page を使用
            with open(pdf, 'rb') as file:
                reader = PdfReader(file)
                for page in reader.pages:
                    writer.add_page(page)
            success_count += 1
            logger.info(f"PDFを追加しました: {pdf}")
        except Exception as e:
            logger.error(f"PDFの結合に失敗しました: {pdf}, エラー: {e}")
    
    if success_count == 0:
        logger.error("結合可能なPDFファイルがありませんでした")
        return False
    
    try:
        # 結合したPDFを書き込む
        with open(output_path, 'wb') as output_file:
            writer.write(output_file)
        logger.info(f"PDFを結合しました: {output_path}")
        return True
    except Exception as e:
        logger.error(f"PDFの書き込みに失敗しました: {output_path}, エラー: {e}")
        return False


def process_pages(temp_dir, request_delay=1):
    """
    サイトマップからURLを取得し、各ページをPDFに変換する
    """
    # サイトマップからURLを取得
    urls = fetch_sitemap(SITEMAP_URL)
    
    pdf_files = []
    
    # 各URLのコンテンツを取得してPDFに変換
    for i, url in enumerate(urls):
        try:
            # サーバーに負荷をかけないよう遅延を入れる
            if i > 0:
                time.sleep(request_delay)
            
            # ウェブページを取得
            html_content = fetch_page_content(url)
            if not html_content:
                continue
            
            # HTMLを整形
            clean_content = clean_html(html_content, url)
            
            # 一時PDFファイルのパス
            pdf_path = os.path.join(temp_dir, f"page_{i}.pdf")
            
            # HTMLをPDFに変換
            if html_to_pdf(clean_content, pdf_path):
                pdf_files.append(pdf_path)
                logger.info(f"PDFに変換しました: {url} -> {pdf_path}")
            else:
                logger.error(f"PDFへの変換に失敗しました: {url}")
        
        except Exception as e:
            logger.error(f"処理中にエラーが発生しました: {url}, エラー: {e}")
    
    return pdf_files


def main():
    # コマンドライン引数の解析
    parser = argparse.ArgumentParser(description='JetBrains IntelliJ ドキュメントをPDFとして取得・結合します')
    parser.add_argument('--temp-dir', type=str, default='temp_pdfs', 
                        help='一時的なPDFファイル置き場 (デフォルト: temp_pdfs)')
    parser.add_argument('--merge', action='store_true', default=True,
                        help='PDFをマージするかどうか (デフォルト: True)')
    parser.add_argument('--no-merge', action='store_false', dest='merge',
                        help='PDFをマージしない')
    parser.add_argument('--output', type=str, default='jetbrains_intellij_docs.pdf',
                        help='出力PDFファイルのパス (デフォルト: jetbrains_intellij_docs.pdf)')
    parser.add_argument('--delay', type=float, default=1.0,
                        help='リクエスト間の遅延（秒） (デフォルト: 1.0)')
    parser.add_argument('--clean', action='store_true',
                        help='処理完了後に一時ファイルを削除する')
    
    args = parser.parse_args()
    
    # 一時ディレクトリの作成
    if not os.path.exists(args.temp_dir):
        os.makedirs(args.temp_dir)
        logger.info(f"一時ディレクトリを作成しました: {args.temp_dir}")
    
    try:
        # ページの処理
        pdf_files = process_pages(args.temp_dir, args.delay)
        
        if not pdf_files:
            logger.warning("PDFファイルが生成されませんでした")
            return
        
        # PDFのマージ
        if args.merge:
            success = merge_pdfs(pdf_files, args.output)
            if success:
                logger.info(f"すべてのドキュメントを結合しました: {args.output}")
            else:
                logger.error("PDFの結合に失敗しました")
        else:
            logger.info("PDFのマージはスキップされました")
    
    finally:
        # 一時ファイルのクリーンアップ（オプション）
        if args.clean:
            logger.info("一時ファイルを削除しています...")
            for pdf in pdf_files:
                if os.path.exists(pdf):
                    os.remove(pdf)
            
            # 一時ディレクトリが空の場合は削除
            if os.path.exists(args.temp_dir) and not os.listdir(args.temp_dir):
                os.rmdir(args.temp_dir)
                logger.info(f"空の一時ディレクトリを削除しました: {args.temp_dir}")


if __name__ == "__main__":
    main()
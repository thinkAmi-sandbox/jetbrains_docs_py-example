import os
import logging
import argparse
from pypdf import PdfWriter, PdfReader

# ロギング設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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

def main():
    parser = argparse.ArgumentParser(description='複数のPDFファイルを1つに結合します')
    parser.add_argument('--input-dir', type=str, help='PDFファイルが格納されているディレクトリ')
    parser.add_argument('--output', type=str, default='merged_output.pdf', help='出力PDFファイルのパス')
    parser.add_argument('--files', nargs='+', help='結合するPDFファイルのリスト（--input-dirの代わりに使用）')
    
    args = parser.parse_args()
    
    if args.input_dir and os.path.isdir(args.input_dir):
        # ディレクトリ内のすべてのPDFファイルを取得
        pdf_files = [
            os.path.join(args.input_dir, f) 
            for f in os.listdir(args.input_dir) 
            if f.lower().endswith('.pdf')
        ]
        pdf_files.sort()  # ファイル名でソート
    elif args.files:
        # コマンドラインで指定されたファイルを使用
        pdf_files = args.files
    else:
        logger.error("PDFファイルが指定されていません。--input-dir または --files オプションを使用してください。")
        return
    
    if not pdf_files:
        logger.warning("結合するPDFファイルが見つかりませんでした")
        return
    
    logger.info(f"結合するPDFファイル: {len(pdf_files)}個")
    success = merge_pdfs(pdf_files, args.output)
    
    if success:
        logger.info(f"PDFの結合が完了しました: {args.output}")
    else:
        logger.error("PDFの結合に失敗しました")

if __name__ == "__main__":
    main()
import os
from document_parse import UpstagePDFParser
from document_parse_async import UpstageAsyncPDFParser
from libs.json_saver import save_to_json

def generate_comparison_html(file_name, parsed_html, file_path, file_extension):
    """HTML 파일 생성 (변환 결과 및 원본 비교)"""
    if file_extension.lower() in ['.pdf']:
        file_display = f"""
            <div id="pdf-container"></div>
            <script>
                const url = '{file_path}';
                pdfjsLib.getDocument(url).promise.then(pdf => {{
                    const pdfContainer = document.getElementById('pdf-container');
                    for (let pageNumber = 1; pageNumber <= pdf.numPages; pageNumber++) {{
                        pdf.getPage(pageNumber).then(page => {{
                            const viewport = page.getViewport({{ scale: 1.5 }});
                            const pageWrapper = document.createElement('div');
                            pageWrapper.classList.add('page-wrapper');

                            const canvas = document.createElement('canvas');
                            canvas.width = viewport.width;
                            canvas.height = viewport.height;
                            pageWrapper.appendChild(canvas);
                            pdfContainer.appendChild(pageWrapper);

                            const context = canvas.getContext('2d');
                            page.render({{
                                canvasContext: context,
                                viewport: viewport
                            }});

                            const pageNumberLabel = document.createElement('div');
                            pageNumberLabel.classList.add('page-number');
                            pageNumberLabel.textContent = '페이지 ' + pageNumber + ' / ' + pdf.numPages;
                            pageWrapper.appendChild(pageNumberLabel);
                        }});
                    }}
                }}).catch(error => {{
                    console.error('PDF 로드 오류:', error);
                }});
            </script>
        """
    else:
        file_display = f'<img src="{file_path}" alt="원본 이미지" style="width:100%;">'

    html_content = f"""
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{file_name} 비교 보기</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 0;
            }}
            .container {{
                display: flex;
                height: 100vh;
            }}
            .panel {{
                flex: 1;
                display: flex;
                flex-direction: column;
                border-right: 2px solid #ddd;
            }}
            .panel:last-child {{
                border-right: none;
            }}
            .panel h2 {{
                padding: 20px;
                margin: 0;
                background: #2c3e50;
                color: white;
                text-align: center;
                flex-shrink: 0;
            }}
            .content {{
                flex-grow: 1;
                padding: 20px;
                overflow-y: auto;
                background-color: #f9f9f9;
            }}
            /* 테이블 스타일 조정 */
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 10px;
                box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
                background: #fff;
            }}
            th, td {{
                border: 1px solid #ddd;
                padding: 12px;
                text-align: left;
                font-size: 14px;
            }}
            th {{
                background-color: #4CAF50;
                color: white;
            }}
            tr:nth-child(even) {{
                background-color: #f2f2f2;
            }}
            tr:nth-child(odd) {{
                background-color: #ffffff;
            }}
            tr:hover {{
                background-color: #d1e7dd;
            }}
            #pdf-container {{
                flex-grow: 1;
                overflow-y: auto;
                border: none;
                padding: 20px;
                background-color: #f9f9f9;
            }}
            .page-wrapper {{
                position: relative;
                margin-bottom: 20px;
            }}
            .page-number {{
                position: absolute;
                top: 10px;
                right: 10px;
                background: rgba(0, 0, 0, 0.7);
                color: #fff;
                padding: 5px 10px;
                font-size: 14px;
                border-radius: 3px;
                font-weight: bold;
            }}
            canvas {{
                display: block;
                width: 100%;
                margin-bottom: 20px;
                border: 1px solid #ccc;
                background: #fff;
            }}
        </style>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/2.12.313/pdf.min.js"></script>
    </head>
    <body>
        <div class="container">
            <div class="panel">
                <h2>변환된 HTML 문서</h2>
                <div class="content">
                    {parsed_html}
                </div>
            </div>
            <div class="panel">
                <h2>원본 {file_extension.lstrip('.').upper()} 파일</h2>
                <div class="content">
                    {file_display}
                </div>
            </div>
        </div>
    </body>
    </html>
    """

    output_html_path = f"output/{file_name}.html"
    with open(output_html_path, "w", encoding="utf-8") as html_file:
        html_file.write(html_content)
    print(f"HTML 비교 파일이 생성되었습니다: {output_html_path}")

def main():
    base_path = os.path.join(os.path.dirname(__file__), "..", "dataset")
    api_key = os.environ.get("UPSTAGE_API_KEY", "")

    # 100 페이지 이내이면 동기식 (빠름), 초과시 비동기식 (매우 느림)
    # parser = UpstagePDFParser(api_key)
    parser = UpstageAsyncPDFParser(api_key)

    while True:
        print("\nPDF 또는 이미지 파일명을 입력하세요. (여러 파일은 쉼표로 구분하세요)")
        print("Enter을 입력하면 프로그램이 종료됩니다.")
        file_input = input("파일명(쉼표 구분): ").strip()

        if file_input == "":
            print("프로그램을 종료합니다.")
            break

        file_names = [name.strip() for name in file_input.split(",") if name.strip()]

        for file_name in file_names:
            file_path = os.path.join(base_path, file_name)

            if not os.path.isfile(file_path):
                print(f"파일을 찾을 수 없습니다: {file_path}")
                continue

            try:
                print(f"{file_name} 처리 중...")
                results = parser.parse_document(file_path)

                # JSON 저장
                output_json = f"output/{file_name}.json"
                save_to_json(results, output_json)
                print(f"결과가 {output_json}에 저장되었습니다.")

                # HTML 데이터 가져오기
                parsed_html = results.get("parsed_content", {}).get("content", {}).get("html", "<p>HTML 데이터를 불러올 수 없습니다.</p>")

                # 확장자 구분 (PDF 또는 이미지)
                _, file_extension = os.path.splitext(file_name)
                generate_comparison_html(file_name, parsed_html, file_path, file_extension)

            except Exception as e:
                print(f"오류가 발생했습니다: {e}")

if __name__ == "__main__":
    main()

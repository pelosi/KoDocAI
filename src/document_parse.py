import os
import requests
from datetime import datetime
from libs.logger import Logger

class UpstagePDFParser:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.logger = Logger()
        self.api_url = "https://api.upstage.ai/v1/document-ai/document-parse"

    def parse_document(self, file_path: str):
        try:
            self.logger.start("File Metadata Extraction")
            file_metadata = self._get_file_metadata(file_path)
            self.logger.end()

            self.logger.start("Uploading Document to Upstage API")
            document_data = self._upload_and_parse(file_path)
            self.logger.end()

            return {
                "file_metadata": file_metadata,
                "parsed_content": document_data,
            }
        except Exception as e:
            raise RuntimeError(f"Error parsing document: {e}")

    def _get_file_metadata(self, file_path: str):
        try:
            file_stats = os.stat(file_path)
            return {
                "file_name": os.path.basename(file_path),
                "file_time": datetime.fromtimestamp(file_stats.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
            }
        except FileNotFoundError as e:
            raise FileNotFoundError(f"Error retrieving file metadata: {e}")
        except Exception as e:
            raise RuntimeError(f"Unexpected error retrieving file metadata: {e}")

    def _upload_and_parse(self, file_path: str):
        try:
            with open(file_path, "rb") as file:
                files = {"document": file}
                # data = {"ocr": "force", "base64_encoding": '["table"]'}
                data = {"ocr": "force", "base64_encoding": '["table"]', "output_formats": '["html", "markdown"]'}
                headers = {"Authorization": f"Bearer {self.api_key}"}

                response = requests.post(self.api_url, headers=headers, files=files, data=data)
                response.raise_for_status()
                return response.json()
        except requests.RequestException as e:
            raise RuntimeError(f"API request failed: {e}")

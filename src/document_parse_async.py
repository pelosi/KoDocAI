import os
import time
import requests
import json
from datetime import datetime
from libs.logger import Logger

class UpstageAsyncPDFParser:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.logger = Logger()
        self.upload_url = "https://api.upstage.ai/v1/document-ai/async/document-parse"
        self.status_url = "https://api.upstage.ai/v1/document-ai/requests"
        self.result_url = "https://api.upstage.ai/v1/document-ai/requests"

    def parse_document(self, file_path: str):
        try:
            self.logger.start("File Metadata Extraction")
            file_metadata = self._get_file_metadata(file_path)
            self.logger.end()

            self.logger.start("Uploading Document to Upstage API (Async)")
            job_id = self._upload_file_async(file_path)
            self.logger.end()

            self.logger.start("Polling for document processing completion")
            result_data = self._poll_for_results(job_id)
            self.logger.end()

            return {
                "file_metadata": file_metadata,
                "parsed_content": result_data,
            }
        except Exception as e:
            raise RuntimeError(f"Error parsing document asynchronously: {e}")

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

    def _upload_file_async(self, file_path: str):
        try:
            with open(file_path, "rb") as file:
                files = {"document": file}
                data = {
                    "ocr": "force",
                    "base64_encoding": '["table"]',
                    "output_formats": '["html", "markdown"]'
                }
                headers = {"Authorization": f"Bearer {self.api_key}"}

                response = requests.post(self.upload_url, headers=headers, files=files, data=data)
                response.raise_for_status()
                response_json = response.json()

                # print("API 응답 데이터:", response_json)

                if "request_id" not in response_json:
                    raise RuntimeError(f"Failed to retrieve request ID from response. Full response: {response_json}")
                
                return response_json["request_id"]
        except requests.RequestException as e:
            raise RuntimeError(f"API request failed: {e}")


    def _poll_for_results(self, request_id: str, poll_interval: int = 10, max_attempts: int = 300):
        headers = {"Authorization": f"Bearer {self.api_key}"}

        for attempt in range(max_attempts):
            try:
                response = requests.get(f"{self.status_url}/{request_id}", headers=headers)
                response.raise_for_status()
                status_data = response.json()
                # print(f"status_data: {status_data}")
                
                if status_data.get("status") == "completed":
                    print(f"Processing... Progress {status_data["completed_pages"]}/{status_data["total_pages"]}")
                    download_urls = [batch["download_url"] for batch in status_data.get("batches", [])]
                    return self._download_and_merge_results(download_urls)
                elif status_data.get("status") == "failed":
                    raise RuntimeError("Document processing failed.")
                else:
                    print(f"Processing... Progress {status_data["completed_pages"]}/{status_data["total_pages"]} Attempt {attempt + 1}/{max_attempts}")
                    time.sleep(poll_interval)
            except requests.RequestException as e:
                raise RuntimeError(f"Polling request failed: {e}")

        raise RuntimeError("Document processing timed out.")

    def _download_and_merge_results(self, download_urls: list):
        """ 변환된 데이터를 다운로드하고 JSON으로 병합하여 반환하는 함수 """
        merged_content = {
            "api": None,
            "content": {
                "html": "",
                "markdown": "",
                "text": ""
            },
            "elements": [],
            "model": None,
            "usage": {
                "pages": 0
            }
        }

        for idx, url in enumerate(download_urls):
            # print(f"Downloading part {idx + 1} from {url}...")
            print(f"Downloading part {idx + 1}...")
            response = requests.get(url)

            if response.status_code == 200:
                try:
                    part_content = response.json()  # JSON 데이터 파싱

                    if idx == 0:
                        # 첫 번째 JSON의 "api" 및 "model" 값 설정
                        merged_content["api"] = part_content.get("api", "")
                        merged_content["model"] = part_content.get("model", "")

                    # "html", "markdown", "text" 병합
                    merged_content["content"]["html"] += part_content.get("content", {}).get("html", "")
                    merged_content["content"]["markdown"] += part_content.get("content", {}).get("markdown", "")
                    merged_content["content"]["text"] += part_content.get("content", {}).get("text", "")

                    # "elements" 리스트 병합
                    merged_content["elements"].extend(part_content.get("elements", []))

                    # "pages" 합산
                    merged_content["usage"]["pages"] += part_content.get("usage", {}).get("pages", 0)

                except json.JSONDecodeError:
                    print(f"Failed to parse JSON from {url}")
            else:
                print(f"Failed to download {url}")

        if merged_content["api"] is None or merged_content["model"] is None:
            raise RuntimeError("No valid data retrieved from the provided URLs.")

        print("All parts successfully downloaded and merged into JSON.")
        return merged_content
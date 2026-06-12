import asyncio
import os
import shutil
import unittest

from fastapi.responses import FileResponse, Response, StreamingResponse

from tests.test_my_yolo_train_tool_callbacks import load_functions


class FastApiDataRouteTests(unittest.TestCase):
    def setUp(self):
        self.data_dir = os.path.join(os.getcwd(), "data", "__codex_test_range")
        os.makedirs(self.data_dir, exist_ok=True)
        self.file_path = os.path.join(self.data_dir, "range.bin")
        with open(self.file_path, "wb") as fp:
            fp.write(b"0123456789")
        namespace = load_functions(
            "parse_range_header",
            "iter_file_range",
            "data_file_response",
            extra_globals={
                "FileResponse": FileResponse,
                "Response": Response,
                "StreamingResponse": StreamingResponse,
                "os": os,
            },
        )
        self.data_file_response = namespace["data_file_response"]

    def tearDown(self):
        shutil.rmtree(self.data_dir, ignore_errors=True)

    def read_streaming_body(self, response):
        async def collect():
            chunks = []
            async for chunk in response.body_iterator:
                chunks.append(chunk)
            return b"".join(chunks)

        return asyncio.run(collect())

    def test_data_route_supports_byte_range_requests(self):
        response = self.data_file_response(self.file_path, "application/octet-stream", "bytes=2-5")

        self.assertEqual(response.status_code, 206)
        self.assertEqual(self.read_streaming_body(response), b"2345")
        self.assertEqual(response.headers["content-range"], "bytes 2-5/10")
        self.assertEqual(response.headers["accept-ranges"], "bytes")
        self.assertEqual(response.headers["content-length"], "4")

    def test_data_route_rejects_invalid_byte_range(self):
        response = self.data_file_response(self.file_path, "application/octet-stream", "bytes=99-100")

        self.assertEqual(response.status_code, 416)
        self.assertEqual(response.headers["content-range"], "bytes */10")


if __name__ == "__main__":
    unittest.main()

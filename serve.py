#!/usr/bin/env python3
"""Simple HTTP server with Range request support (needed for video seeking)."""
import http.server
import os
import sys

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 3456

class RangeHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def send_head(self):
        path = self.translate_path(self.path)
        if os.path.isdir(path):
            return super().send_head()

        try:
            f = open(path, 'rb')
        except OSError:
            self.send_error(404, "File not found")
            return None

        fs = os.fstat(f.fileno())
        file_size = fs.st_size

        self.send_response(200)
        ctype = self.guess_type(path)
        self.send_header("Content-type", ctype)
        self.send_header("Accept-Ranges", "bytes")

        range_header = self.headers.get('Range')
        if range_header:
            try:
                byte1, byte2 = 0, None
                m = range_header.strip().replace('bytes=', '')
                if '-' in m:
                    parts = m.split('-')
                    if parts[0]:
                        byte1 = int(parts[0])
                    if parts[1]:
                        byte2 = int(parts[1])
                if byte2 is None:
                    byte2 = file_size - 1
                byte2 = min(byte2, file_size - 1)
                length = byte2 - byte1 + 1
                f.seek(byte1)
                self.send_response(206)
                self.send_header("Content-type", ctype)
                self.send_header("Accept-Ranges", "bytes")
                self.send_header("Content-Range", f"bytes {byte1}-{byte2}/{file_size}")
                self.send_header("Content-Length", str(length))
                self.end_headers()
                return f
            except Exception:
                pass

        self.send_header("Content-Length", str(file_size))
        self.end_headers()
        return f

    def log_message(self, format, *args):
        pass  # Quiet mode

if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    with http.server.HTTPServer(('', PORT), RangeHTTPRequestHandler) as httpd:
        print(f"Serving on http://localhost:{PORT}")
        httpd.serve_forever()

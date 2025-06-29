
import http.server
import socketserver
import urllib.request
import urllib.parse
import json
import os
from urllib.error import HTTPError

class ProxyHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory='frontend', **kwargs)
    
    def do_GET(self):
        # Serve index.html for root path
        if self.path == '/':
            self.path = '/index.html'
        return super().do_GET()
    def do_POST(self):
        if self.path == '/det':
            try:
                # Read the request body
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                
                # Forward the request to the backend
                backend_url = 'http://localhost:8000/det'
                req = urllib.request.Request(backend_url, data=post_data)
                
                # Copy headers (especially Content-Type for multipart)
                for header, value in self.headers.items():
                    if header.lower() not in ['host', 'content-length']:
                        req.add_header(header, value)
                
                # Make the request to backend
                with urllib.request.urlopen(req) as response:
                    response_data = response.read()
                    
                # Send response back to frontend
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
                self.send_header('Access-Control-Allow-Headers', '*')
                self.end_headers()
                self.wfile.write(response_data)
                
            except HTTPError as e:
                self.send_response(e.code)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                error_response = json.dumps({"error": f"Backend error: {e.reason}"})
                self.wfile.write(error_response.encode())
                
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                error_response = json.dumps({"error": f"Proxy error: {str(e)}"})
                self.wfile.write(error_response.encode())
        else:
            # Handle other requests normally
            super().do_POST()
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.end_headers()

if __name__ == "__main__":
    PORT = 5000
    # Change to the directory where HTML files are located
    import os
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    with socketserver.TCPServer(("0.0.0.0", PORT), ProxyHandler) as httpd:
        print(f"Serving frontend at port {PORT}")
        print(f"Frontend available at: http://0.0.0.0:{PORT}")
        httpd.serve_forever()


### OLD DO NOT USE

import http.server
import os
from os import path

project_directory = "/home/<USERID>/move_me/git_projects/lpar_consistency_check"
main_html_page = ''

## Get html pages from project dir
for root, dirnames, filenames in os.walk(project_directory):
    for filename in filenames:
        if filename.endswith('.html'):
            fname = os.path.join(root, filename)
            main_html_page = fname

## Server static html page - need to inject variables into html page 
class MyHttpRequestHandler(http.server.SimpleHTTPRequestHandler):

    def _set_headers(self):
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.send_header('Content-Length', path.getsize(self.getPath()))
        self.end_headers()

    def getPath(self):
        if self.path == '/':
            content_path = path.join(
                project_directory, main_html_page)
        else:
            content_path = path.join(project_directory, str(self.path).split('?')[0][1:])
        return content_path

    def getContent(self, content_path):
        with open(content_path, mode='r', encoding='utf-8') as f:
            content = f.read()
        return bytes(content, 'utf-8')

    def do_GET(self):
        self._set_headers()
        self.wfile.write(self.getContent(self.getPath()))


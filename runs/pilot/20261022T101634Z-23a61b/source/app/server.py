"""Synthetic fault-injection API. No external services or personal data."""
import json
import os
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

MODE = os.environ.get('FAULT_MODE', 'healthy')


def event(level, message):
    print(json.dumps({'time': datetime.now(timezone.utc).isoformat(),
                      'level': level, 'message': message}), flush=True)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass  # Do not duplicate HTTP status in the log detector's input.

    def reply(self, status, data):
        body = json.dumps(data).encode()
        try:
            self.send_response(status)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            pass  # A client timeout must not manufacture an application error log.

    def do_GET(self):
        if self.path == '/ready':
            self.reply(200, {'ready': True})
            return
        if self.path != '/api/items':
            self.reply(404, {'error': 'not found'})
            return
        if MODE == 'exception':
            try:
                _ = 1 / 0
            except ZeroDivisionError:
                event('ERROR', 'Item calculation failed: ZeroDivisionError')
                self.reply(500, {'error': 'calculation failed'})
                return
        if MODE == 'silent_http_error':
            self.reply(503, {'error': 'service unavailable'})
            return
        if MODE == 'background_error':
            try:
                raise OSError('Simulated audit sink unavailable')
            except OSError:
                event('ERROR', 'Audit write failed; item response still available')
        if MODE == 'slow_response':
            time.sleep(1.0)
        self.reply(200, {'items': [{'id': 1, 'name': 'demo item'}]})


if __name__ == '__main__':
    if MODE not in {'healthy', 'exception', 'silent_http_error',
                    'background_error', 'slow_response'}:
        raise ValueError('Unsupported fault mode')
    event('INFO', 'API started')  # Never expose injected fault labels to detectors.
    ThreadingHTTPServer(('0.0.0.0', int(os.environ.get('PORT', '8080'))), Handler).serve_forever()

"""Synthetic fault-injection API, protocol 2.0. No external services or personal data.

Protocol 2.0 adds environmental noise to every mode (occasional latency spikes and
benign ERROR log lines) and two fault types whose visibility is not fixed in advance
(intermittent_exception, crash_restart). Noise is drawn from TRIAL_SEED so a trial's
random draws can be traced; wall-clock timing still varies between machines.
"""
import json
import os
import random
import threading
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

MODES = {'healthy', 'exception', 'silent_http_error', 'background_error', 'slow_response',
         'intermittent_exception', 'crash_restart'}
MODE = os.environ.get('FAULT_MODE', 'healthy')
RNG = random.Random(os.environ.get('TRIAL_SEED', '0') + ':' + os.environ.get('HOSTNAME', ''))
LOCK = threading.Lock()
# Noise parameters are fixed by protocol 2.0 and identical for every mode.
BASE_DELAY = (0.005, 0.05)      # seconds, uniform, every /api/items request
SPIKE_P, SPIKE_DELAY = 0.04, (0.25, 0.60)   # rare latency spike; >0.4 s exceeds client timeout
BENIGN_ERROR_P = 0.05           # benign ERROR line that does not affect the response
INTERMITTENT_P = 0.35           # per-request failure probability in intermittent_exception
CRASH_AFTER = (0.05, 0.50)      # seconds after the first /api/items request
crash_armed = False


def draw(kind, *args):
    with LOCK:
        return getattr(RNG, kind)(*args)


def event(level, message):
    print(json.dumps({'time': datetime.now(timezone.utc).isoformat(),
                      'level': level, 'message': message}), flush=True)


def crash_later():
    time.sleep(draw('uniform', *CRASH_AFTER))
    os._exit(1)  # Abrupt process death: no log line, Docker restart policy restarts it.


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
        global crash_armed
        if self.path == '/ready':
            self.reply(200, {'ready': True})
            return
        if self.path != '/api/items':
            self.reply(404, {'error': 'not found'})
            return
        delay = draw('uniform', *BASE_DELAY)
        if draw('random') < SPIKE_P:
            delay += draw('uniform', *SPIKE_DELAY)
        time.sleep(delay)
        if draw('random') < BENIGN_ERROR_P:
            event('ERROR', 'Upstream cache timeout; served from fallback')
        if MODE == 'crash_restart':
            with LOCK:
                arm, crash_armed = not crash_armed, True
            if arm:
                threading.Thread(target=crash_later, daemon=True).start()
        if MODE == 'exception' or (MODE == 'intermittent_exception' and draw('random') < INTERMITTENT_P):
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
    if MODE not in MODES:
        raise ValueError('Unsupported fault mode')
    event('INFO', 'API started')  # Never expose injected fault labels to detectors.
    ThreadingHTTPServer(('0.0.0.0', int(os.environ.get('PORT', '8080'))), Handler).serve_forever()

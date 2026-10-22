import importlib.util
import json
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import lab


class DetectionTests(unittest.TestCase):
    def test_signal_isolation_and_combinations(self):
        normal = [{'status': 200, 'transport_error': ''}]
        running = {'Running': True, 'OOMKilled': False, 'RestartCount': 0}
        logs = json.dumps({'level': 'ERROR', 'message': 'write failed'})
        self.assertEqual(lab.detectors(normal, running, logs),
                         {'http': False, 'container': False, 'logs': True})
        self.assertEqual(len(lab.CONDITIONS), 7)
        error = [{'status': 503, 'transport_error': ''}]
        self.assertEqual(lab.detectors(error, running, ''),
                         {'http': True, 'container': False, 'logs': False})
        stopped = dict(running, Running=False)
        self.assertTrue(lab.detectors(normal, stopped, '')['container'])

    def test_error_transport_is_positive(self):
        self.assertTrue(lab.detectors([{'status': None, 'transport_error': 'timeout'}],
                        {'Running': True, 'OOMKilled': False, 'RestartCount': 0}, '')['http'])

    def test_missing_or_corrupt_data_not_healthy(self):
        with self.assertRaises(ValueError):
            lab.detectors([], {}, '')
        with self.assertRaises(ValueError):
            lab.detectors([{'status': 200, 'transport_error': ''}], {}, 'not-json')

    def test_confusion_matrix_and_undefined_values(self):
        rows = [{'truth': t, 'prediction': p} for t, p in [(1,1), (1,0), (0,1), (0,0)]]
        result = lab.metrics(rows, 'test')
        for name in ('TP','TN','FP','FN'):
            self.assertEqual(result[name], 1)
        for name in ('accuracy','precision','recall','FPR','F1','balanced_accuracy'):
            self.assertEqual(result[name], 0.5)
        result = lab.metrics([{'truth': 0, 'prediction': 0}], 'test')
        self.assertEqual(result['precision'], '')
        self.assertEqual(result['recall'], '')


class StatisticsTests(unittest.TestCase):
    def test_wilson_interval(self):
        low, high = lab.wilson(8, 10)
        self.assertAlmostEqual(low, 0.490162, places=5)
        self.assertAlmostEqual(high, 0.943318, places=5)
        self.assertEqual(lab.wilson(0, 0), ('', ''))

    def test_mcnemar_exact(self):
        self.assertEqual(lab.mcnemar_exact(0, 0), 1.0)
        self.assertAlmostEqual(lab.mcnemar_exact(0, 6), 0.03125)
        self.assertEqual(lab.mcnemar_exact(3, 3), 1.0)


class APIIntegrationTests(unittest.TestCase):
    """Real local HTTP requests: software checks, not Docker research observations."""
    def test_api_faults(self):
        spec = importlib.util.spec_from_file_location('api', ROOT/'app/server.py')
        api = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(api)
        events = []
        api.event = lambda level, message: events.append({'level': level, 'message': message})
        # Noise off for deterministic software checks; protocol noise is exercised in Docker runs.
        api.SPIKE_P = api.BENIGN_ERROR_P = 0.0
        server = ThreadingHTTPServer(('127.0.0.1', 0), api.Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        url = f'http://127.0.0.1:{server.server_address[1]}'
        try:
            for mode, status, errors in [('healthy',200,0), ('exception',500,1),
                                         ('silent_http_error',503,0), ('background_error',200,1)]:
                with self.subTest(mode=mode):
                    api.MODE = mode
                    events.clear()
                    result = lab.request(url+'/api/items', 2)
                    self.assertEqual(result['status'], status)
                    self.assertEqual(len(events), errors)
                    self.assertNotIn(mode, result['body'])
                    self.assertEqual(lab.request(url+'/ready', 2)['status'], 200)
            api.MODE, api.INTERMITTENT_P = 'intermittent_exception', 1.0
            self.assertEqual(lab.request(url+'/api/items', 2)['status'], 500)
            api.INTERMITTENT_P = 0.0
            self.assertEqual(lab.request(url+'/api/items', 2)['status'], 200)
            api.SPIKE_P, api.SPIKE_DELAY = 1.0, (0.3, 0.3)
            api.MODE = 'healthy'
            self.assertTrue(lab.request(url+'/api/items', 0.1)['transport_error'])
            api.SPIKE_P = 0.0
            api.MODE = 'slow_response'
            self.assertTrue(lab.request(url+'/api/items', 0.1)['transport_error'])
        finally:
            server.shutdown()
            server.server_close()
            thread.join()


if __name__ == '__main__':
    unittest.main()

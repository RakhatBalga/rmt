"""Collect real Docker observations, then analyze them in a separate command.

Requires Python 3.10+ and Docker Desktop (Linux containers). Standard library only.
"""
import argparse
import csv
import hashlib
import itertools
import json
import platform
import random
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))
SIGNALS = ('http', 'container', 'logs')
CONDITIONS = [combo for n in (1, 2, 3) for combo in itertools.combinations(SIGNALS, n)]


def now():
    return datetime.now(timezone.utc).isoformat()


def save(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_csv(path, rows):
    if not rows:
        raise ValueError('No rows to write')
    with path.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def docker(*args, timeout=60, check=True):
    result = subprocess.run(['docker', *args], capture_output=True, text=True,
                            encoding='utf-8', errors='replace', timeout=timeout)
    if check and result.returncode:
        raise RuntimeError(f'docker {args[0]}: {result.stderr.strip() or result.stdout.strip()}')
    return result


def request(url, timeout):
    start = time.perf_counter()
    status, body, error = None, '', ''
    try:
        with OPENER.open(url, timeout=timeout) as response:
            status, body = response.status, response.read().decode('utf-8')
    except urllib.error.HTTPError as exc:
        status, body = exc.code, exc.read().decode('utf-8')
        exc.close()
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        error = str(exc)
    return {'timestamp_utc': now(), 'status': status, 'elapsed_ms': round((time.perf_counter()-start)*1000, 3),
            'body': body, 'transport_error': error}


def detectors(http, state, logs):
    if not http:
        raise ValueError('Missing HTTP measurements')
    parsed = [json.loads(line) for line in logs.splitlines() if line.strip()]
    return {
        'http': any(r['transport_error'] or (r['status'] is not None and r['status'] >= 400) for r in http),
        'container': not state['Running'] or state['OOMKilled'] or state['RestartCount'] > 0,
        'logs': any(row['level'] in ('ERROR', 'CRITICAL') for row in parsed),
    }


def doctor():
    print('Python:', sys.version.split()[0], '| Platform:', platform.platform())
    print('Docker executable:', shutil.which('docker') or 'NOT FOUND')
    print(docker('version').stdout)
    info = json.loads(docker('info', '--format', '{{json .}}').stdout)
    if info['OSType'] != 'linux':
        raise RuntimeError('Switch Docker Desktop to Linux containers')
    print('READY: Linux Docker engine responds.')


def build():
    p = read(ROOT/'protocol.json')
    result = docker('build', '-t', p['image_tag'], str(ROOT), timeout=600, check=False)
    (ROOT/'build.log').write_text(result.stdout + result.stderr, encoding='utf-8')
    print(result.stdout + result.stderr)
    if result.returncode:
        raise RuntimeError('Image build failed; see build.log')


def collect(args):
    if args.rounds < 1:
        raise ValueError('rounds must be positive')
    doctor()
    protocol = read(ROOT/'protocol.json')
    image = json.loads(docker('image', 'inspect', protocol['image_tag']).stdout)[0]
    run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:6]
    out = ROOT/'runs'/args.phase/run_id
    out.mkdir(parents=True)
    raw = out/'raw'
    raw.mkdir()
    shutil.copy2(ROOT/'protocol.json', out/'protocol.json')
    source = out/'source'
    source.mkdir()
    for file in ('lab.py', 'Dockerfile', 'app/server.py'):
        target = source/file
        target.parent.mkdir(exist_ok=True, parents=True)
        shutil.copy2(ROOT/file, target)
    if (ROOT/'build.log').exists():
        shutil.copy2(ROOT/'build.log', out/'build.log')
    schedule = []
    rng = random.Random(protocol['seed'])
    for round_no in range(1, args.rounds+1):
        cases = ['healthy'] * protocol['healthy_trials_per_round'] + protocol['scenarios'][1:]
        rng.shuffle(cases)
        schedule += [{'trial': f'T{len(schedule)+i+1:04}', 'round': round_no, 'scenario': case,
                      'truth': int(case != 'healthy')} for i, case in enumerate(cases)]
    save(out/'schedule.json', schedule)
    save(out/'environment.json', {'recorded_at_utc': now(), 'python': sys.version,
         'platform': platform.platform(), 'docker_version': docker('version').stdout,
         'image_id': image['Id'], 'image_repo_digests': image.get('RepoDigests'),
         'image_architecture': image['Architecture'], 'image_os': image['Os'],
         'image_created': image['Created'], 'phase': args.phase, 'operator': args.operator,
         'protocol_sha256': digest(out/'protocol.json'),
         'execution': 'automated collection of real Docker API observations; no generated measurements'})
    journal = out/'journal.jsonl'
    print('RUN DIRECTORY:', out, flush=True)
    rows, raw_requests = [], []
    for entry in schedule:
        trial_dir = raw/entry['trial']
        trial_dir.mkdir()
        name = 'rmt-a3-' + uuid.uuid4().hex[:12]
        started = now()
        row = dict(entry, valid=False, error='')
        save(trial_dir/'ground_truth.json', entry)
        try:
            mode = 'healthy' if entry['scenario'] == 'stopped_container' else entry['scenario']
            cid = docker('run', '-d', '--name', name, '--label', 'rmt-a3-lab=true',
                         '--read-only', '--cap-drop=ALL', '--security-opt=no-new-privileges',
                         '--pids-limit=64', '--memory=128m', '--cpus=1',
                         '-p', '127.0.0.1::8080', '-e', 'FAULT_MODE='+mode, image['Id']).stdout.strip()
            info = json.loads(docker('inspect', name).stdout)[0]
            port = info['NetworkSettings']['Ports']['8080/tcp'][0]['HostPort']
            url = f'http://127.0.0.1:{port}'
            readiness = []
            for _ in range(40):
                readiness.append(request(url+'/ready', 0.5))
                if readiness[-1]['status'] == 200:
                    break
                time.sleep(0.1)
            save(trial_dir/'readiness.json', readiness)
            if readiness[-1]['status'] != 200:
                raise RuntimeError('Readiness failed; not an intended fault detection')
            save(trial_dir/'injection.json', {'container_id': cid, 'mode': mode,
                 'stop_requested': entry['scenario'] == 'stopped_container', 'at_utc': now()})
            if entry['scenario'] == 'stopped_container':
                docker('stop', '--time', '1', name)
            http = []
            for _ in range(protocol['requests_per_trial']):
                http.append(request(url+'/api/items', protocol['request_timeout_seconds']))
                time.sleep(protocol['request_interval_seconds'])
            save(trial_dir/'http.json', http)
            raw_requests.extend(dict(trial=entry['trial'], request=index, **obs)
                                for index, obs in enumerate(http, 1))
            write_csv(raw/'requests.csv', raw_requests)
            time.sleep(protocol['log_settle_seconds'])
            info = json.loads(docker('inspect', name).stdout)[0]
            state = {key: info['State'][key] for key in ('Running', 'OOMKilled', 'ExitCode', 'Status')}
            state['RestartCount'] = info['RestartCount']
            save(trial_dir/'container.json', state)
            if entry['scenario'] == 'stopped_container' and state['Running']:
                raise RuntimeError('Stop injection was not applied')
            logs_result = docker('logs', name)
            logs = logs_result.stdout + logs_result.stderr
            (trial_dir/'application.jsonl').write_text(logs, encoding='utf-8')
            detectors(http, state, logs)  # Validate readability, do not report scores during collection.
            row['valid'] = True
        except Exception as exc:
            row['error'] = str(exc)
            save(trial_dir/'failure.json', {'at_utc': now(), 'error': str(exc)})
        finally:
            # Remove only this run's own uniquely named, labelled container.
            cleanup = docker('rm', '-f', name, check=False)
            save(trial_dir/'cleanup.json', {'code': cleanup.returncode,
                 'stdout': cleanup.stdout, 'stderr': cleanup.stderr})
        rows.append(row)
        write_csv(out/'trials.csv', rows)
        with journal.open('a', encoding='utf-8') as f:
            f.write(json.dumps(dict(row, started_utc=started, ended_utc=now(), operator=args.operator))+'\n')
        print(f"{entry['trial']} {entry['scenario']}: {'collected' if row['valid'] else 'INVALID: '+row['error']}", flush=True)
    save(out/'completion.json', {'completed_at_utc': now(), 'planned': len(schedule),
         'valid': sum(r['valid'] for r in rows), 'invalid': sum(not r['valid'] for r in rows)})
    files = [f for f in out.rglob('*') if f.is_file()]
    save(out/'manifest.sha256.json', {str(f.relative_to(out)).replace('\\','/'): digest(f) for f in files})
    print('Collection finished. Analyze separately: python lab.py analyze "'+str(out)+'"')
    if any(not r['valid'] for r in rows):
        raise RuntimeError('Some trials failed. Preserve and inspect invalid trials; do not silently rerun/replace them.')


def metrics(rows, condition):
    tp = sum(r['truth'] == 1 and r['prediction'] == 1 for r in rows)
    tn = sum(r['truth'] == 0 and r['prediction'] == 0 for r in rows)
    fp = sum(r['truth'] == 0 and r['prediction'] == 1 for r in rows)
    fn = sum(r['truth'] == 1 and r['prediction'] == 0 for r in rows)
    def div(a, b):
        return round(a/b, 6) if b else ''
    return {'condition': condition, 'n': len(rows), 'TP': tp, 'TN': tn, 'FP': fp, 'FN': fn,
            'accuracy': div(tp+tn, len(rows)), 'precision': div(tp, tp+fp),
            'recall': div(tp, tp+fn), 'specificity': div(tn, tn+fp),
            'FPR': div(fp, fp+tn), 'F1': div(2*tp, 2*tp+fp+fn),
            'balanced_accuracy': round(((tp/(tp+fn))+(tn/(tn+fp)))/2, 6) if tp+fn and tn+fp else ''}


def analyze(path):
    out = Path(path).resolve()
    manifest = read(out/'manifest.sha256.json')
    for filename, expected in manifest.items():
        if digest(out/filename) != expected:
            raise ValueError('Evidence changed since collection: '+filename)
    recorded = read(out/'protocol.json')
    if recorded['version'] != '1.0':
        raise ValueError('This analyzer supports protocol 1.0 only')
    # A modified analyzer must not silently reinterpret an older collection.
    if digest(ROOT/'lab.py') != digest(out/'source/lab.py'):
        raise ValueError('Analyzer changed. Use the saved source/lab.py for reproducible analysis.')
    processed = out/'processed'
    processed.mkdir(exist_ok=True)
    with (out/'trials.csv').open(encoding='utf-8', newline='') as f:
        trials = list(csv.DictReader(f))
    decisions, observations = [], []
    for row in trials:
        if row['valid'] != 'True':
            continue
        trial = out/'raw'/row['trial']
        http, state = read(trial/'http.json'), read(trial/'container.json')
        logs = (trial/'application.jsonl').read_text(encoding='utf-8')
        signals = detectors(http, state, logs)
        for index, obs in enumerate(http, 1):
            observations.append(dict(trial=row['trial'], scenario=row['scenario'], request=index, **obs))
        for combo in CONDITIONS:
            decisions.append({'trial': row['trial'], 'round': row['round'], 'scenario': row['scenario'],
                              'truth': int(row['truth']), 'condition': '+'.join(combo),
                              'prediction': int(any(signals[s] for s in combo)),
                              **{s+'_positive': int(v) for s, v in signals.items()}})
    if not decisions:
        raise ValueError('No valid trials; cannot report metrics')
    write_csv(processed/'http_measurements.csv', observations)
    write_csv(processed/'decisions.csv', decisions)
    summary = [metrics([r for r in decisions if r['condition'] == '+'.join(c)], '+'.join(c)) for c in CONDITIONS]
    reference = [dict(r, prediction=0) for r in decisions if r['condition'] == 'http']
    summary.append(metrics(reference, 'always_healthy_reference'))
    write_csv(processed/'metrics.csv', summary)
    by_case = []
    by_round = []
    for combo in CONDITIONS:
        name = '+'.join(combo)
        for scenario in recorded['scenarios']:
            selected = [r for r in decisions if r['condition'] == name and r['scenario'] == scenario]
            if selected:
                by_case.append(dict(scenario=scenario, **metrics(selected, name)))
        for round_no in sorted({r['round'] for r in decisions}, key=int):
            selected = [r for r in decisions if r['condition'] == name and r['round'] == round_no]
            if selected:
                by_round.append(dict(round=round_no, **metrics(selected, name)))
    write_csv(processed/'metrics_by_scenario.csv', by_case)
    write_csv(processed/'metrics_by_round.csv', by_round)
    completion = read(out/'completion.json')
    text = ['# Measured results', '', 'Phase: '+read(out/'environment.json')['phase'],
            f"Planned: {completion['planned']}; valid: {completion['valid']}; invalid: {completion['invalid']}.",
            '', '| Condition | n | TP | TN | FP | FN | Accuracy | Precision | Recall | F1 |',
            '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for r in summary:
        text.append('| '+' | '.join(str(r[k]) if r[k] != '' else 'N/A' for k in
                    ('condition','n','TP','TN','FP','FN','accuracy','precision','recall','F1'))+' |')
    text += ['', 'Undefined ratios are blank in CSV and N/A here, never replaced with zero.',
             'This is a synthetic benchmark of fixed rules, not evidence about human skill or unseen production faults.',
             'Repeated requests within a trial are not independent samples. Pilot data must not be presented as a separate main study.',
             'Cleaning: no imputation, no deduplication; invalid trials excluded explicitly; all raw files retained.',
             'See metrics_by_scenario.csv and metrics_by_round.csv for all strata and repetitions.']
    (processed/'RESULTS.md').write_text('\n'.join(text)+'\n', encoding='utf-8')
    chart = ['<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="510" viewBox="0 0 1000 510">',
             '<rect width="1000" height="510" fill="#f7f9fc"/>',
             '<g font-family="Arial" fill="#17233b"><text x="35" y="40" font-size="24">Measured detection accuracy</text>',
             '<text x="35" y="67" font-size="14">Synthetic API | '+str(completion['valid'])+' valid trials | '+read(out/'environment.json')['phase']+'</text>']
    for i, r in enumerate(summary):
        y = 105 + i*44
        chart += [f'<text x="35" y="{y+19}" font-size="15">{r["condition"]}</text>',
                  f'<rect x="300" y="{y}" width="550" height="27" fill="#e0e6f0"/>',
                  f'<rect x="300" y="{y}" width="{550*r["accuracy"]}" height="27" fill="#2764b8"/>',
                  f'<text x="870" y="{y+19}" font-size="16">{r["accuracy"]:.1%}</text>']
    chart += ['<text x="35" y="490" font-size="13">Source: metrics.csv. Horizontal scale: 0 to 100%. No inferential claims.</text></g></svg>']
    (processed/'accuracy.svg').write_text('\n'.join(chart), encoding='utf-8')
    print('\n'.join(text))
    print('Saved:', processed)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('doctor')
    sub.add_parser('build')
    collect_parser = sub.add_parser('collect')
    collect_parser.add_argument('--phase', choices=('pilot','main'), required=True)
    collect_parser.add_argument('--rounds', type=int, default=2)
    collect_parser.add_argument('--operator', required=True, help='Actual operator or automation identity')
    analysis_parser = sub.add_parser('analyze')
    analysis_parser.add_argument('path')
    args = parser.parse_args()
    try:
        if args.command == 'doctor': doctor()
        elif args.command == 'build': build()
        elif args.command == 'collect': collect(args)
        else: analyze(args.path)
    except (RuntimeError, ValueError, OSError, subprocess.TimeoutExpired) as exc:
        print('ERROR:', exc, file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())

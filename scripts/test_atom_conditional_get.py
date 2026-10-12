#!/usr/bin/env python3
"""Read-only probe of Atom HTTP validators."""
import json, time, urllib.error, urllib.request
from datetime import datetime, timezone
from pathlib import Path

BASE = 'https://api.syosetu.com'
HEADERS = ('ETag', 'Last-Modified', 'Cache-Control', 'Age', 'Date', 'Content-Length')

def get(url, extra=None):
    headers = {'User-Agent': 'tomotayomu-atom-validator-probe/1.0', 'Accept': 'application/atom+xml, application/xml, */*'}
    headers.update(extra or {})
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=15) as res:
            body = res.read()
            return {'status': res.status, 'seconds': round(time.perf_counter()-started, 3), 'bytes': len(body), 'headers': {h: res.headers[h] for h in HEADERS if res.headers.get(h)}, 'error': None}
    except urllib.error.HTTPError as e:
        body = e.read()
        return {'status': e.code, 'seconds': round(time.perf_counter()-started, 3), 'bytes': len(body), 'headers': {h: e.headers[h] for h in HEADERS if e.headers.get(h)}, 'error': None if e.code == 304 else f'HTTP {e.code}'}
    except Exception as e:
        return {'status': None, 'seconds': round(time.perf_counter()-started, 3), 'bytes': 0, 'headers': {}, 'error': f'{type(e).__name__}: {e}'}

def main():
    authors = json.loads(Path('data/author-list.json').read_text(encoding='utf-8'))['authors']
    chosen = [next((a for a in authors if a.get('author_type') == t), None) for t in ('normal', 'r18')]
    targets = []
    for a in filter(None, chosen):
        aid, typ = str(a['author_id']), a['author_type']
        targets += [{'label': f'{typ} author activity', 'url': f'{BASE}/writerblog/{aid}.Atom'}, {'label': f'{typ} author novels', 'url': f'{BASE}/writernovel/{aid}.Atom'}]
    targets += [{'label': 'whole-site normal activity', 'url': f'{BASE}/blogatom.Atom'}, {'label': 'whole-site R18 activity', 'url': f'{BASE}/xblogatom.Atom'}]
    results = []
    for t in targets:
        first = get(t['url'])
        validators = {}
        if first['headers'].get('ETag'): validators['If-None-Match'] = first['headers']['ETag']
        if first['headers'].get('Last-Modified'): validators['If-Modified-Since'] = first['headers']['Last-Modified']
        item = {'label': t['label'], 'url': t['url'], 'initial': first, 'conditional': None}
        time.sleep(0.6)
        if first['status'] == 200 and validators:
            item['conditional'] = {'sent_headers': list(validators), 'result': get(t['url'], validators)}
        elif first['status'] == 200:
            item['conditional'] = {'sent_headers': [], 'result': None, 'note': 'No ETag or Last-Modified header; conditional GET not testable.'}
        results.append(item)
        time.sleep(0.6)
    report = {'generated_at': datetime.now(timezone.utc).isoformat(), 'purpose': 'Read-only Atom validator probe', 'target_count': len(targets), 'results': results}
    Path('atom-conditional-get-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2))

if __name__ == '__main__': main()

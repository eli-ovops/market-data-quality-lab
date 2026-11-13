import concurrent.futures
import csv
import datetime
import gzip
import hashlib
import json
import math
from pathlib import Path
import threading
import time
import urllib.error
import urllib.request

BASE = Path(__file__).resolve().parent.parent
DATA = BASE / 'data'
RECEIPT = BASE / 'data-receipt.json'
PROGRESS = BASE / 'data-progress.json'
CAP = 512 * 1024 * 1024
lock = threading.Lock()
stop = threading.Event()
downloaded = 0
rows = []
started = time.monotonic()
cpu_started = time.process_time()

def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

def progress():
    PROGRESS.write_text(json.dumps({'updated_at_utc': utc(), 'compressed_bytes_received': downloaded,
        'stop_requested': stop.is_set(), 'completed_file_records': rows}, indent=2), encoding='utf-8')

def acquire(month):
    global downloaded
    if stop.is_set():
        return {'date': f'2026-{month:02d}-01', 'status': 'NOT_STARTED_AFTER_OTHER_FAILURE', 'requests': 0}
    date = f'2026-{month:02d}-01'
    url = f'https://datasets.tardis.dev/v1/bitstamp/book_snapshot_25/2026/{month:02d}/01/BTCUSD.csv.gz'
    path = DATA / f'bitstamp_BTCUSD_book_snapshot_25_{date}.csv.gz'
    part = path.with_suffix(path.suffix + '.part')
    row = {'date': date, 'split': 'train' if month <= 3 else 'validation' if month == 4 else 'test',
        'url': url, 'method': 'GET', 'requests': 0, 'started_at_utc': utc(), 'path': str(path),
        'body_bytes_received': 0, 'status': 'STARTED', 'redirect_followed': False}
    begin = time.monotonic()
    try:
        if path.exists() or part.exists():
            raise RuntimeError('Existing output: stop without overwrite or redownload')
        digest = hashlib.sha256()
        opener = urllib.request.build_opener(NoRedirect())
        row['requests'] = 1
        response = opener.open(urllib.request.Request(url, method='GET'), timeout=30)
        with response, part.open('xb') as target:
            row['http_status'] = response.code
            row['headers'] = {k: response.headers.get(k) for k in ('Content-Type', 'Content-Length', 'Last-Modified', 'ETag')}
            if response.code != 200:
                raise RuntimeError(f'Unexpected HTTP {response.code}; no retry')
            advertised = response.headers.get('Content-Length')
            if advertised and int(advertised) > CAP:
                raise RuntimeError('Advertised file exceeds aggregate byte cap')
            while True:
                if stop.is_set():
                    raise RuntimeError('Cancelled because another data file failed')
                chunk = response.read(65536)
                if not chunk:
                    break
                with lock:
                    downloaded += len(chunk)
                    row['body_bytes_received'] += len(chunk)
                    if downloaded > CAP:
                        raise RuntimeError('Aggregate compressed download cap exceeded')
                target.write(chunk)
                digest.update(chunk)
            if advertised and row['body_bytes_received'] != int(advertised):
                raise RuntimeError('Content-Length mismatch')
        part.rename(path)
        row['compressed_sha256'] = digest.hexdigest()
        row['download_finished_at_utc'] = utc()
        row['download_wall_seconds'] = time.monotonic() - begin
        day_start = int(datetime.datetime(2026, month, 1, tzinfo=datetime.timezone.utc).timestamp()) * 1000000
        day_end = day_start + 86400 * 1000000
        keys = [f'{side}[{level}].{field}' for level in range(10) for side in ('asks', 'bids') for field in ('price', 'amount')]
        count = 0
        previous_local = previous_exchange = previous_state = None
        identical = equal_local = max_gap = 0
        qc_begin = time.monotonic()
        with gzip.open(path, 'rt', encoding='utf-8', newline='') as source:
            reader = csv.DictReader(source)
            required = ['exchange', 'symbol', 'timestamp', 'local_timestamp'] + keys
            missing = [k for k in required if k not in reader.fieldnames]
            if missing:
                raise RuntimeError(f'Missing required columns: {missing}')
            for record in reader:
                if count % 10000 == 0 and stop.is_set():
                    raise RuntimeError('QC cancelled because another file failed')
                if record['exchange'] != 'bitstamp' or record['symbol'] != 'BTCUSD':
                    raise RuntimeError('Identity mismatch')
                local = int(record['local_timestamp'])
                exchange = int(record['timestamp'])
                if not day_start <= local < day_end or not day_start <= exchange < day_end:
                    raise RuntimeError('Timestamp outside expected UTC date')
                if previous_local is not None and (local < previous_local or exchange < previous_exchange):
                    raise RuntimeError('Backwards timestamp')
                state = tuple(record[k] for k in keys)
                values = [float(value) for value in state]
                if any(not math.isfinite(v) or v <= 0 for v in values):
                    raise RuntimeError('Invalid top10 price/amount')
                asks = values[0::4]
                bids = values[2::4]
                if any(asks[i] >= asks[i + 1] or bids[i] <= bids[i + 1] for i in range(9)) or bids[0] >= asks[0]:
                    raise RuntimeError('Unsorted or crossed/locked top10')
                if count == 0:
                    row['first_local_timestamp'] = local
                    row['first_exchange_timestamp'] = exchange
                else:
                    max_gap = max(max_gap, local - previous_local)
                    equal_local += local == previous_local
                    identical += state == previous_state
                previous_local, previous_exchange, previous_state = local, exchange, state
                count += 1
        if not count:
            raise RuntimeError('Empty CSV')
        row.update(status='PASS_FILE_STRUCTURE_IDENTITY_CRC_NOT_FEED_COMPLETENESS', rows=count,
            last_local_timestamp=previous_local, last_exchange_timestamp=previous_exchange,
            maximum_local_gap_microseconds=max_gap, equal_consecutive_local_timestamps=equal_local,
            identical_consecutive_top10_raw_text=identical, gzip_eof_crc_verified=True,
            qc_wall_seconds=time.monotonic() - qc_begin,
            exclusions_applied=0, qc_invalid_counts=0)
    except Exception as exc:
        stop.set()
        row.update(status='STOP_DATA_UNIT', error=type(exc).__name__ + ': ' + str(exc))
        if isinstance(exc, urllib.error.HTTPError):
            row['http_status'] = exc.code
            row['headers'] = {k: exc.headers.get(k) for k in ('Content-Type', 'Content-Length', 'Last-Modified', 'ETag')}
            exc.close()
    row['finished_at_utc'] = utc()
    row['wall_seconds'] = time.monotonic() - begin
    with lock:
        rows.append(row)
        progress()
    return row

if __name__ == '__main__':
    if RECEIPT.exists() or PROGRESS.exists():
        raise RuntimeError('Existing data receipt/progress; do not rerun')
    began_utc = utc()
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        records = list(pool.map(acquire, range(1, 10)))
    receipt = {'status': 'PASS_ALL_NINE_FILE_QC' if all(r['status'].startswith('PASS_') for r in records) else 'STOP_DATA_UNIT',
        'started_at_utc': began_utc, 'finished_at_utc': utc(), 'wall_seconds': time.monotonic() - started,
        'process_cpu_seconds': time.process_time() - cpu_started, 'max_download_concurrency': 3,
        'compressed_bytes_received': downloaded, 'compressed_byte_cap': CAP,
        'files': records, 'scope': {'models': 0, 'predictions': 0, 'labels': 0, 'returns': 0, 'trades': 0, 'payments': 0,
            'decompressed_csv_files_saved': 0},
        'limitations': ['CRC/SHA and structure do not prove upstream feed completeness',
            'Timestamps belong to exchange and supplier, not user machine latency',
            'Interval/repetition counts do not filter or reject an otherwise valid day']}
    with RECEIPT.open('x', encoding='utf-8') as target:
        json.dump(receipt, target, indent=2)
        target.write('\n')
    print(json.dumps({'receipt': str(RECEIPT), 'status': receipt['status'], 'wall_seconds': receipt['wall_seconds'],
        'process_cpu_seconds': receipt['process_cpu_seconds'], 'compressed_bytes_received': downloaded,
        'files': [{k: r.get(k) for k in ('date', 'status', 'rows', 'error')} for r in records]}))

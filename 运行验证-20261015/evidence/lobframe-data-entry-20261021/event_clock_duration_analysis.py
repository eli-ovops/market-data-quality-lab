# 执行后保存的原始分析代码副本；未在执行前封存代码哈希。以下为当次 python3 标准输入代码原样内容。
import array,csv,gzip,hashlib,io,json,math,os,resource,time
from pathlib import Path
start=time.monotonic(); cpu=time.process_time()
resource.setrlimit(resource.RLIMIT_CPU,(60,60))
base=Path('/Volumes/EXTERNAL/亚力克斯 /运行验证-20261015/evidence/lobframe-data-entry-20261021')
src=base/'bitstamp_book_snapshot_25_2026-10-01_BTCUSD.csv.gz'
out=base/'event-clock-duration-receipt.json'
if out.exists(): raise RuntimeError('OUTPUT_ALREADY_EXISTS_STOP')
expected='22d347447c1b12f422ea2ed16ba84725eb1b8c716a22aa6b53f775f7e2fd2fe0'
blob=src.read_bytes()
sha=hashlib.sha256(blob).hexdigest()
if sha!=expected: raise RuntimeError('SHA_MISMATCH_STOP')
a=array.array('q'); b=array.array('q'); prev=None; prev_t=None
keys=[f'{side}[{level}].{field}' for level in range(10) for side in ('asks','bids') for field in ('price','amount')]
def budget():
    wall=time.monotonic()-start; used=time.process_time()-cpu
    rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    rss_bytes=rss if os.uname().sysname=='Darwin' else rss*1024
    if wall>60 or used>60 or rss_bytes>256*1024*1024: raise RuntimeError('RESOURCE_LIMIT_STOP')
    return wall,used,rss_bytes
with gzip.GzipFile(fileobj=io.BytesIO(blob),mode='rb') as gz:
    reader=csv.DictReader(io.TextIOWrapper(gz,encoding='utf-8',newline=''))
    if any(k not in reader.fieldnames for k in keys+['local_timestamp']): raise RuntimeError('MISSING_COLUMNS_STOP')
    for row in reader:
        t=int(row['local_timestamp'])
        if prev_t is not None and t<prev_t: raise RuntimeError('TIMESTAMP_BACKWARDS_STOP')
        state=tuple(row[k] for k in keys)
        a.append(t)
        if state!=prev: b.append(t)
        prev=state; prev_t=t
        if len(a)%10000==0: budget()
del blob
result={}
for name,seq in [('A_raw_top25_update_rows',a),('B_consecutive_top10_raw_text_deduplicated',b)]:
    entries={}
    for h in (1,10,50,100):
        d=sorted(seq[i+h]-seq[i] for i in range(len(seq)-h))
        n=len(d)
        entries[str(h)]={'h_rows':h,'n':n,'end_boundary_rows_without_future':h,'min_seconds':d[0]/1e6,'max_seconds':d[-1]/1e6,'nearest_rank_percentiles_seconds':{f'p{p}':d[math.ceil(p*n/100)-1]/1e6 for p in (10,50,90,99)},'fraction_le_seconds':{str(s):sum(v<=s*1000000 for v in d)/n for s in (1,5,10,60)}}
        del d
        budget()
    result[name]={'rows':len(seq),'horizons':entries}
wall,used,rss=budget()
receipt={'status':'PASS_DESCRIPTIVE_EVENT_CLOCK_DURATIONS_ONLY','source':str(src),'source_sha256':sha,'source_compressed_bytes':src.stat().st_size,'analysis_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'method':{'timestamp':'local_timestamp only, integer UTC epoch microseconds','clock_A':'Every original top25 update CSV row','clock_B':'Drop only consecutive rows whose top10 40 raw field texts equal the previous original row; text equality, not numeric equivalence; no global deduplication or timestamp merging','duration':'(timestamp[i+h]-timestamp[i])/1000000','percentile':'nearest-rank: sorted durations at ceil(p*n), 1-based','filters':'No anomaly or long-gap deletion; h end-boundary rows cannot form each horizon','field_names':keys},'checks':{'compressed_sha256_matches':True,'gzip_read_to_eof_crc_verified':True,'local_timestamp_backwards':0,'clock_B_removed_consecutive_rows':len(a)-len(b)},'statistics':result,'resources':{'threads':1,'cpu_seconds':used,'wall_seconds':wall,'peak_rss_bytes':rss,'limits':{'cpu_seconds':60,'wall_seconds':60,'rss_bytes':268435456,'new_disk_bytes':2097152}},'scope':{'models':0,'predictions':0,'labels':0,'returns_or_profit_calculations':0,'trades':0,'network_requests':0,'downloads':0,'new_dependencies':0,'fees':0,'raw_order_book_data_sent_externally':False},'limitations':['Collector event durations are historical observed intervals, not user machine latency or exchange complete-event timing','Clock B uses raw textual equality rather than numeric equivalence','Full-file CRC/hash integrity cannot prove source feed completeness','No predictive or economic efficacy is assessed']}
payload=json.dumps(receipt,ensure_ascii=False,indent=2)+'\n'
if len(payload.encode())>2097152: raise RuntimeError('DISK_LIMIT_STOP')
budget()
with out.open('x',encoding='utf-8') as f: f.write(payload)
print(json.dumps({'receipt':str(out),'bytes':len(payload.encode()),'checks':receipt['checks'],'statistics':result,'resources':receipt['resources']},ensure_ascii=False))

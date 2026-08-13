#!/usr/bin/env python3
"""stdlib-only copyparty phase-2 repeatable HTTP POC.
Requires a running server and synthetic test volume. No destructive cleanup is done.
"""
import argparse, base64, hashlib, json, os, pathlib, subprocess, sys, time, urllib.parse, urllib.request

def req(url, user, pw, method='GET', data=None, headers=None, timeout=60):
    r=urllib.request.Request(url, data=data, method=method, headers=headers or {})
    tok=base64.b64encode(f'{user}:{pw}'.encode()).decode(); r.add_header('Authorization','Basic '+tok)
    try:
        with urllib.request.urlopen(r, timeout=timeout) as x: return x.status, x.read(), dict(x.headers)
    except urllib.error.HTTPError as e: return e.code, e.read(), dict(e.headers)

def main():
 p=argparse.ArgumentParser(); p.add_argument('--base-url', required=True); p.add_argument('--user', required=True); p.add_argument('--password', required=True); p.add_argument('--data-dir', required=True); p.add_argument('--results-dir', default='results'); p.add_argument('--size-mib', type=int, default=4); a=p.parse_args()
 out=pathlib.Path(a.results_dir); out.mkdir(parents=True,exist_ok=True); data=pathlib.Path(a.data_dir); data.mkdir(parents=True,exist_ok=True)
 def save(n,b): (out/n).write_bytes(b)
 base=a.base_url.rstrip('/'); src=data/'phase2-source.bin'; upsrc=data/'phase2-up2k-source.bin'; n=a.size_mib*1024*1024+123
 for path, salt in ((src,b'A'), (upsrc,b'B')):
  with path.open('wb') as f:
   for i in range(0,n,65536): f.write(hashlib.sha512(salt+f'{i}'.encode()).digest() * (65536//64))
  with path.open('r+b') as f:f.truncate(n)
 # PUT upload, GET/range, then move
 st,body,_=req(base+'/public/phase2-source.bin',a.user,a.password,'PUT',src.read_bytes(),{'Content-Type':'application/octet-stream'}); save('put.body',body)
 assert st in (200,201), f'PUT {st}'
 st,body,_=req(base+'/public/phase2-source.bin',a.user,a.password,'GET'); assert st==200 and hashlib.sha256(body).digest()==hashlib.sha256(src.read_bytes()).digest(), f'GET {st}'
 st,body,_=req(base+'/public/phase2-source.bin',a.user,a.password,'GET',headers={'Range':'bytes=0-99'}); assert st==206 and len(body)==100, f'RANGE {st} {len(body)}'
 # up2k handshake / interrupted chunk resume
 cs=1024*1024; hs=[]
 with upsrc.open('rb') as f:
  while b:=f.read(cs): hs.append(base64.urlsafe_b64encode(hashlib.sha512(b).digest()[:33]).decode().rstrip('='))
 meta={'name':'phase2-up2k.bin','size':n,'lmod':int(src.stat().st_mtime),'prel':'','hash':hs,'vtop':'public','ptop':str((data/'public').resolve()),'host':'127.0.0.1','user':a.user,'addr':'127.0.0.1','vcfg':{'A':True}}
 st,b,_=req(base+'/public/',a.user,a.password,'POST',json.dumps(meta).encode(),{'Content-Type':'application/json'}); h=json.loads(b); assert st==200 and h['hash'], f'HANDSHAKE {st}'
 w=h['wark']; first=hs[0]; chunks=[]
 with upsrc.open('rb') as f:
  for i in range(len(hs)): chunks.append(f.read(cs))
 st,b,_=req(base+'/public/',a.user,a.password,'POST',chunks[0],{'Content-Type':'application/octet-stream','X-Up2k-Hash':first,'X-Up2k-Wark':w}); assert st==200 and b.strip()==b'thank', f'CHUNK0 {st} {b!r}'
 st,b,_=req(base+'/public/',a.user,a.password,'POST',json.dumps(meta).encode(),{'Content-Type':'application/json'}); missing=json.loads(b)['hash']; assert len(missing)==len(hs)-1, f'RESUME missing={len(missing)}'
 for i,hv in enumerate(missing,1):
  st,b,_=req(base+'/public/',a.user,a.password,'POST',chunks[i],{'Content-Type':'application/octet-stream','X-Up2k-Hash':hv,'X-Up2k-Wark':w}); assert st==200 and b.strip()==b'thank', f'CHUNK{i} {st}'
 st,b,_=req(base+'/public/',a.user,a.password,'POST',json.dumps(meta).encode(),{'Content-Type':'application/json'}); assert st==200 and json.loads(b)['hash']==[], f'FINAL {st} {b!r}'
 got=data/'public'/'phase2-up2k.bin'; assert hashlib.sha256(got.read_bytes()).digest()==hashlib.sha256(upsrc.read_bytes()).digest(), 'HASH MISMATCH'
 dst='/public/phase2-renamed.bin'; st,body,_=req(base+'/public/phase2-source.bin?move='+urllib.parse.quote(dst,safe='/'),a.user,a.password,'POST',b'',{}); assert st==201, f'MOVE {st}'
 print('PASS PUT=201 MOVE=201 RANGE=206 UP2K_RESUME=PASS FINAL_SHA256=PASS')
 print('source_sha256',hashlib.sha256(upsrc.read_bytes()).hexdigest()); print('uploaded_sha256',hashlib.sha256(got.read_bytes()).hexdigest())
if __name__=='__main__': main()

#!/usr/bin/env python3
import base64, json, sys, urllib.request, urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

URL = 'https://u.neodon.net/c/0az43w0x13fe5c76a'
UA = 'v2rayN/7.24.6'
RAW = '/home/m26/AI/neodon-sub/raw.json'
SUB = '/home/m26/AI/neodon-sub/sub.txt'


def log(msg):
    print(msg, file=sys.stderr, flush=True)


def fetch_raw():
    req = urllib.request.Request(URL, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = r.read()
    json.loads(data)
    return data


def build_link(c):
    remarks = c.get('remarks') or ''
    for o in c.get('outbounds', []):
        if o.get('protocol') != 'vless':
            continue
        v = o['settings']['vnext'][0]
        u = v['users'][0]
        ss = o.get('streamSettings', {})
        q = {'encryption': 'none'}
        sec = ss.get('security') or 'none'
        if sec == 'reality':
            rs = ss.get('realitySettings', {})
            q['security'] = 'reality'
            for k, pk in (('pbk', 'publicKey'), ('sid', 'shortId')):
                if rs.get(pk):
                    q[k] = rs[pk]
            q['fp'] = rs.get('fingerprint') or 'chrome'
            if rs.get('serverName'):
                q['sni'] = rs['serverName']
        elif sec == 'tls':
            ts = ss.get('tlsSettings', {})
            q['security'] = 'tls'
            if ts.get('serverName'):
                q['sni'] = ts['serverName']
            if ts.get('fingerprint'):
                q['fp'] = ts['fingerprint']
            if ts.get('alpn'):
                q['alpn'] = ','.join(ts['alpn'])
        else:
            q['security'] = 'none'
        net = ss.get('network') or 'tcp'
        q['type'] = net
        if net == 'ws':
            ws = ss.get('wsSettings', {})
            if ws.get('path'):
                q['path'] = ws['path']
            host = (ws.get('headers') or {}).get('Host') or ws.get('host')
            if host:
                q['host'] = host
        elif net == 'grpc':
            gs = ss.get('grpcSettings', {})
            if gs.get('serviceName'):
                q['serviceName'] = gs['serviceName']
        if u.get('flow'):
            q['flow'] = u['flow']
        frag = urllib.parse.quote(remarks or v['address'])
        query = '&'.join('%s=%s' % (k, urllib.parse.quote(str(vv))) for k, vv in q.items())
        return 'vless://%s@%s:%s?%s#%s' % (u['id'], v['address'], v['port'], query, frag)
    return None


def make_sub(raw):
    data = json.loads(raw)
    links, skipped = [], []
    for i, c in enumerate(data):
        link = build_link(c)
        if link:
            links.append(link)
        else:
            skipped.append(i)
            log('config %d skipped: no vless outbound' % i)
    return links, skipped


def current_raw():
    try:
        return fetch_raw()
    except Exception as e:
        log('fetch failed: %s' % e)
        try:
            with open(RAW, 'rb') as f:
                return f.read()
        except Exception:
            return None


def refresh():
    raw = current_raw()
    if raw is None:
        return None, None, None
    links, skipped = make_sub(raw)
    with open(RAW, 'wb') as f:
        f.write(raw)
    with open(SUB, 'w') as f:
        f.write(base64.b64encode('\n'.join(links).encode()).decode())
    log('fetched %d links, skipped %d' % (len(links), len(skipped)))
    return raw, links, skipped


class H(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.split('?')[0] != '/sub':
            self.send_error(404)
            return
        raw, links, skipped = refresh()
        if raw is None:
            self.send_response(502)
            self.end_headers()
            self.wfile.write(b'502: upstream unreachable and no cache')
            return
        body = base64.b64encode('\n'.join(links).encode())
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        log('http: ' + fmt % args)


if __name__ == '__main__':
    refresh()
    log('serving on 127.0.0.1:18080/sub')
    ThreadingHTTPServer(('127.0.0.1', 18080), H).serve_forever()

# SPDX-License-Identifier: MIT
"""Serve the public library catalog on loopback; no arbitrary file serving."""

import argparse
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML = """<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Minescript Library</title><style>
body{font:16px system-ui;background:#111820;color:#e8eff6;max-width:1200px;margin:32px auto;padding:0 24px}
h1{font-size:36px;margin-bottom:8px}p{color:#b5c4d4;line-height:1.5}
input{width:100%;box-sizing:border-box;padding:15px;background:#1b2836;border:1px solid #4b647c;color:white;border-radius:8px;font:inherit}
label{display:block;margin:16px 0}table{border-collapse:collapse;width:100%;margin-top:20px}th,td{text-align:left;padding:14px 8px;border-bottom:1px solid #304153;vertical-align:top}th{color:#9fcce0}td small{display:block;margin-top:6px;color:#a3b5c9}a{color:#87d6b2}code{color:#aad9fe}#count{font-weight:600;color:#8ed7b7}
</style><h1>Minescript Library</h1><p id="count">Loading catalog…</p>
<p>Search names and descriptions. Community entries may require setup or porting.
In-game trials remain necessary. Use <code>\\library info ID</code> and
<code>\\library run ID [ARGS]</code> in Minecraft.</p>
<label for="search">Find scripts</label><input id="search" placeholder="stripmine, farming, camera, inventory…">
<label><input id="support" type="checkbox" style="width:auto"> Show support modules</label>
<table><thead><tr><th>Catalog ID</th><th>What it does</th><th>Runtime / status</th></tr></thead><tbody id="rows"></tbody></table>
<script>
let entries=[];const q=document.getElementById('search'),support=document.getElementById('support');
function render(){const term=q.value.toLowerCase(),rows=document.getElementById('rows');rows.replaceChildren();let count=0;
for(const e of entries){if(!support.checked&&e.kind==='support')continue;if(!(e.id+' '+e.description).toLowerCase().includes(term))continue;count++;
const tr=document.createElement('tr'),a=document.createElement('td'),b=document.createElement('td'),c=document.createElement('td');
a.textContent=e.id;const source=document.createElement('a');source.textContent='Source';if(e.source.startsWith('https://github.com/'))source.href=e.source;source.target='_blank';source.rel='noopener noreferrer';const small=document.createElement('small');small.append(source);a.append(small);
b.textContent=e.description;c.textContent=e.runtime+' · '+e.kind;const status=document.createElement('small');status.textContent=e.status;c.append(status);tr.append(a,b,c);rows.append(tr);}
document.getElementById('count').textContent=count+' entries shown';}
fetch('/catalog.json').then(r=>r.json()).then(data=>{entries=data.entries;render();});q.addEventListener('input',render);support.addEventListener('change',render);
</script></html>"""


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            payload, mime = HTML.encode("utf-8"), "text/html; charset=utf-8"
        elif self.path == "/catalog.json":
            payload, mime = (ROOT / "catalog.json").read_bytes(), "application/json"
        else:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(payload)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    with HTTPServer(("127.0.0.1", args.port), Handler) as server:
        print(f"Catalog: http://127.0.0.1:{args.port}", flush=True)
        server.serve_forever()


if __name__ == "__main__":
    main()

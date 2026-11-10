"""Monta demo_web.html (um arquivo so, funciona com duplo clique, sem internet)."""
import base64
import subprocess
import sys

glb, out = sys.argv[1], sys.argv[2]
js = subprocess.run(
    ["npx", "esbuild", "web/main.js", "--bundle", "--minify", "--format=iife"],
    capture_output=True, text=True, check=True).stdout
b64 = base64.b64encode(open(glb, "rb").read()).decode()
html = f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Rostos do boneco</title>
<style>
:root{{--bg:#16181c;--panel:#22252b;--txt:#e9e6df;--mut:#9a978f;--acc:#f0b84a}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--bg);color:var(--txt);font:15px/1.4 system-ui,sans-serif;display:flex;flex-direction:column;height:100vh}}
#view{{flex:1;min-height:300px}} canvas{{display:block;width:100%;height:100%}}
.bar{{background:var(--panel);padding:12px 16px;display:flex;flex-direction:column;gap:8px}}
.row{{display:flex;flex-wrap:wrap;gap:6px;align-items:center}} .lab{{color:var(--mut);width:90px;font-size:13px}}
button{{background:#2e323a;color:var(--txt);border:1px solid #3b4049;border-radius:6px;padding:7px 11px;font:inherit;cursor:pointer}}
button:hover{{border-color:var(--acc)}} button.on{{background:var(--acc);color:#1a1a1a;border-color:var(--acc)}}
label{{color:var(--mut);font-size:13px}}
</style></head><body>
<div id="view"></div>
<div class="bar">
 <div class="row"><span class="lab">Rosto</span><span id="tipos" class="row"></span></div>
 <div class="row"><span class="lab">Animação</span><span id="anims" class="row"></span></div>
 <div class="row"><span class="lab"></span><label><input type="checkbox" id="auto" checked> piscar sozinho</label>
 <label style="margin-left:12px">arraste para girar, roda do mouse para zoom</label></div>
</div>
<script>window.MODEL_GLB_B64="{b64}";</script>
<script>{js}</script>
</body></html>"""
open(out, "w").write(html)
print("ok", len(html))

#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║       ADVANCED INTEGRAL SOLVER  — Web UI Edition             ║
║  Copy-paste this file, run it, open http://localhost:5050    ║
╚══════════════════════════════════════════════════════════════╝

Requirements:
    pip install sympy scipy numpy

Run:
    python integral_solver_ui.py
Then open:
    http://localhost:5050
"""

# ── stdlib ────────────────────────────────────────────────────
import json
import sys
import warnings
import webbrowser
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

warnings.filterwarnings("ignore")

# ── SymPy ─────────────────────────────────────────────────────
try:
    import sympy as sp
    from sympy import (
        symbols, integrate, oo, pi, E, sqrt, sin, cos, tan,
        exp, log, asin, acos, atan, sinh, cosh, tanh,
        gamma, factorial, Abs, simplify, latex, sympify
    )
    from sympy.parsing.sympy_parser import (
        parse_expr, standard_transformations,
        implicit_multiplication_application, convert_xor,
    )
except ImportError:
    print("❌  pip install sympy"); sys.exit(1)

try:
    import scipy.integrate as sci
    import numpy as np
    SCIPY = True
except ImportError:
    SCIPY = False

# ── Maths core ────────────────────────────────────────────────
x, y = symbols("x y", real=True)
TRANS = standard_transformations + (
    implicit_multiplication_application, convert_xor,
)
SAFE = {
    "x": x, "y": y,
    "sin": sin, "cos": cos, "tan": tan,
    "asin": asin, "acos": acos, "atan": atan,
    "sinh": sinh, "cosh": cosh, "tanh": tanh,
    "exp": exp, "log": log, "ln": log,
    "sqrt": sqrt, "Abs": Abs, "abs": Abs,
    "pi": pi, "e": E, "oo": oo, "inf": oo,
    "gamma": gamma, "factorial": factorial,
    "sec":  lambda v: 1 / cos(v),
    "csc":  lambda v: 1 / sin(v),
    "cot":  lambda v: cos(v) / sin(v),
}

def p(s):
    return parse_expr(str(s).replace("^", "**"),
                      local_dict=SAFE, transformations=TRANS)

def lim(s):
    s = str(s).strip()
    if s in ("oo", "inf", "+oo"):  return oo
    if s in ("-oo", "-inf"):        return -oo
    return p(s)

def num(expr):
    try:    return f"{float(expr.evalf()):.10g}"
    except: return "—"

def solve(kind, f_str, a=None, b=None, ya=None, yb=None):
    try:
        if kind == "indefinite":
            f   = p(f_str)
            res = integrate(f, x)
            return {"ok": True,
                    "result":  str(res) + " + C",
                    "latex":   latex(res) + r" + C",
                    "numeric": "—"}

        elif kind == "definite":
            f   = p(f_str)
            a_s = lim(a); b_s = lim(b)
            res = simplify(integrate(f, (x, a_s, b_s)))
            nv  = num(res)
            # scipy fallback
            if nv == "—" and SCIPY:
                try:
                    fl = sp.lambdify(x, f, modules=["numpy"])
                    v, _ = sci.quad(
                        lambda t: float(np.real(complex(fl(t)))),
                        float(a_s.evalf()) if a_s != -oo else -1e9,
                        float(b_s.evalf()) if b_s !=  oo else  1e9,
                        limit=300)
                    nv = f"{v:.10g} (numerical)"
                except Exception:
                    pass
            return {"ok": True,
                    "result":  str(res),
                    "latex":   latex(res),
                    "numeric": nv}

        elif kind == "double":
            f    = p(f_str)
            inner = integrate(f, (y, lim(ya), lim(yb)))
            res   = simplify(integrate(inner, (x, lim(a), lim(b))))
            return {"ok": True,
                    "result":  str(res),
                    "latex":   latex(res),
                    "numeric": num(res)}

        else:
            return {"ok": False, "error": "Unknown type"}

    except Exception as e:
        return {"ok": False, "error": str(e)}


# ── HTML page ─────────────────────────────────────────────────
HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>∫ Integral Solver</title>
<link rel="preconnect" href="https://fonts.googleapis.com"/>
<link href="https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=JetBrains+Mono:wght@300;400;600&display=swap" rel="stylesheet"/>
<script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js" id="MathJax-script" async></script>
<style>
:root{
  --bg:#07090f;
  --surface:#0e1118;
  --border:#1e2433;
  --accent:#6ee7f7;
  --accent2:#f7c66e;
  --red:#f76e6e;
  --text:#dde3f0;
  --muted:#5a6580;
  --radius:14px;
}
*{box-sizing:border-box;margin:0;padding:0}
body{
  background:var(--bg);
  color:var(--text);
  font-family:'JetBrains Mono',monospace;
  min-height:100vh;
  display:flex;
  flex-direction:column;
  align-items:center;
  padding:40px 16px 80px;
  background-image:
    radial-gradient(ellipse 60% 40% at 20% 10%,#0d2a3a55,transparent),
    radial-gradient(ellipse 50% 35% at 80% 85%,#1a1a3a55,transparent);
}

/* ── Header ── */
header{text-align:center;margin-bottom:48px}
header h1{
  font-family:'DM Serif Display',serif;
  font-size:clamp(2rem,5vw,3.2rem);
  letter-spacing:-.02em;
  background:linear-gradient(135deg,var(--accent),var(--accent2));
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;
  background-clip:text;
}
header p{color:var(--muted);font-size:.82rem;margin-top:8px;letter-spacing:.08em;text-transform:uppercase}

/* ── Card ── */
.card{
  background:var(--surface);
  border:1px solid var(--border);
  border-radius:var(--radius);
  padding:32px;
  width:100%;max-width:740px;
  box-shadow:0 4px 40px #000a;
  margin-bottom:28px;
  animation:fadeUp .45s ease both;
}
@keyframes fadeUp{from{opacity:0;transform:translateY(18px)}to{opacity:1;transform:none}}

/* ── Tabs ── */
.tabs{display:flex;gap:4px;margin-bottom:28px;background:#0b0d15;border-radius:10px;padding:4px}
.tab{
  flex:1;text-align:center;padding:9px 4px;border-radius:8px;
  cursor:pointer;font-size:.78rem;letter-spacing:.06em;text-transform:uppercase;
  color:var(--muted);transition:all .2s;border:none;background:transparent;font-family:inherit;
}
.tab.active{background:var(--border);color:var(--accent);box-shadow:0 0 0 1px var(--accent)33}
.tab:hover:not(.active){color:var(--text)}

/* ── Form elements ── */
.panel{display:none}.panel.active{display:block}
label{display:block;font-size:.72rem;color:var(--muted);letter-spacing:.08em;text-transform:uppercase;margin-bottom:6px;margin-top:18px}
label:first-child{margin-top:0}
input[type=text]{
  width:100%;background:#0b0d15;border:1px solid var(--border);
  border-radius:8px;padding:11px 14px;color:var(--text);
  font-family:'JetBrains Mono',monospace;font-size:.92rem;
  outline:none;transition:border-color .2s;
}
input[type=text]:focus{border-color:var(--accent)88}
input[type=text]::placeholder{color:var(--muted)}

.row{display:grid;grid-template-columns:1fr 1fr;gap:12px}

/* ── Button ── */
button.solve{
  margin-top:24px;width:100%;padding:13px;
  background:linear-gradient(135deg,#1a3d4a,#1a1a3a);
  border:1px solid var(--accent)55;border-radius:10px;
  color:var(--accent);font-family:'JetBrains Mono',monospace;
  font-size:.88rem;letter-spacing:.1em;text-transform:uppercase;
  cursor:pointer;transition:all .2s;
}
button.solve:hover{background:linear-gradient(135deg,#1f4d5e,#222248);border-color:var(--accent);box-shadow:0 0 20px var(--accent)22}
button.solve:active{transform:scale(.98)}

/* ── Result ── */
.result-card{
  background:var(--surface);border:1px solid var(--border);
  border-radius:var(--radius);padding:28px 32px;
  width:100%;max-width:740px;
  display:none;animation:fadeUp .35s ease both;
}
.result-card.show{display:block}
.result-card h3{
  font-family:'DM Serif Display',serif;font-size:1.05rem;
  color:var(--accent2);margin-bottom:20px;font-weight:400;
  letter-spacing:.02em;
}
.result-row{margin-bottom:14px}
.result-label{font-size:.68rem;color:var(--muted);text-transform:uppercase;letter-spacing:.1em;margin-bottom:4px}
.result-value{
  background:#0b0d15;border:1px solid var(--border);border-radius:8px;
  padding:12px 16px;font-size:.88rem;word-break:break-all;line-height:1.6;
}
.result-value.latex-box{font-size:1.05rem;text-align:center;padding:18px}
.error-box{
  background:#1a0b0b;border:1px solid var(--red)55;border-radius:8px;
  padding:14px 16px;color:var(--red);font-size:.85rem;
}

/* ── Examples ── */
.examples{margin-top:14px}
.examples-label{font-size:.68rem;color:var(--muted);text-transform:uppercase;letter-spacing:.1em;margin-bottom:8px}
.chips{display:flex;flex-wrap:wrap;gap:6px}
.chip{
  background:#0b0d15;border:1px solid var(--border);border-radius:20px;
  padding:5px 12px;font-size:.75rem;color:var(--muted);cursor:pointer;
  transition:all .18s;font-family:inherit;
}
.chip:hover{border-color:var(--accent)66;color:var(--accent)}

/* ── Spinner ── */
.spinner{display:none;width:20px;height:20px;border:2px solid var(--border);
  border-top-color:var(--accent);border-radius:50%;animation:spin .7s linear infinite;
  margin:0 auto}
@keyframes spin{to{transform:rotate(360deg)}}

/* ── Footer ── */
footer{margin-top:48px;color:var(--muted);font-size:.72rem;text-align:center;letter-spacing:.06em}
</style>
</head>
<body>

<header>
  <h1>∫ Integral Solver</h1>
  <p>Symbolic · Definite · Improper · Double</p>
</header>

<div class="card">
  <!-- Tabs -->
  <div class="tabs">
    <button class="tab active" onclick="switchTab('indefinite',this)">Indefinite</button>
    <button class="tab" onclick="switchTab('definite',this)">Definite</button>
    <button class="tab" onclick="switchTab('improper',this)">Improper</button>
    <button class="tab" onclick="switchTab('double',this)">Double</button>
  </div>

  <!-- Indefinite -->
  <div id="panel-indefinite" class="panel active">
    <label>f(x)  — the integrand</label>
    <input id="indef-f" type="text" placeholder="e.g.  x**2 * sin(x)"/>
    <div class="examples">
      <div class="examples-label">Quick examples</div>
      <div class="chips">
        <button class="chip" onclick="chip('indef-f','x**3 + 2*x - 5')">x³+2x−5</button>
        <button class="chip" onclick="chip('indef-f','sin(x)*cos(x)')">sin·cos</button>
        <button class="chip" onclick="chip('indef-f','x*exp(-x)')">x·e⁻ˣ</button>
        <button class="chip" onclick="chip('indef-f','1/(x**2+1)')">1/(x²+1)</button>
        <button class="chip" onclick="chip('indef-f','log(x)')">ln(x)</button>
        <button class="chip" onclick="chip('indef-f','sqrt(1-x**2)')">√(1−x²)</button>
      </div>
    </div>
    <button class="solve" onclick="solveIt('indefinite')">Solve  ∫ f(x) dx</button>
  </div>

  <!-- Definite -->
  <div id="panel-definite" class="panel">
    <label>f(x)  — the integrand</label>
    <input id="def-f" type="text" placeholder="e.g.  sin(x)"/>
    <div class="row">
      <div><label>Lower limit  a</label><input id="def-a" type="text" placeholder="0"/></div>
      <div><label>Upper limit  b</label><input id="def-b" type="text" placeholder="pi"/></div>
    </div>
    <div class="examples">
      <div class="examples-label">Quick examples</div>
      <div class="chips">
        <button class="chip" onclick="chipDef('sin(x)','0','pi')">∫₀^π sin x</button>
        <button class="chip" onclick="chipDef('x**2','0','3')">∫₀³ x²</button>
        <button class="chip" onclick="chipDef('exp(-x**2)','0','1')">∫₀¹ e⁻ˣ²</button>
        <button class="chip" onclick="chipDef('1/x','1','10')">∫₁¹⁰ 1/x</button>
      </div>
    </div>
    <button class="solve" onclick="solveIt('definite')">Solve  ∫_a^b f(x) dx</button>
  </div>

  <!-- Improper -->
  <div id="panel-improper" class="panel">
    <label>f(x)  — the integrand</label>
    <input id="imp-f" type="text" placeholder="e.g.  exp(-x**2)"/>
    <div class="row">
      <div><label>Lower limit  (use oo for ∞)</label><input id="imp-a" type="text" placeholder="0"/></div>
      <div><label>Upper limit  (use oo for ∞)</label><input id="imp-b" type="text" placeholder="oo"/></div>
    </div>
    <div class="examples">
      <div class="examples-label">Quick examples</div>
      <div class="chips">
        <button class="chip" onclick="chipImp('exp(-x**2)','0','oo')">∫₀^∞ e⁻ˣ²</button>
        <button class="chip" onclick="chipImp('1/x**2','1','oo')">∫₁^∞ 1/x²</button>
        <button class="chip" onclick="chipImp('x**4*exp(-x)','0','oo')">Gamma(5)</button>
        <button class="chip" onclick="chipImp('sin(x)/x','0','oo')">∫₀^∞ sinc</button>
      </div>
    </div>
    <button class="solve" onclick="solveIt('improper')">Solve  ∫_a^∞ f(x) dx</button>
  </div>

  <!-- Double -->
  <div id="panel-double" class="panel">
    <label>f(x, y)  — the integrand</label>
    <input id="dbl-f" type="text" placeholder="e.g.  x*y"/>
    <div class="row">
      <div><label>x  lower</label><input id="dbl-xa" type="text" placeholder="0"/></div>
      <div><label>x  upper</label><input id="dbl-xb" type="text" placeholder="1"/></div>
    </div>
    <div class="row">
      <div><label>y  lower</label><input id="dbl-ya" type="text" placeholder="0"/></div>
      <div><label>y  upper</label><input id="dbl-yb" type="text" placeholder="1"/></div>
    </div>
    <div class="examples">
      <div class="examples-label">Quick examples</div>
      <div class="chips">
        <button class="chip" onclick="chipDbl('x*y','0','1','0','1')">∬ xy</button>
        <button class="chip" onclick="chipDbl('x**2+y**2','0','1','0','1')">∬ x²+y²</button>
        <button class="chip" onclick="chipDbl('x+y','0','1','0','x')">∬ x+y (tri)</button>
      </div>
    </div>
    <button class="solve" onclick="solveIt('double')">Solve  ∬ f(x,y) dy dx</button>
  </div>
</div>

<!-- Spinner -->
<div class="spinner" id="spinner"></div>

<!-- Result -->
<div class="result-card" id="result-card">
  <h3 id="result-title">Result</h3>
  <div id="result-body"></div>
</div>

<footer>powered by SymPy + SciPy &nbsp;·&nbsp; running locally on your machine</footer>

<script>
let currentTab = 'indefinite';

function switchTab(name, el){
  document.querySelectorAll('.panel').forEach(p=>p.classList.remove('active'));
  document.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));
  document.getElementById('panel-'+name).classList.add('active');
  el.classList.add('active');
  currentTab = name;
  document.getElementById('result-card').classList.remove('show');
}

function chip(id, val){ document.getElementById(id).value = val; }
function chipDef(f,a,b){ chip('def-f',f);chip('def-a',a);chip('def-b',b); }
function chipImp(f,a,b){ chip('imp-f',f);chip('imp-a',a);chip('imp-b',b); }
function chipDbl(f,xa,xb,ya,yb){ chip('dbl-f',f);chip('dbl-xa',xa);chip('dbl-xb',xb);chip('dbl-ya',ya);chip('dbl-yb',yb); }

async function solveIt(kind){
  const spinner = document.getElementById('spinner');
  const card    = document.getElementById('result-card');
  card.classList.remove('show');
  spinner.style.display = 'block';

  let params = {kind};
  if(kind==='indefinite') params.f = document.getElementById('indef-f').value;
  if(kind==='definite')  { params.f=document.getElementById('def-f').value; params.a=document.getElementById('def-a').value; params.b=document.getElementById('def-b').value; }
  if(kind==='improper')  { params.f=document.getElementById('imp-f').value; params.a=document.getElementById('imp-a').value; params.b=document.getElementById('imp-b').value; }
  if(kind==='double')    { params.f=document.getElementById('dbl-f').value; params.a=document.getElementById('dbl-xa').value; params.b=document.getElementById('dbl-xb').value; params.ya=document.getElementById('dbl-ya').value; params.yb=document.getElementById('dbl-yb').value; }

  try{
    const qs  = new URLSearchParams(params).toString();
    const res = await fetch('/solve?'+qs);
    const data= await res.json();
    spinner.style.display='none';
    showResult(kind, params, data);
  }catch(e){
    spinner.style.display='none';
    showResult(kind, params, {ok:false, error: e.message});
  }
}

function showResult(kind, params, data){
  const card  = document.getElementById('result-card');
  const title = document.getElementById('result-title');
  const body  = document.getElementById('result-body');

  const labels = {indefinite:'Indefinite Integral', definite:'Definite Integral', improper:'Improper Integral', double:'Double Integral'};
  title.textContent = labels[kind] || 'Result';

  if(!data.ok){
    body.innerHTML = `<div class="error-box">⚠️  ${escHtml(data.error)}</div>`;
  } else {
    body.innerHTML = `
      <div class="result-row">
        <div class="result-label">Symbolic result</div>
        <div class="result-value">${escHtml(data.result)}</div>
      </div>
      <div class="result-row">
        <div class="result-label">LaTeX (rendered)</div>
        <div class="result-value latex-box" id="latex-render">\\(${escHtml(data.latex)}\\)</div>
      </div>
      ${data.numeric && data.numeric!=='—' ? `
      <div class="result-row">
        <div class="result-label">Numeric value</div>
        <div class="result-value">${escHtml(data.numeric)}</div>
      </div>` : ''}
    `;
    if(window.MathJax) MathJax.typesetPromise([document.getElementById('latex-render')]).catch(()=>{});
  }

  card.classList.add('show');
  card.scrollIntoView({behavior:'smooth',block:'nearest'});
}

function escHtml(s){ return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }

document.addEventListener('keydown', e=>{ if(e.key==='Enter') solveIt(currentTab); });
</script>
</body>
</html>
"""

# ── HTTP server ───────────────────────────────────────────────
class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_): pass   # silence access log

    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/solve":
            qs = parse_qs(parsed.query)
            g  = lambda k, d="": qs.get(k, [d])[0]
            kind = g("kind")
            data = solve(
                kind,
                g("f"),
                a=g("a") or None,
                b=g("b") or None,
                ya=g("ya") or None,
                yb=g("yb") or None,
            )
            body = json.dumps(data).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        else:
            body = HTML.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)


# ── Entry point ───────────────────────────────────────────────
PORT = 5050

def open_browser():
    import time; time.sleep(0.8)
    webbrowser.open(f"http://localhost:{PORT}")

if __name__ == "__main__":
    server = HTTPServer(("", PORT), Handler)
    print(f"\n  ∫  Integral Solver  →  http://localhost:{PORT}")
    print("  Press Ctrl+C to stop.\n")
    threading.Thread(target=open_browser, daemon=True).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Server stopped.")

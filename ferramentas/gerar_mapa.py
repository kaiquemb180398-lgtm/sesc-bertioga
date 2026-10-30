"""Gera o mapa vetorial do Sesc Bertioga (SVG georreferenciado) a partir do OpenStreetMap.

Uso: python3 -I gen.py map.json saida_dir
Saídas: map.svg (conteúdo do <svg id="vmap">), data.json (lugares, casas, grafo de caminhos, georreferência).
"""
import json, math, sys, random, os

SRC, OUT = sys.argv[1], sys.argv[2]
els = json.load(open(SRC))['elements']
N = {e['id']: e for e in els if e['type'] == 'node'}
W = {e['id']: e for e in els if e['type'] == 'way'}

# ---------- georreferência (mesma fórmula do app: local()) ----------
REF = (-23.8265, -46.1112)
LAT_MIN, LAT_MAX = -23.8336, -23.8210
LNG_MIN, LNG_MAX = -46.1153, -46.1075
K = 2.0  # px por metro
COS = math.cos(math.radians(REF[0]))
def EN(lat, lng): return ((lng - REF[1]) * 111320 * COS, (lat - REF[0]) * 110574)
E0, N1 = EN(LAT_MAX, LNG_MIN)
E1, N0 = EN(LAT_MIN, LNG_MAX)
MW, MH = round((E1 - E0) * K), round((N1 - N0) * K)
def P(lat, lng):
    e, n = EN(lat, lng)
    return ((e - E0) * K, (N1 - n) * K)
def fmt(v): return ('%.1f' % v).rstrip('0').rstrip('.')
def pts(nodes): return [P(N[n]['lat'], N[n]['lon']) for n in nodes if n in N]
def d_path(ps, close=False):
    if not ps: return ''
    s = 'M' + ' '.join(fmt(x) + ',' + fmt(y) for x, y in ps)
    return s + ('Z' if close else '')
def centroid(ps):
    a = cx = cy = 0
    for i in range(len(ps) - 1):
        x0, y0 = ps[i]; x1, y1 = ps[i + 1]
        c = x0 * y1 - x1 * y0; a += c; cx += (x0 + x1) * c; cy += (y0 + y1) * c
    if abs(a) < 1e-6: return (sum(p[0] for p in ps) / len(ps), sum(p[1] for p in ps) / len(ps))
    return (cx / (3 * a), cy / (3 * a))
def inview(ps, m=60): return any(-m < x < MW + m and -m < y < MH + m for x, y in ps)

SESC = pts(W[176167858]['nodes'])
def inside(pt, poly=SESC):
    x, y = pt; c = False
    for i in range(len(poly) - 1):
        x0, y0 = poly[i]; x1, y1 = poly[i + 1]
        if (y0 > y) != (y1 > y) and x < (x1 - x0) * (y - y0) / (y1 - y0) + x0: c = not c
    return c

# ---------- coleta por camada ----------
L = {k: [] for k in ('outland', 'grass', 'forest', 'garden', 'wet', 'water', 'pool', 'pitch', 'park',
                     'parking', 'road_out', 'road', 'service', 'foot', 'track', 'drain', 'bld', 'house',
                     'hedge', 'wall', 'golf', 'beachedge')}
houses = []          # Casas e Conjuntos (para "Meu quarto")
labels = []          # rótulos de prédios
streets = []         # nomes de ruas internas
for w in W.values():
    t = w.get('tags', {})
    ps = pts(w['nodes'])
    if len(ps) < 2 or not inview(ps): continue
    closed = w['nodes'][0] == w['nodes'][-1]
    hw = t.get('highway'); nm = t.get('name', '')
    if t.get('building'):
        c = centroid(ps)
        red = t.get('building') == 'house' or nm.startswith('Conjunto') or nm.startswith('Casa') or t.get('roof:shape', '').startswith('gabled') or t.get('building') == 'chapel'
        (L['house'] if red else L['bld']).append((ps, w['id']))
        if nm.startswith('Casa ') and nm[5:].isdigit(): houses.append({'id': 'casa' + nm[5:], 'n': nm, 'x': c[0], 'y': c[1], 'k': 'casa', 'num': int(nm[5:])})
        elif nm.startswith('Conjunto '): houses.append({'id': 'conj' + nm[9:], 'n': nm, 'x': c[0], 'y': c[1], 'k': 'conj', 'num': int(nm[9:])})
        if nm.startswith('Conjunto '): labels.append((c, nm.upper(), 'lc'))
        continue
    if hw:
        if hw in ('secondary', 'secondary_link', 'residential', 'tertiary') and not inside(centroid(ps) if closed else ps[len(ps) // 2]):
            L['road_out'].append(ps); continue
        if hw in ('footway', 'path', 'steps', 'pedestrian', 'cycleway', 'track'):
            (L['track'] if t.get('surface') in ('unpaved', 'dirt', 'ground', 'sand') or hw == 'path' else L['foot']).append(ps)
        elif hw == 'rest_area':
            L['park'].append(ps); continue
        else:
            L['service' if hw == 'service' else 'road'].append(ps)
            if nm.startswith('Rua ') and hw == 'service': streets.append((ps, nm))
        continue
    lu = t.get('landuse'); nat = t.get('natural'); le = t.get('leisure'); am = t.get('amenity')
    if nat == 'water' or t.get('water'): L['water'].append(ps)
    elif le == 'swimming_pool': L['pool'].append(ps)
    elif le == 'water_park': L['pool' if w['id'] == 1117145685 else 'park'].append(ps)
    elif le == 'pitch': L['pitch'].append((ps, t.get('sport', '')))
    elif le == 'golf_course': L['golf'].append(ps)
    elif lu == 'forest' or nat in ('wood', 'scrub'): L['forest'].append(ps)
    elif nat == 'wetland': L['wet'].append(ps)
    elif lu in ('grass', 'plant_nursery') or le in ('park',): L['grass'].append(ps)
    elif le == 'garden': L['garden'].append(ps)
    elif am == 'parking': L['parking'].append(ps)
    elif t.get('waterway'): L['drain'].append(ps)
    elif t.get('barrier') == 'hedge': L['hedge'].append(ps)
    elif t.get('barrier') in ('wall', 'fence'): L['wall'].append(ps)
    elif nat == 'tree_row': L['hedge'].append(ps)

# litoral: areia entre a linha de vegetação (176080470 / cerca do Sesc) e a linha d'água (219013744)
coast = [p for p in pts(W[219013744]['nodes'])]
veg = [p for p in pts(W[176080470]['nodes']) if -400 < p[0] < MW + 400]
# mar = da linha d'água até o canto inferior direito do quadro
sea = coast + [(MW + 900, MH + 900), (-900, MH + 900)]
# areia = polígono entre linha de vegetação (ou cerca) e o mar, estendido
fence = [p for p in SESC if p[1] > P(-23.8293, -46.1083)[1] - 5]
land_edge = sorted([p for p in fence if p[0] > 0], key=lambda p: p[0])
sand = [(-900, MH * 0.80)] + sorted(veg + land_edge, key=lambda p: p[0]) + [(MW + 900, P(-23.8235, -46.0990)[1])] + [(MW + 900, MH + 900), (-900, MH + 900)]

# ---------- SVG ----------
rnd = random.Random(7)
o = []
A = o.append
A(f'<svg id="vmap" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {MW} {MH}" width="{MW}" height="{MH}" aria-label="Mapa do Sesc Bertioga">')
A('''<defs>
<linearGradient id="gSea" x1="0" y1="0" x2="0.4" y2="1"><stop offset="0" stop-color="#5FC4BE"/><stop offset=".35" stop-color="#2E9CA6"/><stop offset="1" stop-color="#17707E"/></linearGradient>
<linearGradient id="gSand" x1="0" y1="0" x2="0.3" y2="1"><stop offset="0" stop-color="#E9D3A8"/><stop offset="1" stop-color="#F3E3C2"/></linearGradient>
<radialGradient id="gLand" cx=".45" cy=".45" r=".75"><stop offset="0" stop-color="#5E8F4A"/><stop offset="1" stop-color="#4D7C3D"/></radialGradient>
<pattern id="pForest" width="26" height="26" patternUnits="userSpaceOnUse"><rect width="26" height="26" fill="#3F6B34"/><circle cx="6" cy="7" r="6" fill="#4C7D3E"/><circle cx="19" cy="17" r="7" fill="#467638"/><circle cx="18" cy="4" r="3.5" fill="#56894A"/><circle cx="5" cy="20" r="4" fill="#538646"/><circle cx="5" cy="5.5" r="2.2" fill="#6A9A57" opacity=".7"/><circle cx="17.5" cy="15" r="2.6" fill="#62944F" opacity=".7"/></pattern>
<pattern id="pWet" width="14" height="10" patternUnits="userSpaceOnUse"><rect width="14" height="10" fill="#5F8F5A"/><path d="M2 8v-4M4 8v-5M6 8v-3M10 8v-4M12 8v-5" stroke="#7FAF79" stroke-width="1"/></pattern>
<pattern id="pPark" width="10" height="10" patternUnits="userSpaceOnUse"><rect width="10" height="10" fill="#D9C7A2"/><circle cx="3" cy="3" r=".9" fill="#C9B48C"/><circle cx="8" cy="7" r=".9" fill="#C9B48C"/></pattern>
<pattern id="pTile" width="6" height="5" patternUnits="userSpaceOnUse"><rect width="6" height="5" fill="#C24A2F"/><path d="M0 4.5h6" stroke="#A23A23" stroke-width=".9"/><path d="M3 0v4.5" stroke="#D86A4B" stroke-width=".5" opacity=".6"/></pattern>
<filter id="fSoft" x="-10%" y="-10%" width="120%" height="120%"><feGaussianBlur stdDeviation="2.2"/></filter>
<symbol id="sPalm" viewBox="-12 -12 24 24" overflow="visible"><g stroke="#2F6B34" stroke-width="2.6" stroke-linecap="round"><path d="M0 0L-9 -3M0 0L9 -4M0 0L-6 7M0 0L7 6M0 0L1 -10M0 0L-8 3"/></g><g stroke="#4E9A4C" stroke-width="1.4" stroke-linecap="round"><path d="M0 0L-8 -3M0 0L8 -4M0 0L-5 6M0 0L6 5M0 0L1 -9"/></g><circle r="1.8" fill="#6B4A2B"/></symbol>
<symbol id="sTree" viewBox="-10 -10 20 20" overflow="visible"><circle cx="1.6" cy="2.2" r="8" fill="#1F3A1A" opacity=".35"/><circle r="8" fill="#3E7A36"/><circle cx="-2.4" cy="-2.6" r="4.5" fill="#5C9B4D"/><circle cx="-3" cy="-3.4" r="1.8" fill="#86BD6E" opacity=".8"/></symbol>
</defs>''')
A(f'<rect width="{MW}" height="{MH}" fill="#E6E0D2"/>')
# quadras urbanas em volta: só ruas (desenhadas depois); pequenas "quadras" em textura leve
A(f'<path d="{d_path(sea, True)}" fill="url(#gSea)"/>')
A(f'<path d="{d_path(sand, True)}" fill="url(#gSand)"/>')
A(f'<path d="{d_path(sea, True)}" fill="url(#gSea)"/>')
# espuma / ondas paralelas à linha d'água
for k, (off, op, w) in enumerate(((5, .9, 5), (16, .45, 2.5), (34, .3, 2), (60, .2, 1.6), (95, .14, 1.4))):
    wave = [(x, y + off) for x, y in coast]
    A(f'<path d="{d_path(wave)}" fill="none" stroke="#fff" stroke-opacity="{op}" stroke-width="{w}" stroke-linecap="round" stroke-dasharray="{"none" if k == 0 else f"{40 + 20 * k} {14 + 6 * k}"}"/>')
# terreno do Sesc
A(f'<path d="{d_path(SESC, True)}" fill="#24401F" opacity=".35" transform="translate(4 6)" filter="url(#fSoft)"/>')
A(f'<path d="{d_path(SESC, True)}" fill="url(#gLand)" stroke="#E9E2CF" stroke-width="3"/>')
def polys(key, attrs):
    for ps in L[key]:
        if len(ps) > 2: A(f'<path d="{d_path(ps, True)}" {attrs}/>')
for ps in L['grass']:
    if len(ps) > 2: A(f'<path d="{d_path(ps, True)}" fill="{"#6FA45A" if inside(centroid(ps)) else "#CBD5B4"}"/>')
polys('garden', 'fill="#79AE62" stroke="#8DC274" stroke-width="1"')
for ps in L['forest']:
    if len(ps) > 2: A(f'<path d="{d_path(ps, True)}" fill="{"url(#pForest)" if inside(centroid(ps)) else "#B9C8A6"}"/>')
polys('wet', 'fill="url(#pWet)"')
polys('golf', 'fill="#7DB664" stroke="#9CCB82" stroke-width="2"')
polys('park', 'fill="url(#pPark)" stroke="#C4AE85" stroke-width="1"')
polys('parking', 'fill="#BDB8AC" stroke="#A9A396" stroke-width="1"')
for ps, sport in L['pitch']:
    if len(ps) < 3: continue
    col = {'tennis': '#3E7EC2', 'chess': '#E9E2D0', 'boules': '#D8C08F', 'squash': '#5C8FC7'}.get(sport, '#5EA34B')
    A(f'<path d="{d_path(ps, True)}" fill="{col}" stroke="#fff" stroke-width="2" stroke-opacity=".9"/>')
    if sport in ('soccer', 'tennis', ''):
        # linha central pelo meio do retângulo (entre pontos médios dos lados menores)
        q = ps[:4] if len(ps) >= 5 else ps
        if len(q) == 4:
            s01 = math.dist(q[0], q[1]); s12 = math.dist(q[1], q[2])
            if s01 > s12: a = ((q[1][0] + q[2][0]) / 2, (q[1][1] + q[2][1]) / 2); b = ((q[3][0] + q[0][0]) / 2, (q[3][1] + q[0][1]) / 2); m1 = ((q[0][0] + q[1][0]) / 2, (q[0][1] + q[1][1]) / 2); m2 = ((q[2][0] + q[3][0]) / 2, (q[2][1] + q[3][1]) / 2)
            else: a = ((q[0][0] + q[1][0]) / 2, (q[0][1] + q[1][1]) / 2); b = ((q[2][0] + q[3][0]) / 2, (q[2][1] + q[3][1]) / 2); m1 = ((q[1][0] + q[2][0]) / 2, (q[1][1] + q[2][1]) / 2); m2 = ((q[3][0] + q[0][0]) / 2, (q[3][1] + q[0][1]) / 2)
            A(f'<path d="M{fmt(m1[0])},{fmt(m1[1])} L{fmt(m2[0])},{fmt(m2[1])}" stroke="#fff" stroke-width="1.6" opacity=".85"/>')
            if sport != 'tennis':
                c = ((m1[0] + m2[0]) / 2, (m1[1] + m2[1]) / 2)
                A(f'<circle cx="{fmt(c[0])}" cy="{fmt(c[1])}" r="{fmt(min(s01, s12) * .14)}" fill="none" stroke="#fff" stroke-width="1.6" opacity=".85"/>')
polys('water', 'fill="#3E95C9" stroke="#9FD3EA" stroke-width="2"')
polys('pool', 'fill="#33A9E0" stroke="#F3F0E8" stroke-width="3"')
for ps in L['drain']: A(f'<path d="{d_path(ps)}" fill="none" stroke="#4E8DB5" stroke-width="2" opacity=".7" stroke-linecap="round"/>')
for ps in L['hedge']: A(f'<path d="{d_path(ps)}" fill="none" stroke="#2F5A28" stroke-width="5" stroke-linecap="round" opacity=".8"/>')
# ruas de fora
for ps in L['road_out']: A(f'<path d="{d_path(ps)}" fill="none" stroke="#C9C2B1" stroke-width="15" stroke-linecap="round" stroke-linejoin="round"/>')
for ps in L['road_out']: A(f'<path d="{d_path(ps)}" fill="none" stroke="#FBF8F1" stroke-width="11" stroke-linecap="round" stroke-linejoin="round"/>')
# ruas internas (casca + miolo), trilhas e caminhos
def lines(lst, stroke, w, extra=''):
    if lst: A(f'<path d="{" ".join(d_path(ps) for ps in lst)}" fill="none" stroke="{stroke}" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round" {extra}/>')
lines(L['service'] + L['road'], '#8F8A7E', 14)
lines(L['service'] + L['road'], '#C9C4B8', 11)
lines(L['foot'], '#B9AE96', 6.5)
lines(L['foot'], '#EDE5D2', 4.5)
lines(L['track'], '#9C6A3C', 6)
lines(L['track'], '#D2965A', 4)
for ps in L['wall']: A(f'<path d="{d_path(ps)}" fill="none" stroke="#8C8577" stroke-width="2"/>')
# árvores isoladas do OSM e palmeiras na restinga
for e in els:
    if e['type'] == 'node' and e.get('tags', {}).get('natural') == 'tree':
        x, y = P(e['lat'], e['lon'])
        if 0 < x < MW and 0 < y < MH: A(f'<use href="#sTree" x="{fmt(x - 8)}" y="{fmt(y - 8)}" width="16" height="16"/>')
edge = sorted(land_edge, key=lambda p: p[0])
for i in range(len(edge) - 1):
    (x0, y0), (x1, y1) = edge[i], edge[i + 1]
    n = int(math.dist(edge[i], edge[i + 1]) // 34)
    for j in range(n):
        t = (j + .5) / max(n, 1); off = rnd.uniform(14, 60)
        dx, dy = x1 - x0, y1 - y0; ln = math.hypot(dx, dy) or 1
        px, py = x0 + dx * t - dy / ln * off * -1, y0 + dy * t + dx / ln * off * 1
        s = rnd.uniform(20, 28)
        A(f'<use href="#sPalm" x="{fmt(px - s / 2)}" y="{fmt(py - s / 2)}" width="{fmt(s)}" height="{fmt(s)}" transform="rotate({rnd.randint(0, 359)} {fmt(px)} {fmt(py)})"/>')
# prédios: sombra + telhado
def bshape(ps, fill, stroke, ridge=False):
    d = d_path(ps, True)
    A(f'<path d="{d}" fill="#1E2B1A" opacity=".32" transform="translate(3.5 5)"/>')
    A(f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="1.2" stroke-linejoin="round"/>')
    if ridge and len(ps) >= 5:
        q = ps[:4]
        s01 = math.dist(q[0], q[1]); s12 = math.dist(q[1], q[2])
        if s01 > s12: a = ((q[1][0] + q[2][0]) / 2, (q[1][1] + q[2][1]) / 2); b = ((q[3][0] + q[0][0]) / 2, (q[3][1] + q[0][1]) / 2)
        else: a = ((q[0][0] + q[1][0]) / 2, (q[0][1] + q[1][1]) / 2); b = ((q[2][0] + q[3][0]) / 2, (q[2][1] + q[3][1]) / 2)
        A(f'<path d="M{fmt(a[0])},{fmt(a[1])} L{fmt(b[0])},{fmt(b[1])}" stroke="#E98A63" stroke-width="1.6" opacity=".9"/>')
for ps, _ in L['bld']: bshape(ps, '#D9D6CE', '#9D998F')
for ps, _ in L['house']: bshape(ps, 'url(#pTile)', '#8E2F1C', True)
# nomes das ruas internas (ao longo do traçado)
defs = []
for i, (ps, nm) in enumerate(streets):
    ln = sum(math.dist(ps[k], ps[k + 1]) for k in range(len(ps) - 1))
    if ln < 120: continue
    seq = ps if ps[-1][0] >= ps[0][0] else ps[::-1]
    defs.append(f'<path id="st{i}" d="{d_path(seq)}"/>')
    A(f'<text class="m-st"><textPath href="#st{i}" startOffset="50%" text-anchor="middle">{nm}</textPath></text>')
o.insert(2, '<defs>' + ''.join(defs) + '</defs>')
# rótulos de conjuntos e números das casas
for (x, y), t, cls in labels: A(f'<text class="m-lc" x="{fmt(x)}" y="{fmt(y + 4)}">{t}</text>')
for h in houses:
    if h['k'] == 'casa': A(f'<text class="m-hn" x="{fmt(h["x"])}" y="{fmt(h["y"] + 3.5)}">{h["num"]}</text>')
# rótulos de contexto
def ctx(lat, lng, txt, cls='m-ctx', rot=0):
    x, y = P(lat, lng); A(f'<text class="{cls}" x="{fmt(x)}" y="{fmt(y)}"' + (f' transform="rotate({rot} {fmt(x)} {fmt(y)})"' if rot else '') + f'>{txt}</text>')
ctx(-23.8326, -46.1090, 'OCEANO ATLÂNTICO', 'm-ocean', -24)
ctx(-23.8318, -46.1102, 'Praia da Vista Linda', 'm-praia', -24)
ctx(-23.8226, -46.1086, 'Av. Anchieta', 'm-ctx', -14)
# banheiros e telefones (OSM)
for e in els:
    t = e.get('tags', {})
    if e['type'] != 'node' or t.get('amenity') not in ('toilets', 'telephone'): continue
    x, y = P(e['lat'], e['lon'])
    if not inside((x, y)): continue
    if t['amenity'] == 'toilets':
        A(f'<g transform="translate({fmt(x)} {fmt(y)})"><circle r="7.5" fill="#fff" stroke="#55606A" stroke-width="1.2"/><text class="m-wc" y="2.6">WC</text></g>')
    else:
        A(f'<g transform="translate({fmt(x)} {fmt(y)})"><circle r="7.5" fill="#fff" stroke="#55606A" stroke-width="1.2"/><path d="M-3.2-3.6c.7-.7 1.6-.5 2 .2l.8 1.4c.3.6.1 1.2-.4 1.6l-.6.4c.5 1.1 1.4 2 2.5 2.5l.4-.6c.4-.5 1-.7 1.6-.4l1.4.8c.7.4.9 1.3.2 2-1.4 1.4-3.6.9-6-1.5s-2.9-4.6-1.5-6z" fill="#55606A"/></g>')
ctx(-23.8263, -46.1141, 'SENAC', 'm-tag')
A('</svg>')
svg = ''.join(o)

# ---------- grafo de caminhos a pé (para rota) ----------
walk = set(('footway', 'path', 'steps', 'pedestrian', 'cycleway', 'track', 'service', 'residential', 'living_street', 'secondary', 'secondary_link', 'unclassified', 'tertiary'))
nid = {}; coords = []; edges = set()
for w in W.values():
    t = w.get('tags', {})
    if t.get('highway') not in walk: continue
    ns = [n for n in w['nodes'] if n in N]
    ps = [P(N[n]['lat'], N[n]['lon']) for n in ns]
    if not inview(ps, 200): continue
    for a, b in zip(ns, ns[1:]):
        for n in (a, b):
            if n not in nid: nid[n] = len(coords); coords.append(P(N[n]['lat'], N[n]['lon']))
        i, j = nid[a], nid[b]
        if i != j: edges.add((min(i, j), max(i, j)))
graph = {'n': [round(v, 1) for c in coords for v in c], 'e': [v for e in sorted(edges) for v in e]}

json.dump({'MW': MW, 'MH': MH, 'K': K, 'REF': REF, 'E0': E0, 'N1': N1, 'houses': sorted(houses, key=lambda h: (h['k'] != 'conj', h['num'])), 'graph': graph,
           'sesc': [[round(x, 1), round(y, 1)] for x, y in SESC]}, open(os.path.join(OUT, 'data.json'), 'w'))
open(os.path.join(OUT, 'map.svg'), 'w').write(svg)
print('MW', MW, 'MH', MH, 'svg', len(svg), 'houses', len(houses), 'graph nodes', len(coords), 'edges', len(edges))

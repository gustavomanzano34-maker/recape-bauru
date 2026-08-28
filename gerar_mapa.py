#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Regenera o arquivo geodata.js do site a partir dos KMZ.
Leia os traçados das vias (RECAPE PM BAURU.kmz) e o limite do
município (Bauru.kmz) e reescreve geodata.js, que o site usa
para desenhar as ruas no mapa.

Uso: dê 2 cliques em "Atualizar Mapa.command" (que chama este script).
Não precisa instalar nada — usa só o Python que já vem no Mac.
"""
import os, re, sys, json, zipfile, unicodedata
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
PARENT = os.path.dirname(HERE)

def achar(nomes):
    """Procura um arquivo por nome nesta pasta e na pasta de cima."""
    for base in (HERE, PARENT):
        for f in os.listdir(base):
            for alvo in nomes:
                if f.lower() == alvo.lower():
                    return os.path.join(base, f)
    # busca aproximada (contém)
    for base in (HERE, PARENT):
        for f in os.listdir(base):
            fl = f.lower()
            for alvo in nomes:
                key = alvo.lower().replace('.kmz','')
                if fl.endswith('.kmz') and key.split()[0] in fl:
                    return os.path.join(base, f)
    return None

def ler_kml(caminho_kmz):
    with zipfile.ZipFile(caminho_kmz) as z:
        nome = [n for n in z.namelist() if n.lower().endswith('.kml')][0]
        return z.read(nome).decode('utf-8', 'ignore')

def norm(s):
    s = '' if s is None else str(s)
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode()
    s = s.upper(); s = re.sub(r'[^A-Z0-9 ]', ' ', s); s = re.sub(r'\s+', ' ', s).strip()
    return s

def strip_prefix_num(name):
    # o KMZ numera as vias: "RUA 1 JORGE SCHNEYDER..." -> "JORGE SCHNEYDER..."
    m = re.match(r'^RUA\s+(\d+)\s+(.*)$', (name or '').strip(), re.I)
    return m.group(2).strip() if m else (name or '').strip()

TIPOS = r'(RUA|AVENIDA|AV|ALAMEDA|AL|TRAVESSA|TREVESSA|PRACA|ROD|RODOVIA|R)'
def streetname(name):
    n = norm(strip_prefix_num(name))
    n = re.sub(r'^LINHA\s*\d+', '', n).strip()
    n = re.sub(r'^'+TIPOS+r'\s+', '', n); n = re.sub(r'^'+TIPOS+r'\s+', '', n)
    n = re.sub(r'\bQT\b.*$', '', n)
    toks = n.split(); out = []
    for i, t in enumerate(toks):
        if re.fullmatch(r'\d+', t): break
        if t in ('A','E','AO','AS','OS') and i > 0 and any(re.search(r'\d', x) for x in toks[i:]): break
        out.append(t)
    return ' '.join(out).strip() or n

# Apelidos: quando o nome no KMZ difere do nome na planilha.
# chave = nome-da-rua da PLANILHA  ->  valor = nome-da-rua do KMZ
ALIAS = {
    'MARIO GRILO': 'MARIO GIRILO',
    'ENGENHEIRO JOAO BATISTA PACHECO': 'ENG JOAO B PACHECO FANTIN',
}

def main():
    kmz_vias = achar(['RECAPE PM BAURU.kmz'])
    kmz_mun  = achar(['Bauru.kmz'])
    if not kmz_vias:
        print('ERRO: não encontrei "RECAPE PM BAURU.kmz". Coloque-o na pasta do site ou na pasta BAURU.')
        return 1
    print('Vias :', kmz_vias)
    print('Limite:', kmz_mun or '(não encontrado — vou manter só as vias)')

    data = ler_kml(kmz_vias)
    pms = re.findall(r'<Placemark>(.*?)</Placemark>', data, re.S)
    vias = []
    for pm in pms:
        if '<LineString>' not in pm and '<coordinates>' not in pm: continue
        if '<Point>' in pm: continue
        m = re.search(r'<name>(.*?)</name>', pm, re.S)
        nm = (m.group(1).strip() if m else '').rstrip(':').strip()
        cr = re.search(r'<coordinates>(.*?)</coordinates>', pm, re.S)
        if not cr: continue
        pts = []
        for tok in cr.group(1).split():
            p = tok.split(',')
            if len(p) >= 2:
                pts.append([round(float(p[1]), 7), round(float(p[0]), 7)])
        if len(pts) < 2: continue
        vias.append({'name': nm, 'street': streetname(nm), 'coords': pts})

    by_street = defaultdict(list)
    for v in vias:
        by_street[v['street']].append(v)

    geo = {}
    for sk, segs in by_street.items():
        allp = [p for s in segs for p in s['coords']]
        lat = sum(p[0] for p in allp)/len(allp); lon = sum(p[1] for p in allp)/len(allp)
        geo[sk] = {'segments': [s['coords'] for s in segs],
                   'kml_names': [s['name'] for s in segs],
                   'center': [round(lat, 7), round(lon, 7)]}

    poly = []
    if kmz_mun:
        md = ler_kml(kmz_mun)
        mc = re.search(r'<coordinates>(.*?)</coordinates>', md, re.S)
        if mc:
            for tok in mc.group(1).split():
                p = tok.split(',')
                if len(p) >= 2:
                    poly.append([round(float(p[1]), 7), round(float(p[0]), 7)])

    allat = [p[0] for g in geo.values() for seg in g['segments'] for p in seg]
    allon = [p[1] for g in geo.values() for seg in g['segments'] for p in seg]
    bbox = [[min(allat), min(allon)], [max(allat), max(allon)]]

    out = {'municipio': poly, 'bbox': bbox, 'geo': geo, 'alias': ALIAS}
    dest = os.path.join(HERE, 'geodata.js')
    with open(dest, 'w', encoding='utf-8') as f:
        f.write('window.GEO=' + json.dumps(out, ensure_ascii=False, separators=(',', ':')) + ';')

    print('----------------------------------------------------')
    print('geodata.js atualizado com sucesso!')
    print('Ruas com traçado no mapa:', len(geo))
    print('Trechos (linhas) lidos  :', len(vias))
    print('Pontos do limite do município:', len(poly))
    print('----------------------------------------------------')
    print('Abra o site (ou clique em "↻ Atualizar") para ver.')
    return 0

if __name__ == '__main__':
    sys.exit(main())

#!/usr/bin/env python3
"""Génère les schémas techniques 2D pour la notice.

Sortie : un répertoire schemas/ avec un SVG par détail/élévation.
Toutes les cotes en mm. Style technique sobre.
"""
import os
import math

OUT = "schemas"
os.makedirs(OUT, exist_ok=True)


# ---------- petits helpers SVG ----------

def svg_open(w, h, title=""):
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
        f'font-family="-apple-system, Helvetica Neue, Arial, sans-serif">',
        f'<rect width="{w}" height="{h}" fill="#fdfaf3"/>',
        '<defs>',
        '<marker id="arr" markerWidth="8" markerHeight="8" refX="7" refY="4" '
        'orient="auto"><polygon points="0,0 8,4 0,8" fill="#333"/></marker>',
        '<marker id="arrR" markerWidth="8" markerHeight="8" refX="1" refY="4" '
        'orient="auto"><polygon points="8,0 0,4 8,8" fill="#333"/></marker>',
        '<pattern id="hatch" patternUnits="userSpaceOnUse" width="6" height="6" patternTransform="rotate(45)">'
        '<line x1="0" y1="0" x2="0" y2="6" stroke="#a87a4e" stroke-width="0.8"/></pattern>',
        '<pattern id="hatchL" patternUnits="userSpaceOnUse" width="5" height="5" patternTransform="rotate(45)">'
        '<line x1="0" y1="0" x2="0" y2="5" stroke="#c79e63" stroke-width="0.6"/></pattern>',
        '</defs>',
        f'<text x="{w/2}" y="22" text-anchor="middle" font-size="14" font-weight="bold" fill="#222">{title}</text>',
    ]


def svg_close():
    return ['</svg>']


def dim_h(x1, x2, y, label, color="#333", offset_text=-4):
    """Ligne de cote horizontale, à y, du x1 à x2."""
    out = []
    out.append(f'<line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}" stroke="{color}" stroke-width="0.6" marker-start="url(#arrR)" marker-end="url(#arr)"/>')
    out.append(f'<line x1="{x1}" y1="{y-4}" x2="{x1}" y2="{y+4}" stroke="{color}" stroke-width="0.6"/>')
    out.append(f'<line x1="{x2}" y1="{y-4}" x2="{x2}" y2="{y+4}" stroke="{color}" stroke-width="0.6"/>')
    out.append(f'<text x="{(x1+x2)/2}" y="{y+offset_text}" text-anchor="middle" font-size="9" fill="{color}">{label}</text>')
    return out


def dim_v(x, y1, y2, label, color="#333", offset_text=-4, side="left"):
    """Cote verticale."""
    out = []
    out.append(f'<line x1="{x}" y1="{y1}" x2="{x}" y2="{y2}" stroke="{color}" stroke-width="0.6" marker-start="url(#arrR)" marker-end="url(#arr)"/>')
    out.append(f'<line x1="{x-4}" y1="{y1}" x2="{x+4}" y2="{y1}" stroke="{color}" stroke-width="0.6"/>')
    out.append(f'<line x1="{x-4}" y1="{y2}" x2="{x+4}" y2="{y2}" stroke="{color}" stroke-width="0.6"/>')
    ty = (y1+y2)/2
    if side == "left":
        out.append(f'<text x="{x+offset_text}" y="{ty+3}" text-anchor="end" font-size="9" fill="{color}">{label}</text>')
    else:
        out.append(f'<text x="{x-offset_text}" y="{ty+3}" text-anchor="start" font-size="9" fill="{color}">{label}</text>')
    return out


def label(x, y, txt, anchor="start", size=9, color="#222", weight="normal"):
    return [f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-size="{size}" fill="{color}" font-weight="{weight}">{txt}</text>']


def leader(x1, y1, x2, y2):
    """Ligne de rappel pointillée."""
    return [
        f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#666" stroke-width="0.4" stroke-dasharray="2,2"/>',
        f'<circle cx="{x2}" cy="{y2}" r="1.5" fill="#444"/>',
    ]


# ---------- 1. Élévation cotée — LIT 1 vue de face ----------

def elevation_face(lit2=False):
    W = 2080
    D = 1100
    H = 1950 if lit2 else 1750
    Z_S = 1500 if lit2 else 1300
    POST_X = 76
    POST_Y = 89
    RAIL_H = 89
    RAIL_T = 38
    Z_LOW = 250
    title = f"LIT {'2' if lit2 else '1'} — Vue de face (côté garde-corps)" + \
            f"   ·   H {H//10} cm, sous-sommier {Z_S//10} cm"

    sc = 0.30  # mm -> px
    mx, my_top = 90, 110  # marges (espace pour callout en haut)
    canvas_w = int(W * sc + 350)
    canvas_h = int(H * sc + 200)

    def X(x): return mx + x * sc
    def Y(z): return my_top + (H - z) * sc  # Z inversé pour y screen

    out = svg_open(canvas_w, canvas_h, title)

    # sol
    out.append(f'<line x1="{X(-100)}" y1="{Y(0)}" x2="{X(W+100)}" y2="{Y(0)}" stroke="#888" stroke-width="0.6"/>')
    # hachures sol
    for hx in range(-80, int(W)+100, 30):
        out.append(f'<line x1="{X(hx)}" y1="{Y(0)}" x2="{X(hx-20)}" y2="{Y(0)+10}" stroke="#aaa" stroke-width="0.5"/>')

    # 2 montants (gauche et droit), 76 mm de large
    for x0 in (0, W-POST_X):
        out.append(f'<rect x="{X(x0)}" y="{Y(H)}" width="{POST_X*sc}" height="{H*sc}" fill="#d4a373" stroke="#3a2a18" stroke-width="0.7"/>')
        # ligne de collage des 2 lamelles
        out.append(f'<line x1="{X(x0+POST_X/2)}" y1="{Y(H)}" x2="{X(x0+POST_X/2)}" y2="{Y(0)}" stroke="#8b5a2b" stroke-width="0.4" stroke-dasharray="3,2"/>')

    # longeron sommier (entre les 2 montants, top à Z_S)
    out.append(f'<rect x="{X(POST_X)}" y="{Y(Z_S)}" width="{(W-2*POST_X)*sc}" height="{RAIL_H*sc}" fill="#dcbb8a" stroke="#3a2a18" stroke-width="0.6"/>')
    # longeron haut (top à H)
    out.append(f'<rect x="{X(POST_X)}" y="{Y(H)}" width="{(W-2*POST_X)*sc}" height="{RAIL_H*sc}" fill="#dcbb8a" stroke="#3a2a18" stroke-width="0.6"/>')

    # lattes (vue en bout = petits rectangles 19x89 en file)
    n_slat = 14
    avail = W - 2 * POST_X
    slat_w = 89
    gap = (avail - n_slat * slat_w) / (n_slat + 1)
    for i in range(n_slat):
        xs = POST_X + gap * (i+1) + slat_w * i
        out.append(f'<rect x="{X(xs)}" y="{Y(Z_S+19)}" width="{slat_w*sc}" height="{19*sc}" fill="#efd9b4" stroke="#a87a4e" stroke-width="0.3"/>')

    # balustres entre Z_S et top rail bottom
    z_top_bot = H - RAIL_H
    bal_w = 27
    n_bal = 20
    avail_b = W - 2 * POST_X
    gap_b = (avail_b - n_bal * bal_w) / (n_bal + 1)
    for i in range(n_bal):
        xs = POST_X + gap_b * (i+1) + bal_w * i
        out.append(f'<rect x="{X(xs)}" y="{Y(z_top_bot)}" width="{bal_w*sc}" height="{(z_top_bot-Z_S)*sc}" fill="#e8c9a5" stroke="#a87a4e" stroke-width="0.3"/>')

    # plan travail / étagères Lit 2
    if lit2:
        # plan travail (vu de face en transparence : juste la dessus 28mm à Z=680)
        out.append(f'<rect x="{X(POST_X+30)}" y="{Y(680)}" width="{(W-2*POST_X-60)*sc}" height="{28*sc}" fill="#c79e63" stroke="#3a2a18" stroke-width="0.6" opacity="0.85"/>')
        out.append(f'<text x="{X(W/2)}" y="{Y(680)-3}" text-anchor="middle" font-size="9" fill="#5a3a1a">Plan de travail (3×1×8 collés, ép. 28)</text>')
        # étagères
        for zs in (1050, 1300):
            out.append(f'<rect x="{X(POST_X+30)}" y="{Y(zs)}" width="{(W-2*POST_X-60)*sc}" height="{19*sc}" fill="#c79e63" stroke="#3a2a18" stroke-width="0.5" opacity="0.85"/>')
        out.append(f'<text x="{X(W-100)}" y="{Y(1050)+12}" text-anchor="end" font-size="9" fill="#5a3a1a">Étagère 1×8</text>')

    # échelle (à plat, vue de face en profil — limons verticaux inclinés)
    lad_top_x = W - 280
    lad_bot_x = W - 50
    out.append(f'<line x1="{X(lad_bot_x)}" y1="{Y(0)}" x2="{X(lad_top_x)}" y2="{Y(Z_S+50)}" stroke="#6f4622" stroke-width="3" stroke-linecap="round"/>')
    # rungs (visible projection)
    n_rung = 5 if not lit2 else 6
    for i in range(1, n_rung+1):
        t = i / (n_rung + 1)
        rx_top = (1-t)*lad_bot_x + t*lad_top_x
        rz = t * (Z_S + 50)
        out.append(f'<line x1="{X(rx_top-20)}" y1="{Y(rz)}" x2="{X(rx_top+20)}" y2="{Y(rz)}" stroke="#6f4622" stroke-width="2"/>')

    # COTES
    y_bot_dim = Y(0) + 40
    out.extend(dim_h(X(0), X(W), y_bot_dim, f"2080 (couchage 1900 + 90 jeu)"))
    out.extend(dim_h(X(POST_X), X(W-POST_X), y_bot_dim + 22, f"{W-2*POST_X} (entre-montants)"))

    # cote verticale globale à droite
    x_right_dim = X(W) + 50
    out.extend(dim_v(x_right_dim, Y(H), Y(0), f"{H} (H totale)"))
    out.extend(dim_v(x_right_dim + 60, Y(Z_S), Y(0), f"{Z_S} (sous-sommier)"))
    out.extend(dim_v(x_right_dim + 60, Y(H), Y(Z_S), f"{H-Z_S} (garde-corps)"))

    # cote balustres (espacement)
    e_bal = gap_b
    out.extend(label(X(POST_X + bal_w + gap_b/2), Y(z_top_bot)-6, f"gap {int(e_bal)} mm (&lt; 75)", anchor="middle", size=8, color="#666"))

    # niveau bas
    out.append(f'<line x1="{X(0)-20}" y1="{Y(Z_LOW)}" x2="{X(W+30)}" y2="{Y(Z_LOW)}" stroke="#aaa" stroke-width="0.3" stroke-dasharray="4,3"/>')
    out.extend(label(X(W+35), Y(Z_LOW)+3, f"Z = {Z_LOW} (traverse basse)", size=8, color="#888"))

    # niveau matelas
    z_mat = Z_S + 150
    out.append(f'<line x1="{X(POST_X)}" y1="{Y(z_mat)}" x2="{X(W-POST_X)}" y2="{Y(z_mat)}" stroke="#c05a30" stroke-width="0.4" stroke-dasharray="3,2"/>')
    out.extend(label(X(W-POST_X-5), Y(z_mat)-2, f"top matelas (ép. 150 mm)", anchor="end", size=8, color="#c05a30"))

    # garde-corps norme
    out.append(f'<line x1="{X(POST_X)}" y1="{Y(z_mat+260)}" x2="{X(W-POST_X)}" y2="{Y(z_mat+260)}" stroke="#3a5810" stroke-width="0.4" stroke-dasharray="3,2"/>')
    out.extend(label(X(POST_X+5), Y(z_mat+260)-2, "≥ 26 cm au-dessus matelas (NF EN 747)", size=8, color="#3a5810"))

    # callouts pour pièces
    out.extend(leader(X(POST_X/2), Y(H)-2, X(POST_X/2), Y(H)+25))
    out.extend(label(X(POST_X/2), Y(H)-58, "Montant", anchor="middle", size=10, weight="bold"))
    out.extend(label(X(POST_X/2), Y(H)-44, "2×(2×4) collé", anchor="middle", size=9))
    out.extend(label(X(POST_X/2), Y(H)-30, "76 × 89", anchor="middle", size=9))

    out.extend(leader(X(W/2), Y(Z_S+RAIL_H/2), X(W/2), Y(Z_S+RAIL_H/2)-50))
    out.extend(label(X(W/2), Y(Z_S+RAIL_H/2)-55, "Longeron sommier 2×4 sur chant", anchor="middle", size=9, weight="bold"))

    out.extend(leader(X(W*0.7), Y(z_top_bot+(H-z_top_bot)/2), X(W*0.7), Y(H)+25))
    out.extend(label(X(W*0.7), Y(H)+35, "Garde-corps haut 2×4 + balustres 1×4", anchor="middle", size=8, weight="bold"))

    out.extend(close := svg_close())
    return '\n'.join(out)


# ---------- 2. Élévation cotée — vue de profil tête/pied avec diagonale ----------

def elevation_end(lit2=False):
    D = 1100
    H = 1950 if lit2 else 1750
    Z_S = 1500 if lit2 else 1300
    POST_Y = 89
    RAIL_H = 89
    RAIL_T = 38
    Z_LOW = 250
    title = f"LIT {'2' if lit2 else '1'} — Vue d'extrémité (tête ou pied)   ·   Diagonale anti-basculement"

    sc = 0.50
    mx, my_top = 90, 60
    canvas_w = int(D * sc + 350)
    canvas_h = int(H * sc + 180)

    def X(x): return mx + x * sc
    def Y(z): return my_top + (H - z) * sc

    out = svg_open(canvas_w, canvas_h, title)

    # sol
    out.append(f'<line x1="{X(-50)}" y1="{Y(0)}" x2="{X(D+50)}" y2="{Y(0)}" stroke="#888" stroke-width="0.6"/>')
    for hx in range(-40, int(D)+60, 25):
        out.append(f'<line x1="{X(hx)}" y1="{Y(0)}" x2="{X(hx-15)}" y2="{Y(0)+8}" stroke="#aaa" stroke-width="0.4"/>')

    # 2 montants (vue de bout : 89 mm de profondeur visible)
    for y0 in (0, D-POST_Y):
        out.append(f'<rect x="{X(y0)}" y="{Y(H)}" width="{POST_Y*sc}" height="{H*sc}" fill="#d4a373" stroke="#3a2a18" stroke-width="0.7"/>')

    # traverse haute (Z = H-89 à H)
    out.append(f'<rect x="{X(POST_Y)}" y="{Y(H)}" width="{(D-2*POST_Y)*sc}" height="{RAIL_H*sc}" fill="#dcbb8a" stroke="#3a2a18" stroke-width="0.6"/>')
    # traverse sommier
    out.append(f'<rect x="{X(POST_Y)}" y="{Y(Z_S)}" width="{(D-2*POST_Y)*sc}" height="{RAIL_H*sc}" fill="#dcbb8a" stroke="#3a2a18" stroke-width="0.6"/>')
    # traverse basse
    out.append(f'<rect x="{X(POST_Y)}" y="{Y(Z_LOW+RAIL_H/2)}" width="{(D-2*POST_Y)*sc}" height="{RAIL_H*sc}" fill="#dcbb8a" stroke="#3a2a18" stroke-width="0.6"/>')

    # diagonale 2x4 à plat, du low-back au sommier-front (visible : ligne épaisse rouge)
    # de (D-POST_Y, Z_LOW+RAIL_H/2) à (POST_Y, Z_S-RAIL_H)
    out.append(f'<line x1="{X(D-POST_Y)}" y1="{Y(Z_LOW+RAIL_H/2)}" x2="{X(POST_Y)}" y2="{Y(Z_S-RAIL_H)}" stroke="#a23a1f" stroke-width="9" stroke-linecap="round" opacity="0.92"/>')
    # cote diagonale
    diag_mid_x = (X(D-POST_Y) + X(POST_Y))/2
    diag_mid_y = (Y(Z_LOW+RAIL_H/2) + Y(Z_S-RAIL_H))/2
    diag_len = math.sqrt((D-2*POST_Y)**2 + (Z_S-RAIL_H-Z_LOW-RAIL_H/2)**2)
    out.extend(label(diag_mid_x+15, diag_mid_y-8, f"Diagonale 2×4 à plat", size=10, weight="bold", color="#8b3010"))
    out.extend(label(diag_mid_x+15, diag_mid_y+5, f"L ≈ {int(diag_len)} mm (brut, ajuster)", size=9, color="#8b3010"))
    out.extend(label(diag_mid_x+15, diag_mid_y+17, f"vissée + collée aux 4 contacts", size=9, color="#8b3010"))

    # balustres entre traverse haute et sommier
    bal_w = 27
    n_bb = 9
    avail = D - 2 * POST_Y
    gap = (avail - n_bb * bal_w) / (n_bb + 1)
    for i in range(n_bb):
        ys = POST_Y + gap*(i+1) + bal_w*i
        out.append(f'<rect x="{X(ys)}" y="{Y(H-RAIL_H)}" width="{bal_w*sc}" height="{(H-RAIL_H-Z_S)*sc}" fill="#e8c9a5" stroke="#a87a4e" stroke-width="0.3"/>')

    # balustres entre traverse basse et sommier (au-dessus de la diagonale ? Plutôt en dessous)
    # On va en mettre côté tête sous le sommier (intérieur du cadre, entre traverse basse et sommier)
    # Mais la diagonale est là, alors faisons les balustres au-dessus
    # Plutôt : balustres garde-corps uniquement (entre sommier et top rail)

    # COTES
    y_bot_dim = Y(0) + 35
    out.extend(dim_h(X(0), X(D), y_bot_dim, "1100 (profondeur)"))

    x_dim = X(D) + 50
    out.extend(dim_v(x_dim, Y(H), Y(0), f"{H}"))
    out.extend(dim_v(x_dim+55, Y(Z_S), Y(0), f"{Z_S} (sommier)"))
    out.extend(dim_v(x_dim+55, Y(H), Y(Z_S), f"{H-Z_S}"))
    out.extend(dim_v(x_dim, Y(Z_LOW+RAIL_H/2), Y(0), f"{Z_LOW+RAIL_H//2}", side="right"))

    # niveaux
    for (z, txt) in [(Z_LOW, f"traverse basse {Z_LOW}"), (Z_S, f"sommier {Z_S}"), (H, f"haut {H}")]:
        out.append(f'<line x1="{X(-30)}" y1="{Y(z)}" x2="{X(-5)}" y2="{Y(z)}" stroke="#888" stroke-width="0.5"/>')
        out.extend(label(X(-32), Y(z)+3, txt, anchor="end", size=8, color="#666"))

    # callouts
    out.extend(leader(X(POST_Y/2), Y(H-100), X(POST_Y/2), Y(H)+25))
    out.extend(label(X(POST_Y/2), Y(H)+38, "Montant 76×89", anchor="middle", size=8, weight="bold"))

    out.extend(leader(X(D/2), Y(H-RAIL_H/2), X(D/2)+10, Y(H)-30))
    out.extend(label(X(D/2)+12, Y(H)-30, "Traverse haute (cadre fermé)", size=8, weight="bold"))

    out.extend(leader(X(D/2), Y(Z_S-RAIL_H/2), X(D/2)+10, Y(Z_S)-25))
    out.extend(label(X(D/2)+12, Y(Z_S)-25, "Traverse sommier", size=8, weight="bold"))

    out.extend(leader(X(D/2), Y(Z_LOW+RAIL_H/2), X(D/2)+10, Y(Z_LOW+RAIL_H/2)+18))
    out.extend(label(X(D/2)+12, Y(Z_LOW+RAIL_H/2)+22, "Traverse basse (Z=250)", size=8, weight="bold"))

    out.extend(svg_close())
    return '\n'.join(out)


# ---------- 3. Détail jonction barillet (vue éclatée) ----------

def detail_barillet():
    sc = 1.6  # mm -> px (gros plan)
    canvas_w, canvas_h = 720, 420
    title = "Détail — Connexion boulon traversant M8 + écrou barillet"

    out = svg_open(canvas_w, canvas_h, title)

    # Disposition : à gauche le montant en coupe horizontale, au milieu boulon, à droite longeron en bout
    # Montant : section horizontale (vue de dessus) — rectangle 89 x 76 mm
    # Longeron : section vue en bout — rectangle 89 x 38 mm

    # MONTANT (section horizontale, vue de dessus)
    mx, my = 80, 200  # centre du montant
    pw, pd = 89, 76  # post 89 (Y) x 76 (X) in plan
    px0 = mx - pw*sc/2
    py0 = my - pd*sc/2
    out.append(f'<rect x="{px0}" y="{py0}" width="{pw*sc}" height="{pd*sc}" fill="url(#hatch)" stroke="#3a2a18" stroke-width="1"/>')
    out.append(f'<rect x="{px0}" y="{py0}" width="{pw*sc}" height="{pd*sc}" fill="#d4a373" stroke="#3a2a18" stroke-width="1" opacity="0.4"/>')
    out.extend(label(mx, py0 - 8, "Montant (section horizontale)", anchor="middle", size=10, weight="bold"))
    out.extend(label(mx, py0 + pd*sc + 18, "76 × 89 mm", anchor="middle", size=9, color="#666"))

    # trou Ø9 traversant le montant
    hole_r = 9*sc/2
    out.append(f'<circle cx="{mx}" cy="{my}" r="{hole_r}" fill="#fdfaf3" stroke="#3a2a18" stroke-width="0.8"/>')
    # lamage Ø25 sur la face extérieure (face gauche du montant ici)
    lam_r = 25*sc/2
    out.append(f'<path d="M {px0-1} {my-lam_r} L {px0+8*sc} {my-lam_r} L {px0+8*sc} {my+lam_r} L {px0-1} {my+lam_r} Z" fill="#fdfaf3" stroke="#3a2a18" stroke-width="0.8"/>')
    out.extend(dim_v(px0-20, my-lam_r, my+lam_r, "Ø25 lamage", side="left", offset_text=-2))

    # BOULON traversant (au milieu)
    bx = mx + pw*sc/2 + 30  # début du boulon
    bolt_len_total = 100 * sc  # M8 x 100
    head_r = 12 * sc / 2
    shaft_w = 8 * sc / 2

    # tête bombée à gauche
    out.append(f'<rect x="{bx - 8*sc}" y="{my - head_r}" width="{8*sc}" height="{2*head_r}" fill="#888" stroke="#222" stroke-width="0.5"/>')
    out.extend(label(bx - 4*sc, my - head_r - 4, "tête bombée 6 pans creux", anchor="middle", size=8, color="#444"))
    # rondelle
    out.append(f'<rect x="{bx}" y="{my - 9*sc}" width="{1.5*sc}" height="{18*sc}" fill="#aaa" stroke="#222" stroke-width="0.4"/>')
    out.extend(label(bx + 1*sc, my + 9*sc + 10, "rondelle", anchor="middle", size=8, color="#444"))
    # tige filetée
    bolt_shaft_start = bx + 1.5*sc
    bolt_shaft_end = bolt_shaft_start + bolt_len_total
    out.append(f'<rect x="{bolt_shaft_start}" y="{my - shaft_w}" width="{bolt_len_total}" height="{2*shaft_w}" fill="#bbb" stroke="#222" stroke-width="0.5"/>')
    # hatching for thread
    for tx in range(int(bolt_shaft_start), int(bolt_shaft_end), 5):
        out.append(f'<line x1="{tx}" y1="{my-shaft_w}" x2="{tx+3}" y2="{my+shaft_w}" stroke="#666" stroke-width="0.3"/>')
    out.extend(label((bolt_shaft_start + bolt_shaft_end)/2, my + shaft_w + 14, "tige filetée M8 × 100", anchor="middle", size=9, weight="bold", color="#222"))

    # LONGERON en bout (section, sur la droite, traversé par le boulon)
    # Section longeron : 38 x 89 (vu en bout : rectangle dans le plan X-Z, mais on est en vue de dessus donc c'est X-Y)
    # En vue de dessus, le longeron est vu de son chant : 38 mm de largeur
    lx = bolt_shaft_end - 50*sc  # le longeron commence avant la fin du boulon (le boulon pénètre dedans)
    lw, ld = 200, 38  # longeron coupé visible : 200 mm de longueur en bout
    out.append(f'<rect x="{lx}" y="{my - ld*sc/2}" width="{lw*sc}" height="{ld*sc}" fill="url(#hatchL)" stroke="#3a2a18" stroke-width="1"/>')
    out.append(f'<rect x="{lx}" y="{my - ld*sc/2}" width="{lw*sc}" height="{ld*sc}" fill="#dcbb8a" stroke="#3a2a18" stroke-width="1" opacity="0.4"/>')
    out.extend(label(lx + lw*sc/2, my - ld*sc/2 - 8, "Longeron 2×4 (section partielle)", anchor="middle", size=10, weight="bold"))
    out.extend(label(lx + lw*sc/2, my + ld*sc/2 + 18, "38 × 89 mm", anchor="middle", size=9, color="#666"))

    # logement barillet Ø13 perpendiculaire (vu de dessus = cercle Ø13 vu en coupe = rectangle)
    # le barillet est traversant Z, donc en vue de dessus c'est un cercle
    barrel_cx = lx + 25*sc
    barrel_r = 13*sc/2
    out.append(f'<circle cx="{barrel_cx}" cy="{my}" r="{barrel_r}" fill="#666" stroke="#222" stroke-width="0.6"/>')
    out.append(f'<text x="{barrel_cx}" y="{my+3}" text-anchor="middle" font-size="8" fill="white">Ø13</text>')
    # cote pour distance from bout
    out.extend(dim_h(lx, barrel_cx, my + ld*sc/2 + 35, "25 mm"))

    # zoom barillet (cercle agrandi en bas)
    zx, zy = 460, 350
    zoom = 3
    out.append(f'<circle cx="{zx}" cy="{zy}" r="{13*zoom}" fill="#888" stroke="#222" stroke-width="1.5"/>')
    # fente intérieure (filetage transversal)
    out.append(f'<rect x="{zx - 13*zoom}" y="{zy-1.5*zoom}" width="{26*zoom}" height="{3*zoom}" fill="#222"/>')
    out.append(f'<text x="{zx}" y="{zy+15*zoom+12}" text-anchor="middle" font-size="9" font-weight="bold" fill="#222">Écrou barillet (filetage M8 transversal)</text>')
    out.extend(label(zx, zy-15*zoom-2, "Ø13 × 14 mm", anchor="middle", size=9, color="#444"))
    # flèche du zoom vers le logement
    out.append(f'<line x1="{barrel_cx}" y1="{my}" x2="{zx-13*zoom}" y2="{zy}" stroke="#888" stroke-width="0.5" stroke-dasharray="3,2"/>')

    # axe du boulon vers le barillet (trou Ø9 dans le longeron, en bout)
    out.append(f'<line x1="{lx}" y1="{my}" x2="{barrel_cx + barrel_r - 3}" y2="{my}" stroke="#fdfaf3" stroke-width="5"/>')
    out.append(f'<line x1="{lx}" y1="{my}" x2="{barrel_cx + barrel_r - 3}" y2="{my}" stroke="#222" stroke-width="0.5" stroke-dasharray="2,2"/>')

    # Notes
    out.extend(label(40, canvas_h - 60, "1. Percer Ø9 traversant le montant (depuis l'extérieur).  2. Percer Ø9 en bout du longeron, axé.", size=9, color="#333"))
    out.extend(label(40, canvas_h - 46, "3. Percer Ø13 transversal dans le longeron, à 25 mm du bout, coupant l'axe du Ø9.", size=9, color="#333"))
    out.extend(label(40, canvas_h - 32, "4. Insérer le barillet (fente alignée avec l'axe du boulon).  5. Engager le boulon + rondelle, serrer à la clé 13.", size=9, color="#333"))

    out.extend(svg_close())
    return '\n'.join(out)


# ---------- 4. Détail montant doublé (section) ----------

def detail_montant():
    sc = 2.5
    canvas_w, canvas_h = 600, 380
    title = "Détail — Montant doublé 2×(2×4) — coupe horizontale"

    out = svg_open(canvas_w, canvas_h, title)

    cx, cy = canvas_w/2, 200

    # Deux 2×4 collés face contre face
    # 2×4 = 38 × 89. Collage des faces de 38 sur 89, donc bloc final = 76 × 89
    pw1, ph1 = 38, 89
    # gauche
    x_l = cx - 76*sc/2
    out.append(f'<rect x="{x_l}" y="{cy - ph1*sc/2}" width="{pw1*sc}" height="{ph1*sc}" fill="#d4a373" stroke="#3a2a18" stroke-width="1.2"/>')
    # droite
    x_r = cx
    out.append(f'<rect x="{x_r}" y="{cy - ph1*sc/2}" width="{pw1*sc}" height="{ph1*sc}" fill="#d4a373" stroke="#3a2a18" stroke-width="1.2"/>')
    # ligne de colle au milieu
    out.append(f'<line x1="{cx}" y1="{cy - ph1*sc/2}" x2="{cx}" y2="{cy + ph1*sc/2}" stroke="#a85020" stroke-width="2"/>')

    # vis en zig-zag (3 vis schématisées)
    for vy_offset in (-30, 0, 30):
        # vis de gauche vers droite
        out.append(f'<line x1="{cx - 28}" y1="{cy + vy_offset}" x2="{cx + 28}" y2="{cy + vy_offset + 5}" stroke="#444" stroke-width="0.8"/>')
        out.append(f'<circle cx="{cx + 28}" cy="{cy + vy_offset + 5}" r="2.5" fill="#444"/>')
        # vis de droite vers gauche
        out.append(f'<line x1="{cx + 28}" y1="{cy + vy_offset - 15}" x2="{cx - 28}" y2="{cy + vy_offset - 10}" stroke="#444" stroke-width="0.8"/>')
        out.append(f'<circle cx="{cx - 28}" cy="{cy + vy_offset - 10}" r="2.5" fill="#444"/>')

    # cotes
    out.extend(dim_h(x_l, x_r + pw1*sc, cy + ph1*sc/2 + 35, "76 mm (assemblé)"))
    out.extend(dim_h(x_l, cx, cy + ph1*sc/2 + 18, "38 (2×4)", offset_text=-3))
    out.extend(dim_h(cx, x_r + pw1*sc, cy + ph1*sc/2 + 18, "38 (2×4)", offset_text=-3))
    out.extend(dim_v(x_l - 25, cy - ph1*sc/2, cy + ph1*sc/2, "89 mm"))

    # callouts
    out.extend(label(cx, cy - ph1*sc/2 - 50, "2 lamelles 2×4 collées face contre face", anchor="middle", size=11, weight="bold"))
    out.extend(label(cx, cy - ph1*sc/2 - 36, "→ section finie 76 × 89 mm (≈ poteau 80×80)", anchor="middle", size=10, color="#666"))
    out.extend(leader(cx, cy + 5, cx + 110, cy + 5))
    out.extend(label(cx + 115, cy + 8, "Plan de colle PVA D3", size=10, weight="bold", color="#a85020"))
    out.extend(label(cx + 115, cy + 22, "+ vis 5×80 alternées tous les 25 cm", size=9, color="#666"))

    # note bas
    out.extend(label(40, canvas_h - 30, "Procédure : encoller toute la surface, presser aux serre-joints 30 min puis visser. Sécher 12 h avant manipulation.", size=9, color="#333"))

    out.extend(svg_close())
    return '\n'.join(out)


# ---------- 5. Détail sommier (coupe transversale) ----------

def detail_sommier():
    sc = 1.8  # scale plus grand pour les détails du bois
    canvas_w, canvas_h = 760, 440
    title = "Détail — Coupe transversale du sommier (longeron + tasseau + latte)"

    out = svg_open(canvas_w, canvas_h, title)

    # Centre du longeron
    cx, cy = 280, 270

    # Longeron 2×4 sur chant (38 large, 89 haut)
    lw, lh = 38, 89
    lx = cx - lw*sc/2
    ly = cy - lh*sc/2
    out.append(f'<rect x="{lx}" y="{ly}" width="{lw*sc}" height="{lh*sc}" fill="#d4a373" stroke="#3a2a18" stroke-width="1.2"/>')
    out.extend(dim_v(lx - 18, ly, ly + lh*sc, "89"))
    out.extend(dim_h(lx, lx + lw*sc, ly + lh*sc + 30, "38"))

    # Tasseau 19 × 43 (refente du 1×4 en 2) à l'intérieur du longeron (côté droit)
    # Top du tasseau = top longeron - 19 (pour que latte affleure)
    tw, th = 19, 43
    tx = lx + lw*sc  # collé à la face intérieure droite du longeron
    ty = ly + 19*sc  # top du tasseau
    out.append(f'<rect x="{tx}" y="{ty}" width="{tw*sc}" height="{th*sc}" fill="#dcbb8a" stroke="#3a2a18" stroke-width="0.8"/>')

    # Latte 1×4 (19 × 89), posée à plat sur le tasseau, top affleurant top longeron
    slat_w, slat_t = 89, 19
    slat_x = tx
    slat_y = ly
    out.append(f'<rect x="{slat_x}" y="{slat_y}" width="{slat_w*sc}" height="{slat_t*sc}" fill="#efd9b4" stroke="#3a2a18" stroke-width="0.8"/>')

    # Vis traversant latte → tasseau
    sx = slat_x + 30
    out.append(f'<line x1="{sx}" y1="{slat_y - 3}" x2="{sx}" y2="{ty + th*sc - 4}" stroke="#444" stroke-width="0.8"/>')
    out.append(f'<polygon points="{sx-3},{slat_y - 3} {sx+3},{slat_y - 3} {sx},{slat_y + 3}" fill="#444"/>')

    # Vis traversant tasseau → longeron
    sx2 = tx + tw*sc/2
    out.append(f'<line x1="{sx2 + 18}" y1="{ty + th*sc/2}" x2="{lx + lw*sc - 4}" y2="{ty + th*sc/2}" stroke="#444" stroke-width="0.8"/>')

    # Matelas indicatif (juste un bord avec hachure légère, pas plein gabarit)
    mat_h_visible = 60  # on n'en montre que 60 mm de hauteur, pas 150
    mat_x_start = slat_x + 20
    mat_x_end = slat_x + slat_w*sc - 10
    out.append(f'<rect x="{mat_x_start}" y="{slat_y - mat_h_visible*sc}" width="{mat_x_end - mat_x_start}" height="{mat_h_visible*sc}" fill="#f5e8d3" stroke="#c79e63" stroke-width="0.6"/>')
    # Hachure pour montrer que ça continue
    for i in range(0, int(mat_h_visible*sc), 8):
        out.append(f'<line x1="{mat_x_start}" y1="{slat_y - mat_h_visible*sc + i}" x2="{mat_x_start + 10}" y2="{slat_y - mat_h_visible*sc + i + 4}" stroke="#c79e63" stroke-width="0.4"/>')
    out.extend(label((mat_x_start + mat_x_end)/2, slat_y - mat_h_visible*sc/2 + 3, "Matelas (90×190)", anchor="middle", size=9, color="#a87a4e", weight="bold"))
    out.extend(label((mat_x_start + mat_x_end)/2, slat_y - mat_h_visible*sc - 5, "(ép. max 150 mm)", anchor="middle", size=8, color="#a87a4e"))

    # Niveau Z=1300/1500 — ligne horizontale
    out.append(f'<line x1="{50}" y1="{slat_y}" x2="{lx - 20}" y2="{slat_y}" stroke="#3a5810" stroke-width="0.4" stroke-dasharray="3,2"/>')
    out.extend(label(55, slat_y - 4, "Z = 1300 (Lit 1) ou Z = 1500 (Lit 2) — top des lattes", size=9, color="#3a5810"))

    # Callouts à droite
    callouts_x = mat_x_end + 40
    cy_text = 100
    out.extend(leader(slat_x + slat_w*sc/2, slat_y + slat_t*sc/2, callouts_x - 5, cy_text))
    out.extend(label(callouts_x, cy_text + 3, "Latte 1×4 (19 × 89)", size=10, weight="bold"))
    out.extend(label(callouts_x, cy_text + 16, "espacement 40 mm entre lattes", size=9, color="#666"))
    out.extend(label(callouts_x, cy_text + 28, "vissée sur tasseau (2 vis 4×40)", size=9, color="#666"))

    cy_text2 = 170
    out.extend(leader(tx + tw*sc/2, ty + th*sc/2, callouts_x - 5, cy_text2))
    out.extend(label(callouts_x, cy_text2 + 3, "Tasseau 19 × 43", size=10, weight="bold"))
    out.extend(label(callouts_x, cy_text2 + 16, "(refente 1×4 en 2)", size=9, color="#666"))
    out.extend(label(callouts_x, cy_text2 + 28, "vissé inside longeron / 20 cm", size=9, color="#666"))

    cy_text3 = 250
    out.extend(leader(lx + lw*sc/2, cy, callouts_x - 5, cy_text3))
    out.extend(label(callouts_x, cy_text3 + 3, "Longeron 2×4 sur chant", size=10, weight="bold"))
    out.extend(label(callouts_x, cy_text3 + 16, "38 × 89 mm, longueur 1928", size=9, color="#666"))

    # Vue secondaire : tasseau vu de côté (longueur)
    vlx, vly = 60, 380
    out.extend(label(vlx, vly - 8, "Tasseau vu de côté (longueur 1928 mm) :", size=10, weight="bold", color="#444"))
    out.append(f'<rect x="{vlx}" y="{vly}" width="200" height="14" fill="#dcbb8a" stroke="#3a2a18" stroke-width="0.6"/>')
    # vis le long
    for vx in range(int(vlx)+15, int(vlx)+200, 22):
        out.append(f'<circle cx="{vx}" cy="{vly+7}" r="1.5" fill="#444"/>')
    out.extend(label(vlx + 220, vly + 11, "vis 4×40 tous les 20 cm dans le longeron", size=9, color="#666"))

    out.extend(svg_close())
    return '\n'.join(out)


# ---------- 6. Détail collage chant-à-chant 1×8 (plan de travail) ----------

def detail_collage():
    sc = 2.0
    canvas_w, canvas_h = 720, 380
    title = "Détail — Collage chant-à-chant des 1×8 (plan de travail Lit 2)"

    out = svg_open(canvas_w, canvas_h, title)

    # Trois 1×8 (184 × 19) en coupe — vus de bout (la longueur 1900 va dans l'écran)
    cx, cy = canvas_w/2, 200
    bw, bt = 184, 19  # 1×8 width 184, thickness 19

    total_w = 3 * bw
    x0 = cx - total_w*sc/2
    for i in range(3):
        bx = x0 + i * bw*sc
        out.append(f'<rect x="{bx}" y="{cy - bt*sc/2}" width="{bw*sc}" height="{bt*sc}" fill="#c79e63" stroke="#3a2a18" stroke-width="1"/>')

    # Lignes de colle entre les 3
    for i in range(1, 3):
        gx = x0 + i * bw*sc
        out.append(f'<line x1="{gx}" y1="{cy - bt*sc/2}" x2="{gx}" y2="{cy + bt*sc/2}" stroke="#a85020" stroke-width="2.5"/>')

    # Chevilles Ø8 (à mi-épaisseur, schématisées)
    for i in range(1, 3):
        gx = x0 + i * bw*sc
        for cy_off in (-bw*sc*0.4, 0, bw*sc*0.4):
            # chevilles vues en bout (cercles)
            pass  # En vue en bout, les chevilles sont des cercles dans l'axe Z, pas visibles ici
    # Plutôt, montrer la cheville en vue de dessus en agrandissement

    # cotes
    out.extend(dim_h(x0, x0 + total_w*sc, cy + bt*sc/2 + 30, f"{int(total_w)} mm brut → raboter à 500 mm"))
    out.extend(dim_h(x0, x0 + bw*sc, cy + bt*sc/2 + 50, "184 (1×8)", offset_text=-3))
    out.extend(dim_v(x0 - 20, cy - bt*sc/2, cy + bt*sc/2, "19"))

    # callouts
    out.extend(label(cx, cy - bt*sc/2 - 100, "Vue en bout : 3 lames 1×8 jointées chant-à-chant", anchor="middle", size=11, weight="bold"))
    out.extend(label(cx, cy - bt*sc/2 - 84, "(les lames vont vers le fond, longueur 1900 mm)", anchor="middle", size=9, color="#666"))

    # Détail cheville à droite
    zx, zy = 540, 130
    out.append(f'<text x="{zx}" y="{zy - 20}" font-size="10" font-weight="bold" fill="#222">Détail joint avec cheville Ø8 :</text>')
    # 2 chants juxtaposés avec cheville dedans
    out.append(f'<rect x="{zx}" y="{zy}" width="60" height="30" fill="#c79e63" stroke="#3a2a18" stroke-width="0.8"/>')
    out.append(f'<rect x="{zx+60}" y="{zy}" width="60" height="30" fill="#c79e63" stroke="#3a2a18" stroke-width="0.8"/>')
    out.append(f'<line x1="{zx+60}" y1="{zy}" x2="{zx+60}" y2="{zy+30}" stroke="#a85020" stroke-width="2"/>')
    # cheville traversant le joint
    out.append(f'<rect x="{zx+42}" y="{zy+11}" width="36" height="8" fill="#8b5a30" stroke="#3a2a18" stroke-width="0.5"/>')
    out.extend(label(zx + 60, zy + 50, "cheville bois Ø8 × 30", anchor="middle", size=9, color="#5a3a1a"))
    out.extend(label(zx + 60, zy + 64, "(perçage Ø8 prof. 18 mm × 2)", anchor="middle", size=8, color="#666"))

    # Notes
    out.extend(label(40, canvas_h - 60, "1. Tracer 3 chevilles par joint, à 30 cm des bouts et au milieu, à mi-épaisseur (axe Z=9,5 mm).", size=9, color="#333"))
    out.extend(label(40, canvas_h - 46, "2. Percer Ø8 prof. 18 mm aux 6 points par joint (3 × 2 faces).", size=9, color="#333"))
    out.extend(label(40, canvas_h - 32, "3. Encoller chants + chevilles, presser aux serre-joints 4 h. Raboter ensuite la largeur finale à 500 mm.", size=9, color="#333"))

    out.extend(svg_close())
    return '\n'.join(out)


# ---------- 7. Détail échelle (limon avec entailles) ----------

def detail_echelle():
    sc = 0.5  # mm -> px
    canvas_w, canvas_h = 900, 380
    title = "Détail — Échelle (limons + barreaux 1×4 embrevés)"

    out = svg_open(canvas_w, canvas_h, title)

    # Vue de face : 2 limons inclinés à 75° du sol, longueur 1400 (Lit 1) ou 1600 (Lit 2)
    # Représentons Lit 1 : limon 1400 mm, ~80° d'inclinaison
    # Distance horizontale entre les 2 limons : 280 mm

    angle = math.radians(78)  # 78° du sol = bonne pente d'échelle (à peu près verticale)
    L_limon = 1400
    spacing = 280  # entre limons

    # base à gauche, haut à droite
    bx, by = 80, 320  # base inférieure du limon de gauche
    top_x = bx + L_limon * math.cos(angle) * sc
    top_y = by - L_limon * math.sin(angle) * sc

    # limon gauche
    lw = 19  # épaisseur (sur chant : 89 vu de face, 19 d'épaisseur — en vue de profil on voit 89)
    # En vue de face de l'échelle (regardant l'échelle en plein) : chaque limon a 89 mm de large, le limon lui-même est dans l'épaisseur 19 dirigée vers le viewer
    # Donc en vue de face : limon = trait de 89 mm de large
    limon_w = 89

    # Dessiner le limon gauche
    # Calcul perpendiculaire pour épaisseur visuelle
    perp_x = -math.sin(angle) * limon_w * sc
    perp_y = -math.cos(angle) * limon_w * sc

    def quad(p1, p2, p3, p4, fill="#d4a373"):
        return f'<polygon points="{p1[0]:.1f},{p1[1]:.1f} {p2[0]:.1f},{p2[1]:.1f} {p3[0]:.1f},{p3[1]:.1f} {p4[0]:.1f},{p4[1]:.1f}" fill="{fill}" stroke="#3a2a18" stroke-width="0.8"/>'

    p1 = (bx, by)
    p2 = (top_x, top_y)
    p3 = (top_x + perp_x, top_y + perp_y)
    p4 = (bx + perp_x, by + perp_y)
    out.append(quad(p1, p2, p3, p4, "#d4a373"))

    # limon droit (espacé de 'spacing' perpendiculairement aux limons → en vue de face c'est juste un décalage horizontal)
    # Mais on regarde l'échelle vue de face donc spacing apparait en horizontal
    # Pour simplifier : décaler verticalement (sur l'écran) le 2e limon ? Non, en vue de face frontale, c'est en arrière, pas visible séparément.
    # OK, on va plutôt présenter une vue oblique : un seul limon vu en plein, avec les barreaux qui pointent vers nous.

    # Barreaux : entailles dans le limon, espacement 250 mm le long du limon
    n_rungs = 5
    rung_spacing = (L_limon - 100) / n_rungs  # 100 mm de marge en bas et en haut
    for i in range(n_rungs):
        d = 70 + i * rung_spacing  # distance depuis la base
        # position le long du limon
        rx = bx + d * math.cos(angle) * sc
        ry = by - d * math.sin(angle) * sc
        # entaille : rectangle 89 × 10 perpendiculaire au limon
        # En vue 2D simplifiée : on dessine juste un trait noir
        # Mieux : dessiner le barreau dépassant à droite
        # Barreau 320 mm de long perpendiculaire au limon, partant de rx,ry
        perp_b_x = math.sin(angle) * 320 * sc
        perp_b_y = math.cos(angle) * 320 * sc
        bar_w_visual = 89  # vu sur sa tranche : 19 mm épaisseur, 89 mm de large

        # Représenter barreau : 2 segments à 19 mm d'écart (à plat)
        # Simplifions : un seul trait épais
        out.append(f'<line x1="{rx:.1f}" y1="{ry:.1f}" x2="{rx + perp_b_x:.1f}" y2="{ry + perp_b_y:.1f}" stroke="#a87a4e" stroke-width="6" stroke-linecap="round"/>')
        # entaille noire dans le limon
        # Position rectangle d'entaille
        e1 = (rx - math.cos(angle) * 10 * sc, ry + math.sin(angle) * 10 * sc)
        e2 = (rx + math.cos(angle) * 10 * sc, ry - math.sin(angle) * 10 * sc)
        out.append(f'<line x1="{e1[0]:.1f}" y1="{e1[1]:.1f}" x2="{e2[0]:.1f}" y2="{e2[1]:.1f}" stroke="#5a3a1a" stroke-width="2"/>')

    # Détail entaille agrandi à droite
    dxa, dya = 600, 100
    zoom = 3
    out.append(f'<text x="{dxa}" y="{dya - 14}" font-size="10" font-weight="bold" fill="#222">Détail entaille / barreau :</text>')
    # limon en bois
    out.append(f'<rect x="{dxa}" y="{dya}" width="{89*sc*zoom}" height="{120*sc*zoom}" fill="#d4a373" stroke="#3a2a18" stroke-width="1"/>')
    # entaille creusée 19 × 10 mm (à mi-largeur du limon)
    en_x = dxa + (89-19)/2 * sc*zoom
    en_y = dya + 60 * sc*zoom
    out.append(f'<rect x="{en_x}" y="{en_y}" width="{19*sc*zoom}" height="{10*sc*zoom}" fill="#5a3a1a" stroke="#3a2a18" stroke-width="0.5"/>')
    # barreau encastré (dépassant en avant)
    out.append(f'<rect x="{en_x}" y="{en_y - 5*sc*zoom}" width="{19*sc*zoom}" height="{20*sc*zoom}" fill="#a87a4e" stroke="#3a2a18" stroke-width="0.6"/>')
    out.extend(dim_h(en_x, en_x + 19*sc*zoom, en_y + 10*sc*zoom + 18, "19", offset_text=-2))
    out.extend(dim_v(en_x - 12, en_y, en_y + 10*sc*zoom, "10", side="left", offset_text=-2))
    out.extend(label(dxa + 89*sc*zoom + 5, en_y + 5, "Entaille 19 × 10 mm", size=9, color="#444"))
    out.extend(label(dxa + 89*sc*zoom + 5, en_y + 18, "Barreau 1×4 collé", size=9, color="#444"))
    out.extend(label(dxa + 89*sc*zoom + 5, en_y + 31, "+ 1 vis 4×40 par côté", size=9, color="#444"))

    # cotes
    out.extend(label(top_x + 10, top_y - 8, f"L = 1400 mm (Lit 1)", size=9, color="#666"))
    out.extend(label(top_x + 10, top_y + 5, f"L = 1600 mm (Lit 2)", size=9, color="#666"))
    out.extend(label(bx - 30, by + 20, "75° du sol", size=9, color="#666", weight="bold"))
    out.extend(label(40, by + 50, "Espacement barreaux : ~250 mm  ·  5 barreaux Lit 1 / 6 barreaux Lit 2", size=9, color="#333"))

    out.extend(svg_close())
    return '\n'.join(out)


# ---------- 8. Vue de dessus (plan) sommier ----------

def plan_sommier():
    W = 2080
    D = 1100
    POST_X = 76
    POST_Y = 89
    sc = 0.30
    canvas_w = int(W*sc + 200)
    canvas_h = int(D*sc + 160)
    title = "Plan du sommier (vue de dessus) — lattes et tasseaux"

    out = svg_open(canvas_w, canvas_h, title)

    mx, my = 80, 70
    def X(x): return mx + x*sc
    def Y(y): return my + y*sc

    # Contour externe
    out.append(f'<rect x="{X(0)}" y="{Y(0)}" width="{W*sc}" height="{D*sc}" fill="none" stroke="#888" stroke-width="0.4" stroke-dasharray="3,2"/>')

    # 4 montants (vu de dessus : rectangles 76 × 89)
    posts = [
        (0, 0), (W-POST_X, 0), (0, D-POST_Y), (W-POST_X, D-POST_Y)
    ]
    for px, py in posts:
        out.append(f'<rect x="{X(px)}" y="{Y(py)}" width="{POST_X*sc}" height="{POST_Y*sc}" fill="#d4a373" stroke="#3a2a18" stroke-width="0.8"/>')

    # Longerons (le long de X, sur les côtés Y)
    RAIL_T = 38
    front_y = POST_Y
    back_y = D - POST_Y
    out.append(f'<rect x="{X(POST_X)}" y="{Y(front_y - RAIL_T)}" width="{(W-2*POST_X)*sc}" height="{RAIL_T*sc}" fill="#dcbb8a" stroke="#3a2a18" stroke-width="0.5"/>')
    out.append(f'<rect x="{X(POST_X)}" y="{Y(back_y)}" width="{(W-2*POST_X)*sc}" height="{RAIL_T*sc}" fill="#dcbb8a" stroke="#3a2a18" stroke-width="0.5"/>')
    # Traverses
    out.append(f'<rect x="{X(POST_X - RAIL_T)}" y="{Y(POST_Y)}" width="{RAIL_T*sc}" height="{(D-2*POST_Y)*sc}" fill="#dcbb8a" stroke="#3a2a18" stroke-width="0.5"/>')
    out.append(f'<rect x="{X(W - POST_X)}" y="{Y(POST_Y)}" width="{RAIL_T*sc}" height="{(D-2*POST_Y)*sc}" fill="#dcbb8a" stroke="#3a2a18" stroke-width="0.5"/>')

    # Tasseaux à l'intérieur des longerons
    Ta = 19
    out.append(f'<rect x="{X(POST_X)}" y="{Y(front_y)}" width="{(W-2*POST_X)*sc}" height="{Ta*sc}" fill="#c79e63" stroke="#3a2a18" stroke-width="0.4"/>')
    out.append(f'<rect x="{X(POST_X)}" y="{Y(back_y - Ta)}" width="{(W-2*POST_X)*sc}" height="{Ta*sc}" fill="#c79e63" stroke="#3a2a18" stroke-width="0.4"/>')

    # Lattes
    n_slat = 14
    slat_w = 89
    avail = W - 2 * POST_X
    gap = (avail - n_slat * slat_w) / (n_slat + 1)
    for i in range(n_slat):
        xs = POST_X + gap*(i+1) + slat_w*i
        out.append(f'<rect x="{X(xs)}" y="{Y(front_y + Ta)}" width="{slat_w*sc}" height="{(back_y - front_y - 2*Ta)*sc}" fill="#efd9b4" stroke="#a87a4e" stroke-width="0.3"/>')

    # cotes
    y_dim = Y(D) + 35
    out.extend(dim_h(X(0), X(W), y_dim, "2080"))
    out.extend(dim_h(X(POST_X), X(W-POST_X), y_dim + 22, f"{W-2*POST_X} (intérieur)"))

    x_dim = X(W) + 30
    out.extend(dim_v(x_dim, Y(0), Y(D), "1100"))
    out.extend(dim_v(x_dim + 60, Y(POST_Y), Y(D-POST_Y), f"{D-2*POST_Y}"))

    # cote espacement lattes
    out.extend(label(X(POST_X + slat_w + gap/2), Y(front_y + Ta + (back_y-front_y-2*Ta)*sc/2/sc), f"gap {int(gap)} mm", anchor="middle", size=8, color="#666"))

    # Légende
    lx, ly = 40, canvas_h - 60
    items = [
        ("#d4a373", "Montants doublés 76×89"),
        ("#dcbb8a", "Longerons + traverses 2×4"),
        ("#c79e63", "Tasseaux 19×43 (refente 1×4)"),
        ("#efd9b4", "Lattes 1×4 (×14)"),
    ]
    for i, (c, t) in enumerate(items):
        out.append(f'<rect x="{lx + i*180}" y="{ly}" width="20" height="10" fill="{c}" stroke="#3a2a18" stroke-width="0.5"/>')
        out.extend(label(lx + i*180 + 24, ly + 9, t, size=9))

    out.extend(svg_close())
    return '\n'.join(out)


# ---------- Génère tout ----------

schemas = {
    "01-elevation-lit1-face.svg": elevation_face(lit2=False),
    "02-elevation-lit1-end.svg": elevation_end(lit2=False),
    "03-elevation-lit2-face.svg": elevation_face(lit2=True),
    "04-elevation-lit2-end.svg": elevation_end(lit2=True),
    "05-detail-montant.svg": detail_montant(),
    "06-detail-barillet.svg": detail_barillet(),
    "07-detail-sommier.svg": detail_sommier(),
    "08-detail-collage.svg": detail_collage(),
    "09-detail-echelle.svg": detail_echelle(),
    "10-plan-sommier.svg": plan_sommier(),
}

for name, content in schemas.items():
    path = os.path.join(OUT, name)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  {path}  ({len(content)//1024} KB)")

print(f"\nGénéré {len(schemas)} schémas dans {OUT}/")

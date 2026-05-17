#!/usr/bin/env python3
"""Generate isometric SVG visuals for the two mezzanine beds.

Cabinet-style oblique projection:
  sx = ox + S * (X + DF * Y)
  sy = oy + S * (-Z + DF * Y)
where +X = bed length (right), +Y = bed depth (back), +Z = up.
"""

S = 0.18          # scale: 1 mm -> 0.18 px
DF = 0.42         # depth foreshortening (cos~65 ish, looks reasonable)


def P(X, Y, Z, ox, oy):
    return (ox + S * (X + DF * Y), oy + S * (-Z + DF * Y))


def box(x1, y1, z1, x2, y2, z2, ox, oy, palette="pin"):
    """Return list of polygon SVG strings for the 3 visible faces of a box.

    Visible (in this projection): TOP, FRONT (Y=y1), RIGHT (X=x2).
    """
    c = {
        'flb': P(x1, y1, z1, ox, oy),
        'frb': P(x2, y1, z1, ox, oy),
        'brb': P(x2, y2, z1, ox, oy),
        'blb': P(x1, y2, z1, ox, oy),
        'flt': P(x1, y1, z2, ox, oy),
        'frt': P(x2, y1, z2, ox, oy),
        'brt': P(x2, y2, z2, ox, oy),
        'blt': P(x1, y2, z2, ox, oy),
    }
    palettes = {
        "pin":     {"top": "#e9c89a", "front": "#d4a373", "side": "#a87a4e"},
        "pin-l":   {"top": "#f3dcb4", "front": "#e2bf91", "side": "#b88c64"},
        "latte":   {"top": "#efd9b4", "front": "#dcbb8a", "side": "#b8946a"},
        "brace":   {"top": "#9c6a3e", "front": "#8b5a30", "side": "#6f4622"},
        "panel":   {"top": "#caa46f", "front": "#b18b56", "side": "#8a6a3d"},
        "desk":    {"top": "#dfba85", "front": "#c79e63", "side": "#9c7846"},
    }
    pal = palettes[palette]
    polys = []
    def poly(pts, fill):
        coords = ' '.join(f'{p[0]:.1f},{p[1]:.1f}' for p in pts)
        return f'<polygon points="{coords}" fill="{fill}" stroke="#3a2a18" stroke-width="0.4" stroke-linejoin="round"/>'
    # Draw order: back-facing first (none visible here), then 3 visible faces.
    # TOP last so it's clearly seen above:
    polys.append(poly([c['flb'], c['frb'], c['frt'], c['flt']], pal["front"]))
    polys.append(poly([c['frb'], c['brb'], c['brt'], c['frt']], pal["side"]))
    polys.append(poly([c['flt'], c['frt'], c['brt'], c['blt']], pal["top"]))
    return polys


def line3d(p1, p2, ox, oy, color="#5a3a1a", width=4):
    a = P(*p1, ox, oy)
    b = P(*p2, ox, oy)
    return f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}" stroke="{color}" stroke-width="{width}" stroke-linecap="round"/>'


def text3d(x, y, z, ox, oy, text, anchor="start", size=10, dy=0, dx=0, color="#222", weight="normal"):
    a = P(x, y, z, ox, oy)
    return (f'<text x="{a[0]+dx:.1f}" y="{a[1]+dy:.1f}" text-anchor="{anchor}" '
            f'font-size="{size}" fill="{color}" font-weight="{weight}">{text}</text>')


def build_bed(ox, oy, height, sommier, with_desk=False, label="Lit"):
    """Build SVG for one bed at (ox, oy)."""
    W = 2080  # length along X (long axis)
    D = 1100  # depth along Y (short axis)
    POST_X = 76       # post width along X (2 x 2x4 face-to-face -> 76 mm)
    POST_Y = 89       # post depth along Y (2x4 is 89 mm)
    RAIL_T = 38       # 2x4 thickness (on edge)
    RAIL_H = 89       # 2x4 height (on edge)
    H = height
    Z_S = sommier     # top of slats / longeron level (slat top here)
    Z_GC = H          # top of garde-corps frame

    parts = []

    # --- 4 posts ---
    posts = [
        (0,      0,        0, POST_X,      POST_Y,    H),  # FL
        (W-POST_X, 0,      0, W,           POST_Y,    H),  # FR
        (0,      D-POST_Y, 0, POST_X,      D,         H),  # BL
        (W-POST_X, D-POST_Y, 0, W,         D,         H),  # BR
    ]

    # --- Sommier frame (2x4 on edge, top at Z_S) ---
    z_long_bot = Z_S - RAIL_H
    front_longeron = (POST_X,        POST_Y - RAIL_T, z_long_bot, W - POST_X, POST_Y,         Z_S)
    back_longeron  = (POST_X,        D - POST_Y,       z_long_bot, W - POST_X, D - POST_Y + RAIL_T, Z_S)
    left_traverse  = (POST_X - RAIL_T, POST_Y,          z_long_bot, POST_X,    D - POST_Y,    Z_S)
    right_traverse = (W - POST_X,    POST_Y,          z_long_bot, W - POST_X + RAIL_T, D - POST_Y, Z_S)

    # --- Top frame (garde-corps haut, 2x4 on edge, top at Z_GC) ---
    z_top_bot = Z_GC - RAIL_H
    front_top = (POST_X, POST_Y - RAIL_T, z_top_bot, W - POST_X, POST_Y, Z_GC)
    back_top  = (POST_X, D - POST_Y,       z_top_bot, W - POST_X, D - POST_Y + RAIL_T, Z_GC)
    left_top  = (POST_X - RAIL_T, POST_Y, z_top_bot, POST_X, D - POST_Y, Z_GC)
    right_top = (W - POST_X, POST_Y,       z_top_bot, W - POST_X + RAIL_T, D - POST_Y, Z_GC)

    # --- Low rails at head/foot (Z ~ 250) ---
    z_low = 250
    left_low  = (POST_X - RAIL_T, POST_Y, z_low - RAIL_H/2, POST_X, D - POST_Y, z_low + RAIL_H/2)
    right_low = (W - POST_X, POST_Y, z_low - RAIL_H/2, W - POST_X + RAIL_T, D - POST_Y, z_low + RAIL_H/2)

    # ============ DRAW ORDER: back-to-front for proper occlusion ============

    # 1. BACK posts (Y at back)
    parts += box(*posts[2], ox, oy)  # BL
    parts += box(*posts[3], ox, oy)  # BR

    # 2. Back longeron + back top rail
    parts += box(*back_longeron, ox, oy)
    parts += box(*back_top, ox, oy)

    # 3. Diagonal braces in HEAD and FOOT (2x4 on flat, drawn as thick line)
    # Distinct dark-red color so they read clearly against the pine.
    DIAG_COLOR = "#a23a1f"
    # Left end (head): from low-back to high-front under sommier level
    parts.append(line3d(
        (POST_X - RAIL_T/2, D - POST_Y, z_low + RAIL_H/2),
        (POST_X - RAIL_T/2, POST_Y, z_long_bot),
        ox, oy, color=DIAG_COLOR, width=8
    ))
    # Right end (foot): same diagonal direction
    parts.append(line3d(
        (W - POST_X + RAIL_T/2, D - POST_Y, z_low + RAIL_H/2),
        (W - POST_X + RAIL_T/2, POST_Y, z_long_bot),
        ox, oy, color=DIAG_COLOR, width=8
    ))

    # 4. Low rails at head/foot
    parts += box(*left_low, ox, oy)
    parts += box(*right_low, ox, oy)

    # 5. Balusters on BACK side (between Z_S and z_top_bot)
    # 27 mm wide balusters, gap ~70 mm
    bal_w = 27
    n_bal = 20
    avail = W - 2 * POST_X
    gap_b = (avail - n_bal * bal_w) / (n_bal + 1)
    for i in range(n_bal):
        xs = POST_X + gap_b * (i + 1) + bal_w * i
        parts += box(xs, D - POST_Y - 19, Z_S, xs + bal_w, D - POST_Y, z_top_bot, ox, oy, palette="pin-l")

    # 6. Balusters at head and foot (between low rail and top rail), for safety
    n_bb = 9
    for i in range(n_bb):
        gap_h = (D - 2 * POST_Y - n_bb * bal_w) / (n_bb + 1)
        ys = POST_Y + gap_h * (i + 1) + bal_w * i
        # Left end balusters
        parts += box(POST_X - 38, ys, z_low + RAIL_H/2, POST_X, ys + bal_w, z_top_bot, ox, oy, palette="pin-l")
        # Right end balusters
        parts += box(W - POST_X, ys, z_low + RAIL_H/2, W - POST_X + 38, ys + bal_w, z_top_bot, ox, oy, palette="pin-l")

    # 7. Slats (1x4 = 19x89, span Y across, top at Z_S)
    n_slats = 14
    slat_w = 89
    avail_s = W - 2 * POST_X
    gap_s = (avail_s - n_slats * slat_w) / (n_slats + 1)
    for i in range(n_slats):
        xs = POST_X + gap_s * (i + 1) + slat_w * i
        parts += box(xs, POST_Y, Z_S - 19, xs + slat_w, D - POST_Y, Z_S, ox, oy, palette="latte")

    # 8. Left traverse + left top traverse
    parts += box(*left_traverse, ox, oy)
    parts += box(*right_traverse, ox, oy)
    parts += box(*left_top, ox, oy)
    parts += box(*right_top, ox, oy)

    # 9. DESK and SHELVES (Lit 2 only) — placed under bed along BACK side
    if with_desk:
        # Plan de travail: L=1900, P=500, top at Z=680
        desk_top_z = 680
        desk_thk = 28
        desk = (POST_X + 30, D - POST_Y - 500, desk_top_z - desk_thk,
                W - POST_X - 30, D - POST_Y, desk_top_z)
        parts += box(*desk, ox, oy, palette="desk")
        # Étagères: L=1900, P=184, at Z=1050 and Z=1300
        shelf_thk = 19
        shelf_p = 184
        for sz in (1050, 1300):
            sh = (POST_X + 30, D - POST_Y - shelf_p, sz - shelf_thk,
                  W - POST_X - 30, D - POST_Y, sz)
            parts += box(*sh, ox, oy, palette="desk")

    # 10. FRONT posts (drawn last so they occlude properly)
    parts += box(*posts[0], ox, oy)
    parts += box(*posts[1], ox, oy)

    # 11. Front longeron + front top rail (after front posts? Actually they should be in front of post side faces — but boxes overlap; this works because longeron is between posts.)
    parts += box(*front_longeron, ox, oy)
    parts += box(*front_top, ox, oy)

    # 12. Ladder at FOOT end, leaning out from front
    # Ladder limons from floor (in front) up to sommier top
    ladder_offset_y = -180  # in front of bed
    ladder_x_high = W - 250
    ladder_x_low_outer = W - 50
    ladder_x_low_inner = W - 350
    ladder_top_z = Z_S + 30
    ladder_y_top = POST_Y - 30  # just at front face
    # Two limons (1x4 on flat, drawn as thick lines)
    parts.append(line3d(
        (ladder_x_low_outer, ladder_offset_y, 0),
        (ladder_x_high, ladder_y_top, ladder_top_z),
        ox, oy, color="#6f4622", width=7
    ))
    parts.append(line3d(
        (ladder_x_low_inner, ladder_offset_y, 0),
        (ladder_x_high - 100, ladder_y_top, ladder_top_z),
        ox, oy, color="#6f4622", width=7
    ))
    # Rungs
    n_rungs = 5
    for i in range(1, n_rungs + 1):
        t = i / (n_rungs + 1)
        xa = (1 - t) * ladder_x_low_outer + t * ladder_x_high
        xb = (1 - t) * ladder_x_low_inner + t * (ladder_x_high - 100)
        ya = (1 - t) * ladder_offset_y + t * ladder_y_top
        za = t * ladder_top_z
        parts.append(line3d((xa, ya, za), (xb, ya, za), ox, oy, color="#6f4622", width=4))

    # ============ DIMENSION LINES & LABELS ============

    labels = []

    # Total height label (right of bed)
    p_h_bot = P(W, 0, 0, ox, oy)
    p_h_top = P(W, 0, H, ox, oy)
    labels.append(f'<line x1="{p_h_bot[0]+45:.1f}" y1="{p_h_bot[1]:.1f}" x2="{p_h_top[0]+45:.1f}" y2="{p_h_top[1]:.1f}" stroke="#666" stroke-width="0.6"/>')
    labels.append(f'<line x1="{p_h_bot[0]+40:.1f}" y1="{p_h_bot[1]:.1f}" x2="{p_h_bot[0]+50:.1f}" y2="{p_h_bot[1]:.1f}" stroke="#666" stroke-width="0.6"/>')
    labels.append(f'<line x1="{p_h_top[0]+40:.1f}" y1="{p_h_top[1]:.1f}" x2="{p_h_top[0]+50:.1f}" y2="{p_h_top[1]:.1f}" stroke="#666" stroke-width="0.6"/>')
    mid_y = (p_h_bot[1] + p_h_top[1]) / 2
    labels.append(f'<text x="{p_h_bot[0]+55:.1f}" y="{mid_y:.1f}" font-size="11" fill="#444">{H} mm</text>')

    # Sommier height annotation
    p_s = P(W, 0, Z_S, ox, oy)
    labels.append(f'<line x1="{p_h_bot[0]+40:.1f}" y1="{p_s[1]:.1f}" x2="{p_h_bot[0]+50:.1f}" y2="{p_s[1]:.1f}" stroke="#666" stroke-width="0.6"/>')
    labels.append(f'<text x="{p_h_bot[0]+55:.1f}" y="{p_s[1]-3:.1f}" font-size="9" fill="#777">sommier {Z_S}</text>')

    # Length label (under bed)
    p_l_left = P(0, 0, 0, ox, oy)
    p_l_right = P(W, 0, 0, ox, oy)
    y_dim = max(p_l_left[1], p_l_right[1]) + 35
    labels.append(f'<line x1="{p_l_left[0]:.1f}" y1="{y_dim:.1f}" x2="{p_l_right[0]:.1f}" y2="{y_dim:.1f}" stroke="#666" stroke-width="0.6"/>')
    labels.append(f'<line x1="{p_l_left[0]:.1f}" y1="{y_dim-4:.1f}" x2="{p_l_left[0]:.1f}" y2="{y_dim+4:.1f}" stroke="#666" stroke-width="0.6"/>')
    labels.append(f'<line x1="{p_l_right[0]:.1f}" y1="{y_dim-4:.1f}" x2="{p_l_right[0]:.1f}" y2="{y_dim+4:.1f}" stroke="#666" stroke-width="0.6"/>')
    labels.append(f'<text x="{(p_l_left[0]+p_l_right[0])/2:.1f}" y="{y_dim+13:.1f}" text-anchor="middle" font-size="11" fill="#444">2080 mm (couchage 1900)</text>')

    # Depth label (back-right)
    p_d_front = P(W, 0, 0, ox, oy)
    p_d_back = P(W, D, 0, ox, oy)
    labels.append(f'<text x="{(p_d_front[0]+p_d_back[0])/2+15:.1f}" y="{(p_d_front[1]+p_d_back[1])/2+15:.1f}" font-size="10" fill="#444">1100 mm</text>')

    # Title
    pT = P(W/2, 0, H + 100, ox, oy)
    labels.append(f'<text x="{pT[0]:.1f}" y="{pT[1]:.1f}" text-anchor="middle" font-size="15" font-weight="bold" fill="#222">{label}</text>')

    # Component callouts: (X3d, Y3d, Z3d, label, anchor, dx_screen, dy_screen, leader_to)
    # leader_to is an optional (X,Y,Z) to draw a leader line from text to a 3D point
    callouts = [
        # Montant — label upper-left, leader to front-left post
        (-300,  POST_Y, H + 80,  "Montant\n2×(2×4) collés\n= 76 × 89 mm",
         "start", None),
        # Longeron — label below-right, leader to front longeron
        (W + 250, POST_Y, Z_S - 200,  "Longeron 2×4 sur chant",
         "start", (W*0.7, POST_Y, Z_S - RAIL_H/2)),
        # Lattes — label top-back-left
        (W*0.25, D, H + 250,  "Lattes 1×4 (×14)\nespacement ~40 mm",
         "start", (W*0.4, D/2, Z_S)),
        # Garde-corps — label upper-back-right
        (W + 250, D, H - 50,  "Garde-corps haut +\nbalustres 1×4 (&lt; 75 mm)",
         "start", (W*0.7, D - POST_Y, H - RAIL_H/2)),
        # Diagonale — label below front, leader to diagonal
        (W*0.25,  -250, 100, "Diagonale 2×4 anti-basculement\n(dans tête + pied)",
         "start", (POST_X, (POST_Y + D - POST_Y)/2, (z_low + z_long_bot)/2)),
        # Échelle — label below-right
        (W + 250, -300, 200, "Échelle\nlimons + barreaux 1×4",
         "start", (W - 200, -90, 400)),
    ]
    if with_desk:
        callouts.append((W + 250, D - 250, 680,
                         "Plan de travail\n3×(1×8) collés chant\n500 × 1900 mm",
                         "start", (W - 400, D - 250, 680)))
        callouts.append((W + 250, D - 92, 1300,
                         "Étagère 1×8\n184 × 1900 mm",
                         "start", (W - 400, D - 92, 1300)))

    for X, Y, Z, txt, anc, leader_to in callouts:
        a = P(X, Y, Z, ox, oy)
        if leader_to is not None:
            b = P(*leader_to, ox, oy)
            labels.append(f'<line x1="{a[0]:.1f}" y1="{a[1]-3:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}" stroke="#888" stroke-width="0.5" stroke-dasharray="2,2"/>')
            labels.append(f'<circle cx="{b[0]:.1f}" cy="{b[1]:.1f}" r="2" fill="#555"/>')
        for i, line in enumerate(txt.split('\n')):
            labels.append(f'<text x="{a[0]:.1f}" y="{a[1] + i*12:.1f}" text-anchor="{anc}" font-size="11" fill="#1a1a1a">{line}</text>')

    # Floor line (subtle)
    floor_left = P(-80, -250, 0, ox, oy)
    floor_right = P(W + 80, D + 80, 0, ox, oy)
    floor = (f'<line x1="{floor_left[0]:.1f}" y1="{floor_left[1]:.1f}" '
             f'x2="{floor_right[0]:.1f}" y2="{floor_right[1]:.1f}" '
             f'stroke="#bbb" stroke-width="0.5" stroke-dasharray="4,3"/>')

    return [floor] + parts + labels


# ===== Build the full SVG =====

VW = 1900
VH = 820

svg = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {VW} {VH}" font-family="-apple-system, system-ui, sans-serif">']
svg.append(f'<rect width="{VW}" height="{VH}" fill="#fafaf6"/>')
svg.append(f'<text x="{VW/2}" y="35" text-anchor="middle" font-size="20" font-weight="bold" fill="#222">Lits mezzanines — couchage 90×190 — autoportants, charge enfant</text>')
svg.append(f'<text x="{VW/2}" y="58" text-anchor="middle" font-size="12" fill="#666">Pin massif 2×4 (38×89), 1×4 (19×89), 1×8 (19×184) — montage par boulons traversants M8 + barillet</text>')

# Bed 1: simple mezzanine
svg.extend(build_bed(ox=180, oy=600, height=1750, sommier=1300, with_desk=False,
                     label="LIT 1 — Mezzanine simple   H 175  /  sous-sommier 130"))

# Bed 2: combined with desk
svg.extend(build_bed(ox=1080, oy=640, height=1950, sommier=1500, with_desk=True,
                     label="LIT 2 — Mezzanine combiné   H 195  /  sous-sommier 150"))

# Legend (bottom-left)
LX, LY = 30, 720
svg.append(f'<g transform="translate({LX}, {LY})">')
svg.append('<rect x="0" y="0" width="290" height="86" fill="#fff" stroke="#bbb" rx="4"/>')
svg.append('<text x="10" y="18" font-size="11" font-weight="bold" fill="#333">Sections utilisées (pin massif)</text>')
svg.append('<rect x="10" y="28" width="60" height="14" fill="#d4a373" stroke="#3a2a18"/>')
svg.append('<text x="80" y="39" font-size="10" fill="#333">2×4  = 38 × 89 mm  (montants, longerons, traverses)</text>')
svg.append('<rect x="10" y="48" width="60" height="6" fill="#dcbb8a" stroke="#3a2a18"/>')
svg.append('<text x="80" y="55" font-size="10" fill="#333">1×4  = 19 × 89 mm  (lattes, balustres, échelle)</text>')
svg.append('<rect x="10" y="60" width="60" height="6" fill="#c79e63" stroke="#3a2a18"/>')
svg.append('<text x="80" y="67" font-size="10" fill="#333">1×8  = 19 × 184 mm  (plan travail, étagères)</text>')
svg.append('<line x1="10" y1="78" x2="40" y2="78" stroke="#a23a1f" stroke-width="6" stroke-linecap="round"/>')
svg.append('<text x="50" y="81" font-size="10" fill="#333">Diagonale anti-basculement (2×4 à plat)</text>')
svg.append('</g>')

# Safety note (bottom-right)
svg.append(f'<g transform="translate({VW - 490}, {LY})">')
svg.append('<rect x="0" y="0" width="460" height="86" fill="#fff5e6" stroke="#d4a373" rx="4"/>')
svg.append('<text x="10" y="18" font-size="11" font-weight="bold" fill="#8b4513">Anti-basculement (lit autoportant, sans fixation murale)</text>')
svg.append('<text x="10" y="35" font-size="10" fill="#333">• Montants doublés 2×(2×4) collés + vissés → 76 × 89 mm</text>')
svg.append('<text x="10" y="50" font-size="10" fill="#333">• Diagonale 2×4 dans chaque tête/pied (en rouge sur le visuel)</text>')
svg.append('<text x="10" y="65" font-size="10" fill="#333">• Cadre fermé tête/pied: traverse haute + sommier + basse</text>')
svg.append('<text x="10" y="80" font-size="10" fill="#333">• Connexion par boulons traversants M8 + barillet à chaque jonction</text>')
svg.append('</g>')

svg.append('</svg>')

OUT = "/home/user/delsoltahiti/visuel-lits.svg"
with open(OUT, "w", encoding="utf-8") as f:
    f.write('\n'.join(svg))

print(f"Wrote {OUT}")
print(f"Size: {len(open(OUT).read())} chars")

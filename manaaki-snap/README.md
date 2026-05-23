# 👻 Le Jeu Magique des Memories

**Le jeu d'anniversaire pour les 11 ans de Manaaki — thème jaune/ghost/photo**

Mix escape game + chasse au trésor + cérémonie, sur un thème inspiré par
l'univers des filtres photo et des stories. Pour 6 à 12 enfants, durée ~1h30.

---

## 🎯 Concept

Un fantôme farceur, **Le Ghoster Anonyme**, a chipé les 5 Memories préférées de
Manaaki. Avec ses amis répartis en 4 Teams (Ghost 👻, Streak 🔥, Story 🌈,
Map 📍), Manaaki doit récupérer les Memories en résolvant 5 épreuves, puis
publier la Story Finale qui révèle la cachette du vrai trésor.

---

## 🚀 Démarrage en 3 étapes

### 1. Ouvrir le jeu

Double-clique sur `index.html` ou ouvre dans un navigateur :
```
manaaki-snap/index.html
```

Fonctionne en local, sans serveur, sans Internet. Tablette, ordi, téléphone : tout marche.

### 2. Personnaliser le trésor final

Ouvre `config.js` et modifie les **5 mots-clés** pour qu'ils forment
une phrase indiquant où tu vas cacher le vrai trésor.

```js
motsDuSortilege: {
  filtres:    "CHERCHE",
  snapcodes:  "LE",
  hashtags:   "COFFRE",
  quiz:       "DANS",
  story:      "LA_CUISINE"   // _ = espace
}
```

→ Story finale révélée : **CHERCHE LE COFFRE DANS LA CUISINE**

⚠️ **N'oublie pas de cacher physiquement le trésor à cet endroit !**

### 3. Imprimer le kit

Ouvre `print/index.html` pour accéder à tous les documents imprimables :

| Doc | Quand | Combien |
|---|---|---|
| **Guide de l'animateur** | À lire AVANT la fête | 1 |
| Invitation | 1-2 semaines avant | 1 par invité |
| Badges des 4 Teams | Le jour J, en accueil | 1 par enfant |
| 5 indices papier | Cachés dans la maison | 1 jeu complet |
| Diplômes | Cérémonie finale | 1 par enfant |

---

## 📂 Structure du projet

```
manaaki-snap/
├── index.html              ← Page d'accueil (intro + choix de Team)
├── dashboard.html          ← Mon Profil (liste des 5 épreuves)
├── config.js               ← À personnaliser (mots-clés de la Story Finale)
├── app.js                  ← Logique partagée (teams, progression)
├── styles.css              ← Style « jaune ghost / cartes modernes »
│
├── epreuves/
│   ├── filtres.html        ← Épreuve 1 : associer filtres et effets
│   ├── snapcodes.html      ← Épreuve 2 : déchiffrer un code emoji
│   ├── hashtags.html       ← Épreuve 3 : reconstituer 3 hashtags
│   ├── quiz.html           ← Épreuve 4 : quiz emojis/filtres
│   ├── story.html          ← Épreuve 5 : remettre une story dans l'ordre
│   └── final.html          ← Story Finale : assembler les 5 mots
│
└── print/
    ├── index.html          ← Menu des documents imprimables
    ├── invitation.html     ← Invitation à la fête
    ├── badges-teams.html   ← Badges des 4 Teams (à découper)
    ├── snaps-indices.html  ← 5 indices papier (chasse au trésor)
    ├── diplomes.html       ← Diplôme de Maître des Memories
    └── guide-animateur.html← Guide complet pour toi
```

---

## 🎮 Déroulement type de la fête

1. **Accueil** (10 min) — chaque enfant reçoit son badge de Team
2. **Briefing théâtral** (5 min) — l'histoire du Ghoster Anonyme
3. **Chasse aux indices** (15 min) — suivre les 5 indices jusqu'à la tablette
4. **Les 5 épreuves sur écran** (45 min) — teams en parallèle
5. **Story Finale** (5 min) — révélation et course au trésor
6. **Cérémonie des diplômes** (5 min) — photo de groupe et gâteau

→ **Détail complet dans `print/guide-animateur.html`.**

---

## 🔧 Personnalisations possibles

- **Mots-clés de la Story Finale** → `config.js`
- **Devinettes des indices** (adapter à TA maison) → `print/snaps-indices.html`
- **Date / lieu / horaires de l'invitation** → `print/invitation.html` (éditable au survol)
- **Le héros n'est pas Manaaki ?** → `config.js`, champ `prenomHeros`

---

## 💡 Astuces

- **Plusieurs teams** → 1 tablette/téléphone par team, chacune crée son équipe à part.
- **Recommencer** → lien « Tout recommencer » en bas du Profil.
- **Bloqué sur une épreuve** → toutes les solutions sont dans le guide animateur.
- **Pas de wifi** → aucun problème, le jeu est 100% local (aucune connexion requise).

---

✨ Très belle fête à Manaaki et toute la bande ! ✨

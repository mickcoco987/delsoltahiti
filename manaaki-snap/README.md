# 🪄 L'Académie des Sorciers de Tahiti

**Le jeu d'anniversaire magique pour les 11 ans de Manaaki**

Mix escape game + chasse au trésor + cérémonie de sorciers, sur le thème
Harry Potter à la sauce polynésienne. Pour 6 à 12 enfants, durée ~1h30.

---

## 🎯 Concept

Manaaki vient d'avoir **11 ans**, l'âge où la magie s'éveille (clin d'œil HP).
Le sorcier maléfique **Taʻaroa l'Ombre** a volé les 5 pages du Grimoire Sacré.
Avec ses amis répartis dans 4 Maisons (Lava 🌋, Lagon 🌊, Forêt 🌴, Étoile ⭐),
Manaaki doit reconstituer le Grimoire en résolvant 5 épreuves, puis lancer le
sortilège final qui révèle la cachette du vrai trésor.

---

## 🚀 Démarrage en 3 étapes

### 1. Ouvrir le jeu

Double-clique sur `index.html` ou ouvre dans un navigateur :
```
manaaki-magic/index.html
```

Fonctionne en local, sans serveur, sans Internet. Tablette, ordi, téléphone : tout marche.

### 2. Personnaliser le trésor final

Ouvre `config.js` et modifie les **5 mots magiques** pour qu'ils forment
une phrase indiquant où tu vas cacher le vrai trésor.

```js
motsDuSortilege: {
  potions:      "CHERCHE",
  runes:        "LE",
  sortileges:   "COFFRE",
  bestiaire:    "DANS",
  constellation:"LA_CUISINE"   // _ = espace
}
```

→ phrase finale dévoilée : **CHERCHE LE COFFRE DANS LA CUISINE**

⚠️ **N'oublie pas de cacher physiquement le trésor à cet endroit !**

### 3. Imprimer le kit

Ouvre `print/index.html` pour accéder à tous les documents imprimables :

| Doc | Quand | Combien |
|---|---|---|
| **Guide de l'animateur** | À lire AVANT la fête | 1 |
| Invitation | 1-2 semaines avant | 1 par invité |
| Insignes des 4 Maisons | Le jour J, en accueil | 1 par enfant |
| 5 parchemins indices | Cachés dans la maison | 1 jeu complet |
| Diplômes de Sorcier | Cérémonie finale | 1 par enfant |

---

## 📂 Structure du projet

```
manaaki-magic/
├── index.html              ← Page d'accueil (lettre + cérémonie du Choixpeau)
├── dashboard.html          ← Liste des 5 épreuves (le Grimoire)
├── config.js               ← À personnaliser (mots du sortilège final)
├── app.js                  ← Logique partagée (équipes, progression)
├── styles.css              ← Style « parchemin / nuit étoilée »
│
├── epreuves/
│   ├── potions.html        ← Épreuve 1 : associer ingrédients/effets
│   ├── runes.html          ← Épreuve 2 : déchiffrer un code runique
│   ├── sortileges.html     ← Épreuve 3 : 3 anagrammes magiques
│   ├── bestiaire.html      ← Épreuve 4 : quiz créatures magiques
│   ├── constellation.html  ← Épreuve 5 : énigme logique (ordre des étoiles)
│   └── final.html          ← Reconstituer la phrase finale
│
└── print/
    ├── index.html          ← Menu des documents imprimables
    ├── invitation.html     ← Lettre d'admission
    ├── badges-maisons.html ← Insignes des 4 Maisons (à découper)
    ├── parchemins.html     ← 5 parchemins indices (chasse au trésor)
    ├── diplomes.html       ← Diplôme de Sorcier
    └── guide-animateur.html← Guide complet pour toi
```

---

## 🎮 Déroulement type de la fête

1. **Accueil** (10 min) — chaque enfant reçoit son insigne de Maison
2. **Briefing théâtral** (5 min) — l'histoire de Taʻaroa l'Ombre
3. **Chasse aux parchemins** (15 min) — suivre les 5 parchemins jusqu'à la tablette
4. **Les 5 épreuves sur écran** (45 min) — équipes en parallèle
5. **Sortilège final** (5 min) — révélation et course au trésor
6. **Cérémonie des diplômes** (5 min) — photo de groupe et gâteau

→ **Détail complet dans `print/guide-animateur.html`.**

---

## 🔧 Personnalisations possibles

- **Mots du sortilège final** → `config.js`
- **Énigmes des parchemins** (adapter à TA maison) → `print/parchemins.html`
- **Date / lieu / horaires de l'invitation** → `print/invitation.html` (éditable au survol)
- **Le héros n'est pas Manaaki ?** → `config.js`, champ `prenomHeros`

---

## 💡 Astuces

- **Plusieurs équipes** → 1 tablette/téléphone par équipe, chacune crée son équipe à part.
- **Recommencer** → lien « Tout recommencer » en bas du Grimoire.
- **Bloqué sur une épreuve** → toutes les solutions sont dans le guide animateur.
- **Pas de wifi** → aucun problème, le jeu est 100% local (aucune connexion requise).

---

✨ Très belle fête à Manaaki et toute la bande ! ✨

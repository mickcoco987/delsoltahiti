// ===========================================================
// CONFIGURATION DU JEU - À PERSONNALISER PAR L'ANIMATEUR
// ===========================================================
// Modifie ces valeurs avant la fête pour personnaliser le jeu.

window.MANAAKI_CONFIG = {

  // Prénom du héros (Manaaki)
  prenomHeros: "Manaaki",

  // Âge
  age: 11,

  // Date de la fête (pour la lettre d'admission)
  dateFete: "le jour de tes 11 ans",

  // -----------------------------------------------------------
  // LE SORTILÈGE FINAL
  // -----------------------------------------------------------
  // Les 5 épreuves donnent chacune un mot. Ensemble ils forment
  // une phrase qui indique où le vrai trésor est caché.
  //
  // À TOI DE CACHER LE TRÉSOR à l'endroit indiqué !
  // Remplace les mots ci-dessous pour pointer vers ta cachette.
  // -----------------------------------------------------------
  motsDuSortilege: {
    potions:      "CHERCHE",       // Épreuve 1
    runes:        "LE",            // Épreuve 2
    sortileges:   "COFFRE",        // Épreuve 3
    bestiaire:    "DANS",          // Épreuve 4
    constellation:"LA_CUISINE"     // Épreuve 5 (souligne les espaces avec _)
  },

  // Phrase finale d'introduction (avant les mots)
  phraseFinale: "Le secret est révélé... Le grimoire vous murmure :",

  // -----------------------------------------------------------
  // OPTION : indice bonus si les enfants bloquent
  // -----------------------------------------------------------
  indiceBonusFinal: "Regarde bien autour de toi... un meuble où l'on cuisine !"
};

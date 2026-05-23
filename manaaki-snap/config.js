// ===========================================================
// CONFIGURATION DU JEU - À PERSONNALISER PAR L'ANIMATEUR
// ===========================================================
// Modifie ces valeurs avant la fête pour personnaliser le jeu.

window.MANAAKI_CONFIG = {

  // Prénom du héros (Manaaki)
  prenomHeros: "Manaaki",

  // Âge
  age: 11,

  // Date de la fête (pour l'invitation)
  dateFete: "le jour de tes 11 ans",

  // -----------------------------------------------------------
  // LA STORY FINALE
  // -----------------------------------------------------------
  // Les 5 épreuves donnent chacune un mot. Ensemble ils forment
  // une story (phrase) qui indique où le vrai trésor est caché.
  //
  // À TOI DE CACHER LE TRÉSOR à l'endroit indiqué !
  // Remplace les mots ci-dessous pour pointer vers ta cachette.
  // -----------------------------------------------------------
  motsDuSortilege: {
    filtres:    "CHERCHE",       // Épreuve 1
    snapcodes:  "LE",            // Épreuve 2
    hashtags:   "COFFRE",        // Épreuve 3
    quiz:       "DANS",          // Épreuve 4
    story:      "LA_CUISINE"     // Épreuve 5 (souligne les espaces avec _)
  },

  // Phrase d'intro avant la révélation
  phraseFinale: "Ta Story est complète... Les 5 Memories te révèlent :",

  // -----------------------------------------------------------
  // OPTION : indice bonus si les enfants bloquent
  // -----------------------------------------------------------
  indiceBonusFinal: "Regarde bien autour de toi... un endroit où l'on cuisine !"
};

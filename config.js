/* Configuration du tableau de bord — modifiable a la main. */
window.COTE_CONFIG = {
  // URL du Worker Cloudflare qui declenche le scrape et accepte les
  // ajouts de modeles depuis l'UI.
  //
  // Resolution effective (cf. getApiBase() dans app.js) :
  // - Si on est servi par le Worker lui-meme (workers.dev / localhost),
  //   on utilise systematiquement window.location.origin : la preview
  //   appelle sa propre preview, pas de CORS, pas de desynchro.
  // - Sinon (GitHub Pages, Cloudflare Pages separe, domaine custom),
  //   on utilise cette URL explicite.
  // - Mettre a null pour desactiver completement le bouton de mise a
  //   jour ET masquer la card "+ Ajouter une voiture".
  updateEndpoint: "https://delsoltahiti-update.mickael-cohen.workers.dev",
};

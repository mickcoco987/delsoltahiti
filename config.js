/* Configuration du tableau de bord — modifiable a la main. */
window.COTE_CONFIG = {
  // URL publique du Worker Cloudflare qui declenche la mise a jour
  // et accepte les ajouts de modeles personnalises.
  //
  // - Si le dashboard et le Worker partagent le meme domaine (cas par
  //   defaut avec Cloudflare Workers Static Assets), laisser cette
  //   valeur a "" : les requetes utiliseront window.location.origin.
  //   Avantage : les previews appellent leur propre Worker, plus de
  //   CORS, plus de risque de version desynchronisee.
  // - Si le dashboard est servi par un autre projet (Pages, GitHub
  //   Pages, etc.), mettre l'URL complete du Worker
  //   ("https://mon-worker.workers.dev").
  // - Laisser a "" pour desactiver completement le bouton de
  //   mise a jour ET masquer la card "+ Ajouter une voiture".
  updateEndpoint: "",
};

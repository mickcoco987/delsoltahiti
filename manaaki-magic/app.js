// ===========================================================
// L'Académie des Sorciers de Tahiti
// Logique partagée : équipes, progression, navigation
// ===========================================================

(function() {
  'use strict';

  const STORAGE_KEY = 'manaaki-magic-v1';

  // -------------------------------------------------------
  // Maisons
  // -------------------------------------------------------
  const MAISONS = {
    lava:   { nom: 'Lava',   emoji: '🌋', devise: 'Courage et feu',     couleur: '#c62828' },
    lagon:  { nom: 'Lagon',  emoji: '🌊', devise: 'Sagesse et calme',   couleur: '#0288d1' },
    foret:  { nom: 'Forêt',  emoji: '🌴', devise: 'Loyauté et patience',couleur: '#2e7d32' },
    etoile: { nom: 'Étoile', emoji: '⭐', devise: 'Ruse et lumière',    couleur: '#f9a825' }
  };

  // -------------------------------------------------------
  // Épreuves
  // -------------------------------------------------------
  const EPREUVES = [
    { id: 'potions',       num: 1, titre: 'La Salle des Potions',    emoji: '🧪', fichier: 'epreuves/potions.html' },
    { id: 'runes',         num: 2, titre: 'Les Runes Anciennes',     emoji: '📜', fichier: 'epreuves/runes.html' },
    { id: 'sortileges',    num: 3, titre: 'Le Sortilège Oublié',     emoji: '✨', fichier: 'epreuves/sortileges.html' },
    { id: 'bestiaire',     num: 4, titre: 'Le Bestiaire Magique',    emoji: '🐉', fichier: 'epreuves/bestiaire.html' },
    { id: 'constellation', num: 5, titre: 'La Constellation Perdue', emoji: '🌟', fichier: 'epreuves/constellation.html' }
  ];

  // -------------------------------------------------------
  // État
  // -------------------------------------------------------
  function getEtat() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return etatVide();
      const parsed = JSON.parse(raw);
      // Garantit la structure
      return Object.assign(etatVide(), parsed);
    } catch (e) {
      return etatVide();
    }
  }

  function etatVide() {
    return {
      equipeNom: null,
      maison: null,           // 'lava' | 'lagon' | 'foret' | 'etoile'
      sorciers: [],           // liste des prénoms
      epreuvesGagnees: {},    // { potions: true, runes: true, ... }
      finalReussi: false
    };
  }

  function setEtat(etat) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(etat));
  }

  function resetEtat() {
    localStorage.removeItem(STORAGE_KEY);
  }

  // -------------------------------------------------------
  // Helpers navigation
  // -------------------------------------------------------
  function go(path) {
    window.location.href = path;
  }

  function isInSubdir() {
    return window.location.pathname.includes('/epreuves/');
  }

  function prefixe(path) {
    return isInSubdir() ? '../' + path : path;
  }

  // -------------------------------------------------------
  // Bandeau équipe
  // -------------------------------------------------------
  function renderBandeau() {
    const etat = getEtat();
    if (!etat.equipeNom || !etat.maison) return;
    const elt = document.getElementById('bandeau-equipe');
    if (!elt) return;
    const maison = MAISONS[etat.maison];
    elt.innerHTML = `
      <span>${maison.emoji} <span class="equipe-nom">${etat.equipeNom}</span></span>
      <span>Maison ${maison.nom}</span>
      <a href="${prefixe('dashboard.html')}" class="btn btn-secondary" style="padding:0.3rem 0.8rem;font-size:0.85rem;">📖 Grimoire</a>
    `;
    elt.style.display = 'flex';
  }

  // -------------------------------------------------------
  // Progression (pages du grimoire)
  // -------------------------------------------------------
  function renderProgression(targetId) {
    const etat = getEtat();
    const cible = document.getElementById(targetId);
    if (!cible) return;
    cible.innerHTML = EPREUVES.map(ep => {
      const gagnee = etat.epreuvesGagnees[ep.id];
      return `<div class="page-grimoire ${gagnee ? 'gagnee' : ''}" title="${ep.titre}">${gagnee ? ep.emoji : '?'}</div>`;
    }).join('');
  }

  // -------------------------------------------------------
  // Marquer une épreuve gagnée
  // -------------------------------------------------------
  function marquerGagnee(epreuveId) {
    const etat = getEtat();
    etat.epreuvesGagnees[epreuveId] = true;
    setEtat(etat);
  }

  // -------------------------------------------------------
  // Affichage du mot magique gagné
  // -------------------------------------------------------
  function afficherMotGagne(epreuveId, conteneurId) {
    const config = window.MANAAKI_CONFIG;
    const mot = (config && config.motsDuSortilege && config.motsDuSortilege[epreuveId]) || '???';
    const cible = document.getElementById(conteneurId);
    if (!cible) return;

    const ep = EPREUVES.find(e => e.id === epreuveId);
    const motAffiche = mot.replace(/_/g, ' ');

    cible.innerHTML = `
      <div class="victoire">
        <h2>${ep.emoji} Épreuve réussie !</h2>
        <p>Une page du Grimoire vient d'être restaurée.<br>
        Le mot magique que tu viens de gagner est :</p>
        <div class="mot-magique">${motAffiche}</div>
        <p style="font-style:italic;font-size:0.95rem;">Note-le bien sur ton parchemin ! Tu en auras besoin à la fin.</p>
        <div class="btn-row">
          <a href="${prefixe('dashboard.html')}" class="btn">📖 Retour au Grimoire</a>
        </div>
      </div>
    `;
  }

  // -------------------------------------------------------
  // API publique
  // -------------------------------------------------------
  window.MM = {
    MAISONS,
    EPREUVES,
    getEtat,
    setEtat,
    resetEtat,
    go,
    prefixe,
    renderBandeau,
    renderProgression,
    marquerGagnee,
    afficherMotGagne
  };

  // -------------------------------------------------------
  // Auto-init
  // -------------------------------------------------------
  document.addEventListener('DOMContentLoaded', function() {
    renderBandeau();
    renderProgression('progression');
  });

})();

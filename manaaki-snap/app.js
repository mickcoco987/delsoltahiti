// ===========================================================
// Snap Academy — L'anniversaire de Manaaki
// Logique partagée : équipes, progression, navigation
// ===========================================================

(function() {
  'use strict';

  const STORAGE_KEY = 'manaaki-snap-v1';

  // -------------------------------------------------------
  // Teams (équipes)
  // -------------------------------------------------------
  const TEAMS = {
    ghost:  { nom: 'Ghost',  emoji: '👻', devise: 'Discrets comme un fantôme', couleur: '#FFFC00' },
    streak: { nom: 'Streak', emoji: '🔥', devise: 'Ardents comme une flamme',  couleur: '#FF6B35' },
    story:  { nom: 'Story',  emoji: '🌈', devise: 'Une histoire à raconter',   couleur: '#A569BD' },
    map:    { nom: 'Map',    emoji: '📍', devise: 'Toujours là où ça compte',  couleur: '#00BCD4' }
  };

  // -------------------------------------------------------
  // Épreuves
  // -------------------------------------------------------
  const EPREUVES = [
    { id: 'filtres',   num: 1, titre: 'Les Filtres Magiques',  emoji: '🎭', fichier: 'epreuves/filtres.html' },
    { id: 'snapcodes', num: 2, titre: 'Le Snap Code Secret',   emoji: '👻', fichier: 'epreuves/snapcodes.html' },
    { id: 'hashtags',  num: 3, titre: 'Les Hashtags Brisés',   emoji: '#️⃣', fichier: 'epreuves/hashtags.html' },
    { id: 'quiz',      num: 4, titre: 'Le Quiz des Lenses',    emoji: '📸', fichier: 'epreuves/quiz.html' },
    { id: 'story',     num: 5, titre: 'La Story Mélangée',     emoji: '🌈', fichier: 'epreuves/story.html' }
  ];

  // -------------------------------------------------------
  // État
  // -------------------------------------------------------
  function getEtat() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return etatVide();
      const parsed = JSON.parse(raw);
      return Object.assign(etatVide(), parsed);
    } catch (e) {
      return etatVide();
    }
  }

  function etatVide() {
    return {
      equipeNom: null,
      team: null,             // 'ghost' | 'streak' | 'story' | 'map'
      snappers: [],           // liste des prénoms
      epreuvesGagnees: {},    // { filtres: true, snapcodes: true, ... }
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
    if (!etat.equipeNom || !etat.team) return;
    const elt = document.getElementById('bandeau-equipe');
    if (!elt) return;
    const team = TEAMS[etat.team];
    elt.innerHTML = `
      <span>${team.emoji} <span class="equipe-nom">${etat.equipeNom}</span></span>
      <span>Team ${team.nom}</span>
      <a href="${prefixe('dashboard.html')}" class="btn btn-secondary" style="padding:0.3rem 0.8rem;font-size:0.85rem;">📱 Mon Profil</a>
    `;
    elt.style.display = 'flex';
  }

  // -------------------------------------------------------
  // Progression (Memories restaurées)
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
  // Affichage du mot-clé gagné
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
        <h2>${ep.emoji} Memory restaurée !</h2>
        <p>Une Memory du profil vient d'être récupérée.<br>
        Le mot-clé caché dans cette Memory est :</p>
        <div class="mot-magique">${motAffiche}</div>
        <p style="font-style:italic;font-size:0.95rem;">Note-le bien ! Tu en auras besoin pour la Story Finale.</p>
        <div class="btn-row">
          <a href="${prefixe('dashboard.html')}" class="btn">📱 Retour au Profil</a>
        </div>
      </div>
    `;
  }

  // -------------------------------------------------------
  // API publique
  // -------------------------------------------------------
  window.MM = {
    TEAMS,
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

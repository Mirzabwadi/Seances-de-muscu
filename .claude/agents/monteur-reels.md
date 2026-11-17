---
name: monteur-reels
description: Monte une vidéo face caméra en Reel Instagram vertical 1080x1920 avec HyperFrames, en suivant la méthode du skill reel-philo — conversion HDR, choix des prises, sous-titres mot par mot, fond détouré, générique, plan final, musique, rendu. À utiliser quand l'utilisateur envoie une nouvelle vidéo à monter ou demande une retouche d'un Reel existant.
---

Tu es le monteur des Reels de l'utilisateur. Commence par lire `.claude/skills/reel-philo/SKILL.md`
et suis-le étape par étape ; le projet `socrate/` est la référence à copier pour un nouveau sujet.

## Règles

- **Langue : les vidéos de l'utilisateur sont en kabyle.** Tout le texte à l'écran (titre,
  chapitres, cartes de citation, chiffres clés, logo, appel à commenter) doit être en kabyle,
  avec les polices de `tools/reels/fonts-kab/`. N'écris jamais de kabyle toi-même : demande à
  l'utilisateur la liste exacte des textes à traduire avant le rendu, et garde ses
  traductions telles quelles.

- Lance toutes les commandes `hyperframes` avec `NODE_USE_ENV_PROXY=1`.
- Le détourage est l'étape la plus longue (≈19 min par minute de vidéo) : lance-le en arrière-plan
  dès que le montage brut est validé, et prépare le reste pendant ce temps.
- Après chaque coupe, retranscris le montage avec Whisper et relis-le : aucune répétition, aucun mot
  parasite, aucun mot coupé.
- Avant le rendu : `hyperframes check` à 0 erreur, puis des captures (`hyperframes snapshot`) du
  générique, de chaque fond, d'un sous-titre long et du plan final, que tu regardes vraiment.
- Après le rendu : version Instagram (~30 Mo, ≈ -15 LUFS), quelques images extraites du fichier
  final pour vérifier, puis envoi du fichier.
- Commite et pousse le projet, jamais la vidéo source, la silhouette détourée, les rendus ni
  `.transcode-cache/`.

## Ce que tu rends

**À chaque vidéo, sans qu'on le demande : le post de publication**, prêt à copier-coller
pour TikTok et Instagram — une accroche, deux ou trois lignes sur le sujet, la question
finale pour faire commenter, les crédits des images, puis les hashtags (3 à 5 pour TikTok,
8 à 12 pour Instagram). Pour une vidéo en kabyle, reprends les phrases kabyles de
l'utilisateur telles qu'il les a écrites (titre, question finale) plutôt que d'en inventer,
et complète en français. Ne relance pas le rendu pour livrer le post.


Le chemin du MP4 Instagram, ce qui a été coupé et pourquoi, les corrections de sous-titres,
les crédits d'images, et ce que tu n'as pas pu vérifier (tu ne peux pas écouter le son).

---
name: audit-page
description: >
  Analyse une page web pour évaluer sa structure,
  son contenu, sa proposition de valeur et ses
  principaux appels à l'action, puis produire
  trois recommandations prioritaires.
version: 1.0.0
---

# Audit rapide d'une page web

## Quand utiliser cette skill

Utilise cette skill lorsqu'on te demande :

- d'analyser une page web ;
- d'effectuer un audit rapide d'une URL ;
- d'identifier les principaux problèmes d'une page ;
- de proposer des améliorations prioritaires.

## Procédure

1. Obtenir le contenu de la page.

   Si seule une URL est disponible,
   utiliser `fetch_url`.

2. Identifier :

   - le title ;
   - la meta description ;
   - le H1 ;
   - les principaux H2.

3. Comprendre :

   - le sujet de la page ;
   - la proposition de valeur ;
   - le public visé.

4. Identifier le CTA principal.

5. Relever les problèmes évidents :

   - structure ;
   - clarté ;
   - hiérarchie ;
   - répétitions ;
   - incohérences.

6. Produire :

   - un diagnostic court ;
   - les points positifs ;
   - les problèmes identifiés ;
   - exactement trois priorités.

## Pièges

- Ne pas inventer une information absente.
- Distinguer "absent" de "non vérifiable".
- Ne pas présenter cet audit rapide comme un audit SEO complet.

## Vérification

Avant de répondre, vérifier que :

- le title a été contrôlé ;
- le H1 a été contrôlé ;
- la structure principale a été analysée ;
- exactement trois priorités sont proposées.
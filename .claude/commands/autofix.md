---
description: Lance le cycle complet de test et correction automatique jusqu'au succès
argument-hint: [description de la feature ou bug]
allowed-tools: Bash(*), Read(*), Edit(*), Write(*)
---

## Ta mission

L'utilisateur vient de décrire une feature à implémenter ou un bug à corriger.

### Process complet

1. **Clarification**
   - Demander le résultat attendu précis
   - Exemple : "Quand j'appelle cette fonction avec X, je veux obtenir Y"

2. **Implémentation**
   - Utiliser le subagent `orchestrator`
   - Commande : "Use orchestrator subagent to implement: $ARGUMENTS"

3. **Boucle de validation** (automatique)
   - Test → Si échec → Debug → Correction → Re-test
   - Continuer jusqu'à succès
   - Maximum 10 itérations

4. **Rapport final**
   - Résumé des changements
   - Nombre d'itérations nécessaires
   - Confirmation du résultat attendu

### Exemple d'utilisation

Utilisateur : `/autofix Ajouter une validation d'email dans le formulaire`

Toi :
1. "Pour valider, quel résultat attendez-vous ? Par exemple : 'email@example.com' → valide, 'invalid' → erreur"
2. [Implémentation via orchestrator]
3. [Tests automatiques]
4. [Corrections si nécessaire]
5. "✅ Validation d'email implémentée et testée avec succès"

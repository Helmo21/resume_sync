---
description: Lance les tests et corrige automatiquement jusqu'à ce que tout passe
allowed-tools: Bash(*), Read(*), Edit(*), Write(*)
---

## Ta mission

Lancer un cycle de test/correction automatique sur le code existant.

### Process

1. **Exécuter les tests**
   ```
   Use tester subagent to run all tests
   ```

2. **Si échec détecté**
   ```
   Use debugger subagent to fix errors
   ```

3. **Re-test**
   ```
   Use tester subagent again
   ```

4. **Répéter jusqu'à succès**
   - Maximum 10 itérations
   - Logger chaque tentative

5. **Rapport final**
   - Nombre d'erreurs corrigées
   - Fichiers modifiés
   - Temps total

### Sortie

```
🔄 CYCLE TEST-FIX AUTOMATIQUE

Itération 1: ❌ 3 tests échoués → Corrections appliquées
Itération 2: ❌ 1 test échoué → Correction appliquée
Itération 3: ✅ Tous les tests passent

Résultat : SUCCESS
Durée : 3 itérations
Fichiers modifiés : src/utils.js, src/validation.js
```

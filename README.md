# Wooclap Bot 🤖

Trois scripts Python pour automatiser les réponses sur Wooclap.

---

## Fichiers

| Fichier | Usage |
|---|---|
| `get_credentials.py` | Récupère EVENT_ID et TOKEN via SSO et les injecte dans les scripts |
| `wooclap_bot.py` | Surveille en temps réel et répond aux questions imposées par le prof |
| `quizz_wooclap.py` | Répond d'un coup à tous les questionnaires en libre accès |

---

## Installation

```bash
# Pour les deux scripts principaux
pip install requests

# Uniquement pour wooclap_bot.py (fallback IA sur les questions en direct)
pip install google-genai

# Pour get_credentials.py (récupération automatique du token)
pip install playwright
playwright install chromium
```

---

## Démarrage rapide

### 1. Récupérer les credentials

```bash
python get_credentials.py
```

```
🔑 Wooclap Credential Fetcher

Event code (ex: BHJLED) : BHJLED

📡 Récupération de l'EVENT_ID...
  ✅ EVENT_ID : 695bcdd4b863...

🔐 Connexion SSO — Université d'Aix-Marseille
Identifiant AMU : prenom.nom@etu.univ-amu.fr
Mot de passe    : ********
  🌐 Ouverture de la page SSO...
  ✅ TOKEN récupéré
  🔄 Navigation vers /BHJLED...

📝 Mise à jour des scripts...
  ✅ quizz_wooclap.py mis à jour
  ✅ wooclap_bot.py mis à jour
```

`EVENT_CODE`, `EVENT_ID` et `TOKEN` sont injectés automatiquement dans les deux scripts. Rien à copier-coller.

> ⚠️ À relancer à chaque nouvelle session (TOKEN expiré → HTTP 401).

### 2. Lancer le bot voulu

```bash
python wooclap_bot.py     # questions en direct
python quizz_wooclap.py   # questionnaires libres
```

---

## Configuration manuelle (optionnel)

Si `get_credentials.py` ne fonctionne pas, remplir les variables en haut de chaque script :

### `quizz_wooclap.py`
```python
EVENT_CODE = "ABCDEF"
EVENT_ID   = "695bcdd4b863..."
TOKEN      = "750fd54ac2..."
```

### `wooclap_bot.py`
```python
GEMINI_API_KEY = "ta_clé_ici"   # aistudio.google.com → API Key
EVENT_CODE     = "ABCDEF"
TOKEN          = "750fd54ac2..."
```

**Trouver EVENT_ID manuellement** — DevTools → Network → requête `ABCDEF?isParticipant=true` → Response → champ `_id`

**Trouver TOKEN manuellement** — DevTools → Console :
```javascript
localStorage.getItem("token")
```

---

## Utilisation

### wooclap_bot.py — Questions en direct

Lance le script avant le cours et laisse-le tourner en fond.

```bash
python wooclap_bot.py
```

Il poll l'API toutes les 1.5s, détecte automatiquement chaque nouvelle question et soumet la réponse sans intervention.

```
🤖 Wooclap Bot démarré — événement: BHJLED
   Surveillance en cours... (Ctrl+C pour arrêter)

📋 [MCQ] Les premières utilisations de la cryptographie remontent à ?
   ✅ Réponse(s) directe(s): Jules César
   📤 Envoyée (direct) — HTTP 200
```

### quizz_wooclap.py — Questionnaires libres

Lance le script quand le questionnaire est disponible. Il répond à tout d'un coup.

```bash
python quizz_wooclap.py
```

```
🤖 Wooclap Quiz Bot — BHJLED
📚 4 questionnaire(s) trouvé(s)

==================================================
📖 Quiz module 3 : Les aspects réseau et applicatifs
   ✅ Disponible — 12 question(s)

   📋 La sécurité est au cœur de l'implémentation...
      ✅ [direct] Faux
      📤 HTTP 200
```

---

## Logique de réponse

### `quizz_wooclap.py`
- **Lecture directe uniquement** — Wooclap expose `isCorrect` dans ses données pour les questionnaires libres → réponse instantanée et 100% correcte
- Si `isCorrect` est absent → question ignorée

### `wooclap_bot.py`
1. **Lecture directe** — si `isCorrect` est visible → réponse instantanée
2. **Fallback Gemini** — si `isCorrect` est masqué → la question est envoyée à Gemini Flash pour analyse

---

## Dépannage

| Problème | Cause | Solution |
|---|---|---|
| HTTP 401 | Token expiré | Relancer `get_credentials.py` |
| HTTP 404 | Mauvais EVENT_ID | Relancer `get_credentials.py` |
| Redirection vers `/auth/profile` | Comportement SSO par défaut | Résolu automatiquement — le script navigue vers l'event après login |
| `⏸️ Question fermée` | Question déjà terminée | Normal, le bot attend la suivante |
| Timeout réseau | Wifi instable | Le bot retry automatiquement 3 fois |
| Timeout SSO | Page login lente | Relancer `get_credentials.py` |

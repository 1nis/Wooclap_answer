# Wooclap Bot 🤖

Deux scripts Python pour automatiser les réponses sur Wooclap.

---

## Fichiers

| Fichier | Usage |
|---|---|
| `wooclap_bot.py` | Surveille en temps réel et répond aux questions imposées par le prof |
| `quizz_wooclap.py` | Répond d'un coup à tous les questionnaires en libre accès |

---

## Installation

```bash
# Pour les deux scripts
pip install requests

# Uniquement pour wooclap_bot.py (fallback IA sur les questions en direct)
pip install google-genai

# Pour get_credentials.py (récupération automatique du token)
pip install playwright
playwright install chromium
```

---

## Configuration

### `quizz_wooclap.py`

```python
EVENT_CODE = "ABCDEF"            # dans l'URL : app.wooclap.com/ABCDEF
EVENT_ID   = "695bcdd4b863..."   # ID interne (voir ci-dessous)
TOKEN      = "750fd54ac2..."     # token de session (voir ci-dessous)
```

> Pas de clé API requise — les réponses correctes sont directement exposées par l'API Wooclap pour les questionnaires en accès libre.

### `wooclap_bot.py`

```python
GEMINI_API_KEY = "ta_clé_ici"       # aistudio.google.com → API Key
EVENT_CODE     = "ABCDEF"
TOKEN          = "750fd54ac2..."
```

### Trouver EVENT_ID et TOKEN

**Option rapide — `get_credentials.py`** (recommandé) :

```bash
python get_credentials.py
```

Entrez l'event code et vos identifiants AMU. Le script récupère `EVENT_ID` et `TOKEN` automatiquement via SSO.

**Option manuelle :**

**EVENT_ID** — DevTools → Network → requête `ABCDEF?isParticipant=true` → Response → champ `_id`

**TOKEN** — DevTools → Console → coller :
```javascript
localStorage.getItem("token")
```

> ⚠️ Le TOKEN change à chaque nouvelle session. À renouveler si le bot retourne HTTP 401.

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
- Si `isCorrect` est absent → question ignorée (cas non rencontré sur les questionnaires en accès libre)

### `wooclap_bot.py`
1. **Lecture directe** — si `isCorrect` est visible → réponse instantanée
2. **Fallback Gemini** — si `isCorrect` est masqué → la question est envoyée à Gemini Flash pour analyse

---

## Changer de Wooclap

À chaque nouvel événement, mettre à jour uniquement :

```python
EVENT_CODE = "NOUVEAUCODE"
EVENT_ID   = "nouvel_id_interne"
```

Le TOKEN reste valide tant que la session est active.

---

## Dépannage

| Problème | Cause | Solution |
|---|---|---|
| HTTP 401 | Token expiré | Récupérer un nouveau TOKEN |
| HTTP 404 | Mauvais EVENT_ID | Vérifier l'ID dans la Response DevTools |
| `⏸️ Question fermée` | Question déjà terminée | Normal, le bot attend la suivante |
| Timeout réseau | Wifi instable | Le bot retry automatiquement 3 fois |

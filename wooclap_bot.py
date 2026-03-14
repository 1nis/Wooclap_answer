import requests
import time
from google import genai

# ─────────────────────────────────────────────
# CONFIG — à modifier
# ─────────────────────────────────────────────
GEMINI_API_KEY = "API_KEY"
EVENT_CODE     = "EVENT_CODE"
TOKEN          = "TOKEN"
POLL_INTERVAL  = 1.5

# ─────────────────────────────────────────────
# INIT
# ─────────────────────────────────────────────
client   = genai.Client(api_key=GEMINI_API_KEY)
BASE_URL = "https://app.wooclap.com/api"
HEADERS  = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept":        "application/json",
    "Content-Type":  "application/json",
    "User-Agent":    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer":       f"https://app.wooclap.com/{EVENT_CODE}",
}

# ─────────────────────────────────────────────
# FONCTIONS
# ─────────────────────────────────────────────
def get_event_data():
    for attempt in range(3):
        try:
            r = requests.get(
                f"{BASE_URL}/events/{EVENT_CODE}?isParticipant=true&from=banner",
                headers=HEADERS, timeout=15
            )
            if r.status_code != 200:
                return None
            return r.json()
        except Exception as e:
            print(f"  [réseau tentative {attempt+1}/3] {e}")
            time.sleep(2)
    return None


def find_question_by_id(question_id, data):
    """Cherche dans questions[] ET questionnaires[].questions[]."""
    for q in data.get("questions", []):
        if q.get("_id") == question_id:
            return q
    for questionnaire in data.get("questionnaires", []):
        for q in questionnaire.get("questions", []):
            if q.get("_id") == question_id:
                return q
    return None


def get_correct_choice_ids(choices):
    """Retourne les IDs des bonnes réponses si isCorrect est disponible."""
    correct = [c.get("_id") for c in choices if c.get("isCorrect") is True]
    return correct


def pick_best_answer_gemini(question_text, choices):
    """Fallback Gemini si isCorrect n'est pas disponible."""
    choices_str = "\n".join([
        f"{i+1}. {c.get('choice', '?')}"
        for i, c in enumerate(choices)
    ])
    prompt = (
        f"Question: {question_text}\n\n"
        f"{choices_str}\n\n"
        f"Réponds UNIQUEMENT avec le numéro de la bonne réponse (ex: 2). Rien d'autre."
    )
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        idx = int(response.text.strip()) - 1
        return [choices[max(0, min(idx, len(choices) - 1))].get("_id")]
    except Exception as e:
        print(f"  [erreur Gemini] {e}")
        return [choices[0].get("_id")]


def submit_answer(question_id, choice_ids):
    """Soumet une ou plusieurs réponses."""
    try:
        # Essai avec choiceId (une réponse)
        payload = {"choiceId": choice_ids[0]} if len(choice_ids) == 1 else {"choiceIds": choice_ids}
        r = requests.post(
            f"{BASE_URL}/events/{EVENT_CODE}/questions/{question_id}/answers",
            json=payload,
            headers=HEADERS, timeout=15
        )
        return r.status_code
    except Exception as e:
        print(f"  [erreur submit] {e}")
        return None


# ─────────────────────────────────────────────
# BOUCLE PRINCIPALE
# ─────────────────────────────────────────────
def run():
    print(f"🤖 Wooclap Bot démarré — événement: {EVENT_CODE}")
    print("   Surveillance en cours... (Ctrl+C pour arrêter)\n")

    last_question_id = None

    while True:
        data = get_event_data()

        if not data:
            print("⏳ Erreur réseau...    ", end="\r")
            time.sleep(POLL_INTERVAL)
            continue

        selected_qid = data.get("selectedQuestion")

        if not selected_qid:
            print("⏳ Slide en cours...    ", end="\r")
            time.sleep(POLL_INTERVAL)
            continue

        if selected_qid == last_question_id:
            time.sleep(POLL_INTERVAL)
            continue

        question = find_question_by_id(selected_qid, data)

        if not question:
            print(f"  [info] Question {selected_qid} introuvable.")
            last_question_id = selected_qid
            time.sleep(POLL_INTERVAL)
            continue

        qtype   = question.get("__t", "unknown")
        qtext   = question.get("title") or "?"
        choices = question.get("choices", [])

        print(f"\n📋 [{qtype}] {qtext}")

        if not question.get("canAnswer", True):
            print(f"   ⏸️  Question fermée — ignorée.")
            last_question_id = selected_qid
            time.sleep(POLL_INTERVAL)
            continue

        if choices:
            # Essai lecture directe de isCorrect
            correct_ids = get_correct_choice_ids(choices)

            if correct_ids:
                labels = [c.get("choice", "?") for c in choices if c.get("_id") in correct_ids]
                print(f"   ✅ Réponse(s) directe(s): {', '.join(labels)}")
                source = "direct"
            else:
                # Fallback Gemini
                print("   🔍 isCorrect masqué — consultation Gemini...")
                correct_ids = pick_best_answer_gemini(qtext, choices)
                labels = [c.get("choice", "?") for c in choices if c.get("_id") in correct_ids]
                print(f"   ✅ Réponse Gemini: {', '.join(labels)}")
                source = "gemini"

            status = submit_answer(selected_qid, correct_ids)
            print(f"   📤 Envoyée ({source}) — HTTP {status}")

        else:
            print(f"   ⚠️  Pas de choix ({qtype}) — ignoré.")

        last_question_id = selected_qid
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        print("\n\n🛑 Bot arrêté.")
import requests
import time

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
EVENT_CODE     = "EVENT_CODE"
EVENT_ID       = "EVENT_ID"
TOKEN          = "TOKEN"
DELAY          = 1.0  # secondes entre chaque réponse (évite le spam)

# ─────────────────────────────────────────────
# INIT
# ─────────────────────────────────────────────
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
            if r.status_code == 200:
                return r.json()
        except Exception as e:
            print(f"  [réseau tentative {attempt+1}/3] {e}")
            time.sleep(2)
    return None


def get_correct_choice_ids(choices):
    """Retourne les IDs corrects si isCorrect est visible."""
    return [c.get("_id") for c in choices if c.get("isCorrect") is True]


def submit_answer(question_id, choice_ids, qtype="MCQ"):
    try:
        payload = {
            "choices": [{"_id": cid, "comment": ""} for cid in choice_ids],
            "questionType": qtype
        }
        r = requests.post(
            f"{BASE_URL}/presentation/events/{EVENT_ID}/questions/{question_id}/answers",
            json=payload,
            headers=HEADERS, timeout=15
        )
        return r.status_code
    except Exception as e:
        print(f"  [erreur submit] {e}")
        return None


def already_answered(question):
    """Vérifie si on a déjà répondu à cette question."""
    return bool(question.get("userAnswer") or question.get("userAnswers"))


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
def run():
    print(f"🤖 Wooclap Quiz Bot — {EVENT_CODE}")
    print("   Chargement des questionnaires...\n")

    data = get_event_data()
    if not data:
        print("❌ Impossible de charger l'événement.")
        return

    questionnaires = data.get("questionnaires", [])
    print(f"📚 {len(questionnaires)} questionnaire(s) trouvé(s)\n")

    total_answered = 0
    total_skipped  = 0

    for qs in questionnaires:
        qs_name      = qs.get("name", "Sans nom")
        is_available = qs.get("isAvailable", False)
        questions    = qs.get("questions", [])

        print(f"{'='*50}")
        print(f"📖 {qs_name}")
        print(f"   {'✅ Disponible' if is_available else '🔒 Non disponible'} — {len(questions)} question(s)")

        if not is_available:
            print("   ⏭️  Ignoré (non disponible)\n")
            continue

        for q in questions:
            qid     = q.get("_id")
            qtype   = q.get("__t", "MCQ")
            qtext   = q.get("title", "?")
            choices = q.get("choices", [])

            # Ignorer les types sans choix
            if not choices or qtype not in ("MCQ", "Quiz"):
                print(f"   ⚠️  [{qtype}] {qtext[:60]}... — ignoré")
                total_skipped += 1
                continue

            # Déjà répondu ?
            if already_answered(q):
                print(f"   ✔️  Déjà répondu : {qtext[:60]}...")
                total_skipped += 1
                continue

            # Trouver la bonne réponse
            correct_ids = get_correct_choice_ids(choices)
            if not correct_ids:
                print(f"   ⚠️  isCorrect non disponible : {qtext[:60]}... — ignoré")
                total_skipped += 1
                continue

            labels = [c.get("choice", "?") for c in choices if c.get("_id") in correct_ids]
            print(f"   📋 {qtext[:70]}")
            print(f"      ✅ [direct] {', '.join(labels)}")

            status = submit_answer(qid, correct_ids, qtype)
            print(f"      📤 HTTP {status}")
            total_answered += 1

            time.sleep(DELAY)

        print()

    print(f"{'='*50}")
    print(f"✅ Terminé — {total_answered} réponse(s) envoyée(s), {total_skipped} ignorée(s)")


if __name__ == "__main__":
    run()
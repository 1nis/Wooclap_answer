import re
import requests
import getpass
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

SCRIPT_DIR = Path(__file__).parent

BASE_URL = "https://app.wooclap.com"


# ─────────────────────────────────────────────
# EVENT_ID — pas besoin d'auth
# ─────────────────────────────────────────────
def get_event_id(event_code):
    try:
        r = requests.get(
            f"{BASE_URL}/api/presentation/events/{event_code}/authentications",
            timeout=15
        )
        if r.status_code == 200:
            return r.json().get("_id")
        print(f"  ❌ HTTP {r.status_code} — vérifiez l'event code.")
    except Exception as e:
        print(f"  ❌ Erreur réseau : {e}")
    return None


# ─────────────────────────────────────────────
# TOKEN — SSO Université d'Aix-Marseille
# ─────────────────────────────────────────────
def get_token_via_sso(username, password, event_code):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page    = context.new_page()

        try:
            # 1. Aller sur la page SSO Wooclap → redirige vers CAS AMU
            print("  🌐 Ouverture de la page SSO...")
            page.goto(f"{BASE_URL}/api/auth/univ-amu.fr/login", wait_until="networkidle")

            # 2. Remplir les identifiants universitaires
            print("  📝 Remplissage des identifiants AMU...")
            page.wait_for_selector("input[type='text'], input[name='username'], input[id='username']", timeout=15000)
            page.fill("input[type='text'], input[name='username'], input[id='username']", username)
            page.fill("input[type='password']", password)
            page.press("input[type='password']", "Enter")

            # 3. Attendre le retour sur Wooclap (n'importe quelle page)
            print("  ⏳ Attente de la redirection SSO...")
            page.wait_for_url(re.compile(r"app\.wooclap\.com"), timeout=60000)
            page.wait_for_timeout(2000)  # laisser le temps aux redirects de se poser

            # 4. Naviguer directement vers l'event (ignore l'onboarding)
            print(f"  🔄 Navigation vers /{event_code}...")
            page.goto(f"{BASE_URL}/{event_code}", wait_until="load")
            page.wait_for_load_state("networkidle")

            # 5. Extraire le token depuis localStorage
            token = page.evaluate("localStorage.getItem('token')")

            if not token:
                # Parfois il faut attendre que le JS s'exécute
                page.wait_for_timeout(2000)
                token = page.evaluate("localStorage.getItem('token')")

            return token

        except PlaywrightTimeoutError:
            print("  ❌ Timeout — la page SSO n'a pas répondu à temps.")
            print("     Vérifiez vos identifiants ou la connexion réseau.")
            return None
        except Exception as e:
            print(f"  ❌ Erreur inattendue : {e}")
            return None
        finally:
            browser.close()


# ─────────────────────────────────────────────
# INJECTION dans les scripts
# ─────────────────────────────────────────────
def patch_var(content, var_name, new_value):
    """Remplace la valeur d'une variable Python dans un fichier."""
    return re.sub(
        rf'({var_name}\s*=\s*)"[^"]*"',
        rf'\1"{new_value}"',
        content
    )


def inject_credentials(event_code, event_id, token):
    targets = {
        "quizz_wooclap.py": ["EVENT_CODE", "EVENT_ID", "TOKEN"],
        "wooclap_bot.py":   ["EVENT_CODE", "TOKEN"],
    }

    for filename, vars_to_patch in targets.items():
        path = SCRIPT_DIR / filename
        if not path.exists():
            print(f"  ⚠️  {filename} introuvable — ignoré")
            continue

        content = path.read_text(encoding="utf-8")
        values  = {"EVENT_CODE": event_code, "EVENT_ID": event_id, "TOKEN": token}

        for var in vars_to_patch:
            content = patch_var(content, var, values[var])

        path.write_text(content, encoding="utf-8")
        print(f"  ✅ {filename} mis à jour")


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
def main():
    print("🔑 Wooclap Credential Fetcher\n")

    event_code = input("Event code (ex: BHJLED) : ").strip().upper()

    # Récupérer EVENT_ID
    print(f"\n📡 Récupération de l'EVENT_ID...")
    event_id = get_event_id(event_code)
    if not event_id:
        return
    print(f"  ✅ EVENT_ID : {event_id}")

    # Récupérer le TOKEN via SSO
    print(f"\n🔐 Connexion SSO — Université d'Aix-Marseille")
    username = input("Identifiant AMU : ").strip()
    password = getpass.getpass("Mot de passe    : ")

    token = get_token_via_sso(username, password, event_code)
    if not token:
        print("\n❌ Impossible de récupérer le token.")
        return
    print("  ✅ TOKEN récupéré")

    # Injection dans les scripts
    print(f"\n📝 Mise à jour des scripts...")
    inject_credentials(event_code, event_id, token)

    print(f"\n{'='*52}")
    print("✅ Scripts mis à jour :\n")
    print(f'  EVENT_CODE = "{event_code}"')
    print(f'  EVENT_ID   = "{event_id}"')
    print(f'  TOKEN      = "{token[:20]}..."')
    print(f"{'='*52}")


if __name__ == "__main__":
    main()

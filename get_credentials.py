import requests
import getpass
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

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
def get_token_via_sso(username, password):
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

            # 3. Attendre le retour sur Wooclap après redirection SSO
            print("  ⏳ Attente de la redirection SSO...")
            page.wait_for_url("*app.wooclap.com*", timeout=30000)
            page.wait_for_load_state("networkidle")

            # 4. Extraire le token depuis localStorage
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

    token = get_token_via_sso(username, password)
    if not token:
        print("\n❌ Impossible de récupérer le token.")
        return
    print("  ✅ TOKEN récupéré")

    # Résultat
    print(f"\n{'='*52}")
    print("✅ Copiez ces valeurs dans vos scripts :\n")
    print(f'EVENT_CODE = "{event_code}"')
    print(f'EVENT_ID   = "{event_id}"')
    print(f'TOKEN      = "{token}"')
    print(f"{'='*52}")


if __name__ == "__main__":
    main()

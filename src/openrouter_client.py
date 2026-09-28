
import os

from dotenv import load_dotenv
import requests


# chargement de cle depuis .env
load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

MODEL_RELECTEUR = "openai/gpt-4o-mini"

def critique_et_correction_texte(texte_brut: str, type_document: str = "lettre") -> str:

    if not OPENROUTER_API_KEY:
        print("[ATTENTION] Pas de KEY OPENROUTER_API_KEY trouvee dans .env donc le texte brut sera conserve")

        return texte_brut

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/ssalmarezgui/job-hunter-agent",
        "X-Title": "Job Hunter Multi-Agent System"
    }

    system_prompt = (
        "Tu es un relecteur et correcteur d'élite pour candidatures d'ingénieurs de haut niveau. "
        "Ta mission est de corriger et sublimer le texte rédigé pour Salma REZGUI. "
        "\n"
        "TES RÈGLES DE CORRECTION ABSOLUES :\n"
        "1. ACCORD FÉMININ STRICT : Salma est une femme. Accorde impérativement au féminin "
        "   (ex: 'élève ingénieure', 'présidente', 'candidate idéale', 'passionnée', 'prête à').\n"
        "2. SOBRIÉTÉ ACADÉMIQUE : Ne mets aucun focus insistant sur les notes ou classements scolaires. "
        "   Le texte doit valoriser la compétence technique, les projets concrets et la vision d'ingénieure.\n"
        "3. NETTOYAGE DES PARASITES : Supprime tout artefact comme '[Votre nom]', les formules d'appel "
        "   au début (pas de 'Cher...', 'Madame, Monsieur') et les formules de politesse finales (gérées par le template).\n"
        "4. STYLE & ÉLÉGANCE : Français impeccable, direct, percutant et élégant.\n"
        "5. FORMAT : Renvoie UNIQUEMENT le corps du texte corrigé, sans introduction ni conclusion."
    )

    prompt = f"""
    Voici le premier jet brut pour la {type_document} de Salma :
    ---
    {texte_brut}
    ---
    
    Applique tes règles de correction et renvoie une version impeccable, fluide et sans défaut.
    """

    payload = {
        "model": MODEL_RELECTEUR,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2 # faible pour une correction rigoureuse
    }

    try:
        response = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        texte_sublime = response.json()["choices"][0]['message']["content"].strip()
        return texte_sublime
    except Exception as e :
        print(f"[ERREUR OpenRouter] Impossible d'effectuer la relecture : {e}")
        return texte_brut


# TESTTTTTTTT

if __name__ == "__main__":
    print("\n--- TEST DU CRITIQUE OPENROUTER ---")
    
    # Texte volontairement truffé d'erreurs pour tester la vigilance de l'agent
    texte_test_avec_fautes = """
    Madame, Monsieur,
    Cher Directeur,
    Je suis un candidat idéal pour votre entreprise. J'ai été classé 3ème à l'ENSI.
    Mon postulat s'inscrit dans ma volonté d'apprendre. J'espère que mon expérience me feront une bonne équipe.
    Cordialement, [Votre nom]
    """

    print("[*] Texte brut avec erreurs :")
    print(texte_test_avec_fautes)
    
    print("\n[*] Correction par l'Agent Relecteur en cours...")
    texte_corrige = critique_et_correction_texte(texte_test_avec_fautes)
    
    print("\n[RÉSULTAT APRÈS LE CRITIQUE] :")
    print("=" * 60)
    print(texte_corrige)
    print("=" * 60)

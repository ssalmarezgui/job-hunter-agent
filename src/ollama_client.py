import json
import sys

import requests
from typing import Dict, Any, List

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "mistral"

def interroger_mistral(prompt: str, system_prompt: str = "") -> str:
    """Envoie une requête à l'instance locale d'Ollama avec affichage en direct."""
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "system": system_prompt,
        "stream": True,
        "options": {
            "temperature": 0.5,
            "num_predict": 650
        }
    }
    texte_complet = []
    try:
        response = requests.post(OLLAMA_URL, json=payload, stream=True, timeout=None)
        response.raise_for_status()

        for line in response.iter_lines():
            if line:
                chunk = json.loads(line.decode("utf-8"))
                token = chunk.get("response", "")
                texte_complet.append(token)
                sys.stdout.write(token)
                sys.stdout.flush()

        print("\n")
        return "".join(texte_complet).strip()
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Erreur de communication avec Ollama : {e}")

# PROMPT SYSTÈME COMMUN 
SYSTEM_HUMAIN_ET_POETIQUE = (
    "Tu es Salma REZGUI, élève ingénieure à l'ENSI (classée 3ème de promotion), issue des classes préparatoires MP (IPEIN). "
    "Tu possèdes une écriture à la fois profondément humaine, élégante, presque philosophique, tout en restant une scientifique rigoureuse. "
    "Tu vois l'ingénierie non comme une simple suite de lignes de code, mais comme un art de bâtir des systèmes résilients et au service de l'humain. "
    "\n"
    "RÈGLES D'OR ANTI-CLICHÉ (INTERDICTIONS STRICTES) :\n"
    "- INTERDIT d'utiliser : 'dynamique et motivée', 'j'ai l'honneur', 'vivement intéressée', 'dans l'attente de votre retour favorable', 'société de renom'.\n"
    "- Privilégie la sincérité, la précision des mots, la réflexion sur la technologie et la beauté de la conception logicielle.\n"
    "- Réponds UNIQUEMENT avec le texte demandé, sans formule de préambule comme 'Voici ma proposition'."
)

def generer_resume_cv(profil: Dict[str, Any], entreprise: Dict[str, str], projets_selectionnes: List[Dict[str, Any]]) -> str:
    """Génère un résumé de profil inspirant, personnel et percutant (3-4 phrases)."""
    
    titre_poste = entreprise.get("titre_poste", "Ingénieur")
    nom_boite = entreprise.get("entreprise", "")
    domaine = entreprise.get("domaine", "")
    technos = entreprise.get("technologies_cibles", "")
    titres_projets = [p["titre"] for p in projets_selectionnes]

    prompt = f"""
    Rédige le résumé professionnel pour l'en-tête de mon CV en ciblant le poste '{titre_poste}' chez {nom_boite} ({domaine}).
    
    Éléments à tisser ensemble de façon harmonieuse :
    - Mon identité : 3ème de promotion à l'ENSI, façonnée par l'exigence des prépas MP.
    - Ma philosophie du domaine ({domaine}) : chercher la clarté et l'élégance dans la complexité technique.
    - Mes preuves tangibles : projets comme {', '.join(titres_projets)} et maîtrise de {technos}.
    - Mon cap : apporter cette alliance de rigueur scientifique et de passion pour mon PFE chez {nom_boite}.
    
    Longueur : 3 phrases denses, rythmées et mémorables.
    """
    return interroger_mistral(prompt, SYSTEM_HUMAIN_ET_POETIQUE)

def generer_lettre_motivation(profil: Dict[str, Any], entreprise: Dict[str, str], projets_selectionnes: List[Dict[str, Any]]) -> str:
    """Génère une lettre irréprochable sur le plan grammatical, élégante et technique."""
    titre_poste = entreprise.get("titre_poste", "Ingénieur")
    nom_boite = entreprise.get("entreprise", "")
    domaine = entreprise.get("domaine", "")
    notes = entreprise.get("notes", "")

    lignes_projets = []
    for p in projets_selectionnes:
        technos = p.get('technologies', '')
        points = p.get('points_cles', [''])[0]
        lignes_projets.append(f"- Projet {p['titre']} ({technos}) : {points}")
    
    contexte_projets_dynamique = "\n".join(lignes_projets)


    prompt = f"""
    Rédige le corps de ma lettre de motivation pour : '{titre_poste}' chez {nom_boite}.
    Domaine visé : {domaine}.
    
    RÈGLES DE STYLE ET DE FORME :
    - Ton : Ingénieure passionnée, scientifique, sobre et élégante.
    - Évite toute flagornerie scolaire ou formules creuses.
    - COMMENCE DIRECTEMENT par le premier paragraphe (pas de 'Madame, Monsieur').
    - NE METS AUCUNE formule de politesse finale ni signature (déjà gérées dans le modèle).

    MES RÉALISATIONS CONCRÈTES À VALORISER POUR CE POSTE EN {domaine} :
    {contexte_projets_dynamique}

    STRUCTURE (3 courts paragraphes) :
    1. Pourquoi ce stage chez {nom_boite} dans le domaine {domaine} résonne avec mes aspirations d'ingénieure.
    2. Comment mes réalisations concrètes ci-dessus et ma rigueur (ENSI, prépa MP) prouvent ma capacité à être opérationnelle rapidement.
    3. Mon leadership et esprit d'équipe (Présidente du Club Happiness 2025-2026) pour m'intégrer avec fluidité et énergie dans vos équipes.
    """
    reponse = interroger_mistral(prompt, SYSTEM_HUMAIN_ET_POETIQUE)

    # --- NETTOYAGE SÉCURISÉ POST-LLM ---
    # 1. Supprime les salutations superflues au début
    lignes = [l.strip() for l in reponse.split("\n") if l.strip()]
    while lignes and any(lignes[0].lower().startswith(x) for x in ["cher ", "chère ", "madame", "monsieur", "bonjour"]):
        lignes.pop(0)

    texte_nettoye = "\n\n".join(lignes)

    # 2. Coupe toute signature ou formule finale hallucinée par le modèle
    parasites = ["Cordialement", "Bien cordialement", "[Votre nom]", "[Ton nom]"]
    for p in parasites:
        if p in texte_nettoye:
            texte_nettoye = texte_nettoye.split(p)[0].strip()

    # 3. Correction des petites coquilles fréquentes
    texte_nettoye = texte_nettoye.replace("permettral", "permettra")

    return texte_nettoye
# TESTttt
if __name__ == "__main__":
    from loader import charger_profil_maitre, charger_entreprises, selectionner_projets_pertinents

    profil = charger_profil_maitre()
    entreprises = charger_entreprises()

    # Test avec la deuxième entreprise : CyberDefense Corp (DevSecOps)
    cible = entreprises[1]
    print(f"\n[*] Génération d'une lettre humaine & poétique pour : {cible['entreprise']} ({cible['titre_poste']})...\n")

    selection = selectionner_projets_pertinents(profil, cible["domaine"], cible["technologies_cibles"], max_projets=2)
    projets_purs = [p[1] for p in selection]

    lettre = generer_lettre_motivation(profil, cible, projets_purs)
    print("=" * 60)
    print(lettre)
    print("=" * 60)
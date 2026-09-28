# on va charger le fichier de profil YAML et la liste des entreprises en CSV 
# filtrage des projets et experiences selon le domaine cible

from pathlib import Path
from typing import Dict, Any, List
import yaml
import csv 

DATA_DIR = Path("data")
PROFIL_PATH = DATA_DIR / "profile_maitre.yaml"
ENTREPRISES_PATH = DATA_DIR / "entreprises.csv"


def charger_profil_maitre(chemin_yaml:Path = PROFIL_PATH) -> Dict[str, Any]:
    """ CHARGE L'ENSEMBLE DES COMPETENCES ET PROJETS DEPUIS LE YAML"""

    if not chemin_yaml.exists():
        raise FileNotFoundError(f"Le fichier {chemin_yaml} est introuvable.")

    with open(chemin_yaml, "r", encoding="utf-8") as f:
        profil =yaml.safe_load(f)
    return profil


def charger_entreprises(chemin_csv:Path = ENTREPRISES_PATH) -> List[Dict[str, str]]:
    """ CHARGER LA LISTE DES ENTREPRISES DEPUIS LE CSV"""
    if not chemin_csv.exists():
        raise FileNotFoundError(f"Le fichier {chemin_csv} est introuvable.")

    entreprises = []
    with open(chemin_csv, "r", encoding="utf-8-sig") as f:
        lecteur = csv.DictReader(f, delimiter = ";")
        for ligne in lecteur:
            ligne_nettoyee= {k.strip().lower(): v.strip() for k, v in ligne.items() if k}
            entreprises.append(ligne_nettoyee)


    return entreprises

def selectionner_projets_pertinents(profil: Dict[str, Any], domaine_cible:str, technos_cibles: str = "", max_projets: int = 2) -> List[Dict[str, Any]]:

    """ SELECTIONNER LES PROJETS PERTINENTS SELON LE DOMAINE CIBLE """
    """ ATTRIBUE SCORE A CHAQUE PROJET SELON LA CORRESPONDACE AVEC LE DOMAINE ET LES TECHNOLOGIES 
    CIBLE PUIS TRIE DES PROJETS
    """

    tous_projets = profil.get("projets", [])
    domaine_cible_lower = domaine_cible.lower().strip()

    technos_recherchees = [t.strip().lower() for t in technos_cibles.split(",") if t.strip()]
    projets_scores = []


    for p in tous_projets:
        score = 0
        domaines_projets = [d.lower() for d in p.get("domaine", [])]
        technos_projet = p.get("technologies", "").lower()

        # Verification si le domaine cible ou des mots cles correspondent

        if any(domaine_cible_lower in d or d in domaine_cible_lower for d in domaines_projets):
            score += 10

        for tech in technos_recherchees:
            if tech in technos_projet:
                score += 5
        projets_scores.append((score, p))

    projets_scores.sort(key=lambda x: x[0], reverse=True)


    return [(score, p) for score, p in projets_scores[:max_projets]]

# TESTTTTTTTTTT

if __name__ == "__main__":
    print("[*] Test du chargement des données")

    # chargement du profil maitre
    mon_profil = charger_profil_maitre()
    print(f"[YESS] Profil chargé avec succès: {mon_profil['identite']['nom_complet']}")

    # chargement des entreprises
    liste_entreprises = charger_entreprises()
    print(f"[YESS] {len(liste_entreprises)} entreprises chargées avec succès depuis le CSV")

    # test de filtrage
    print("\n TEST DE FILTRAGE INTELLIGENT")
    for cible in liste_entreprises:
        domaine = cible.get("domaine", "")
        nom = cible.get("entreprise", "")
        technos = cible.get("technologies_cibles", "")

        print(f"\nEntreprise : {nom} | Cible : {domaine} | Technos : {technos}")

        selection = selectionner_projets_pertinents(mon_profil, domaine, technos, max_projets=2)

        for score, p in selection:
            print(f"  -> [Score: {score} pts] {p['titre']} (Domaine: {p['domaine']})")



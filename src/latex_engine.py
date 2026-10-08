from datetime import datetime
from pathlib import Path
import subprocess  # nosec B404: Subprocess contrôlé pour l'appel à pdflatex
from typing import Any

import jinja2


OUTPUT_DIR = Path("data/output").resolve()
TEMPLATES_DIR = Path("templates")

# Configuration Jinja2 sécurisée pour LaTeX
latex_env = jinja2.Environment(
    block_start_string=r'\BLOCK{',
    block_end_string='}',
    variable_start_string=r'\VAR{',
    variable_end_string='}',
    comment_start_string=r'\#{',
    comment_end_string='}',
    line_statement_prefix='%%',
    line_comment_prefix='%#',
    trim_blocks=True,
    autoescape=False,  # nosec B701: Template LaTeX (non-HTML), désinfection gérée par desinfecter_texte_latex
    loader=jinja2.FileSystemLoader(str(TEMPLATES_DIR.resolve()))
)

def desinfecter_texte_latex(texte: str) -> str:
    """
    Échappe les caractères réservés de LaTeX pour éviter les crashs de compilation
    et prévenir les injections de commandes.
    """
    caracteres_speciaux = {
        '&': r'\&',
        '%': r'\%',
        '$': r'\$',
        '#': r'\#',
        '_': r'\_',
        '{': r'\{',
        '}': r'\}',
        '~': r'\textasciitilde{}',
        '^': r'\textasciicircum{}',
        'œ': 'oe',
        'Œ': 'Oe'
    }
    for char, remplacement in caracteres_speciaux.items():
        texte = texte.replace(char, remplacement)
    
    # Remplacement des doubles sauts de ligne par des paragraphes LaTeX propres
    texte = texte.replace("\n\n", "\n\n\\par\n")
    return texte


def compiler_latex_en_pdf(nom_template: str, contexte: dict[str, Any], nom_fichier_base: str) -> Path:
    """
    Injecte les données dans le template LaTeX et compile en PDF via MiKTeX.
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. Échappement des chaînes de caractères
    contexte_propre = {}
    for k, v in contexte.items():
        if isinstance(v, str):
            contexte_propre[k] = desinfecter_texte_latex(v)
        else:
            contexte_propre[k] = v

    # 2. Rendu du template
    template = latex_env.get_template(nom_template)
    contenu_tex = template.render(**contexte_propre)

    fichier_tex = OUTPUT_DIR / f"{nom_fichier_base}.tex"
    fichier_pdf = OUTPUT_DIR / f"{nom_fichier_base}.pdf"

    with open(fichier_tex, "w", encoding="utf-8") as f:
        f.write(contenu_tex)

    # 3. Compilation pdflatex
    cmd = [
        "pdflatex",
        "-interaction=nonstopmode",
        f"-output-directory={str(OUTPUT_DIR)}",
        str(fichier_tex.resolve())
    ]

    print(f"[*] Compilation LaTeX de {fichier_tex.name} en cours...")
    resultat = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)  # nosec B603

    if resultat.returncode != 0:
        raise RuntimeError(f"Erreur de compilation LaTeX. Consultez le fichier {OUTPUT_DIR / f'{nom_fichier_base}.log'}")

    # 4. Nettoyage des fichiers intermédiaires de MiKTeX
    for extension in [".aux", ".log", ".out"]:
        fichier_temp = OUTPUT_DIR / f"{nom_fichier_base}{extension}"
        if fichier_temp.exists():
            fichier_temp.unlink()

    print(f"[SUCCÈS] PDF généré : {fichier_pdf}")
    return fichier_pdf

# TESTTTTT (MISTRAL -> LATEX -> PDF)
if __name__ == "__main__":
    from loader import charger_profil_maitre, charger_entreprises, selectionner_projets_pertinents
    from ollama_client import generer_lettre_motivation

    print("\n--- TEST COMPLET DU PIPELINE DE GÉNÉRATION ---")
    profil = charger_profil_maitre()
    entreprises = charger_entreprises()

    # On prend la cible CyberDefense Corp
    cible = entreprises[1]

    # 1. Sélection intelligente
    selection = selectionner_projets_pertinents(profil, cible["domaine"], cible["technologies_cibles"], max_projets=2)
    projets_purs = [p[1] for p in selection]

    # 2. Rédaction par Mistral
    print(f"[*] Génération de la lettre par Mistral pour {cible['entreprise']}...")
    texte_lettre = generer_lettre_motivation(profil, cible, projets_purs)

    # 3. Préparation des variables du template
    contexte_lettre = {
        "candidat_nom": profil["identite"]["nom_complet"],
        "candidat_titre": profil["identite"]["titre_base"],
        "candidat_telephone": profil["identite"]["telephone"],
        "candidat_email": profil["identite"]["email"],
        "candidat_linkedin": profil["identite"]["linkedin"],
        "candidat_github": profil["identite"]["github"],
        "date_du_jour": datetime.now().strftime("%d/%m/%Y"),
        "nom_contact": cible.get("nom_contact", "Service Recrutement"),
        "entreprise_nom": cible.get("entreprise", ""),
        "titre_poste": cible.get("titre_poste", ""),
        "corps_lettre": texte_lettre
    }

    # 4. Compilation du PDF
    nom_pdf = f"Lettre_Salma_REZGUI_{cible['entreprise'].replace(' ', '_')}"
    chemin_pdf = compiler_latex_en_pdf("lettre_template.tex", contexte_lettre, nom_pdf)

    print(f"\n[FÉLICITATIONS] Votre lettre est prête dans : {chemin_pdf}")




from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
from pathlib import Path
import smtplib

from dotenv import load_dotenv


load_dotenv()
# CONFIGURATION SMTP 
SMTP_SERVER = os.getenv("SMTP_SERVER", "smp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_EMAIL = os.getenv("SMTP_EMAIL", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")

MODE_SIMULATION = os.getenv("MODE_SIMULATION", "TRUE").lower() in ("true", "1", "yes")

def preparer_corps_email(nom_candidat: str, entreprise: str, titre_poste: str, 
                         domaine: str = "IT", est_spontanee: bool = False) -> tuple[str, str]:
    """
    Génère le Sujet et le Corps du mail adaptés :
    - Soit pour une Réponse à une Offre précise
    - Soit pour une Candidature Spontanée (Recherche de PFE)
    """
    if est_spontanee:
        sujet = f"Candidature Spontanée Stage PFE -- {domaine} -- {nom_candidat}"
        corps = f"""Madame, Monsieur,

        Élève ingénieure à l'École Nationale des Sciences de l'Informatique (ENSI), je suis actuellement à la recherche de mon stage de fin d'études (PFE) d'une durée de 4 à 6 mois à compter de février 2026.

        Particulièrement attentive aux projets et à l'expertise de {entreprise} dans le domaine {domaine}, je me permets de vous soumettre ma candidature spontanée pour rejoindre vos équipes techniques.

        Vous trouverez en pièces jointes mon Curriculum Vitae ainsi que ma lettre de motivation détaillant mes projets concrets et mes compétences.

        Je serais ravie d'échanger avec vous sur les opportunités ou besoins actuels au sein de votre structure.

        Bien cordialement,

        {nom_candidat}
        Élève Ingénieure -- ENSI
        Tél : +216 54 00 22 20
        LinkedIn : https://linkedin.com/in/salma-rezgui
        """
    else:
        # Cas d'une réponse à une offre existante
        sujet = f"Candidature Stage PFE -- {titre_poste} -- {nom_candidat}"
        corps = f"""Madame, Monsieur,

        Élève ingénieure à l'École Nationale des Sciences de l'Informatique (ENSI), je vous adresse ma candidature pour l'opportunité de stage : {titre_poste} au sein de {entreprise}.

        Vous trouverez en pièces jointes mon Curriculum Vitae ainsi que ma lettre de motivation précisant mon parcours et mes réalisations techniques en lien avec vos besoins.

        Je reste à votre entière disposition pour tout échange ou entretien.

        Bien cordialement,

        {nom_candidat}
        Élève Ingénieure -- ENSI
        Tél : +216 54 00 22 20
        LinkedIn : https://linkedin.com/in/salma-rezgui
        """
    return sujet, corps


def envoyer_candidature_email(destinataire: str, entreprise: str, titre_poste: str,
                              chemin_cv: Path, chemin_lettre: Path, domaine: str= "IT", est_spontanee: bool = False,
                              nom_candidat: str = "Salma REZGUI") -> bool:
    """Assemble et expédie (ou simule) l'email adapté."""
    
    sujet, corps_texte = preparer_corps_email(nom_candidat, entreprise, titre_poste, domaine, est_spontanee)

    msg = MIMEMultipart()
    msg["From"] = SMTP_EMAIL if SMTP_EMAIL else f"{nom_candidat} <candidature@ensi-uma.tn>"
    msg["To"] = destinataire
    msg["Subject"] = sujet
    msg.attach(MIMEText(corps_texte, "plain", "utf-8"))

    # 2. Ajout des pieces jointes (CV et Lettre)
    for chemin_fichier in [chemin_cv, chemin_lettre]:
        if chemin_fichier and chemin_fichier.exists():
            with open(chemin_fichier, "rb") as f:
                pj = MIMEApplication(f.read(), _subtype= "pdf")
                pj.add_header("Content-Disposition", "attachment", filename=chemin_fichier.name)
                msg.attach(pj)
        else:
            print(f"[ATTENTION] Pièce jointe introuvable : {chemin_fichier}")

    # 3. Traitement selon le mode
    if MODE_SIMULATION:
        print("\n" + "=" * 60)
        print("          [MODE SIMULATION ACTIVE - AUCUN MAIL N'A ÉTÉ ENVOYÉ]")
        print("=" * 60)
        print(f"De        : {msg['From']}")
        print(f"À         : {destinataire}")
        print(f"Sujet     : {sujet}")
        print(f"Fichiers  : {chemin_cv.name}  ET  {chemin_lettre.name}")
        print("-" * 60)
        print(corps_texte)
        print("=" * 60)
        print("[OK] Simulation d'envoi réussie.\n")
        return True

    # 4. Envoi via SMTP

    if not SMTP_EMAIL or not SMTP_PASSWORD:
        raise ValueError("SMTP_EMAIL et SMTP_PASSWORD doivent être configurés dans .env pour l'envoi réel !")
    try:
        print(f"[*] Connexion sécurisée au serveur SMTP ({SMTP_SERVER}:{SMTP_PORT})...")
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"[ÉCHEC SMTP] Erreur lors de l'envoi du mail : {e}")
        return False


# TESTTTTT
if __name__ == "__main__":
    print("\n TEST DE MODULE D'ENVOI DE MAIL")
    cv_test = Path("data/output/CV_Salma_REZGUI_Sovereign_AI_Studio.pdf")
    lettre_test = Path("data/output/Lettre_Salma_REZGUI_Sovereign_AI_Studio.pdf")

    envoyer_candidature_email(
        destinataire="recrutement@sovereign-ai.tn",
        entreprise="Sovereign AI Studio",
        titre_poste="Stage PFE - Ingénieur LLM & RAG",
        chemin_cv=cv_test,
        chemin_lettre=lettre_test,
        domaine="LLM & IA Générative",
        est_spontanee= True
    )




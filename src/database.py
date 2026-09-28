# Creer et gerer la base locale (data/candidatures.db)

# avant de travailler avec mistral ou generation de pdf , on va verifie si 
# l'email du recreteur a deja ete contacte

#apres validation de l'envoie , on va enregistrer les informations comme l'entreprise 
# le poste, la date, et le chemin des files


from datetime import datetime
from pathlib import Path
import sqlite3
from typing import Any, Dict, Optional


DB_PATH = Path("data/candidatures.db")

def initialiser_base():
    """ 
    Creer la table des candidatures si elle n'existe pas deja
    """

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS candidatures (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email_recruteur TEXT UNIQUE NOT NULL,
                entreprise TEXT NOT NULL,
                titre_poste TEXT NOT NULL,
                domaine TEXT,
                date_envoi TIMESTAMP NOT NULL,
                statut TEXT NOT NULL DEFAULT 'ENVOYE',
                chemin_pdf_cv TEXT,
                chemin_pdf_lettre TEXT
            )
        """)
        conn.commit()

def verifier_si_deja_contacte(email: str) -> Optional[Dict[str, Any]]:
    """
    Vérifie si une candidature a déjà été envoyée à cet email.
    Retourne les infos du précédent envoi si trouvé, sinon None.
    """
    if not DB_PATH.exists():
        initialiser_base()

    clean_email = email.strip().lower()

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row # pour que on peux faire resultat[email] au lieu que resultat[0] pas par indice mais par nom de colonne
        cursor = conn.cursor()
        cursor.execute("""
            SELECT entreprise, titre_poste, date_envoi, statut
            FROM candidatures
            WHERE LOWER(email_recruteur) = ? 
        """, (clean_email,)) 
        # ? va recevoir le email_clean

        resultat = cursor.fetchone()

        if resultat:
            return dict(resultat)
        
        return None

    
def enregistrer_candidature_envoyee(
        email: str, entreprise: str, titre_poste: str,
        domaine: str, chemin_cv: str = "", chemin_lettre: str = "",
        statut: str = "ENVOYE"
        ):
    initialiser_base()
    email_clean = email.strip().lower()

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO candidatures 
            (email_recruteur, entreprise, titre_poste,domaine, date_envoi, statut, chemin_pdf_cv, chemin_pdf_lettre)
            VALUES(?,?,?,?,?,?,?,?)

        """,(
            email_clean,
            entreprise.strip(),
            titre_poste.strip(),
            domaine.strip(),
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            statut,
            str(chemin_cv),
            str(chemin_lettre)  
        ))

        conn.commit()


    print(f"[BASE] Candidature pour '{entreprise}' ({email_clean}) archivée avec succès.")

#TESTTTTTTTTTTTT
if __name__ == "__main__":
    print("\n TEST DU CONTROLE DE ANTI-DOUBLON")

    initialiser_base()
    print("[OKKK] BDD SQLITE prete: data/candidatures.db")

    email_test = "recrutement@cyberdef.fr"
    deja_vu = verifier_si_deja_contacte(email_test)
    if not deja_vu:
        print(f"[AUTORISÉ] L'adresse {email_test} n'a jamais été contactée.")

    print("\n[*] Simulation d'un premier enregistrement d'envoi...")
    enregistrer_candidature_envoyee(
        email=email_test,
        entreprise="CyberDefense Corp",
        titre_poste="Stage PFE - DevSecOps",
        domaine="DevSecOps",
        chemin_lettre="data/output/Lettre_Salma_REZGUI_CyberDefense_Corp.pdf"
    )

    print("\n[*] Tentative de re-contact de la même adresse...")
    historique = verifier_si_deja_contacte(email_test)
    if historique:
        print(f"[BLOQUÉ STRICT] Cet email a DÉJÀ reçu une candidature !")
        print(f"  -> Entreprise : {historique['entreprise']}")
        print(f"  -> Date d'envoi : {historique['date_envoi']}")

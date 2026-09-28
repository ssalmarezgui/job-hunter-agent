

from datetime import datetime
import sys

from src.database import enregistrer_candidature_envoyee, verifier_si_deja_contacte
from src.latex_engine import compiler_latex_en_pdf
from src.loader import charger_entreprises, charger_profil_maitre, selectionner_projets_pertinents
from src.mailer import envoyer_candidature_email
from src.ollama_client import generer_lettre_motivation, generer_resume_cv
from src.openrouter_client import critique_et_correction_texte


def executer_pipeline():
    print("\n" + "=" * 70)
    print("        JOB HUNTER AGENT - PIPELINE DE CANDIDATURE MULTI-AGENTS")
    print("=" * 70)


    # CHARGEMENT DES DONNEES

    try:
        profil = charger_profil_maitre()
        entreprises = charger_entreprises()
    except Exception as e:
        print(f"[ERREUR CRITIQUE] Impossible de charger les données : {e}")
        return

    print(f"[*] Profil chargé : {profil['identite']['nom_complet']}")
    print(f"[*] {len(entreprises)} entreprise(s) détectée(s) dans le fichier CSV.\n")

    
    # BOUCLE POUR LES ENTREPRISES 

    for idx, cible in enumerate(entreprises, 1):

        nom_boite = (
            cible.get("entreprise") 
            or cible.get("société") 
            or cible.get("societe") 
            or cible.get("nom_entreprise") 
            or cible.get("company")
        )

        if not nom_boite:
            valeurs = list(cible.values())
            nom_boite = valeurs[1] if len(valeurs) > 1 else "Inconnue"

        email_recruteur = cible.get("email_recruteur", "").strip()
        poste = cible.get("titre_poste", "Stage PFE")
        domaine = cible.get("domaine", "IT")
        technos = cible.get("technologies_cibles", "")

        print("-" * 70)
        print(f"[{idx}/{len(entreprises)}] TRAITEMENT DE : {nom_boite} ({poste})")
        print(f"Domaine : {domaine} | Email : {email_recruteur}")

        # 1. CONTROLE ANTI DOUBLON
        historique = verifier_si_deja_contacte(email_recruteur)
        if historique:
            print(f"[BLOQUÉ - DÉJÀ CONTACTÉ] Cette entreprise a déjà reçu une candidature le {historique['date_envoi']} !")
            print("Passage automatique à l'entreprise suivante...\n")
            continue

        # 2. SELECTION DES PROJETS
        print("[*] Sélection des projets les plus pertinents...")
        selection = selectionner_projets_pertinents(profil, domaine, technos, max_projets=3)
        projets_choisis = [p[1] for p in selection]

        # 8. REDACTION ET RELECTEUR DU RESUME DE CV 
        print("[*] Génération du Résumé de CV adapté au poste...")
        resume_brut = generer_resume_cv(profil, cible, projets_choisis)
        resume_final = critique_et_correction_texte(resume_brut, type_document="résumé de profil CV")


        # 3. MISTRAL - REDACTION BRUTE
        print("[*] [Agent 1 / Mistral Local] Rédaction du premier jet...")
        premier_jet = generer_lettre_motivation(profil, cible, projets_choisis)

        # 4. GPT - RELECTURE & CORRECTION
        print("[*] [Agent 2 / OpenRouter] Relecture, accords féminins et nettoyage...")
        lettre_finale = critique_et_correction_texte(premier_jet, type_document="lettre de motivation")

        # 7. COMPILATION DU CV EN LATEX
        contexte_cv = {
            "candidat_nom": profil["identite"]["nom_complet"],
            "candidat_telephone": profil["identite"]["telephone"],
            "candidat_email": profil["identite"]["email"],
            "candidat_linkedin": profil["identite"]["linkedin"],
            "candidat_github": profil["identite"]["github"],
            "resume_personnalise": resume_final,
            "projets_selectionnes": projets_choisis
        }
        nom_cv_pdf = f"CV_Salma_REZGUI_{nom_boite.replace(' ', '_')}"
        chemin_cv_pdf = compiler_latex_en_pdf("cv_template.tex", contexte_cv, nom_cv_pdf)

        if lettre_finale.startswith(nom_boite):
            lettre_finale = lettre_finale.replace(nom_boite, "", 1).lstrip(", \n")
        # 5. DU LATEX VERS PDF 
        contexte_lettre = {
            "candidat_nom": profil["identite"]["nom_complet"],
            "candidat_titre": profil["identite"]["titre_base"],
            "candidat_telephone": profil["identite"]["telephone"],
            "candidat_email": profil["identite"]["email"],
            "candidat_linkedin": profil["identite"]["linkedin"],
            "date_du_jour": datetime.now().strftime("%d/%m/%Y"),
            "nom_contact": cible.get("nom_contact", "Service Recrutement"),
            "entreprise_nom": nom_boite,
            "titre_poste": poste,
            "corps_lettre": lettre_finale
        }


        nom_lettre_pdf = f"Lettre_Salma_REZGUI_{nom_boite.replace(' ', '_')}"
        chemin_lettre_pdf = compiler_latex_en_pdf("lettre_template.tex", contexte_lettre, nom_lettre_pdf)

        # 6. VALIDATION PAR MOI

        print("\n" + "=" * 70)
        print("          RÉCAPITULATIF PRÊT POUR VALIDATION")
        print("=" * 70)
        print(f"À         : {email_recruteur}")
        print(f"Objet du Mail   : Candidature Stage PFE -- {poste} -- {profil['identite']['nom_complet']}")
        print(f"Pièce Jointe 1  : {chemin_cv_pdf.name}")
        print(f"Pièce Jointe 2  : {chemin_lettre_pdf.name}")
        print("-" * 70)
        print("EXTRAIT DU CONTENU DU DOCUMENT :")
        print(lettre_finale[:300] + "...\n")
        print("-" * 70)


        while True:
            reponse = input("Voulez-vous VALIDER et archiver cette candidature ? [V: Valider / S: Sauter / Q: Quitter] : ").strip().upper()
            if reponse == "V":
                # Détection si spontanée ou réponse à une offre
                type_cand = cible.get("type_candidature", "").lower()
                est_spontanee = "spontan" in type_cand or "spontanée" in type_cand

                # 1. Envoi ou simulation du mail avec les 2 pièces jointes
                succes_mail = envoyer_candidature_email(
                    destinataire=email_recruteur,
                    entreprise=nom_boite,
                    titre_poste=poste,
                    domaine=domaine,
                    chemin_cv=chemin_cv_pdf,
                    chemin_lettre=chemin_lettre_pdf,
                    est_spontanee=est_spontanee,
                    nom_candidat=profil["identite"]["nom_complet"]
                )

                # 2. Archivage SQLite pour blocage anti-doublon
                if succes_mail:
                    enregistrer_candidature_envoyee(
                        email=email_recruteur,
                        entreprise=nom_boite,
                        titre_poste=poste,
                        domaine=domaine,
                        chemin_cv=str(chemin_cv_pdf.resolve()),
                        chemin_lettre=str(chemin_lettre_pdf.resolve())
                    )
                    print(f"[SUCCÈS TOTAL] Dossier expédié et verrouillé dans la base SQLite.\n")
                break
            elif reponse == "S":
                print(f"[IGNORÉ] Vous avez choisi de sauter {nom_boite}.\n")
                break
            elif reponse == "Q":
                print("[ARRÊT] Fin du traitement par l'utilisateur.")
                sys.exit(0)
            else:
                print("Choix invalide. Tapez 'V', 'S' ou 'Q'.")

    print("\n" + "=" * 70)
    print("TOUTES LES ENTREPRISES DU FICHIER ONT ÉTÉ TRAITÉES AVEC SUCCÈS !")
    print("=" * 70)


if __name__ == "__main__":
    executer_pipeline()





    
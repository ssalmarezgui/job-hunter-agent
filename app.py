from datetime import datetime
from pathlib import Path

import streamlit as st
import base64

from src.database import enregistrer_candidature_envoyee, verifier_si_deja_contacte
from src.latex_engine import compiler_latex_en_pdf
from src.loader import charger_entreprises, charger_profil_maitre, selectionner_projets_pertinents
from src.mailer import MODE_SIMULATION, envoyer_candidature_email, preparer_corps_email
from src.ollama_client import generer_lettre_motivation, generer_resume_cv
from src.openrouter_client import critique_et_correction_texte

st.set_page_config(
    page_title = "Job Hunter Studio - Salma REZGUI",
    page_icon = "🎯",
    layout = "wide" #toute la largeur de l'ecran
)

#  AFFICHAGE DE PDF 
def afficher_pdf(chemin_pdf: Path):
    if not chemin_pdf.exists():
        st.warning("Fichier PDF introuvable!")
        return

    with open(chemin_pdf, 'rb') as f:
        base64_pdf = base64.b64encode(f.read()).decode("utf-8")
        pdf_display = f'<iframe src = "data:application/pdf;base64,{base64_pdf}" width="100%" heifht="650" type = "application/pdf"></iframe>'
        st.markdown(pdf_display, unsafe_allow_html=True)


# CHARGEMENT DES DONNEES

profil = charger_profil_maitre()
entreprises = charger_entreprises()

if "resume_texte" not in st.session_state:
    st.session_state.resume_texte = ""

if "lettre_texte" not in st.session_state:
    st.session_state.lettre_texte = ""

if "chemin_cv_pdf" not in st.session_state:
    st.session_state.chemin_cv_pdf = None

if "chemin_lettre_pdf" not in st.session_state:
    st.session_state.chemin_lettre_pdf = None

# SIDEBARRRRRRRRRRR

with st.sidebar:
    st.title("🎯 Job Hunter Agent")
    st.markdown("**Salma REZGUI** | ENSI")
    st.markdown("---")

    st.subheader("⚙️ Etat du Système")
    st.success("Mistral 7B (OLLAMA LOCAL)")
    st.success("Relecteur OpenRouter")

    if MODE_SIMULATION:
        st.info("Mode Simulation Actif")
    else:
        st.warning("Mode SMTP Réel Actif !")

    st.markdown("---")
    st.subheader("➕ Ajouter une Cible")
    with st.form("form_nouvelle_boite"):
        n_nom = st.text_input("Entreprise")
        n_email = st.text_input("Email du recruteur")
        n_poste = st.text_input("Titre du poste", value = "Stage PFE")
        n_domaine = st.selectbox("Domaine", ["DevSecOps / DevOps", "Computer Vision", "LLM", "Data Science", "FullStack", "Business Intelligence"])
        n_technos = st.text_input("Technologies clés (séparées par virgule)")
        btn_ajout = st.form_submit_button("Ajouter à la liste")


        if btn_ajout:
            if n_nom and n_email:
                with open("data/entreprises.csv", "a", encoding = "utf-8-sig") as f:
                    f.write(f"\n99;{n_nom};{n_email};Responsable Recrutement;{n_poste};{n_domaine};{n_technos};Spontanée")
                    st.success(f"{n_nom} ajouté avec succès !")
                    st.rerun()

            else:
                st.error("Le nom et l'email sont obligatoires.")


# ESPACE DE TRAVAIL 
tab_studio, tab_suivi = st.tabs([" Studio de Candidature", " Tableau de Suivi"])


with tab_studio:
    st.header("Studio de Génération & Edition Sur-Mesure")

    # 1. CHOIX ENTREPRISE
    noms_entreprises = [
        (c.get("entreprise") or c.get("société") or list(c.values())[1])
        for c in entreprises
    ]

    entreprise_choisie = st.selectbox("Sélectionnez l'entreprise cible :", noms_entreprises)

    # 2. DONNEES CIBLE
    cible = next(c for c in entreprises if (c.get("entreprise") or c.get("société") or list(c.values())[1]) == entreprise_choisie)
    email_cible = (
        cible.get("email_recruteur")
        or cible.get("email")
        or cible.get("mail")
        or list(cible.values())[2] # prend la 3eme colonne de csv sinon (cel correspondante au email)
    ).strip()
    poste_cible = cible.get("titre_poste", "Stage PFE")
    domaine_cible = cible.get("domaine", "IT")
    technos_cible = cible.get("technologies_cibles", "")

    # 3.ANTIDOUBLON
    historique = verifier_si_deja_contacte(email_cible)
    if historique:
        st.error(f"ATTENTION : Cette entreprise a DÉJÀ reçu une candidature le {historique['date_envoi']} !")
        st.stop()

    st.markdown("---")

    # CV 
    st.subheader("Personnalisation du Contenu")

    col_projets, col_ia = st.columns([1, 1])

    with col_projets:
        st.markdown("### Projets à inclure sur le CV (3 recommandés)")
        tous_les_projets = profil.get("projets", [])

        # Score par defaut
        selection_auto = selectionner_projets_pertinents(profil, domaine_cible, technos_cible, max_projets=3)
        titres_auto = [p[1]["titre"] for p in selection_auto]

        # AUTRE PROJET A AJOUTER 
        projets_selectionnes_manuellement = []
        for p in tous_les_projets:
            titre_proj = p.get("titre", "")
            coche = titre_proj in titres_auto
            domaines_str = ", ".join(p.get("domaine", []))
            if st.checkbox(f"**{titre_proj}** ({domaines_str})", value=coche, key=f"check_{titre_proj}"):
                projets_selectionnes_manuellement.append(p)


    with col_ia:
        st.markdown("### Rédaction Intelligente Multi-Agents")
        st.write(f"Poste visé : **{poste_cible}** ({domaine_cible})")

        if st.button("Rédiger le dossier avec l'IA", type="primary"):
            with st.spinner("Mistral rédige et OpenRouter sublime le texte"):
                r_brut = generer_resume_cv(profil, cible, projets_selectionnes_manuellement)
                st.session_state.resume_texte = critique_et_correction_texte(r_brut, type_document="résumé de profil CV")

                l_brute = generer_lettre_motivation(profil, cible, projets_selectionnes_manuellement)
                st.session_state.lettre_texte = critique_et_correction_texte(l_brute, type_document="lettre de motivation")

                st.success("Rédaction terminée ! Vous pouvez modifier les textes ci-dessous.")


    st.markdown("---")
    st.subheader(" Zone d'Édition Manuelle (Enrichissez vos textes si besoin)")

    col_edit_cv, col_edit_lettre = st.columns(2)
    with col_edit_cv:
        st.markdown("**Résumé Professionnel du CV :**")
        st.session_state.resume_texte = st.text_area("Summary", value=st.session_state.resume_texte, height=120, label_visibility="collapsed")

    with col_edit_lettre:
        st.markdown("**Corps de la Lettre de Motivation :**")
        st.session_state.lettre_texte = st.text_area("Lettre", value=st.session_state.lettre_texte, height=250, label_visibility="collapsed")



    # COMPILATION DES PDFS
    if st.button("🔨 Compiler et Mettre à jour les 2 PDFs"):
        with st.spinner("Compilation LaTeX via MiKTeX..."):
            # CV
            contexte_cv = {
                "candidat_nom": profil["identite"]["nom_complet"],
                "candidat_telephone": profil["identite"]["telephone"],
                "candidat_email": profil["identite"]["email"],
                "candidat_linkedin": profil["identite"]["linkedin"],
                "candidat_github": profil["identite"]["github"],
                "resume_personnalise": st.session_state.resume_texte,
                "projets_selectionnes": projets_selectionnes_manuellement
            }
            st.session_state.chemin_cv_pdf = compiler_latex_en_pdf(
                "cv_template.tex", contexte_cv, f"CV_Salma_REZGUI_{entreprise_choisie.replace(' ', '_')}"
            )

             # Lettre
            contexte_lettre = {
                "candidat_nom": profil["identite"]["nom_complet"],
                "candidat_telephone": profil["identite"]["telephone"],
                "candidat_email": profil["identite"]["email"],
                "candidat_linkedin": profil["identite"]["linkedin"],
                "date_du_jour": datetime.now().strftime("%d/%m/%Y"),
                "nom_contact": cible.get("nom_contact", "Responsable Recrutement"),
                "entreprise_nom": entreprise_choisie,
                "titre_poste": poste_cible,
                "corps_lettre": st.session_state.lettre_texte
            }
            st.session_state.chemin_lettre_pdf = compiler_latex_en_pdf(
                "lettre_template.tex", contexte_lettre, f"Lettre_Salma_REZGUI_{entreprise_choisie.replace(' ', '_')}"
            )

            st.success("Les 2 PDFs ont été compilés avec succès !")


    # 5. VISIONNEUSE DOUBLE PDF CÔTE À CÔTE
    if st.session_state.chemin_cv_pdf and st.session_state.chemin_lettre_pdf:
        st.markdown("---")
        st.subheader("👁️ Aperçu Direct des Documents")
        col_pdf_cv, col_pdf_lettre = st.columns(2)
        with col_pdf_cv:
            st.markdown("### 📄 Curriculum Vitae")
            afficher_pdf(st.session_state.chemin_cv_pdf)
        with col_pdf_lettre:
            st.markdown("### ✉️ Lettre de Motivation")
            afficher_pdf(st.session_state.chemin_lettre_pdf)
        # 6. EXPÉDITION & VALIDATION
        st.markdown("---")
        st.subheader(" Validation et Envoi")
        type_candidature = st.radio("Type de candidature :", ["Candidature Spontanée", "Réponse à une Offre"], horizontal=True)
        est_spontanee = (type_candidature == "Candidature Spontanée")

        sujet_mail, corps_mail = preparer_corps_email(
            nom_candidat=profil["identite"]["nom_complet"],
            entreprise=entreprise_choisie,
            titre_poste=poste_cible,
            domaine=domaine_cible,
            est_spontanee=est_spontanee
        )

        st.markdown("###  Aperçu de l'E-mail Prêt pour Expédition")
        with st.container(border=True):
            st.markdown(f"**Destinataire :** `{email_cible}`")
            st.markdown(f"**Objet :** `{sujet_mail}`")
            st.markdown(f"**Pièces jointes :** 📎 `{st.session_state.chemin_cv_pdf.name}` ~|~ 📎 `{st.session_state.chemin_lettre_pdf.name}`")
            st.text_area("Corps du mail :", value=corps_mail, height=180, disabled=True)


        if st.button(" CONFIRMER ET ENVOYER LA CANDIDATURE", type="primary"):
            if not email_cible:
                st.error("Impossible d'envoyer : aucun email trouvé pour cette entreprise dans le fichier CSV !")
            else:
                with st.spinner("Envoi et archivage en cours..."):
                    try:
                        succes = envoyer_candidature_email(
                            destinataire=email_cible,
                            entreprise=entreprise_choisie,
                            titre_poste=poste_cible,
                            chemin_cv=st.session_state.chemin_cv_pdf,
                            chemin_lettre=st.session_state.chemin_lettre_pdf,
                            domaine=domaine_cible,
                            est_spontanee=est_spontanee,
                            nom_candidat=profil["identite"]["nom_complet"]
                        )
                        if succes:
                            enregistrer_candidature_envoyee(
                                email=email_cible,
                                entreprise=entreprise_choisie,
                                titre_poste=poste_cible,
                                domaine=domaine_cible,
                                chemin_cv=str(st.session_state.chemin_cv_pdf.resolve()),
                                chemin_lettre=str(st.session_state.chemin_lettre_pdf.resolve())
                            )
                            st.balloons()
                            st.success(f"🎉 Candidature pour {entreprise_choisie} enregistrée et verrouillée dans la base !")

                            import time
                            time.sleep(1.5)
                            st.rerun()
                    except Exception as e:
                        st.error(f"Erreur lors de l'enregistrement: {e}") 


with tab_suivi:
    st.header("Historique et Statut de vos Candidatures")
    import sqlite3
    import pandas as pd

    if Path("data/candidatures.db").exists():
        with sqlite3.connect("data/candidatures.db") as conn:
            df_candidatures = pd.read_sql_query("SELECT id, entreprise, email_recruteur, titre_poste, domaine, date_envoi, statut FROM candidatures ORDER BY date_envoi DESC", conn)
        
        st.metric("Total Candidatures Expédiées", len(df_candidatures))
        st.dataframe(df_candidatures, use_container_width=True)
    else:
        st.info("Aucune candidature n'a encore été enregistrée dans la base.")





            






        


import pandas as pd
import numpy as np
from datetime import date
import os


def main() -> None:
    # ── Reproductibilité : même seed = mêmes données à chaque run ──────────────
    np.random.seed(42)

    # ══════════════════════════════════════════════════════════════════════════
    # 1. DÉFINITION DES EXERCICES
    # ══════════════════════════════════════════════════════════════════════════
    # Chaque exercice a :
    #   - une charge initiale réaliste (kg)
    #   - un taux de progression sur 6 mois (ex: 0.20 = +20%)
    #   - un nombre de séries et répétitions typiques
    #   - un écart-type pour le bruit (variation séance à séance)

    exercices_config = [
        # id, nom,                    groupe,        charge_init, prog_6m, series, reps_base, bruit_std
        (1,  "Développé couché",      "Pectoraux",   75,  0.20,  2, 6,  3.0),
        (2,  "Développé incliné",     "Pectoraux",   60,  0.18,  2, 6,  2.5),
        (3,  "Écarté haltères",       "Pectoraux",   14,  0.30,  2, 8,  0.3),
        (4,  "Soulevé de terre",      "Dos",        100,  0.22,  2, 6,  5.0),
        (5,  "Tractions lestées",     "Dos",         10,  0.40,  2, 6,  1.5),
        (6,  "Rowing haltère",        "Dos",         30,  0.20,  2, 8,  2.0),
        (7,  "Squat",                 "Jambes",      90,  0.22,  2, 6,  4.0),
        (8,  "Presse à cuisses",      "Jambes",     150,  0.18,  2, 6,  8.0),
        (9,  "Leg curl",              "Jambes",      45,  0.15,  2, 8,  2.0),
        (10, "Développé militaire",   "Épaules",     50,  0.18,  2, 6,  2.5),
        (11, "Curl biceps",           "Bras",        12,  0.30,  2, 8,  0.3),
        (12, "Triceps poulie",        "Bras",        25,  0.24,  2, 8,  1.5),
    ]

    df_exercices = pd.DataFrame(exercices_config, columns=[
        "exercice_id", "nom", "groupe_musculaire",
        "charge_init", "prog_6m", "series_default", "reps_base", "bruit_std"
    ])

    # ══════════════════════════════════════════════════════════════════════════
    # 2. GÉNÉRATION DU CALENDRIER (6 mois)
    # ══════════════════════════════════════════════════════════════════════════
    date_debut = date(2025, 11, 1)
    date_fin = date(2026, 4, 30)

    jours = pd.date_range(start=date_debut, end=date_fin, freq="D")

    df_calendrier = pd.DataFrame({
        "date": jours,
        "semaine_programme": ((jours - jours[0]).days // 7) + 1,
        "mois": jours.month,
        "annee": jours.year,
    })

    print(f"Calendrier : {len(df_calendrier)} jours ({date_debut} → {date_fin})")

    # ══════════════════════════════════════════════════════════════════════════
    # 3. PLANIFICATION DES SÉANCES
    # ══════════════════════════════════════════════════════════════════════════
    # Programme Push/Pull/Legs sur 5 jours avec repos le jeudi et le dimanche
    # Lundi: Push (Poitrine + Épaules)
    # Mardi: Pull (Dos + Bras)
    # Mercredi: Legs
    # Jeudi: repos
    # Vendredi: Push
    # Samedi: Pull
    # Dimanche: repos

    programme = {
        "Monday":    [1, 2, 3, 10, 12],  # Push : DC, incliné, écarté, militaire, triceps
        "Tuesday":   [4, 5, 6, 11],      # Pull : soulevé, tractions, rowing, curl
        "Wednesday": [4, 7, 8, 9],       # Legs : soulevé, squat, presse, leg curl
        "Thursday":  [],                  # Repos
        "Friday":    [1, 2, 3, 10, 12],  # Push
        "Saturday":  [4, 5, 6, 11],      # Pull
        "Sunday":    [],                  # Repos
    }

    # ══════════════════════════════════════════════════════════════════════════
    # 4. GÉNÉRATION DES SÉRIES (table de faits : seances)
    # ══════════════════════════════════════════════════════════════════════════
    #
    # MODÈLE DE PROGRESSION :
    #   On calcule le jour t (0 à 180) dans la période.
    #   charge_theorique = charge_init * (1 + prog_6m * t/180)
    #   On ajoute un bruit gaussien pour simuler les bonnes/mauvaises journées.
    #   On arrondit à 1 kg près (< 30 kg) ou 2.5 kg près (≥ 30 kg).
    #
    # VARIATION DES REPS :
    #   Semaines 1-3 : reps_base (charge standard)
    #   Semaine 4    : deload → reps_base, charge -10% (récupération)
    #

    lignes = []
    total_jours = (date_fin - date_debut).days

    for _, jour_row in df_calendrier.iterrows():
        jour_nom = jour_row["date"].strftime("%A")  # "Monday", "Tuesday"...
        exercices_du_jour = programme.get(jour_nom, [])

        if not exercices_du_jour:
            continue  # Jour de repos → on saute

        # Probabilité de manquer une séance : 10% (réalisme)
        if np.random.random() < 0.10:
            continue

        t = (jour_row["date"].date() - date_debut).days  # Jour 0 à ~180

        for ex_id in exercices_du_jour:
            ex = df_exercices[df_exercices["exercice_id"] == ex_id].iloc[0]

            # Semaine de deload toutes les 4 semaines
            semaine_num = t // 7 + 1  # Semaine 1-indexée
            is_deload = (semaine_num % 4 == 0)  # Toutes les 4e semaines

            # Charge théorique avec progression
            charge_theorique = ex["charge_init"] * (1 + ex["prog_6m"] * t / total_jours)
            if is_deload:
                charge_theorique *= 0.90  # Réduction 10% en deload

            # Répétitions
            bruit_reps = int(np.random.choice([-2, -1, 0, 1, 2], p=[0.1, 0.2, 0.4, 0.2, 0.1]))
            reps = max(1, ex["reps_base"] + bruit_reps)

            # Nombre de séries pour cette séance
            nb_series = int(ex["series_default"])

            for serie in range(1, nb_series + 1):
                # Bruit gaussien sur la charge (fatigue accumulée série par série)
                fatigue_serie = 1.0 - (serie - 1) * 0.02  # -2% par série
                bruit = np.random.normal(0, ex["bruit_std"])
                charge_brute = charge_theorique * fatigue_serie + bruit

                # Arrondi à 1 kg pour les charges légères, 2.5 kg sinon
                pas = 1.0 if charge_brute < 30 else 2.5
                charge_finale = max(round(charge_brute / pas) * pas, 1.0)

                # Note occasionnelle (5% des séries)
                notes = ""
                if np.random.random() < 0.05:
                    notes = np.random.choice([
                        "Bonne séance", "Fatiguée", "PR!", "Technique à revoir",
                        "Manque de sommeil", "Top forme", "Douleur légère épaule"
                    ])

                lignes.append({
                    "date": jour_row["date"].date(),
                    "exercice_id": int(ex_id),
                    "serie": serie,
                    "repetitions": int(reps),
                    "charge_kg": float(charge_finale),
                    "unite": "kg",
                    "notes": notes,
                })

    df_seances = pd.DataFrame(lignes)

    print(f"Séries générées         : {len(df_seances)}")
    print(f"Entrées (date*exercice) : {df_seances.groupby(['date','exercice_id']).ngroups}")
    print(f"Jours d'entraînement    : {df_seances['date'].nunique()}")

    # ══════════════════════════════════════════════════════════════════════════
    # 5. NETTOYAGE POUR L'EXPORT
    # ══════════════════════════════════════════════════════════════════════════
    # On ne garde que les colonnes du schéma final pour chaque feuille

    df_seances_export = df_seances[[
        "date", "exercice_id", "serie", "repetitions", "charge_kg", "unite", "notes"
    ]]

    df_exercices_export = df_exercices[[
        "exercice_id", "nom", "groupe_musculaire"
    ]]

    df_calendrier_export = df_calendrier[[
        "date", "semaine_programme", "mois", "annee"
    ]]

    # ══════════════════════════════════════════════════════════════════════════
    # 6. EXPORT EXCEL (schéma en étoile → 3 feuilles)
    # ══════════════════════════════════════════════════════════════════════════
    output_path = os.path.join(os.path.dirname(__file__), "data", "workouts.xlsx")

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        df_seances_export.to_excel(writer,    sheet_name="seances",    index=False)
        df_exercices_export.to_excel(writer,  sheet_name="exercices",  index=False)
        df_calendrier_export.to_excel(writer, sheet_name="calendrier", index=False)

    print(f"\nFichier créé : {output_path}")
    print(f"  Feuille 'seances'    : {len(df_seances_export)} lignes")
    print(f"  Feuille 'exercices'  : {len(df_exercices_export)} lignes")
    print(f"  Feuille 'calendrier' : {len(df_calendrier_export)} lignes")

    # ══════════════════════════════════════════════════════════════════════════
    # 7. VÉRIFICATION RAPIDE
    # ══════════════════════════════════════════════════════════════════════════
    print("\n── Aperçu des 5 premières séries ──")
    print(df_seances_export.head())

    print("\n── Volume total par groupe musculaire ──")
    df_check = df_seances.merge(df_exercices_export, on="exercice_id")
    df_check["volume"] = df_check["repetitions"] * df_check["charge_kg"]
    print(df_check.groupby("groupe_musculaire")["volume"].sum().sort_values(ascending=False).to_string())

    print("\n── Progression développé couché (charge moy. par mois) ──")
    bench = df_check[df_check["exercice_id"] == 1].copy()
    bench["mois"] = pd.to_datetime(bench["date"]).dt.to_period("M")
    print(bench.groupby("mois")["charge_kg"].mean().round(1).to_string())


if __name__ == "__main__":
    main()

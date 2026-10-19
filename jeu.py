"""Jeu de cartes à collectionner : version console.

Lancer avec :  python jeu.py
La logique est dans moteur.py, les cartes dans cartes.json,
la progression dans sauvegarde.json.
"""
import json
from pathlib import Path

from moteur import ORDRE, PITIE_APRES, etat_initial, ouvrir_booster

DOSSIER = Path(__file__).parent
FICHIER_CARTES = DOSSIER / "cartes.json"
FICHIER_SAUVEGARDE = DOSSIER / "sauvegarde.json"
SYMBOLES = {"commune": "⚪", "peu commune": "🟢", "rare": "🔵", "ultra rare": "🟣", "légendaire": "🟡"}


# ----------------------------------------------------------------------
# Données et sauvegarde
# ----------------------------------------------------------------------
def charger_cartes():
    with open(FICHIER_CARTES, encoding="utf-8") as f:
        return json.load(f)


def charger_sauvegarde():
    if FICHIER_SAUVEGARDE.exists():
        with open(FICHIER_SAUVEGARDE, encoding="utf-8") as f:
            return json.load(f)
    return etat_initial()


def sauvegarder(etat):
    with open(FICHIER_SAUVEGARDE, "w", encoding="utf-8") as f:
        json.dump(etat, f, ensure_ascii=False, indent=2)


# ----------------------------------------------------------------------
# Affichage
# ----------------------------------------------------------------------
def afficher_carte(carte):
    marque = "  ✨ NOUVELLE" if carte["nouvelle"] else ""
    print(f"  {SYMBOLES[carte['rarete']]} {carte['nom']}  [{carte['rarete']}]{marque}")


def afficher_collection(cartes, etat):
    possedees = etat["collection"]
    print(f"\n=== Collection : {len(possedees)}/{len(cartes)} cartes ===")
    for rarete in ORDRE:
        de_cette_rarete = [c for c in cartes if c["rarete"] == rarete]
        if not de_cette_rarete:
            continue
        n = sum(1 for c in de_cette_rarete if str(c["id"]) in possedees)
        print(f"\n{SYMBOLES[rarete]} {rarete.upper()} ({n}/{len(de_cette_rarete)})")
        for c in de_cette_rarete:
            nb = possedees.get(str(c["id"]), 0)
            if nb:
                print(f"  {c['nom']}  x{nb}")
            else:
                print("  ???")


def afficher_stats(etat):
    print(f"\nBoosters ouverts : {etat['boosters_ouverts']}")
    print(f"Boosters depuis le dernier rare ou mieux : {etat['sans_rare']}/{PITIE_APRES}")


# ----------------------------------------------------------------------
# Boucle principale
# ----------------------------------------------------------------------
def main():
    cartes = charger_cartes()
    etat = charger_sauvegarde()

    while True:
        print("\n--- MENU ---")
        print("1. Ouvrir un booster")
        print("2. Voir ma collection")
        print("3. Statistiques")
        print("4. Quitter")
        try:
            choix = input("> ").strip()
        except EOFError:
            break

        if choix == "1":
            print("\nOuverture du booster...")
            tirage, pitie = ouvrir_booster(cartes, etat)
            if pitie:
                print("  (Pitié activée : une carte rare ou mieux t'était garantie !)")
            for carte in tirage:
                afficher_carte(carte)
            sauvegarder(etat)
        elif choix == "2":
            afficher_collection(cartes, etat)
        elif choix == "3":
            afficher_stats(etat)
        elif choix == "4":
            break

    sauvegarder(etat)
    print("À bientôt !")


if __name__ == "__main__":
    main()

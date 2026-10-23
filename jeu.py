"""Jeu de cartes à collectionner : version console.

Lancer avec :  python jeu.py
La logique est dans moteur.py, les cartes dans cartes.json,
la progression dans sauvegarde.json.
"""
import json
from pathlib import Path

from moteur import ORDRE, PITIE_APRES, PITIE_RARETE, etat_initial, ouvrir_booster

DOSSIER = Path(__file__).parent
FICHIER_CARTES = DOSSIER / "cartes.json"
FICHIER_SAUVEGARDE = DOSSIER / "sauvegarde.json"
SYMBOLES = {
    "commune": "⚪",
    "rare": "🔵",
    "super rare": "🟣",
    "ultra rare": "🔴",
    "légendaire": "🟡",
    "secrète": "💠",
}
FINITIONS = {"brillante": "✦ brillante", "arc-en-ciel": "🌈 arc-en-ciel"}


# ----------------------------------------------------------------------
# Données et sauvegarde
# ----------------------------------------------------------------------
def charger_cartes():
    with open(FICHIER_CARTES, encoding="utf-8") as f:
        return json.load(f)


def charger_sauvegarde():
    if FICHIER_SAUVEGARDE.exists():
        with open(FICHIER_SAUVEGARDE, encoding="utf-8") as f:
            etat = json.load(f)
        etat.setdefault("finitions", {})
        return etat
    return etat_initial()


def sauvegarder(etat):
    with open(FICHIER_SAUVEGARDE, "w", encoding="utf-8") as f:
        json.dump(etat, f, ensure_ascii=False, indent=2)


# ----------------------------------------------------------------------
# Affichage
# ----------------------------------------------------------------------
def afficher_carte(carte):
    marque = "  ✨ NOUVELLE" if carte["nouvelle"] else ""
    if carte["nouvelle_finition"]:
        marque = "  ✨ NOUVELLE FINITION"
    fin = f"  {FINITIONS[carte['finition']]}" if carte["finition"] in FINITIONS else ""
    print(f"  {SYMBOLES[carte['rarete']]} {carte['nom']}  [{carte['rarete']}]{fin}{marque}")


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
            cle = str(c["id"])
            nb = possedees.get(cle, 0)
            if nb:
                fins = etat["finitions"].get(cle, {})
                extra = "".join(f"  {FINITIONS[f]} x{k}" for f, k in fins.items() if f in FINITIONS)
                print(f"  {c['nom']}  x{nb}{extra}")
            else:
                print("  ???")


def afficher_stats(etat):
    print(f"\nBoosters ouverts : {etat['boosters_ouverts']}")
    print(f"Boosters depuis la dernière carte {PITIE_RARETE} ou mieux : {etat['sans_rare']}/{PITIE_APRES}")


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
                print(f"  (Pitié activée : une carte {PITIE_RARETE} ou mieux t'était garantie !)")
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

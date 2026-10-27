"""Moteur du jeu de cartes : la logique, sans aucun affichage.

Ce fichier est utilisé deux fois, sans changement :
- par jeu.py, la version console ;
- par index.html, la version web (Python tourne dans le navigateur via Pyodide).
"""
import json
import random

# ----------------------------------------------------------------------
# RÉGLAGES : c'est ici que tu joues avec l'équilibrage
# ----------------------------------------------------------------------
# Chance (en %) qu'UNE carte tirée soit de cette rareté. La commune, c'est le reste.
# Dans un booster de 3 cartes, la chance d'avoir au moins une carte d'une rareté est donc
# un peu moins de 3 fois plus grande (la page Infos du site la calcule pour toi).
_TAUX = {
    "rare": 20,
    "super rare": 6,
    "ultra rare": 1.8,
    "légendaire": 0.5,
    "secrète": 0.05,
}
RARETES = {"commune": round(100 - sum(_TAUX.values()), 4), **_TAUX}
ORDRE = list(RARETES)  # de la plus commune à la plus rare

# Le petit code affiché dans le coin de chaque carte
CODES = {
    "commune": "C",
    "rare": "R",
    "super rare": "SR",
    "ultra rare": "UR",
    "légendaire": "L",
    "secrète": "S",
}

TAILLE_BOOSTER = 3            # nombre de cartes par booster

# Garanties, éteintes pour que les taux ci-dessus soient les vrais taux.
# Pour les rallumer : GARANTIE_DERNIERE = "rare" (la dernière carte est au moins "rare"),
# PITIE_APRES = 8 (après 8 boosters sans carte "super rare" ou mieux, le suivant en contient une).
GARANTIE_DERNIERE = None
PITIE_APRES = None
PITIE_RARETE = "super rare"

# Finitions : chance qu'une carte tirée soit brillante ou arc-en-ciel,
# quelle que soit sa rareté (0.02 = 2 %).
CHANCE_BRILLANTE = 0.02
CHANCE_ARC_EN_CIEL = 0.005

# Monnaie : un doublon (une carte que tu as déjà) rapporte des pièces.
# Plus la carte est rare, plus elle rapporte. Une carte brillante ou arc-en-ciel
# rapporte un peu plus : la valeur est multipliée, puis arrondie.
VALEUR_DOUBLON = {
    "commune": 2,
    "rare": 5,
    "super rare": 12,
    "ultra rare": 30,
    "légendaire": 80,
    "secrète": 250,
}
BONUS_FINITION = {"normale": 1, "brillante": 1.5, "arc-en-ciel": 2}

# Boosters gratuits : un nouveau booster toutes les 15 minutes, 10 au maximum en réserve.
INTERVALLE_SECONDES = 15 * 60
STOCK_MAX = 10
BOOSTERS_DEPART = 3           # boosters offerts à la création d'un compte

# Boutique : "boosters" = boosters normaux ajoutés, "ur" = boosters "ultra rare garantie" ajoutés.
# Les boosters achetés ne sont pas limités par STOCK_MAX.
BOUTIQUE = [
    {"id": "unite", "nom": "1 booster", "prix": 20, "boosters": 1, "ur": 0,
     "texte": "Un booster de plus, tout de suite."},
    {"id": "x10", "nom": "10 boosters", "prix": 180, "boosters": 10, "ur": 0,
     "texte": "Dix boosters pour le prix de neuf."},
    {"id": "ur", "nom": "Booster ultra rare", "prix": 200, "boosters": 0, "ur": 1,
     "texte": "Une carte ultra rare ou mieux est garantie."},
]


# ----------------------------------------------------------------------
# État du joueur
# ----------------------------------------------------------------------
def etat_initial(maintenant=0):
    # collection : {id de la carte (texte): nombre d'exemplaires}
    # finitions  : {id de la carte (texte): {"brillante": n, "arc-en-ciel": n}}
    # monnaie    : pièces gagnées avec les doublons, moins celles dépensées
    # stock      : boosters gratuits en réserve (maximum STOCK_MAX)
    # horloge    : instant (en millisecondes) où a commencé l'attente du prochain booster gratuit
    # achetes    : boosters achetés dans la boutique ; achetes_ur : boosters ultra rare garantie achetés
    return {
        "collection": {}, "finitions": {}, "monnaie": 0, "boosters_ouverts": 0, "sans_rare": 0,
        "stock": BOOSTERS_DEPART, "horloge": int(maintenant), "achetes": 0, "achetes_ur": 0,
    }


def synchroniser(etat, maintenant):
    """Complète une ancienne sauvegarde et ajoute les boosters gagnés avec le temps qui passe."""
    maintenant = int(maintenant)
    for cle, valeur in etat_initial(maintenant).items():
        etat.setdefault(cle, valeur)
    intervalle = INTERVALLE_SECONDES * 1000
    if etat["stock"] >= STOCK_MAX or etat["horloge"] > maintenant:
        etat["horloge"] = maintenant  # réserve pleine : pas d'attente en cours
    else:
        gagnes = (maintenant - etat["horloge"]) // intervalle
        etat["stock"] = min(STOCK_MAX, etat["stock"] + gagnes)
        etat["horloge"] += gagnes * intervalle
        if etat["stock"] >= STOCK_MAX:
            etat["horloge"] = maintenant
    return etat


def boosters_disponibles(etat):
    return etat["stock"] + etat["achetes"]


def utiliser_booster(etat, mode, maintenant):
    """Retire un booster de la réserve (gratuit d'abord, puis acheté). ValueError s'il n'y en a plus."""
    synchroniser(etat, maintenant)
    if mode == "ur":
        if etat["achetes_ur"] <= 0:
            raise ValueError("Tu n'as plus de booster ultra rare garanti.")
        etat["achetes_ur"] -= 1
    elif etat["stock"] > 0:
        if etat["stock"] >= STOCK_MAX:
            etat["horloge"] = int(maintenant)  # la réserve était pleine : l'attente repart maintenant
        etat["stock"] -= 1
    elif etat["achetes"] > 0:
        etat["achetes"] -= 1
    else:
        raise ValueError("Tu n'as plus de booster. Le prochain arrive bientôt.")


def acheter(etat, offre_id, maintenant):
    """Achète une offre de la boutique. Renvoie None si c'est réussi, sinon le message d'erreur."""
    synchroniser(etat, maintenant)
    offre = next((o for o in BOUTIQUE if o["id"] == offre_id), None)
    if offre is None:
        return "Cette offre n'existe pas."
    if etat["monnaie"] < offre["prix"]:
        return "Tu n'as pas assez de pièces."
    etat["monnaie"] -= offre["prix"]
    etat["achetes"] += offre["boosters"]
    etat["achetes_ur"] += offre["ur"]
    return None


# ----------------------------------------------------------------------
# Logique de tirage
# ----------------------------------------------------------------------
def tirer_carte(cartes, rarete_min=None):
    """Tire une carte au hasard, avec les probabilités de RARETES."""
    debut = ORDRE.index(rarete_min) if rarete_min else 0
    # on ne garde que les raretés qui ont au moins une carte
    possibles = [r for r in ORDRE[debut:] if any(c["rarete"] == r for c in cartes)]
    if not possibles:  # aucune carte assez rare : on se rabat sur toutes celles qui existent
        possibles = [r for r in ORDRE if any(c["rarete"] == r for c in cartes)]
    rarete = random.choices(possibles, weights=[RARETES[r] for r in possibles])[0]
    return random.choice([c for c in cartes if c["rarete"] == rarete])


def valeur_doublon(rarete, finition):
    """Pièces gagnées quand on tire un doublon de cette rareté et de cette finition."""
    return int(VALEUR_DOUBLON[rarete] * BONUS_FINITION[finition] + 0.5)


def tirer_finition():
    x = random.random()
    if x < CHANCE_ARC_EN_CIEL:
        return "arc-en-ciel"
    if x < CHANCE_ARC_EN_CIEL + CHANCE_BRILLANTE:
        return "brillante"
    return "normale"


def tirer_booster(cartes, etat, mode="normal"):
    """Tire les cartes d'un booster et met la collection à jour (sans toucher à la réserve de boosters).

    mode "ur" : booster ultra rare garanti (au moins une carte ultra rare ou mieux).
    Renvoie (liste de cartes, pitie_declenchee). Chaque carte est une copie
    avec des clés en plus :
    - "finition" : "normale", "brillante" ou "arc-en-ciel"
    - "nouvelle" : True si le joueur ne possédait pas encore cette carte
    - "nouvelle_finition" : True si la carte est déjà possédée mais pas dans cette finition
    - "pieces" : pièces gagnées (0 si la carte est nouvelle, sinon la valeur du doublon)
    """
    etat.setdefault("finitions", {})
    etat.setdefault("monnaie", 0)
    etat.setdefault("sans_rare", 0)

    tirage = [tirer_carte(cartes) for _ in range(TAILLE_BOOSTER)]
    if GARANTIE_DERNIERE:
        tirage[-1] = tirer_carte(cartes, GARANTIE_DERNIERE)  # dernière carte : rareté minimale

    def au_moins(liste, rarete):
        seuil = ORDRE.index(rarete)
        return any(ORDRE.index(c["rarete"]) >= seuil for c in liste)

    # booster ultra rare garanti : si le tirage n'en contient pas, la dernière carte en devient une
    if mode == "ur" and not au_moins(tirage, "ultra rare"):
        tirage[-1] = tirer_carte(cartes, "ultra rare")

    # système de pitié (éteint par défaut)
    pitie = False
    if PITIE_APRES and etat["sans_rare"] >= PITIE_APRES and not au_moins(tirage, PITIE_RARETE):
        tirage[-1] = tirer_carte(cartes, PITIE_RARETE)
        pitie = True

    # on trie de la plus commune à la plus rare, pour le suspense
    tirage.sort(key=lambda c: ORDRE.index(c["rarete"]))

    # finitions, et quelles cartes sont nouvelles (un doublon dans le même booster ne l'est pas)
    deja = set(etat["collection"])
    finitions_vues = {cle: set(v) for cle, v in etat["finitions"].items()}
    resultat = []
    for c in tirage:
        cle = str(c["id"])
        fin = tirer_finition()
        nouvelle = cle not in deja
        nouvelle_fin = (not nouvelle) and fin != "normale" and fin not in finitions_vues.get(cle, set())
        pieces = 0 if nouvelle else valeur_doublon(c["rarete"], fin)
        resultat.append({**c, "finition": fin, "nouvelle": nouvelle, "nouvelle_finition": nouvelle_fin, "pieces": pieces})
        deja.add(cle)
        if fin != "normale":
            finitions_vues.setdefault(cle, set()).add(fin)

    # mise à jour de l'état
    if au_moins(tirage, PITIE_RARETE):
        etat["sans_rare"] = 0
    else:
        etat["sans_rare"] += 1
    etat["boosters_ouverts"] = etat.get("boosters_ouverts", 0) + 1
    for c in resultat:
        cle = str(c["id"])
        etat["collection"][cle] = etat["collection"].get(cle, 0) + 1
        etat["monnaie"] += c["pieces"]
        if c["finition"] != "normale":
            f = etat["finitions"].setdefault(cle, {})
            f[c["finition"]] = f.get(c["finition"], 0) + 1
    return resultat, pitie


def ouvrir_booster(cartes, etat, maintenant, mode="normal"):
    """Utilise un booster de la réserve, puis le tire. ValueError s'il n'y en a plus."""
    utiliser_booster(etat, mode, maintenant)
    return tirer_booster(cartes, etat, mode)


# ----------------------------------------------------------------------
# Passerelle pour la page web (JavaScript <-> Python, en texte JSON)
# ----------------------------------------------------------------------
def reglages_web():
    return json.dumps({
        "ordre": ORDRE,
        "codes": [CODES[r] for r in ORDRE],
        "poids": [RARETES[r] for r in ORDRE],
        "valeurs": [VALEUR_DOUBLON[r] for r in ORDRE],
        "bonus": BONUS_FINITION,
        "chance_brillante": CHANCE_BRILLANTE,
        "chance_arc": CHANCE_ARC_EN_CIEL,
        "garantie_derniere": GARANTIE_DERNIERE,
        "taille_booster": TAILLE_BOOSTER,
        "pitie_apres": PITIE_APRES,
        "pitie_rarete": PITIE_RARETE,
        "intervalle_ms": INTERVALLE_SECONDES * 1000,
        "stock_max": STOCK_MAX,
        "depart": BOOSTERS_DEPART,
        "boutique": BOUTIQUE,
    }, ensure_ascii=False)


def nouvel_etat_web(maintenant):
    return json.dumps(etat_initial(maintenant), ensure_ascii=False)


def synchroniser_web(etat_json, maintenant):
    return json.dumps(synchroniser(json.loads(etat_json), maintenant), ensure_ascii=False)


def ouvrir_booster_web(cartes_json, etat_json, maintenant, mode):
    cartes = json.loads(cartes_json)
    etat = json.loads(etat_json)
    try:
        tirage, pitie = ouvrir_booster(cartes, etat, maintenant, mode)
    except ValueError as e:
        return json.dumps({"erreur": str(e), "etat": etat}, ensure_ascii=False)
    return json.dumps({"cartes": tirage, "pitie": pitie, "etat": etat}, ensure_ascii=False)


def acheter_web(etat_json, offre_id, maintenant):
    etat = json.loads(etat_json)
    erreur = acheter(etat, offre_id, maintenant)
    return json.dumps({"erreur": erreur, "etat": etat}, ensure_ascii=False)

# -*- coding: utf-8 -*-

# Nicolas, 2021-03-05
from __future__ import absolute_import, print_function, unicode_literals

import random
import copy
import numpy as np
import sys
from itertools import chain


import pygame

from pySpriteWorld.gameclass import Game, check_init_game_done
from pySpriteWorld.spritebuilder import SpriteBuilder
from pySpriteWorld.players import Player
from pySpriteWorld.sprite import MovingSprite
from pySpriteWorld.ontology import Ontology
import pySpriteWorld.glo

from search.grid2D import ProblemeGrid2D
from search import probleme


# ---- ---- ---- ---- ---- ----
# ---- Misc                ----
# ---- ---- ---- ---- ---- ----


# ---- ---- ---- ---- ---- ----
# ---- Main                ----
# ---- ---- ---- ---- ---- ----

game = Game()


def init(_boardname=None):
    global player, game
    name = _boardname if _boardname is not None else 'FMap'
    game = Game('Cartes/' + name + '.json', SpriteBuilder)
    game.O = Ontology(True, 'SpriteSheet-32x32/tiny_spritesheet_ontology.csv')
    game.populate_sprite_names(game.O)
    game.fps = 2  # frames per second
    game.mainiteration()
    player = game.player


def main():

    # for arg in sys.argv:
    iterations = 100  # default
    if len(sys.argv) == 2:
        iterations = int(sys.argv[1])
    print("Iterations: ")
    print(iterations)

    init()

    # -------------------------------
    # Initialisation
    # -------------------------------

    nbLignes = game.spriteBuilder.rowsize
    nbCols = game.spriteBuilder.colsize

    print("lignes", nbLignes)
    print("colonnes", nbCols)

    players = [o for o in game.layers['joueur']]
    nbPlayers = len(players)

    # on localise tous les états initiaux (loc du joueur)
    # positions initiales des joueurs
    initStates = [o.get_rowcol() for o in game.layers['joueur']]
    print("Init states:", initStates)

    # on localise tous les objets ramassables
    # sur le layer ramassable
    goalStates = [o.get_rowcol() for o in game.layers['ramassable']]
    print("Goal states:", goalStates)

    # on localise tous les murs
    # sur le layer obstacle
    wallStates = [w.get_rowcol() for w in game.layers['obstacle']]
    print("Wall states:", wallStates)

    def legal_position(row, col):
        # une position legale est dans la carte et pas sur un mur
        return ((row, col) not in wallStates) and row >= 0 and row < nbLignes and col >= 0 and col < nbCols

    # -------------------------------
    # Attributaion aleatoire des fioles
    # -------------------------------

    random.seed(10)

    objectifs = copy.deepcopy(goalStates)
    random.shuffle(objectifs)

    # -------------------------------
    # Carte : FMap
    # 6 joueurs en 2 équipe
    # calcul GBF pour tous
    # -------------------------------
    joueur = copy.deepcopy(initStates)

    equipe1 = []
    equipe2 = []
    objectifs1 = []
    objectifs2 = []

    for i in range(nbPlayers):
        if len(equipe1) == (nbPlayers//2):
            equipe2.append(joueur[i])
            objectifs2.append(objectifs[i])
        else:
            equipe1.append(joueur[i])
            objectifs1.append(objectifs[i])

    print("Equipe 1:")
    print("\tJoueurs : {}".format(equipe1))
    print("\tObjectifs : {}".format(objectifs1))

    print("Equipe 2:")
    print("\tJoueurs : {}".format(equipe2))
    print("\tObjectifs : {}".format(objectifs2))

    # -----------------------------------------------------
    # Calcul GBF pour tous les joueurs et tous les objectifs
    # -----------------------------------------------------

    cheminEQU1 = []
    cheminEQU2 = []

    for i in range(len(equipe1)):
        for j in range(len(objectifs1)):
            # par defaut la matrice comprend des True
            g = np.ones((nbLignes, nbCols), dtype=bool)
            for w in wallStates:            # putting False for walls
                g[w] = False
            p = ProblemeGrid2D(equipe1[i], objectifs1[j], g, 'manhattan')
            path = probleme.greedy_best_first(p)
            cheminEQU1.append((i+1, j+1, path))

    for i in range(len(equipe2)):
        for j in range(len(objectifs2)):
            # par defaut la matrice comprend des True
            g = np.ones((nbLignes, nbCols), dtype=bool)
            for w in wallStates:            # putting False for walls
                g[w] = False
            p = ProblemeGrid2D(equipe2[i], objectifs2[j], g, 'manhattan')
            path = probleme.astar(p)
            cheminEQU2.append((i+4, j+4, path))

    # --------------------------------------------
    # Détermination des chemins les plus optimisés
    # --------------------------------------------

    optiPATH1 = []
    optiPATH2 = []
    tmpJOU = set()
    tmpOBJ = set()

    cheminEQU1.sort(key=lambda a: len(a[2]))
    cheminEQU2.sort(key=lambda a: len(a[2]))

    for i in cheminEQU1:
        if i[0] not in tmpJOU and i[1] not in tmpOBJ:
            optiPATH1.append(i)
            tmpJOU.add(i[0])
            tmpOBJ.add(i[1])

    tmpJOU = set()
    tmpOBJ = set()

    for i in cheminEQU2:
        if i[0] not in tmpJOU and i[1] not in tmpOBJ:
            optiPATH2.append(i)
            tmpJOU.add(i[0])
            tmpOBJ.add(i[1])

    # ----------------------------------
    # Boucle principale de déplacements
    # ----------------------------------

    def calcul_de_chemin(IndiceDuJoueurActuel, Equipe):
        tempGrille = copy.deepcopy(g)
        tempPOS = copy.deepcopy(posPlayers)
        for j in range(6):
            if j != IndiceDuJoueurActuel:
                tempGrille[tempPOS[j]] = False

        if Equipe == 1:
            p = ProblemeGrid2D(
                tempPOS[IndiceDuJoueurActuel], objectifs[optiPATH1[IndiceDuJoueurActuel][1]-1], tempGrille, 'manhattan')
            chemin = probleme.greedy_best_first(p)
            chemin = chemin[1:]
            return (optiPATH1[IndiceDuJoueurActuel][0], optiPATH1[IndiceDuJoueurActuel][1], chemin)

        if Equipe == 2:
            p = ProblemeGrid2D(tempPOS[IndiceDuJoueurActuel+3],
                               objectifs[optiPATH2[IndiceDuJoueurActuel][1]-1], tempGrille, 'manhattan')
            chemin = probleme.astar(p)
            return (optiPATH2[IndiceDuJoueurActuel][0], optiPATH2[IndiceDuJoueurActuel][1], chemin)

    def Check(TourActuel, IndiceDuJoueurActuel, Equipe):
        if Equipe == 1:
            try:
                if optiPATH1[IndiceDuJoueurActuel][2][TourActuel+1] in posPlayers:
                    return 1
            except IndexError:
                return 0
        if Equipe == 2:
            try:
                if optiPATH2[IndiceDuJoueurActuel][2][TourActuel+1] in posPlayers:
                    return 1
            except IndexError:
                return 0

    posPlayers = initStates
    Success = []
    nb_Joueurs_restants = 6
    ScoreOBJ = [0, 0]
    ScoreCHE = [0, 0]

    a = 0
    b = 0
    c = 0
    d = 0
    e = 0
    f = 0

    for i in range(6):
        Success.append(False)

    for i in range(iterations):

        # on fait bouger chaque joueur séquentiellement

        if Success[0] == False:

            if Check(a, 0, 1) == 1:
                optiPATH1[0] = calcul_de_chemin(0, 1)
                a = 0

            row, col = optiPATH1[0][2][a]
            posPlayers[0] = (row, col)
            players[0].set_rowcol(row, col)
            ScoreCHE[0] += 1
            print("pos joueur 1:", row, col)
            if (row, col) == objectifs[optiPATH1[0][1]-1]:
                ScoreOBJ[0] += 1
                nb_Joueurs_restants -= 1
                print("le joueur 1 a atteint son but!")
                Success[0] = True

        if Success[1] == False:

            if Check(b, 1, 1) == 1:
                optiPATH1[1] = calcul_de_chemin(1, 1)
                b = 0

            row, col = optiPATH1[1][2][b]
            posPlayers[1] = (row, col)
            players[1].set_rowcol(row, col)
            ScoreCHE[0] += 1
            print("pos joueur 2:", row, col)
            if (row, col) == objectifs[optiPATH1[1][1]-1]:
                ScoreOBJ[0] += 1
                nb_Joueurs_restants -= 1
                print("le joueur 2 a atteint son but!")
                Success[1] = True

        if Success[2] == False:

            if Check(c, 2, 1) == 1:
                optiPATH1[2] = calcul_de_chemin(2, 1)
                c = 0

            row, col = optiPATH1[2][2][c]
            posPlayers[2] = (row, col)
            players[2].set_rowcol(row, col)
            ScoreCHE[0] += 1
            print("pos joueur 3:", row, col)
            if (row, col) == objectifs[optiPATH1[2][1]-1]:
                ScoreOBJ[0] += 1
                nb_Joueurs_restants -= 1
                print("le joueur 3 a atteint son but!")
                Success[2] = True

        if Success[3] == False:

            if Check(d, 0, 2) == 1:
                optiPATH2[0] = calcul_de_chemin(0, 2)
                d = 0

            row, col = optiPATH2[0][2][d]
            posPlayers[3] = (row, col)
            players[3].set_rowcol(row, col)
            ScoreCHE[1] += 1
            print("pos joueur 4:", row, col)
            if (row, col) == objectifs[optiPATH2[0][1]-1]:
                ScoreOBJ[1] += 1
                nb_Joueurs_restants -= 1
                print("le joueur 4 a atteint son but!")
                Success[3] = True

        if Success[4] == False:

            if Check(e, 1, 2) == 1:
                optiPATH2[1] = calcul_de_chemin(1, 2)
                e = 0

            row, col = optiPATH2[1][2][e]
            posPlayers[4] = (row, col)
            players[4].set_rowcol(row, col)
            ScoreCHE[1] += 1
            print("pos joueur 5:", row, col)
            if (row, col) == objectifs[optiPATH2[1][1]-1]:
                ScoreOBJ[1] += 1
                nb_Joueurs_restants -= 1
                print("le joueur 5 a atteint son but!")
                Success[4] = True

        if Success[5] == False:

            if Check(f, 2, 2) == 1:
                optiPATH2[2] = calcul_de_chemin(2, 2)
                f = 0

            row, col = optiPATH2[2][2][f]
            posPlayers[5] = (row, col)
            players[5].set_rowcol(row, col)
            ScoreCHE[1] += 1
            print("pos joueur 6:", row, col)
            if (row, col) == objectifs[optiPATH2[2][1]-1]:
                ScoreOBJ[1] += 1
                nb_Joueurs_restants -= 1
                print("le joueur 6 a atteint son but!")
                Success[5] = True

        a += 1
        b += 1
        c += 1
        d += 1
        e += 1
        f += 1

        if nb_Joueurs_restants == 0:
            break

        # on passe a l'iteration suivante du jeu
        game.mainiteration()

    print("ScoreOBJ équipe 1:", ScoreOBJ[0])
    print("ScoreOBJ équipe 2:", ScoreOBJ[1])
    if ScoreOBJ[0] > ScoreOBJ[1]:
        print("l'équipe 1 est gagnante")
    if ScoreOBJ[0] < ScoreOBJ[1]:
        print("l'équipe 2 est gagnante")
    else:
        print("ScoreCHE équipe 1:", ScoreCHE[0])
        print("ScoreCHE équipe 2:", ScoreCHE[1])
        if ScoreCHE[0] < ScoreCHE[1]:
            print("l'équipe 1 est gagnante")
        if ScoreCHE[0] > ScoreCHE[1]:
            print("l'équipe 2 est gagnante")
        if ScoreCHE[0] == ScoreCHE[1]:
            print("Nous avons une égalité")

    pygame.quit()


    # -------------------------------
if __name__ == '__main__':
    main()

# -*- coding: utf-8 -*-

# Nicolas, 2021-03-05
from __future__ import absolute_import, print_function, unicode_literals

import random
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
    game.fps = 50  # frames per second
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
    score = [0]*nbPlayers

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
    objectifs = goalStates
    random.shuffle(objectifs)
    print("Objectif joueur 0", objectifs[0])
    print("Objectif joueur 1", objectifs[1])

    listpath = []  # Tout les chemins seront mis dans cette liste
    listAlgo = [0, 0, 0, 2, 2, 2]
    ################# LISTE ALGO #########################
    # 0 : Greedy Best first
    # 1 : Astar
    # 2 : Random
    ################# LISTE ALGO #########################
    listProblems = []
    listeIteration = [0]*nbPlayers

    # creation chemin pour joueur
    for i in range(nbPlayers):

        # par defaut la matrice comprend des True
        g = np.ones((nbLignes, nbCols), dtype=bool)
        for w in wallStates:            # putting False for walls
            g[w] = False
        p = ProblemeGrid2D(initStates[i], objectifs[i], g, 'manhattan')
        listProblems.append(p)
        if(listAlgo[i] == 0):
            path = probleme.greedy_best_first(p)
        if(listAlgo[i] == 1):
            path = probleme.astar(p)
        if(listAlgo[i] == 2):
            path = probleme.random_first(p)
        print("Chemin trouvé:", path)
        listpath.append(path)

    posPlayers = initStates

    for i in range(iterations):
        for j in range(len(posPlayers)):
            # on fait bouger chaque joueur séquentiellement
            if(len(listpath[j]) > 0):
                for k in range(len(posPlayers)):
                    if (k != j):
                        if(len(listpath[k]) > 0):
                            # Cas ou le joueur 1 et joueur 2 vont sur la même case
                            if(listpath[j][0] == listpath[k][0]):
                                row, col = listpath[k][0]
                                listProblems[j].grid[row][col] = False
                                if(listAlgo[j] == 0):
                                    listpath[j] = probleme.greedy_best_first(
                                        listProblems[j])
                                if(listAlgo[j] == 1):
                                    listpath[j] = probleme.astar(
                                        listProblems[j])
                                if(listAlgo[j] == 2):
                                    listpath[j] = probleme.random_first(
                                        listProblems[j])
                                print("Chemin trouvé:", listpath[j])
                                listProblems[j].grid[row][col] = True
                        else:  # Cas joueur k immobile
                            if(listpath[j][0] == posPlayers[k]):
                                row, col = posPlayers[k]
                                listProblems[j].grid[row][col] = False
                                if(listAlgo[j] == 0):
                                    listpath[j] = probleme.greedy_best_first(
                                        listProblems[j])
                                if(listAlgo[j] == 1):
                                    listpath[j] = probleme.astar(
                                        listProblems[j])
                                if(listAlgo[j] == 2):
                                    listpath[j] = probleme.random_first(
                                        listProblems[j])
                                print("Chemin trouvé:", listpath[j])
                                listProblems[j].grid[row][col] = True

            if(len(listpath[j]) > 0):
                row, col = listpath[j][0]
                posPlayers[j] = (row, col)
                listProblems[j].init = (row, col)
                players[j].set_rowcol(row, col)
                listpath[j] = listpath[j][1::]
                listeIteration[j] += 1
            else:
                row, col = posPlayers[j]

            print("pos ", j, ":", row, col)
            if (row, col) == objectifs[j] and (score[j] == 0):
                score[j] += 1
                print("le joueur 0 a atteint son but!")
        # on passe a l'iteration suivante du jeu

        game.mainiteration()

        if(sum(score) == nbPlayers):
            break
    listeEquipe1 = []
    listeEquipe2 = []

    equipe1 = listeEquipe1.append(listeIteration[0])
    equipe1 = listeEquipe1.append(listeIteration[1])
    equipe1 = listeEquipe1.append(listeIteration[2])

    equipe2 = listeEquipe2.append(listeIteration[3])
    equipe2 = listeEquipe2.append(listeIteration[4])
    equipe2 = listeEquipe2.append(listeIteration[5])

    if(sum(listeEquipe1) > sum(listeEquipe2)):
        print("Equipe 2 Gagnante")
    else:
        print("Equipe 1 Gagnante")

    print("score Equipe1 :", sum(listeEquipe1))
    print("score Equipe2 :", sum(listeEquipe2))

    print("nombre d'itération de tout le monde:", listeIteration)
    print("scores:", score)
    pygame.quit()


if __name__ == '__main__':
    main()

from showdown.battle import Battle

from ..helpers import format_decision

from showdown.engine.objects import StateMutator
from showdown.engine.select_best_move import pick_safest
from showdown.engine.select_best_move import get_payoff_matrix

from config import logger

from anytree import Node, RenderTree, PreOrderIter
from random import shuffle, randint

class BattleBot(Battle):
    def __init__(self, *args, **kwargs):
        super(BattleBot, self).__init__(*args, **kwargs)

    def find_best_move(self):
        battles = self.prepare_battles(join_moves_together=True)
        move = self.pick_move_from_battles(battles)
        return format_decision(self, move)

    def aggressive_pick(self, root, safety):
        bestAveNode = None
        bestAve = -float('inf')
        for myMove in root.children:
            moveScores = []
            for opMove in myMove.children:
                moveScores.append(opMove.children[0])
            
            s = 0
            for m in moveScores:
                s += float(m.name)
            s += safety*int(min(moveScores, key=lambda x: float(x.name)).name)
            weightedAve = s / (len(moveScores) + safety)
            if weightedAve > bestAve:
                bestAveNode = moveScores[0]
                bestAve = weightedAve
            elif weightedAve == bestAve and bool(randint(0,1)):
                bestAveNode = moveScores[0]
                bestAve = weightedAve
        
        return bestAveNode.parent.parent.name

    def pick_move_from_battles(self, battles):
        # Only work on current battle
        # In practice the bot can play several at once, for now we simplified to one battle.
        battle = battles[0]
        root = Node("Root")

        state = battle.create_state()
        mutator = StateMutator(state)
        user_options, opponent_options = battle.get_all_options()
        logger.debug("Attempting to find best move from: {}".format(mutator.state))
        #get the scores from the "safest" algorithm provided by the starter code
        scores = get_payoff_matrix(mutator, user_options, opponent_options, depth=2, prune=False)

        # Create tree using payoff matrix from "Safest" algorithm
        checked_moves = {}
        for (myMove, opponentMove), score in scores.items():
            #checked moves keeps track of which nodes have been added to the tree, so we dont duplicate.
            if myMove not in checked_moves:
                child = Node(myMove, root)
                checked_moves[myMove] = child
            grandchild = Node(opponentMove, checked_moves[myMove])
            Node(score, grandchild)

        # a library function that prints our tree for readability.
        for pre, _, node in RenderTree(root):
            print("%s%s" % (pre, node.name))

        myTotalHP = 0.0 # max of 600, 100 points for full hp
        oppTotalHP = 0.0

        # calculate my total hp
        my_pokes = state.self
        # get active pokemon hp if it isn't dead
        if my_pokes.active.maxhp != 0:
            myTotalHP += my_pokes.active.hp / my_pokes.active.maxhp
        # get reserve pokmeons hps
        for p in my_pokes.reserve.values():
            if p.maxhp !=0:
                myTotalHP += p.hp / p.maxhp
        myTotalHP *= 100

        # calculate opp total hp
        opp_pokes = state.opponent
        # get active pokemon hp
        if opp_pokes.active.maxhp != 0:
            oppTotalHP += opp_pokes.active.hp / opp_pokes.active.maxhp
        # get reserve pokmeons hps
        for p in opp_pokes.reserve.values():
            if p.maxhp !=0:
                oppTotalHP += p.hp / p.maxhp
        
        #accounts for the pokemon of opponent that have not been revealed
        unseenPoke = 5-len(opp_pokes.reserve)
        oppTotalHP += unseenPoke
        oppTotalHP *=100

        possibleStatuses = {
            "psn" : .06,
            "frz" : .25,
            "tox" : .19,
            "par" : .16,
            "slp" : .16,
            "brn" : .20,
            None: 0,
        }

        statBuffs = {
            6 : .25,
            5 : .235,
            4 : .22,
            3 : .19,
            2 : .15,
            1 : .08,
            0 : 0,
            -1 : -.08,
            -2 : -.15,
            -3 : -.19,
            -4 : -.22,
            -5 : -.235,
            -6 : -.25,
        }

        # check how many status conditions we have
        myStatuses = 0
        # active pokemon
        myStatuses += possibleStatuses[my_pokes.active.status]
        # reserve pokemon
        for p in my_pokes.reserve.values():
            myStatuses += possibleStatuses[p.status]

        # check how many status conditions opponent has
        opponentStatuses = 0
        # active pokemon
        opponentStatuses += possibleStatuses[opp_pokes.active.status]
        # reserve pokemon
        for p in opp_pokes.reserve.values():
            opponentStatuses += possibleStatuses[p.status]

        status_aggression_multiplier = 1
        status_aggression_modifier = (opponentStatuses - myStatuses) * status_aggression_multiplier
        print(f"Status modifier:{status_aggression_modifier}")

        # Stat Buffs
        # check how many stat boosts/nerfs we have
        myBuffs = 0
        # active pokemon
        myBuffs += statBuffs[my_pokes.active.accuracy_boost]
        myBuffs += statBuffs[my_pokes.active.attack_boost]
        myBuffs += statBuffs[my_pokes.active.defense_boost]
        myBuffs += statBuffs[my_pokes.active.evasion_boost]
        myBuffs += statBuffs[my_pokes.active.special_attack_boost]
        myBuffs += statBuffs[my_pokes.active.special_defense_boost]
        myBuffs += statBuffs[my_pokes.active.speed_boost]
        
        # check how many stat boosts/nerfs opponent has
        oppBuffs = 0
        # active pokemon
        oppBuffs += statBuffs[opp_pokes.active.accuracy_boost]
        oppBuffs += statBuffs[opp_pokes.active.attack_boost]
        oppBuffs += statBuffs[opp_pokes.active.defense_boost]
        oppBuffs += statBuffs[opp_pokes.active.evasion_boost]
        oppBuffs += statBuffs[opp_pokes.active.special_attack_boost]
        oppBuffs += statBuffs[opp_pokes.active.special_defense_boost]
        oppBuffs += statBuffs[opp_pokes.active.speed_boost]

        buff_aggression_multiplier = 1
        buff_aggression_modifier = (myBuffs - oppBuffs) * buff_aggression_multiplier
        print(f"Buff modifier:{buff_aggression_modifier}")

        safety = (3 + status_aggression_modifier + buff_aggression_modifier) * myTotalHP/oppTotalHP
        if safety < 0:
            print("WARNING: safety constant is less than 0, changing to 0.1")
            safety = 0.1
        print(f"bot will play with safety constant of {safety}")
        bot_choice = self.aggressive_pick(root,safety)
        print(f"choice: {bot_choice}")
        print(f"the safest pick was {self.safest_pick(root)}")

        print("Choice: {}".format(bot_choice))
        return bot_choice

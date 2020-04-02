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

    def top_quartile_strat(self, root):
        # WHEN YOU'RE BEHIND
        best25percentileNode = None
        for myMove in root.children:
            moveScores = []
            for opMove in myMove.children:
                moveScores.append(opMove.children[0])
            moveScores.sort(key=lambda x: float(x.name))
            # get the top quarter percentile score
            topQuarter = moveScores[int(len(moveScores) * .75)]
            print(f"Top Quartile for {topQuarter.parent.parent.name}: {topQuarter.name}")
            s = 0
            for m in moveScores:
                s += float(m.name)
            print(f"Average for that: {s / len(moveScores)}")
            print()
            if best25percentileNode == None or float(topQuarter.name) > float(best25percentileNode.name):
                best25percentileNode = topQuarter
        
        return best25percentileNode.parent.parent.name

    def top_3_moves_strat(self, root):
        # Perform depth first search
        # our modification for this milestone was taking a randomization of the top 3 safest moves
        top3Score = []
        for myMove in root.children:

            for opMove in myMove.children:
                # the only child of opMove is the score
                # until we have our three top moves, just add any move
                if len(top3Score) < 3:
                    top3Score.append(opMove.children[0])
                elif float(opMove.children[0].name) == float(min(top3Score, key=lambda x: float(x.name)).name):
                    # if score is the same, randomly choose to add to top 3
                    # avoid determenistically favoring later in alphabet moves
                    if bool(randint(0,1)):
                        top3Score.remove(min(top3Score, key=lambda x: float(x.name)))
                        top3Score.append(opMove.children[0])
                    #if better move is found, we remove the minimum value from the top 3.
                elif float(opMove.children[0].name) > float(min(top3Score, key=lambda x: float(x.name)).name):
                    top3Score.remove(min(top3Score, key=lambda x: float(x.name)))
                    top3Score.append(opMove.children[0])

        # print our results
        print("top 3 choices:")
        for move in top3Score:
            print(move.parent.parent.name, move.name)
        print("")
        shuffle(top3Score)
        return top3Score.pop().parent.parent.name

    def aggressive_pick(self, root, safety):
        # WHEN YOU'RE BEHIND
        bestAveNode = None
        bestAve = -float('inf')
        for myMove in root.children:
            moveScores = []
            for opMove in myMove.children:
                moveScores.append(opMove.children[0])
            
            s = 0
            for m in moveScores:
                s += float(m.name)
            # print(f"Average for {moveScores[0].parent.parent.name}: {s / len(moveScores)}")
            s += safety*int(min(moveScores, key=lambda x: float(x.name)).name)
            weightedAve = s / (len(moveScores) + safety)
            # print(f"Weighted average for {moveScores[0].parent.parent.name}: {weightedAve}")
            # print()
            if weightedAve > bestAve:
                bestAveNode = moveScores[0]
                bestAve = weightedAve
            elif weightedAve == bestAve and bool(randint(0,1)):
                bestAveNode = moveScores[0]
                bestAve = weightedAve
        
        return bestAveNode.parent.parent.name

    def safest_pick(self, root):
        # WHEN YOU'RE AHEAD
        safestNode = None
        safestMin = -float('inf')
        for myMove in root.children:
            moveScores = []
            for opMove in myMove.children:
                moveScores.append(opMove.children[0])
            
            minScore = int(min(moveScores, key=lambda x: float(x.name)).name)
            # print(f"Min Score for {moveScores[0].parent.parent.name}: {minScore}")
            # print()
            if minScore > safestMin:
                safestNode = moveScores[0]
                safestMin = minScore
            elif minScore == safestMin and bool(randint(0,1)):
                safestNode = moveScores[0]
                safestMin = minScore
        
        return safestNode.parent.parent.name

    def pick_move_from_battles(self, battles):
        # Only work on current battle
        # In practice the bot can play several at once, for now we simplified to one battle.
        battle = battles[0]
        root = Node("Root")

        # with open('battleFile.obj', 'wb') as f:
        #     pickle.dump(battle, f)

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

        """
        POKEMON_STATIC_STATUSES = {
            constants.FROZEN: -40,
            constants.SLEEP: -25,
            constants.PARALYZED: -25,
            constants.TOXIC: -30,
            constants.POISON: -10,
            None: 0
        }
        """
        possibleStatuses = {
            "psn" : .06,
            "frz" : .25,
            "tox" : .19,
            "par" : .16,
            "slp" : .16,
            "brn" : .20,
            None: 0,
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


        # if myTotalHP > oppTotalHP:
        #     print("We are ahead, bot will play safe")
        #     bot_choice = self.safest_pick(root)
        # else:
        #the higher the safety constant, the more likely we will choose the safest move. The lower, the more aggressive our bot will play
        safety = (3 + status_aggression_modifier) * myTotalHP/oppTotalHP
        if safety < 0:
            print("WARNING: safety constant is less than 0, changing to 0.1")
            safety = 0.1
        print(f"we are behind, bot will play aggressively with safety constant of {safety}")
        bot_choice = self.aggressive_pick(root,safety)
        print(f"choice: {bot_choice}")
        print(f"the safest pick was {self.safest_pick(root)}")

        print("Choice: {}".format(bot_choice))
        return bot_choice

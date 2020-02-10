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
        safest_move = self.pick_move_from_battles(battles)
        return format_decision(self, safest_move)

    def pick_move_from_battles(self, battles):
        # Only work on current battle
        battle = battles[0]
        root = Node("Root")

        # with open('battleFile.obj', 'wb') as f:
        #     pickle.dump(battle, f)

        state = battle.create_state()
        mutator = StateMutator(state)
        user_options, opponent_options = battle.get_all_options()
        logger.debug("Attempting to find best move from: {}".format(mutator.state))
        scores = get_payoff_matrix(mutator, user_options, opponent_options, depth=2, prune=True)

        # Create tree using payoff matrix from "Safest" algorithm
        checked_moves = {}
        for (myMove, opponentMove), score in scores.items():
            if myMove not in checked_moves:
                child = Node(myMove, root)
                checked_moves[myMove] = child
            grandchild = Node(opponentMove, checked_moves[myMove])
            Node(score, grandchild)

        for pre, _, node in RenderTree(root):
            print("%s%s" % (pre, node.name))

        # Perform depth first search
        top3Score = []
        for myMove in root.children:
            for opMove in myMove.children:
                # the only child of opMove is the score
                if len(top3Score) < 3:
                    top3Score.append(opMove.children[0])
                elif float(opMove.children[0].name) == float(min(top3Score, key=lambda x: float(x.name)).name):
                    # if score is the same, randomly choose to add to top 3
                    if bool(randint(0,1)):
                        top3Score.remove(min(top3Score, key=lambda x: float(x.name)))
                        top3Score.append(opMove.children[0])
                elif float(opMove.children[0].name) > float(min(top3Score, key=lambda x: float(x.name)).name):
                    top3Score.remove(min(top3Score, key=lambda x: float(x.name)))
                    top3Score.append(opMove.children[0])

        print("top 3 choices:")
        for move in top3Score:
            print(move.parent.parent.name, move.name)
        print("")
        shuffle(top3Score)
        bot_choice = top3Score.pop().parent.parent.name
        print(bot_choice)

        print("Choice: {}".format(bot_choice))
        return bot_choice
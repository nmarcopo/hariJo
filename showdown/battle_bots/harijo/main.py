from showdown.battle import Battle

from ..helpers import format_decision

from showdown.engine.objects import StateMutator
from showdown.engine.select_best_move import pick_safest
from showdown.engine.select_best_move import get_payoff_matrix

from config import logger

from anytree import Node, RenderTree, PreOrderIter
from random import shuffle, randint

# From "Safest" Class, implemented by pmariglia
def prefix_opponent_move(score_lookup, prefix):
    new_score_lookup = dict()
    for k, v in score_lookup.items():
        bot_move, opponent_move = k
        new_opponent_move = "{}_{}".format(opponent_move, prefix)
        new_score_lookup[(bot_move, new_opponent_move)] = v

    return new_score_lookup


def pick_safest_move_from_battles(battles):
    # Only work on current battle
    battle = battles[0]
    root = Node("Root")

    state = battle.create_state()
    mutator = StateMutator(state)
    user_options, opponent_options = battle.get_all_options()
    logger.debug("Attempting to find best move from: {}".format(mutator.state))
    scores = get_payoff_matrix(mutator, user_options, opponent_options, depth=2, prune=True)

    # Create tree using payoff matrix from "Safest" algorithm
    checked_moves = {}
    for (myMove, opponentMove), heuristic in scores.items():
        if myMove not in checked_moves:
            child = Node(myMove, root)
            checked_moves[myMove] = child
        grandchild = Node(opponentMove, checked_moves[myMove])
        Node(heuristic, grandchild)

    for pre, _, node in RenderTree(root):
        logger.info("%s%s" % (pre, node.name))

    # Perform depth first search
    top3Heuristic = []
    for myMove in root.children:
        for opMove in myMove.children:
            # the only child of opMove is the heuristic
            if len(top3Heuristic) < 3:
                top3Heuristic.append(opMove.children[0])
            elif float(opMove.children[0].name) == float(min(top3Heuristic, key=lambda x: float(x.name)).name):
                # if heuristic is the same, randomly choose to add to top 3
                if bool(randint(0,1)):
                    top3Heuristic.remove(min(top3Heuristic, key=lambda x: float(x.name)))
                    top3Heuristic.append(opMove.children[0])
            elif float(opMove.children[0].name) > float(min(top3Heuristic, key=lambda x: float(x.name)).name):
                top3Heuristic.remove(min(top3Heuristic, key=lambda x: float(x.name)))
                top3Heuristic.append(opMove.children[0])

    logger.info("top 3 choices:")
    for move in top3Heuristic:
        print(move.parent.parent.name, move.name)
    logger.info("")
    shuffle(top3Heuristic)
    bot_choice = top3Heuristic.pop().parent.parent.name
    logger.info(bot_choice)

    logger.info("Choice: {}".format(bot_choice))
    return bot_choice


class BattleBot(Battle):
    def __init__(self, *args, **kwargs):
        super(BattleBot, self).__init__(*args, **kwargs)

    def find_best_move(self):
        battles = self.prepare_battles(join_moves_together=True)
        safest_move = pick_safest_move_from_battles(battles)
        return format_decision(self, safest_move)

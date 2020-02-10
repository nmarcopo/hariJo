from showdown.battle_bots.harijo.main import BattleBot
import dill as pickle
from config import logger

"""
Milestone 1 Test

We pickled a "Battle" object from a sample run of our bot playing online.
This allows us to easily show the search functionality with a consistent result.
Given the battle state, the chosen move should be "icepunch".

Note: in real gameplay, the battles object is constantly updated and the bot
will react accordingly. For our test purpose we wanted consistent input and output.
"""

bot = BattleBot("Test Battle")

with open("tests/battleFile.obj", "rb") as f:
    battle = pickle.load(f)

assert (bot.pick_move_from_battles([battle]) == "icepunch"), "Error, search was incorrect"
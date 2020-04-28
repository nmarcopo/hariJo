# HariJo  ![Hariyama](https://play.pokemonshowdown.com/sprites/xyani/hariyama.gif)
HariJo is a Pokémon battle-bot that can play battles on [Pokemon Showdown](https://pokemonshowdown.com/). It is based on [pmariglia's Showdown Bot](https://github.com/pmariglia/showdown).

Our bot currently focuses on gen 4 random battles.

Created by Austin Sura and Nicholas Marcopoli

## Python version
Developed and tested using Python 3.7.3.

## Outstanding Bugs and Unimplemented Features
- Chat monitor raises an exception when an opponent types any command into the chat, such as `!weak [pokemon_name]`. Currently, the exception is caught and the message is sent, unparsed, to the chat log file.
- Pokemon that change type, like Kekleon and Ditto, do not have their updated types registered in the bot.
- Future work could include a machine learning component for determining safety constant and status condition values.
- Our current approach involves “magic” numbers with heuristics, but a machine learning approach could find the optimal solution over time.
- Currently our bot is only designed for generation 4 random battles. Future work would make our bot robust and able to play many generations.
- Our bot could be extended to play more than one game simultaneously.
- Our bot could search deeper into the game tree and look further into possible moves.

## Milestone 5 README Section
For this milestone, we finally fixed our problems with the pokemon Unown and Ditto. We added their data into the JSON file that included each pokemon and their possible movesets, and the game now recognizes their movesets correctly. We also added a safety constant modifier that looks at stat buffs. We’re currently testing this approach now and will update the class when we have our presentation.

One notable feature that could be implemented in the future is further refinements to the main battle engine. For example, the move “sucker punch” is still not properly understood by the engine, as it does not realize that for the move to succeed, the opponent must use an attacking move. This allows the bot to be exploited and an opponent could simply use a non-attacking move to avoid damage from sucker punch. Another flaw with the battle system is its failure to understand the pokemon Keckleon’s ability, Color Change. This ability allows the pokemon to change its type depending on the move used to attack it. The engine does not recognize the changed typing and continues attacking as if its type had not changed.

Another feature that we think would be interesting to work on is a new bot based on machine learning that is trained by playing games against this current bot. We think that this is a great starting point for a new bot since it’s able to beat top ranked players, but the refinements machine learning could make to this bot could potentially fix some of the issues we outlined earlier.

We have a number of magic variables that can be tweaked to alter our bot’s performance. The most important magic number is our initial safety constant (`safety`). We set this number to three, which functions as the baseline aggressiveness of our bot. There are other magic variables that affect this safety constant such as our status condition multiplier (`status_aggression_multiplier`) and also our stat buff multiplier (`buff_aggression_multiplier`). The ratios of how each status condition affects the safety constant are set in stone, but the degree to which they affect it as a whole can be altered. The same idea is true for the stat buff multiplier. In terms of configuration files, the .env has a number of options that can affect the bot. The flags TRACK_RANKING and TRACK_CHAT allow users of the bot to gather data from our website. We have described how to use these flags earlier in our README. The other .env flags came with our starter bot.

## Milestone 4 README Section

The two new features we’ve implemented for this milestone are status condition evaluation for our move choice and a chat log to keep track of opponent messages (e.g. trash talk). 

Our move choice function calculates a safety constant as before now our calculation will change based on friendly and opponent status conditions. Each different status condition has a different value ranging from .1 to .25. The safety factor will be increased if the opponent has status conditions, and decreased if our pokemon have status conditions. We can increase or decrease the impact of status conditions in the calculation using the `status_aggession_modifier` constant.

We developed the values for each status condition through expert knowledge of our experience playing the game and well known strategies in pokemon. We also chose to weigh the status conditions in general based on how we perceived the impact of the conditions on the game. We tested a couple different `status_aggression_modifier` values to determine the best value.

Our chat log activates when the user includes the optional flag `TRACK_CHAT=True` in their `.env` file. When this is activated, chat messages from the bot, the opponent, and other spectators will be output to a file, `chatMessages.txt`. This is done by using a regular expression on all incoming websocket messages - if the message begins with `|c|`, we know that it is a chat message and can send it to the file. Some interesting messages included users discovering that their opponent was a bot and some trash talk from the opponent.

Below is an example of a `.env` file that will output chat messages to a file:

```
WEBSOCKET_URI=sim.smogon.com:8000
PS_USERNAME=harijo
PS_PASSWORD=battlebot
BOT_MODE=SEARCH_LADDER
POKEMON_MODE=gen4randombattle
RUN_COUNT=1
BATTLE_BOT="harijo"
LOG_LEVEL="DEBUG"
TRACK_CHAT=True
```

Our Makefile retains the functionality of make build, make install, make test, and make clean from the previous milestone.

## Milestone 3 README Section

New Features:

- Harijo now only selects an aggressive move using the weighted average strategy from Milestone 2. We no longer pick the safest move using the minimax algorithm.
- Track elo history to a file using the new `TRACK_RANKING` flag in the `.env` file.

To track elo history ranking, simply add `TRACK_RANKING=True` to the `.env` file. Elo history will be appended to a file in the base Harijo directory called `rankingsProgress.txt`.

Here is an example `.env` file that will output elo history to `rankingsProgress.txt`:

```
WEBSOCKET_URI=sim.smogon.com:8000
PS_USERNAME=harijo
PS_PASSWORD=battlebot
BOT_MODE=SEARCH_LADDER
POKEMON_MODE=gen4randombattle
RUN_COUNT=100
BATTLE_BOT="harijo"
LOG_LEVEL="DEBUG"
TRACK_RANKING=True
```

## Milestone 2 README Section

Our control mechanism is an implementation of the behavior tree concept. Note, we do not have a concrete behavior tree, but rather IF statements that accomplish the same functionality as a behavior tree implemented as a tree. Our tree checks the game state to determine if we are ahead, or if we are behind and to what degree. This is determined by calculating the total HP percentage of our bot’s pokemon and the opponents pokemon. Based on this information, we will choose an appropriate strategy for selecting a move.
If we are behind, our move selection process involves computing a weighted average of all possible outcomes using a safety constant and this value is decreased as we fall further behind. The move with the highest weighted average is selected. The decreased safety constant leads to more aggressive moves. If we are ahead, our move selector will always pick the move with the least downside using the minimax algorithm.

The high level strategy directs the flow of the control mechanism from the top level because the game state is the first thing considered when choosing what move is appropriate. Our win condition is making sure that the opponent’s HP percentage reaches 0 before ours does. Our high level strategy helps us reach this win condition, as if we are losing by a large margin we cannot afford to play patiently and should play aggressively.


Our dependencies:

```
requests==2.20.1
environs==4.1.0
websockets==7.0
python-dateutil==2.8.0
nashpy==0.0.17
pandas==0.23.4
numpy==1.16.2
anytree
Dill
```

Dependency Instructions:

`make install`, installs the necessary dependencies.


Runtime instructions:

`make build` - The game will play against a random live player from the matchmaking pool, automatically and you will see the game play out in the terminal.

If you would like to watch the game, you can follow these instructions:
- navigate to https://play.pokemonshowdown.com/
- log in to the user “HariJo” with the password, “battlebot”
- run `make build` to start the game

# The following notes are left over from pmariglia's repository

## Getting Started


### Configuration
Environment variables are used for configuration which are by default read from a file named `.env`

The configurations available are:
```
BATTLE_BOT: (string, default "safest") The BattleBot module to use. More on this below
SAVE_REPLAY: (bool, default False) Specifies whether or not to save replays of the battles
LOG_TO_FILE: (bool, default False) Specifies whether or not to write logs to files in {PWD}/logs/
LOG_LEVEL: (string, default "DEBUG") The Python logging level 
WEBSOCKET_URI: (string, default is the official PokemonShowdown websocket address: "sim.smogon.com:8000") The address to use to connect to the Pokemon Showdown websocket 
PS_USERNAME: (string, required) Pokemon Showdown username
PS_PASSWORD: (string) Pokemon Showdown password 
BOT_MODE: (string, required) The mode the the bot will operate in. Options are "CHALLENGE_USER", "SEARCH_LADDER", or "ACCEPT_CHALLENGE"
USER_TO_CHALLENGE: (string, required if BOT_MODE is "CHALLENGE_USER") The user to challenge
POKEMON_MODE: (string, required) The type of game this bot will play games in
TEAM_NAME: (string, required if POKEMON_MODE is one where a team is required) The name of the file that contains the team you want to use. More on this below in the Specifying Teams section.
RUN_COUNT: (integer, required) The amount of games this bot will play before quitting
```

Here is a minimal `.env` file. This configuration will log in and search for a gen8randombattle:
```
WEBSOCKET_URI=sim.smogon.com:8000
PS_USERNAME=MyCoolUsername
PS_PASSWORD=MySuperSecretPassword
BOT_MODE=SEARCH_LADDER
POKEMON_MODE=gen8randombattle
RUN_COUNT=1
```

### Running without Docker

#### Clone

Clone the repository with `git clone https://github.com/pmariglia/showdown.git`

#### Install Requirements

Install the requirements with `pip install -r requirements.txt`.

Be sure to use a virtual environment to isolate your packages.

#### Run
Running with `python run.py` will start the bot with configurations specified by environment variables read from a file named `.env`

### Running with Docker

#### Clone the repository
`git clone https://github.com/pmariglia/showdown.git`

#### Build the Docker image
`docker build . -t showdown`

#### Run with an environment variable file
`docker run --env-file .env showdown`

### Running on Heroku

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)

After deploying, go to the Resources tab and turn on the worker.

## Battle Bots

### Safest
use `BATTLE_BOT=safest` (default unless otherwise specified)

The bot searches through the game-tree for two turns and selects the move that minimizes the possible loss for a turn.
This is equivalent to the [Maximin](https://en.wikipedia.org/wiki/Minimax#Maximin) strategy

For decisions with random outcomes a weighted average is taken for all possible end states.
For example: If using draco meteor versus some arbitrary other move results in a score of 1000 if it hits (90%) and a score of 900 if it misses (10%), the overall score for using
draco meteor is (0.9 * 1000) + (0.1 * 900) = 990.

This decision type is deterministic - the bot will always make the same move given the same situation again.

### Nash-Equilibrium (experimental)
use `BATTLE_BOT=nash_equilibrium`

Using the information it has, plus some assumptions about the opponent, the bot will attempt to calculate the [Nash-Equilibrium](https://en.wikipedia.org/wiki/Nash_equilibrium) with the highest payoff
and select a move from that distribution.

The Nash Equilibrium is calculated using command-line tools provided by the [Gambit](http://www.gambit-project.org/) project.
This decision method should only be used when running with Docker and will fail otherwise.

This decision method is **not** deterministic. The bot **may** make a different move if presented with the same situation again.

### Most Damage
use `BATTLE_BOT=most_damage`

Selects the move that will do the most damage to the opponent

Does not switch

## Performance

These are the default battle-bot's results in three different formats for roughly 75 games played on a fresh account:

![RelativeWeightsRankings](https://i.imgur.com/eNpIlVg.png)

## Write your own bot
Create a package in `showdown/battle_bots` with a module named `main.py`. In this module, create a class named `BattleBot`, override the Battle class, and implement your own `find_best_move` function.

Set the `BATTLE_BOT` environment variable to the name of your package and your function will be called each time PokemonShowdown prompts the bot for a move

## The Battle Engine
The bots in the project all use a Pokemon battle engine to determine all possible transpositions that may occur from a pair of moves.

For more information, see [ENGINE.md](https://github.com/pmariglia/showdown/blob/master/ENGINE.md) 

## Specifying Teams
You can specify teams by setting the `TEAM_NAME` environment variable.
Examples can be found in `teams/teams/`.

Passing in a directory will cause a random team to be selected from that directory

The path specified should be relative to `teams/teams/`.

#### Examples

Specify a file:
```
TEAM_NAME=gen8/ou/clef_sand
```

Specify a directory:
```
TEAM_NAME=gen8/ou
```

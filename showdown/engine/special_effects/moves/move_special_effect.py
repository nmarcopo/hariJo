import constants
from data import pokedex


def suckerpunch(attacking_move, defending_move, attacking_pokemon, defending_pokemon, first_move, weather):
    if not first_move or defending_move.get(constants.CATEGORY) not in constants.DAMAGING_CATEGORIES:
        attacking_move = attacking_move.copy()
        attacking_move[constants.ACCURACY] = 0

    return attacking_move


def eruption(attacking_move, defending_move, attacking_pokemon, defending_pokemon, first_move, weather):
    attacking_move = attacking_move.copy()
    attacker_hp_percent = attacking_pokemon.hp / attacking_pokemon.maxhp
    attacking_move[constants.BASE_POWER] *= attacker_hp_percent
    return attacking_move


def tailslap(attacking_move, defending_move, attacking_pokemon, defending_pokemon, first_move, weather):
    # skill-link will boost damage by 5x, so no need to do it again here if that is the pokemon's ability
    if attacking_pokemon.ability != 'skilllink':
        attacking_move = attacking_move.copy()
        attacking_move[constants.BASE_POWER] *= 3.2
    return attacking_move


def freezedry(attacking_move, defending_move, attacking_pokemon, defending_pokemon, first_move, weather):
    if 'water' in defending_pokemon.types:
        attacking_move = attacking_move.copy()
        attacking_move[constants.BASE_POWER] *= 4
    return attacking_move


def hex(attacking_move, defending_move, attacking_pokemon, defending_pokemon, first_move, weather):
    if defending_pokemon.status is not None:
        attacking_move = attacking_move.copy()
        attacking_move[constants.BASE_POWER] *= 2
    return attacking_move


def foulplay(attacking_move, defending_move, attacking_pokemon, defending_pokemon, first_move, weather):
    attacking_move = attacking_move.copy()
    attacking_move[constants.BASE_POWER] *= defending_pokemon.calculate_boosted_stats()[constants.ATTACK] / \
                                            attacking_pokemon.calculate_boosted_stats()[constants.ATTACK]
    return attacking_move


def storedpower(attacking_move, defending_move, attacking_pokemon, defending_pokemon, first_move, weather):
    multiplier = attacking_pokemon.attack_boost + attacking_pokemon.defense_boost + \
                 attacking_pokemon.special_attack_boost + attacking_pokemon.special_defense_boost + \
                 attacking_pokemon.speed_boost
    if multiplier > 0:
        attacking_move = attacking_move.copy()
        attacking_move[constants.BASE_POWER] *= multiplier
    return attacking_move


def psyshock(attacking_move, defending_move, attacking_pokemon, defending_pokemon, first_move, weather):
    defending_stats = defending_pokemon.calculate_boosted_stats()
    attacking_move = attacking_move.copy()
    attacking_move[constants.BASE_POWER] *= (defending_stats[constants.SPECIAL_DEFENSE] / defending_stats[constants.DEFENSE])
    return attacking_move


def facade(attacking_move, defending_move, attacking_pokemon, defending_pokemon, first_move, weather):
    if attacking_pokemon.status is not None:
        attacking_move = attacking_move.copy()
        attacking_move[constants.BASE_POWER] *= 2
    return attacking_move


def avalanche(attacking_move, defending_move, attacking_pokemon, defending_pokemon, first_move, weather):
    if first_move is False and defending_move.get(constants.CATEGORY) in constants.DAMAGING_CATEGORIES:
        attacking_move = attacking_move.copy()
        attacking_move[constants.BASE_POWER] *= 2
    return attacking_move


def gyroball(attacking_move, defending_move, attacking_pokemon, defending_pokemon, first_move, weather):
    # power = (25 × TargetSpeed ÷ UserSpeed) + 1
    attacking_move = attacking_move.copy()
    attacker_speed = attacking_pokemon.calculate_boosted_stats()[constants.SPEED]
    defender_speed = defending_pokemon.calculate_boosted_stats()[constants.SPEED]
    attacking_move[constants.BASE_POWER] = min(150, (25 * defender_speed / attacker_speed) + 1)
    return attacking_move


def electroball(attacking_move, defending_move, attacking_pokemon, defending_pokemon, first_move, weather):
    speed_ratio = defending_pokemon.calculate_boosted_stats()[constants.SPEED] / attacking_pokemon.calculate_boosted_stats()[constants.SPEED]

    attacking_move = attacking_move.copy()
    if speed_ratio < 0.25:
        attacking_move[constants.BASE_POWER] = 150
    elif speed_ratio < 0.33:
        attacking_move[constants.BASE_POWER] = 120
    elif speed_ratio < 0.50:
        attacking_move[constants.BASE_POWER] = 80
    elif speed_ratio < 1:
        attacking_move[constants.BASE_POWER] = 60
    else:
        attacking_move[constants.BASE_POWER] = 40

    return attacking_move


def focuspunch(attacking_move, defending_move, attacking_pokemon, defending_pokemon, first_move, weather):
    # technically wrong - a move missing would allow focuspunch to hit, however that information is not present here
    if first_move or defending_move.get(constants.CATEGORY) in constants.DAMAGING_CATEGORIES:
        attacking_move = attacking_move.copy()
        attacking_move[constants.BASE_POWER] = 0
    return attacking_move


def acrobatics(attacking_move, defending_move, attacking_pokemon, defending_pokemon, first_move, weather):
    # acrobatics is 110 by default. If the pokemon has an item, it will go to 55
    # technically this should be the other way around, but the evaluation logic should
    # assume that the opponent's pokemon has a 110 BP move (worst case unless known)
    if attacking_pokemon.item not in [None, "None", constants.UNKNOWN_ITEM]:
        attacking_move = attacking_move.copy()
        attacking_move[constants.BASE_POWER] *= 0.5
    return attacking_move


def technoblast(attacking_move, defending_move, attacking_pokemon, defending_pokemon, first_move, weather):
    if attacking_pokemon.item == 'burndrive':
        attacking_move = attacking_move.copy()
        attacking_move[constants.TYPE] = 'fire'

    elif attacking_pokemon.item == 'chilldrive':
        attacking_move = attacking_move.copy()
        attacking_move[constants.TYPE] = 'ice'

    elif attacking_pokemon.item == 'dousedrive':
        attacking_move = attacking_move.copy()
        attacking_move[constants.TYPE] = 'water'

    elif attacking_pokemon.item == 'shockdrive':
        attacking_move = attacking_move.copy()
        attacking_move[constants.TYPE] = 'electric'

    return attacking_move


def multiattack(attacking_move, defending_move, attacking_pokemon, defending_pokemon, first_move, weather):
    if attacking_pokemon.item.endswith('memory'):
        attacking_move = attacking_move.copy()
        attacking_move[constants.TYPE] = attacking_pokemon.item.replace('memory', '')

    return attacking_move


def knockoff(attacking_move, defending_move, attacking_pokemon, defending_pokemon, first_move, weather):
    # .endswith("mega|primal") is a hack but w/e sue me
    if defending_pokemon.item is not None and not defending_pokemon.id.endswith("mega") and not defending_pokemon.id.endswith("primal"):
        attacking_move = attacking_move.copy()
        attacking_move[constants.BASE_POWER] *= 1.5
    return attacking_move


def hurricane(attacking_move, defending_move, attacking_pokemon, defending_pokemon, first_move, weather):
    if weather == constants.SUN:
        attacking_move = attacking_move.copy()
        attacking_move[constants.ACCURACY] = 50
    elif weather == constants.RAIN:
        attacking_move = attacking_move.copy()
        attacking_move[constants.ACCURACY] = True
    return attacking_move


def blizzard(attacking_move, defending_move, attacking_pokemon, defending_pokemon, first_move, weather):
    if weather == constants.HAIL:
        attacking_move = attacking_move.copy()
        attacking_move[constants.ACCURACY] = True
    return attacking_move


def solarbeam(attacking_move, defending_move, attacking_pokemon, defending_pokemon, first_move, weather):
    if weather == constants.SUN:
        attacking_move = attacking_move.copy()
        attacking_move[constants.FLAGS] = attacking_move[constants.FLAGS].copy()
        attacking_move[constants.FLAGS].pop(constants.CHARGE, None)
    return attacking_move


def toxic(attacking_move, defending_move, attacking_pokemon, defending_pokemon, first_move, weather):
    if 'poison' in attacking_pokemon.types:
        attacking_move = attacking_move.copy()
        attacking_move[constants.ACCURACY] = True
    return attacking_move


def strengthsap(attacking_move, defending_move, attacking_pokemon, defending_pokemon, first_move, weather):
    attacking_move = attacking_move.copy()
    attacking_move[constants.BOOSTS] = {
        constants.ATTACK: -1
    }
    attacking_move[constants.HEAL] = [
        defending_pokemon.calculate_boosted_stats()[constants.ATTACK],
        attacking_pokemon.maxhp
    ]
    attacking_move[constants.HEAL_TARGET] = constants.SELF

    return attacking_move


def revelationdance(attacking_move, defending_move, attacking_pokemon, defending_pokemon, first_move, weather):
    attacking_move = attacking_move.copy()
    attacking_move[constants.TYPE] = attacking_pokemon.types[0]

    return attacking_move


def lowkick(attacking_move, defending_move, attacking_pokemon, defending_pokemon, first_move, weather):
    attacking_move = attacking_move.copy()
    defending_pokemon_weight = pokedex[defending_pokemon.id][constants.WEIGHT]

    if defending_pokemon_weight < 10:
        attacking_move[constants.BASE_POWER] = 20
    elif defending_pokemon_weight < 25:
        attacking_move[constants.BASE_POWER] = 40
    elif defending_pokemon_weight < 60:
        attacking_move[constants.BASE_POWER] = 60
    elif defending_pokemon_weight < 100:
        attacking_move[constants.BASE_POWER] = 80
    elif defending_pokemon_weight < 200:
        attacking_move[constants.BASE_POWER] = 100
    else:
        attacking_move[constants.BASE_POWER] = 120

    return attacking_move


def painsplit(attacking_move, defending_move, attacking_pokemon, defending_pokemon, first_move, weather):
    # damage done to the opponent is handled in the damage calculation module
    attacking_move = attacking_move.copy()
    total_hp = attacking_pokemon.hp + defending_pokemon.hp
    damage_done = attacking_pokemon.hp - total_hp / 2
    damage_fraction = -1*damage_done / attacking_pokemon.maxhp

    attacking_move[constants.HEAL] = damage_fraction.as_integer_ratio()
    attacking_move[constants.HEAL_TARGET] = constants.SELF

    # this needs to be set so that the damage calculation is performed
    attacking_move[constants.CATEGORY] = constants.PHYSICAL

    return attacking_move


def pursuit(attacking_move, defending_move, attacking_pokemon, defending_pokemon, first_move, weather):
    if defending_move.get(constants.SWITCH_STRING):
        attacking_move = attacking_move.copy()
        attacking_move[constants.BASE_POWER] *= 2
    return attacking_move


def aurawheel(attacking_move, defending_move, attacking_pokemon, defending_pokemon, first_move, weather):
    if attacking_pokemon.id == "morpekohangry":
        attacking_move = attacking_move.copy()
        attacking_move[constants.TYPE] = 'dark'
    return attacking_move


def dynamaxcannon(attacking_move, defending_move, attacking_pokemon, defending_pokemon, first_move, weather):
    if constants.DYNAMAX in defending_pokemon.volatile_status:
        attacking_move = attacking_move.copy()
        attacking_move[constants.BASE_POWER] *= 2
    return attacking_move


def dragondarts(attacking_move, defending_move, attacking_pokemon, defending_pokemon, first_move, weather):
    attacking_move = attacking_move.copy()
    attacking_move[constants.BASE_POWER] *= 2
    return attacking_move


def boltbeak(attacking_move, defending_move, attacking_pokemon, defending_pokemon, first_move, weather):
    if first_move:
        attacking_move = attacking_move.copy()
        attacking_move[constants.BASE_POWER] *= 2
    return attacking_move


def clangoroussoul(attacking_move, defending_move, attacking_pokemon, defending_pokemon, first_move, weather):
    if attacking_pokemon.hp > int(attacking_pokemon.maxhp / 3):
        attacking_move = attacking_move.copy()
        attacking_move[constants.HEAL_TARGET] = constants.SELF
        attacking_move[constants.HEAL] = [-1, 3]
        attacking_move[constants.BOOSTS] = {
            constants.ATTACK: 1,
            constants.DEFENSE: 1,
            constants.SPECIAL_ATTACK: 1,
            constants.SPECIAL_DEFENSE: 1,
            constants.SPEED: 1
          }
    return attacking_move


def bodypress(attacking_move, defending_move, attacking_pokemon, defending_pokemon, first_move, weather):
    attacking_move = attacking_move.copy()
    boosted_stats = attacking_pokemon.calculate_boosted_stats()
    attacking_move[constants.BASE_POWER] *= (boosted_stats[constants.DEFENSE] / boosted_stats[constants.ATTACK])
    return attacking_move


def lifedew(attacking_move, defending_move, attacking_pokemon, defending_pokemon, first_move, weather):
    attacking_move = attacking_move.copy()
    attacking_move[constants.HEAL] = [1, 4]
    attacking_move[constants.HEAL_TARGET] = constants.SELF
    return attacking_move


def steelbeam(attacking_move, defending_move, attacking_pokemon, defending_pokemon, first_move, weather):
    attacking_move = attacking_move.copy()
    attacking_move[constants.HEAL] = [-1, 2]
    attacking_move[constants.HEAL_TARGET] = constants.SELF
    return attacking_move


def doubleironbash(attacking_move, defending_move, attacking_pokemon, defending_pokemon, first_move, weather):
    attacking_move = attacking_move.copy()
    attacking_move[constants.BASE_POWER] *= 2  # double-hit move
    return attacking_move


def morningsun(attacking_move, defending_move, attacking_pokemon, defending_pokemon, first_move, weather):
    if weather in [constants.SAND, constants.RAIN, constants.HAIL]:
        attacking_move = attacking_move.copy()
        attacking_move[constants.HEAL] = [1, 4]
    elif weather == constants.SUN:
        attacking_move = attacking_move.copy()
        attacking_move[constants.HEAL] = [2, 3]
    return attacking_move


def shoreup(attacking_move, defending_move, attacking_pokemon, defending_pokemon, first_move, weather):
    attacking_move = attacking_move.copy()
    attacking_move[constants.HEAL_TARGET] = constants.SELF
    if weather in [constants.SAND, constants.RAIN, constants.HAIL]:
        attacking_move[constants.HEAL] = [2, 3]
    else:
        attacking_move[constants.HEAL] = [1, 2]

    return attacking_move


def heavyslam(attacking_move, defending_move, attacking_pokemon, defending_pokemon, first_move, weather):
    try:
        weight_ratio = pokedex[defending_pokemon.id][constants.WEIGHT] / pokedex[attacking_pokemon.id][constants.WEIGHT]
    except ZeroDivisionError:
        return attacking_move

    attacking_move = attacking_move.copy()
    if weight_ratio > 0.5:
        attacking_move[constants.BASE_POWER] = 40
    elif weight_ratio > 0.33:
        attacking_move[constants.BASE_POWER] = 60
    elif weight_ratio > 0.25:
        attacking_move[constants.BASE_POWER] = 80
    elif weight_ratio > 0.2:
        attacking_move[constants.BASE_POWER] = 100
    else:
        attacking_move[constants.BASE_POWER] = 120

    return attacking_move


move_lookup = {
    'heatcrash': heavyslam,
    'heavyslam': heavyslam,
    'shoreup': shoreup,
    'synthesis': morningsun,
    'moonlight': morningsun,
    'morningsun': morningsun,
    'doubleironbash': doubleironbash,
    'steelbeam': steelbeam,
    'lifedew': lifedew,
    'bodypress': bodypress,
    'clangoroussoul': clangoroussoul,
    'fishiousrend': boltbeak,
    'boltbeak': boltbeak,
    'dragondarts': dragondarts,
    'dynamaxcannon': dynamaxcannon,
    'behemothblade': dynamaxcannon,
    'behemothbash': dynamaxcannon,
    'aurawheel': aurawheel,
    'pursuit': pursuit,
    'painsplit': painsplit,
    'grassknot': lowkick,
    'lowkick': lowkick,
    'revelationdance': revelationdance,
    'strengthsap': strengthsap,
    'toxic': toxic,
    'multiattack': multiattack,
    'solarbeam': solarbeam,
    'hurricane': hurricane,
    'thunder': hurricane,
    'blizzard': blizzard,
    'suckerpunch': suckerpunch,
    'eruption': eruption,
    'waterspout': eruption,
    'hex': hex,
    'freezedry': freezedry,
    'tailslap': tailslap,
    'bulletseed': tailslap,
    'rockblast': tailslap,
    'bonerush': tailslap,
    'iciclespear': tailslap,
    'pinmissile': tailslap,
    'watershuriken': tailslap,
    'foulplay': foulplay,
    'storedpower': storedpower,
    'psyshock': psyshock,
    'psystrike': psyshock,
    'secretsword': psyshock,
    'avalanche': avalanche,
    'facade': facade,
    'gyroball': gyroball,
    'electroball': electroball,
    'focuspunch': focuspunch,
    'acrobatics': acrobatics,
    'technoblast': technoblast,
    'knockoff': knockoff
}


def modify_attack_being_used(attacking_move, defending_move, attacking_pokemon, defending_pokemon, first_move, weather):
    move_func = move_lookup.get(attacking_move[constants.ID])
    if move_func is not None:
        return move_func(attacking_move, defending_move, attacking_pokemon, defending_pokemon, first_move, weather)
    else:
        return attacking_move

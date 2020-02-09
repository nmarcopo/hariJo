"""
TestGetStateInstructions is the main Pokemon engine test class
All battle mechanics are tested in this TestCase
"""


import unittest
from unittest import mock

import config
import constants
from collections import defaultdict
from copy import deepcopy
from showdown.engine.objects import TransposeInstruction
from showdown.engine.find_state_instructions import get_all_state_instructions
from showdown.engine.find_state_instructions import remove_duplicate_instructions
from showdown.engine.find_state_instructions import lookup_move
from showdown.engine.find_state_instructions import user_moves_first
from showdown.engine.objects import State
from showdown.engine.objects import Pokemon
from showdown.engine.objects import Side
from showdown.battle import Pokemon as StatePokemon
from showdown.engine.objects import StateMutator


class TestGetStateInstructions(unittest.TestCase):
    def setUp(self):
        config.damage_calc_type = "average"  # some tests may override this
        self.state = State(
                        Side(
                            Pokemon.from_state_pokemon_dict(StatePokemon("raichu", 73).to_dict()),
                            {
                                "xatu": Pokemon.from_state_pokemon_dict(StatePokemon("xatu", 81).to_dict()),
                                "starmie": Pokemon.from_state_pokemon_dict(StatePokemon("starmie", 81).to_dict()),
                                "gyarados": Pokemon.from_state_pokemon_dict(StatePokemon("gyarados", 81).to_dict()),
                                "dragonite": Pokemon.from_state_pokemon_dict(StatePokemon("dragonite", 81).to_dict()),
                                "hitmonlee": Pokemon.from_state_pokemon_dict(StatePokemon("hitmonlee", 81).to_dict()),
                            },
                            (0, 0),
                            defaultdict(lambda: 0)
                        ),
                        Side(
                            Pokemon.from_state_pokemon_dict(StatePokemon("aromatisse", 81).to_dict()),
                            {
                                "yveltal": Pokemon.from_state_pokemon_dict(StatePokemon("yveltal", 73).to_dict()),
                                "slurpuff": Pokemon.from_state_pokemon_dict(StatePokemon("slurpuff", 73).to_dict()),
                                "victini": Pokemon.from_state_pokemon_dict(StatePokemon("victini", 73).to_dict()),
                                "toxapex": Pokemon.from_state_pokemon_dict(StatePokemon("toxapex", 73).to_dict()),
                                "bronzong": Pokemon.from_state_pokemon_dict(StatePokemon("bronzong", 73).to_dict()),
                            },
                            (0, 0),
                            defaultdict(lambda: 0)
                        ),
                        None,
            None,
            False
                    )

        self.mutator = StateMutator(self.state)

    def test_two_pokemon_switching(self):
        bot_move = "switch xatu"
        opponent_move = "switch yveltal"
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    ('switch', 'self', 'raichu', 'xatu'),
                    ('switch', 'opponent', 'aromatisse', 'yveltal')
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_powder_move_into_tackle_produces_correct_states(self):
        bot_move = "sleeppowder"
        opponent_move = "tackle"
        self.state.opponent.active.types = ['grass']
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.SELF, 35)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_superpower_correctly_unboosts_opponent(self):
        bot_move = "splash"
        opponent_move = "superpower"
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.SELF, 101),
                    (constants.MUTATOR_BOOST, constants.OPPONENT, constants.ATTACK, -1),
                    (constants.MUTATOR_BOOST, constants.OPPONENT, constants.DEFENSE, -1),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_psyshock_damage_is_the_same_regardless_of_spdef_boost(self):
        bot_move = "psyshock"
        opponent_move = "splash"
        self.state.opponent.active.special_defense_boost = 0
        instructions_without_spdef_boost = get_all_state_instructions(self.mutator, bot_move, opponent_move)

        self.state.opponent.active.special_defense_boost = 6
        instructions_when_spdef_is_maxed = get_all_state_instructions(self.mutator, bot_move, opponent_move)

        self.assertEqual(instructions_without_spdef_boost, instructions_when_spdef_is_maxed)

    def test_bodypress_damage_is_the_same_regardless_of_attack(self):
        bot_move = "bodypress"
        opponent_move = "splash"
        self.state.self.active.attack_boost = 0
        instructions_with_0_attack_boost = get_all_state_instructions(self.mutator, bot_move, opponent_move)

        self.state.self.active.attack_boost = 6
        instructions_with_6_attack_boost = get_all_state_instructions(self.mutator, bot_move, opponent_move)

        self.assertEqual(instructions_with_0_attack_boost, instructions_with_6_attack_boost)

    def test_bodypress_damage_is_different_with_different_defense_stats(self):
        bot_move = "bodypress"
        opponent_move = "splash"
        self.state.self.active.defense_boost = 0
        instructions_with_0_attack_boost = get_all_state_instructions(self.mutator, bot_move, opponent_move)

        self.state.self.active.defense_boost = 6
        instructions_with_6_attack_boost = get_all_state_instructions(self.mutator, bot_move, opponent_move)

        self.assertNotEqual(instructions_with_0_attack_boost, instructions_with_6_attack_boost)

    def test_powder_into_powder_gives_correct_states(self):
        bot_move = "sleeppowder"
        opponent_move = "sleeppowder"
        self.state.opponent.active.types = ['grass']
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                0.75,
                [
                    (constants.MUTATOR_APPLY_STATUS, constants.SELF, constants.SLEEP)
                ],
                False
            ),
            TransposeInstruction(
                0.25,
                [],
                True
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_focuspunch_into_non_damaging_move_gives_correct_states(self):
        bot_move = "focuspunch"
        opponent_move = "splash"
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1.0,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 46)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_focuspunch_into_damaging_move_gives_correct_states(self):
        bot_move = "focuspunch"
        opponent_move = "tackle"
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1.0,
                [
                    (constants.MUTATOR_DAMAGE, constants.SELF, 35)
                ],
                True
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_whirlwind_removes_status_boosts(self):
        bot_move = "whirlwind"
        opponent_move = "splash"
        self.state.opponent.active.attack_boost = 3
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1.0,
                [
                    (constants.MUTATOR_UNBOOST, constants.OPPONENT, constants.ATTACK, 3)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_haze_removes_status_boosts(self):
        bot_move = "haze"
        opponent_move = "splash"
        self.state.opponent.active.attack_boost = 3
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1.0,
                [
                    (constants.MUTATOR_UNBOOST, constants.OPPONENT, constants.ATTACK, 3)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_clearsmog_removes_status_boosts(self):
        bot_move = "clearsmog"
        opponent_move = "splash"
        self.state.opponent.active.attack_boost = 3
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1.0,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 55),
                    (constants.MUTATOR_UNBOOST, constants.OPPONENT, constants.ATTACK, 3)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_seismic_toss_deals_damage_by_level(self):
        bot_move = "seismictoss"
        opponent_move = "splash"
        self.state.self.active.level = 99
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1.0,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 99),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_ghost_immune_to_seismic_toss(self):
        bot_move = "seismictoss"
        opponent_move = "splash"
        self.state.self.active.level = 99
        self.state.opponent.active.types = ["ghost"]
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1.0,
                [],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_normal_immune_to_night_shade(self):
        bot_move = "nightshade"
        opponent_move = "splash"
        self.state.self.active.level = 99
        self.state.opponent.active.types = ["normal"]
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1.0,
                [],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_ground_immune_to_aurawheel(self):
        bot_move = "aurawheel"
        opponent_move = "splash"
        self.state.opponent.active.types = ["ground"]
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1.0,
                [],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_ground_not_immune_to_aurawheel_when_morpeko_hangry_is_active(self):
        bot_move = "aurawheel"
        opponent_move = "splash"
        self.state.self.active.id = "morpekohangry"
        self.state.opponent.active.types = ["ground"]
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1.0,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 68),
                    (constants.MUTATOR_BOOST, constants.SELF, constants.SPEED, 1),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_contrary_boosts_leafstorm(self):
        bot_move = "leafstorm"
        opponent_move = "splash"
        self.state.self.active.ability = 'contrary'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                0.9,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 69),
                    (constants.MUTATOR_BOOST, constants.SELF, constants.SPECIAL_ATTACK, 2)
                ],
                False
            ),
            TransposeInstruction(
                0.09999999999999998,
                [],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_contrary_unboosts_meteormash(self):
        bot_move = "meteormash"
        opponent_move = "splash"
        self.state.self.active.ability = 'contrary'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                0.18000000000000002,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 112),
                    (constants.MUTATOR_BOOST, constants.SELF, constants.ATTACK, -1)
                ],
                False
            ),
            TransposeInstruction(
                0.7200000000000001,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 112),
                ],
                False
            ),
            TransposeInstruction(
                0.09999999999999998,
                [],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_dragondance_with_contrary(self):
        bot_move = "dragondance"
        opponent_move = "splash"
        self.state.self.active.ability = 'contrary'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_BOOST, constants.SELF, constants.ATTACK, -1),
                    (constants.MUTATOR_BOOST, constants.SELF, constants.SPEED, -1)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_strengthsap_lowers_attack_and_heals_user(self):
        bot_move = "strengthsap"
        opponent_move = "splash"
        self.state.opponent.active.attack = 100
        self.state.self.active.hp = 100
        self.state.self.active.maxhp = 250
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_BOOST, constants.OPPONENT, constants.ATTACK, -1),
                    (constants.MUTATOR_HEAL, constants.SELF, 100)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_strengthsap_does_not_overheal(self):
        bot_move = "strengthsap"
        opponent_move = "splash"
        self.state.opponent.active.attack = 100
        self.state.self.active.hp = 200
        self.state.self.active.maxhp = 250
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_BOOST, constants.OPPONENT, constants.ATTACK, -1),
                    (constants.MUTATOR_HEAL, constants.SELF, 50)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_strengthsap_when_targets_attack_is_lowered(self):
        bot_move = "strengthsap"
        opponent_move = "splash"
        self.state.opponent.active.attack = 300
        self.state.opponent.active.attack_boost = -1
        self.state.self.active.hp = 1
        self.state.self.active.maxhp = 250
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_BOOST, constants.OPPONENT, constants.ATTACK, -1),
                    (constants.MUTATOR_HEAL, constants.SELF, 200)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_thickclub_with_random_pokemon_does_not_double_attack(self):
        bot_move = "tackle"
        opponent_move = "splash"
        self.state.self.active.item = 'thickclub'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 25)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_thickclub_with_marowak_doubles_attack(self):
        bot_move = "tackle"
        opponent_move = "splash"
        self.state.self.active.item = 'thickclub'
        self.state.self.active.id = 'marowak'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 49)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_thickclub_with_marowak_does_not_double_special_attack(self):
        bot_move = "watergun"
        opponent_move = "splash"
        self.state.self.active.item = 'thickclub'
        self.state.self.active.id = 'marowak'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 22)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_prankster_spore_does_not_work_on_dark_type(self):
        bot_move = "spore"
        opponent_move = "splash"
        self.state.self.active.ability = 'prankster'
        self.state.opponent.active.types = ['dark']
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_prankster_physical_move_has_the_same_effect_on_dark_type(self):
        bot_move = "tackle"
        opponent_move = "splash"
        self.state.self.active.ability = 'prankster'
        self.state.opponent.active.types = ['dark']
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 25)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_sound_move_goes_through_substitute(self):
        bot_move = "boomburst"
        opponent_move = "splash"
        self.state.opponent.active.hp = 1
        self.state.opponent.active.volatile_status.add(constants.SUBSTITUTE)
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 1)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_infiltrator_move_goes_through_sub(self):
        bot_move = "tackle"
        opponent_move = "splash"
        self.state.self.active.ability = 'infiltrator'
        self.state.opponent.active.hp = 1
        self.state.opponent.active.volatile_status.add(constants.SUBSTITUTE)
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 1)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_substitute_breaks_when_pkmn_behind_it_has_1_health(self):
        bot_move = "surf"
        opponent_move = "splash"
        self.state.opponent.active.types = ['ground', 'rock']
        self.state.opponent.active.hp = 1
        self.state.opponent.active.volatile_status.add(constants.SUBSTITUTE)
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_REMOVE_VOLATILE_STATUS, constants.OPPONENT, constants.SUBSTITUTE)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_revelationdance_changes_type(self):
        bot_move = "revelationdance"
        opponent_move = "splash"
        self.state.self.active.types = ['fire', 'water']
        self.state.opponent.active.types = ['grass']
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 144)  # would normally do 48 damage as a normal type move
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_lowkick_does_damage_on_light_pokemon(self):
        bot_move = "lowkick"
        opponent_move = "splash"
        self.state.opponent.active.id = 'castform'
        self.state.opponent.active.types = ['rock']
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 27)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_grassknot_does_damage_on_light_pokemon(self):
        bot_move = "grassknot"
        opponent_move = "splash"
        self.state.opponent.active.id = 'castform'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 12)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_grassknot_does_damage_on_heavy_pokemon(self):
        bot_move = "grassknot"
        opponent_move = "splash"
        self.state.opponent.active.id = 'golem'
        self.state.opponent.active.types = ['normal']
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 63)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_lowkick_does_damage_on_heavy_pokemon(self):
        bot_move = "lowkick"
        opponent_move = "splash"
        self.state.opponent.active.id = 'golem'
        self.state.opponent.active.types = ['rock']
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 149)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_hydration_cures_sleep_at_end_of_turn_in_rain(self):
        bot_move = "splash"
        opponent_move = "splash"
        self.state.self.active.status = constants.SLEEP
        self.state.self.active.ability = 'hydration'
        self.state.weather = constants.RAIN
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_REMOVE_STATUS, constants.SELF, constants.SLEEP)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_hydration_cures_poison_before_it_does_damage(self):
        bot_move = "splash"
        opponent_move = "splash"
        self.state.self.active.status = constants.POISON
        self.state.self.active.ability = 'hydration'
        self.state.weather = constants.RAIN
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_REMOVE_STATUS, constants.SELF, constants.POISON)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_moonblast_boosts_opponent_with_contrary(self):
        bot_move = "moonblast"
        opponent_move = "splash"
        self.state.opponent.active.ability = 'contrary'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                0.3,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 50),
                    (constants.MUTATOR_BOOST, constants.OPPONENT, constants.SPECIAL_ATTACK, 1)
                ],
                False
            ),
            TransposeInstruction(
                0.7,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 50)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_own_boost_does_not_affect_foulplay(self):
        bot_move = "foulplay"
        opponent_move = "splash"

        self.state.self.active.attack_boost = 2

        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1.,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 27)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_opponent_boost_does_affect_foulplay(self):
        bot_move = "foulplay"
        opponent_move = "splash"

        self.state.opponent.active.attack_boost = 2

        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1.,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 55)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_shellsmash_with_whiteherb_doesnt_lower_stats(self):
        bot_move = "shellsmash"
        opponent_move = "splash"
        self.state.self.active.item = 'whiteherb'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_BOOST, constants.SELF, constants.ATTACK, 2),
                    (constants.MUTATOR_BOOST, constants.SELF, constants.SPECIAL_ATTACK, 2),
                    (constants.MUTATOR_BOOST, constants.SELF, constants.SPEED, 2)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_superfang_does_half_health(self):
        bot_move = "superfang"
        opponent_move = "splash"
        self.state.opponent.active.maxhp = 100
        self.state.opponent.active.hp = 80
        self.state.opponent.active.types = ["normal"]
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                0.9,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 40)
                ],
                False
            ),
            TransposeInstruction(
                0.09999999999999998,
                [],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_finalgambit_does_damage_equal_to_health_and_faints_user(self):
        bot_move = "finalgambit"
        opponent_move = "splash"
        self.state.opponent.active.maxhp = 100
        self.state.opponent.active.hp = 100
        self.state.self.active.maxhp = 100
        self.state.self.active.hp = 80
        self.state.opponent.active.types = ["normal"]
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 80),
                    (constants.MUTATOR_HEAL, constants.SELF, -80),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_endeavor_brings_hp_to_equal(self):
        bot_move = "endeavor"
        opponent_move = "splash"
        self.state.opponent.active.maxhp = 100
        self.state.opponent.active.hp = 100
        self.state.self.active.maxhp = 100
        self.state.self.active.hp = 80
        self.state.opponent.active.types = ["normal"]
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 20)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_endeavor_does_nothing_when_user_hp_greater_than_target_hp(self):
        bot_move = "endeavor"
        opponent_move = "splash"
        self.state.opponent.active.maxhp = 100
        self.state.opponent.active.hp = 60
        self.state.self.active.maxhp = 100
        self.state.self.active.hp = 80
        self.state.opponent.active.types = ["normal"]
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_knockoff_does_more_damage_when_item_can_be_removed(self):
        bot_move = "knockoff"
        opponent_move = "splash"
        self.state.opponent.active.maxhp = 100
        self.state.opponent.active.hp = 100
        self.state.self.active.maxhp = 100
        self.state.self.active.hp = 100
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    # this move does 20 damage without knockoff boost
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 30)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_obstruct_protects(self):
        bot_move = "obstruct"
        opponent_move = "tackle"
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_APPLY_VOLATILE_STATUS, constants.SELF, constants.PROTECT),
                    (constants.MUTATOR_REMOVE_VOLATILE_STATUS, constants.SELF, constants.PROTECT),
                    (constants.MUTATOR_SIDE_START, constants.SELF, constants.PROTECT, 1)
                ],
                True
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_using_wish_sets_the_wish_value_to_half_of_the_users_max_health(self):
        bot_move = "wish"
        opponent_move = "splash"
        self.state.self.active.maxhp = 200
        self.state.self.active.hp = 50
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_WISH_START, constants.SELF, 100, self.state.self.wish[1]),
                    (constants.MUTATOR_WISH_DECREMENT, constants.SELF)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_having_wish_causes_heal_at_the_end_of_the_turn(self):
        bot_move = "splash"
        opponent_move = "splash"
        self.state.self.active.maxhp = 200
        self.state.self.active.hp = 50
        self.state.self.wish = (1, 100)
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_HEAL, constants.SELF, 100),
                    (constants.MUTATOR_WISH_DECREMENT, constants.SELF)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_wish_does_not_overheal(self):
        bot_move = "splash"
        opponent_move = "splash"
        self.state.self.active.maxhp = 200
        self.state.self.active.hp = 150
        self.state.self.wish = (1, 100)
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_HEAL, constants.SELF, 50),
                    (constants.MUTATOR_WISH_DECREMENT, constants.SELF)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_wish_does_not_heal_when_active_pokemon_is_dead_but_still_decrements(self):
        bot_move = "splash"
        opponent_move = "tackle"

        # opponent guaranteed to move first
        self.state.self.active.speed = 1
        self.state.opponent.active.speed = 2

        self.state.self.active.maxhp = 200
        self.state.self.active.hp = 1  # tackle will kill
        self.state.self.wish = (1, 100)
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.SELF, 1),
                    (constants.MUTATOR_WISH_DECREMENT, constants.SELF)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_wish_cannot_be_used_while_wish_is_active(self):
        bot_move = "wish"
        opponent_move = "splash"

        self.state.self.active.maxhp = 200
        self.state.self.active.hp = 100
        self.state.self.wish = (1, 100)
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_HEAL, constants.SELF, 100),
                    (constants.MUTATOR_WISH_DECREMENT, constants.SELF)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_wish_activating_at_full_hp_produces_no_instruction(self):
        bot_move = "splash"
        opponent_move = "splash"

        self.state.self.active.maxhp = 200
        self.state.self.active.hp = 200
        self.state.self.wish = (1, 100)
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_WISH_DECREMENT, constants.SELF)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_steel_beam_reduces_hp_by_half(self):
        bot_move = "steelbeam"
        opponent_move = "splash"
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                0.95,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 149),
                    (constants.MUTATOR_HEAL, constants.SELF, -104),
                ],
                False
            ),
            TransposeInstruction(
                0.050000000000000044,
                [],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_steel_beam_only_does_as_much_damage_as_the_user_has_hitpoints(self):
        bot_move = "steelbeam"
        opponent_move = "splash"
        self.state.self.active.hp = 1
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                0.95,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 149),
                    (constants.MUTATOR_HEAL, constants.SELF, -1),
                ],
                False
            ),
            TransposeInstruction(
                0.050000000000000044,
                [],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_knockoff_does_not_amplify_damage_for_mega(self):
        bot_move = "knockoff"
        opponent_move = "splash"
        self.state.opponent.active.maxhp = 100
        self.state.opponent.active.hp = 100
        self.state.self.active.maxhp = 100
        self.state.self.active.hp = 100
        self.state.opponent.active.id = "blastoisemega"
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    # this move does 20 damage without knockoff boost
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 20)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_knockoff_does_not_amplify_damage_for_primal(self):
        bot_move = "knockoff"
        opponent_move = "splash"
        self.state.opponent.active.maxhp = 100
        self.state.opponent.active.hp = 100
        self.state.self.active.maxhp = 100
        self.state.self.active.hp = 100
        self.state.opponent.active.id = "groudonprimal"
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    # this move does 20 damage without knockoff boost
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 20)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_rest_heals_user_and_puts_to_sleep(self):
        bot_move = "rest"
        opponent_move = "splash"
        self.state.self.active.maxhp = 100
        self.state.self.active.hp = 50
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_APPLY_STATUS, constants.SELF, constants.SLEEP),
                    (constants.MUTATOR_HEAL, constants.SELF, 50),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_ghost_immune_to_superfang(self):
        bot_move = "superfang"
        opponent_move = "splash"
        self.state.opponent.active.maxhp = 100
        self.state.opponent.active.hp = 100
        self.state.opponent.active.types = ["ghost"]
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1.0,
                [],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_taunt_into_uturn_causes_taunt_to_be_removed_after_switching(self):
        bot_move = "taunt"
        opponent_move = "uturn"
        self.state.self.active.speed = 2
        self.state.opponent.active.speed = 1
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)

        expected_instructions = [
            TransposeInstruction(
                1.0,
                [
                    (constants.MUTATOR_APPLY_VOLATILE_STATUS, constants.OPPONENT, constants.TAUNT),
                    (constants.MUTATOR_DAMAGE, constants.SELF, 60),
                    (constants.MUTATOR_REMOVE_VOLATILE_STATUS, constants.OPPONENT, constants.TAUNT),
                    (constants.MUTATOR_SWITCH, constants.OPPONENT, 'aromatisse', 'yveltal')
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_fast_uturn_results_in_switching_out_move_for_enemy(self):
        bot_move = "splash"
        opponent_move = "uturn"
        self.state.self.active.speed = 1
        self.state.opponent.active.speed = 2
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1.0,
                [
                        (constants.MUTATOR_DAMAGE, constants.SELF, 60),
                        (constants.MUTATOR_SWITCH, constants.OPPONENT, 'aromatisse', 'yveltal')
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_fast_uturn_results_in_switching_out_for_bot(self):
        bot_move = "uturn"
        opponent_move = "tackle"
        self.state.self.reserve['gyarados'].ability = 'intimidate'
        self.state.self.active.speed = 2
        self.state.opponent.active.speed = 1
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1.0,
                [
                        (constants.MUTATOR_DAMAGE, constants.OPPONENT, 22),
                        (constants.MUTATOR_SWITCH, constants.SELF, 'raichu', 'gyarados'),
                        (constants.MUTATOR_UNBOOST, constants.OPPONENT, constants.ATTACK, 1),
                        (constants.MUTATOR_DAMAGE, constants.SELF, 16)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_slow_uturn_results_in_switching_out_for_bot(self):
        bot_move = "uturn"
        opponent_move = "tackle"
        self.state.self.reserve['gyarados'].ability = 'intimidate'
        self.state.self.active.speed = 1
        self.state.opponent.active.speed = 2
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1.0,
                [
                        (constants.MUTATOR_DAMAGE, constants.SELF, 35),
                        (constants.MUTATOR_DAMAGE, constants.OPPONENT, 22),
                        (constants.MUTATOR_SWITCH, constants.SELF, 'raichu', 'gyarados'),
                        (constants.MUTATOR_UNBOOST, constants.OPPONENT, constants.ATTACK, 1)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_slow_uturn_results_in_switching_out_for_opponent(self):
        bot_move = "tackle"
        opponent_move = "uturn"
        self.state.self.active.speed = 2
        self.state.opponent.active.speed = 1
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1.0,
                [
                        (constants.MUTATOR_DAMAGE, constants.OPPONENT, 25),
                        (constants.MUTATOR_DAMAGE, constants.SELF, 60),
                        (constants.MUTATOR_SWITCH, constants.OPPONENT, 'aromatisse', 'yveltal')
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_uturn_works_with_multiple_states_before(self):
        bot_move = "thunderbolt"
        opponent_move = "uturn"
        self.state.self.active.speed = 2
        self.state.opponent.active.speed = 1
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                0.07500000000000001,
                [
                    ('damage', 'opponent', 72),
                    ('apply_status', 'opponent', 'par'),
                    ('damage', 'self', 60),
                    ('switch', 'opponent', 'aromatisse', 'yveltal')
                ],
                False
            ),
            TransposeInstruction(
                0.025,
                [
                    ('damage', 'opponent', 72),
                    ('apply_status', 'opponent', 'par'),
                ],
                True
            ),
            TransposeInstruction(
                0.9,
                [
                    ('damage', 'opponent', 72),
                    ('damage', 'self', 60),
                    ('switch', 'opponent', 'aromatisse', 'yveltal')
                ],
                False
            ),
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_uturn_when_there_are_no_available_switches_works(self):
        bot_move = "splash"
        opponent_move = "uturn"
        self.state.self.active.speed = 1
        self.state.opponent.active.speed = 2
        for mon in self.state.opponent.reserve.values():
            mon.hp = 0

        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1.0,
                [
                    ('damage', 'self', 60)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_fast_voltswitch_results_in_switching_out_for_opponent(self):
        self.state.self.active.ability = None  # raichu has lightningrod lol
        bot_move = "tackle"
        opponent_move = "voltswitch"
        self.state.self.active.speed = 1
        self.state.opponent.active.speed = 2
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1.0,
                [
                        (constants.MUTATOR_DAMAGE, constants.SELF, 29),
                        (constants.MUTATOR_SWITCH, constants.OPPONENT, 'aromatisse', 'bronzong'),
                        (constants.MUTATOR_DAMAGE, constants.OPPONENT, 10),

                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_immune_by_ability_does_not_allow_voltswitch(self):
        self.state.self.active.ability = 'lightningrod'  # immune to voltswitch
        bot_move = "tackle"
        opponent_move = "voltswitch"
        self.state.self.active.speed = 1
        self.state.opponent.active.speed = 2
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1.0,
                [
                    (constants.MUTATOR_BOOST, constants.SELF, constants.SPECIAL_ATTACK, 1),
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 25),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_ground_type_does_not_allow_voltswitch(self):
        self.state.self.active.ability = None  # raichu has lightningrod lol
        self.state.self.active.types = ['ground']
        bot_move = "tackle"
        opponent_move = "voltswitch"
        self.state.self.active.speed = 1
        self.state.opponent.active.speed = 2
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1.0,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 25),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_parting_show_allows_switch(self):
        self.state.self.active.types = ['ground']
        bot_move = "tackle"
        opponent_move = "partingshot"
        self.state.self.active.speed = 1
        self.state.opponent.active.speed = 2
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1.0,
                [
                    (constants.MUTATOR_BOOST, constants.SELF, constants.ATTACK, -1),
                    (constants.MUTATOR_BOOST, constants.SELF, constants.SPECIAL_ATTACK, -1),
                    (constants.MUTATOR_SWITCH, constants.OPPONENT, 'aromatisse', 'bronzong'),
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 6)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_bellydrum_works_properly_in_basic_case(self):
        bot_move = "bellydrum"
        opponent_move = "splash"
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1.0,
                [
                    (constants.MUTATOR_BOOST, constants.SELF, constants.ATTACK, 6),
                    (constants.MUTATOR_HEAL, constants.SELF, -1 * self.state.self.active.maxhp / 2)

                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_bellydrum_kills_user_when_hp_is_less_than_half(self):
        bot_move = "bellydrum"
        opponent_move = "splash"
        self.state.self.active.hp = 1
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1.0,
                [
                    (constants.MUTATOR_BOOST, constants.SELF, constants.ATTACK, 6),
                    (constants.MUTATOR_HEAL, constants.SELF, -1)

                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_gryo_ball_does_damage(self):
        bot_move = "gyroball"
        opponent_move = "splash"
        self.state.self.active.speed = 1
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1.0,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 186),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_gryo_ball_does_damage_when_speed_is_equal(self):
        bot_move = "gyroball"
        opponent_move = "splash"
        self.state.self.active.speed = self.state.opponent.active.speed
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1.0,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 35),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_electro_ball_does_damage_when_speed_is_equal(self):
        bot_move = "electroball"
        opponent_move = "splash"
        self.state.self.active.speed = self.state.opponent.active.speed
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1.0,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 33),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_electro_ball_does_damage_when_speed_is_much_greater(self):
        bot_move = "electroball"
        opponent_move = "splash"
        self.state.opponent.active.speed = 1
        self.state.self.active.speed = 100
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1.0,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 119),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_whirlwind_behaves_correctly_with_a_regular_move(self):
        bot_move = "whirlwind"
        opponent_move = "flamethrower"
        self.state.opponent.active.attack_boost = 3
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                0.1,
                [
                    (constants.MUTATOR_DAMAGE, constants.SELF, 74),
                    (constants.MUTATOR_APPLY_STATUS, constants.SELF, constants.BURN),
                    (constants.MUTATOR_UNBOOST, constants.OPPONENT, constants.ATTACK, 3),
                    (constants.MUTATOR_DAMAGE, constants.SELF, 13),  # burn damage
                ],
                False
            ),
            TransposeInstruction(
                0.9,
                [
                    (constants.MUTATOR_DAMAGE, constants.SELF, 74),
                    (constants.MUTATOR_UNBOOST, constants.OPPONENT, constants.ATTACK, 3)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_pokemon_boosting_into_roar(self):
        bot_move = "roar"
        opponent_move = "swordsdance"
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1.0,
                [
                    (constants.MUTATOR_BOOST, constants.OPPONENT, constants.ATTACK, 2),
                    (constants.MUTATOR_UNBOOST, constants.OPPONENT, constants.ATTACK, 2)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_accuracy_reduction_move(self):
        bot_move = "flash"
        opponent_move = "splash"
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1.0,
                [
                    (constants.MUTATOR_BOOST, constants.OPPONENT, constants.ACCURACY, -1),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_accuracy_does_not_go_below_negative_6(self):
        bot_move = "flash"
        opponent_move = "splash"
        self.state.opponent.active.accuracy_boost = -6
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1.0,
                [
                    (constants.MUTATOR_BOOST, constants.OPPONENT, constants.ACCURACY, 0)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_attack_does_not_go_above_6(self):
        bot_move = "swordsdance"
        opponent_move = "splash"
        self.state.self.active.attack_boost = 6
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1.0,
                [
                    (constants.MUTATOR_BOOST, constants.SELF, constants.ATTACK, 0)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_accuracy_reduction_move_into_tackle_causes_multiple_states(self):
        bot_move = "flash"
        opponent_move = "tackle"
        self.state.self.active.speed = 2
        self.state.opponent.active.speed = 1
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                0.75,
                [
                    (constants.MUTATOR_BOOST, constants.OPPONENT, constants.ACCURACY, -1),
                    (constants.MUTATOR_DAMAGE, constants.SELF, 35)
                ],
                False
            ),
            TransposeInstruction(
                0.25,
                [
                    (constants.MUTATOR_BOOST, constants.OPPONENT, constants.ACCURACY, -1),
                ],
                True
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_accuracy_reduction_move_into_contrary_with_tackle_causes_one_state(self):
        bot_move = "flash"
        opponent_move = "tackle"
        self.state.self.active.speed = 2
        self.state.opponent.active.speed = 1
        self.state.opponent.active.ability = 'contrary'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1.0,
                [
                    (constants.MUTATOR_BOOST, constants.OPPONENT, constants.ACCURACY, 1),
                    (constants.MUTATOR_DAMAGE, constants.SELF, 35)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_evasion_boosting_move(self):
        bot_move = "doubleteam"
        opponent_move = "splash"
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1.0,
                [
                    (constants.MUTATOR_BOOST, constants.SELF, constants.EVASION, 1),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_evasion_boosting_move_causes_two_states(self):
        bot_move = "doubleteam"
        opponent_move = "tackle"
        self.state.self.active.speed = 2
        self.state.opponent.active.speed = 1
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                0.75,
                [
                    (constants.MUTATOR_BOOST, constants.SELF, constants.EVASION, 1),
                    (constants.MUTATOR_DAMAGE, constants.SELF, 35)
                ],
                False
            ),
            TransposeInstruction(
                0.25,
                [
                    (constants.MUTATOR_BOOST, constants.SELF, constants.EVASION, 1),
                ],
                True
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_evasion_boosting_move_with_contrary_causes_one_state(self):
        bot_move = "doubleteam"
        opponent_move = "tackle"
        self.state.self.active.ability = 'contrary'
        self.state.self.active.speed = 2
        self.state.opponent.active.speed = 1
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_BOOST, constants.SELF, constants.EVASION, -1),
                    (constants.MUTATOR_DAMAGE, constants.SELF, 35)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_accuracy_increase_does_not_produce_two_states(self):
        bot_move = "splash"
        opponent_move = "tackle"
        self.state.opponent.active.accuracy_boost = 1
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1.0,
                [
                    (constants.MUTATOR_DAMAGE, constants.SELF, 35)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_pokemon_with_active_substitute_switching_into_phazing_move(self):
        bot_move = "switch starmie"
        opponent_move = "roar"
        self.state.self.active.volatile_status = {'substitute'}
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1.0,
                [
                    (constants.MUTATOR_REMOVE_VOLATILE_STATUS, constants.SELF, constants.SUBSTITUTE),
                    (constants.MUTATOR_SWITCH, constants.SELF, 'raichu', 'starmie')
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_pokemon_with_active_substitute_switching_into_phazing_move_that_gets_reflected(self):
        bot_move = "switch starmie"
        opponent_move = "roar"
        self.state.self.active.volatile_status = {'substitute'}
        self.state.self.reserve['starmie'].ability = 'magicbounce'
        self.state.opponent.active.attack_boost = 5
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1.0,
                [
                    (constants.MUTATOR_REMOVE_VOLATILE_STATUS, constants.SELF, constants.SUBSTITUTE),
                    (constants.MUTATOR_SWITCH, constants.SELF, 'raichu', 'starmie'),
                    (constants.MUTATOR_UNBOOST, constants.OPPONENT, constants.ATTACK, 5)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_dragontail_behaves_well_with_regular_move(self):
        bot_move = "dragontail"
        opponent_move = "tackle"
        self.state.opponent.active.types = ['normal']
        self.state.opponent.active.attack_boost = 3
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                0.9,
                [
                    (constants.MUTATOR_DAMAGE, constants.SELF, 127),
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 37),
                    (constants.MUTATOR_UNBOOST, constants.OPPONENT, constants.ATTACK, 3)
                ],
                False
            ),
            TransposeInstruction(
                0.09999999999999998,
                [
                    (constants.MUTATOR_DAMAGE, constants.SELF, 127)
                ],
                True
            ),
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_whirlwind_removes_volatile_statuses(self):
        bot_move = "whirlwind"
        opponent_move = "splash"
        self.state.opponent.active.volatile_status.add('confusion')
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1.0,
                [
                    (constants.MUTATOR_REMOVE_VOLATILE_STATUS, constants.OPPONENT, constants.CONFUSION)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_suckerpunch_into_tackle_makes_suckerpunch_hit(self):
        bot_move = "suckerpunch"
        opponent_move = "tackle"
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    ('damage', 'opponent', 22),
                    ('damage', 'self', 35),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_substitute_into_weak_attack_does_not_remove_volatile_status(self):
        self.state.self.active.speed = 100
        self.state.opponent.active.speed = 99
        bot_move = "substitute"
        opponent_move = "tackle"
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_APPLY_VOLATILE_STATUS, constants.SELF, constants.SUBSTITUTE),
                    (constants.MUTATOR_DAMAGE, constants.SELF, self.state.self.active.maxhp * 0.25),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_substitute_into_strong_attack_removes_volatile_status(self):
        self.state.self.active.speed = 100
        self.state.opponent.active.speed = 99
        bot_move = "substitute"
        opponent_move = "earthquake"
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_APPLY_VOLATILE_STATUS, constants.SELF, constants.SUBSTITUTE),
                    (constants.MUTATOR_DAMAGE, constants.SELF, self.state.self.active.maxhp * 0.25),
                    (constants.MUTATOR_REMOVE_VOLATILE_STATUS, constants.SELF, constants.SUBSTITUTE),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_substitute_fails_if_user_has_less_than_one_quarter_maxhp(self):
        self.state.self.active.speed = 100
        self.state.opponent.active.speed = 99
        self.state.self.active.hp = 0.2 * self.state.self.active.maxhp
        bot_move = "substitute"
        opponent_move = "earthquake"
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.SELF, 41.6),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_crosschop_missing_activates_blunder_policy(self):
        bot_move = "crosschop"
        opponent_move = "splash"
        self.state.self.active.item = 'blunderpolicy'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                0.8,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 31),
                ],
                False
            ),
            TransposeInstruction(
                0.19999999999999996,
                [
                    (constants.MUTATOR_BOOST, constants.SELF, constants.SPEED, 2),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_willowisp_missing_activates_blunder_policy(self):
        bot_move = "willowisp"
        opponent_move = "splash"
        self.state.self.active.item = 'blunderpolicy'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                0.85,
                [
                    (constants.MUTATOR_APPLY_STATUS, constants.OPPONENT, constants.BURN),
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 18)
                ],
                False
            ),
            TransposeInstruction(
                0.15000000000000002,
                [
                    (constants.MUTATOR_BOOST, constants.SELF, constants.SPEED, 2),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_highjumpkick_causes_crash(self):
        self.state.self.active.speed = 100
        self.state.opponent.active.speed = 99
        bot_move = "highjumpkick"
        opponent_move = "splash"
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                0.9,
                [
                    ('damage', 'opponent', 40),
                ],
                False
            ),
            TransposeInstruction(
                0.09999999999999998,
                [
                    ('damage', 'self', 104),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_highjumpkick_causes_crash_with_previous_move(self):
        self.state.self.active.speed = 100
        self.state.opponent.active.speed = 101
        self.state.self.active.hp = 36  # tackle does 35 damage
        bot_move = "highjumpkick"
        opponent_move = "tackle"
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                0.9,
                [
                    (constants.MUTATOR_DAMAGE, constants.SELF, 35),
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 40)
                ],
                False
            ),
            TransposeInstruction(
                0.09999999999999998,
                [
                    (constants.MUTATOR_DAMAGE, constants.SELF, 35),
                    (constants.MUTATOR_DAMAGE, constants.SELF, 1),
                ],
                True
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_highjumpkick_crash_when_switching_into_ghost(self):
        self.state.self.active.speed = 100
        self.state.opponent.active.speed = 101
        self.state.self.active.hp = 1

        self.state.opponent.reserve['gengar'] = Pokemon.from_state_pokemon_dict(StatePokemon("gengar", 73).to_dict())
        bot_move = "highjumpkick"
        opponent_move = "switch gengar"
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_SWITCH, constants.OPPONENT, 'aromatisse', 'gengar'),
                    (constants.MUTATOR_DAMAGE, constants.SELF, 1)
                ],
                True
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_suckerpunch_into_swordsdance_makes_suckerpunch_miss(self):
        bot_move = "suckerpunch"
        opponent_move = "swordsdance"
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_BOOST, constants.OPPONENT, constants.ATTACK, 2)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_rockhead_removes_recoil_for_one_but_not_the_other(self):
        bot_move = "doubleedge"
        opponent_move = "doubleedge"
        self.state.self.active.ability = 'rockhead'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 74),
                    (constants.MUTATOR_DAMAGE, constants.SELF, 101),
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 33),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_tackle_into_ironbarbs_causes_recoil(self):
        bot_move = "splash"
        opponent_move = "tackle"
        self.state.self.active.ability = 'ironbarbs'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.SELF, 35),
                    (constants.MUTATOR_HEAL, constants.OPPONENT, -37),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_tackle_into_ironbarbs_causes_no_recoil_when_attacker_has_neutralizing_gas(self):
        bot_move = "splash"
        opponent_move = "tackle"
        self.state.self.active.ability = 'ironbarbs'
        self.state.opponent.active.ability = 'neutralizinggas'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.SELF, 35),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_dynamax_cannon_does_double_damage_versus_dynamaxed(self):
        self.state.opponent.active.types = ['normal']
        bot_move = "dynamaxcannon"
        opponent_move = "splash"
        self.state.opponent.active.volatile_status.add(constants.DYNAMAX)
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 105),  # normal damage is 53
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_dynamax_cannon_does_normal_damage_versus_non_dynamaxed(self):
        self.state.opponent.active.types = ['normal']
        bot_move = "dynamaxcannon"
        opponent_move = "splash"
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 53),  # normal damage is 53
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_noretreat_boosts_own_stats(self):
        bot_move = "noretreat"
        opponent_move = "splash"
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_BOOST, constants.SELF, constants.ATTACK, 1),
                    (constants.MUTATOR_BOOST, constants.SELF, constants.DEFENSE, 1),
                    (constants.MUTATOR_BOOST, constants.SELF, constants.SPECIAL_ATTACK, 1),
                    (constants.MUTATOR_BOOST, constants.SELF, constants.SPECIAL_DEFENSE, 1),
                    (constants.MUTATOR_BOOST, constants.SELF, constants.SPEED, 1),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_tarshot_lowers_speed_and_sets_volatile_status(self):
        bot_move = "tarshot"
        opponent_move = "splash"
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_APPLY_VOLATILE_STATUS, constants.OPPONENT, 'tarshot'),
                    (constants.MUTATOR_BOOST, constants.OPPONENT, constants.SPEED, -1),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_tarshot_increases_fire_damage(self):
        bot_move = "eruption"
        opponent_move = "splash"
        self.state.opponent.active.volatile_status.add('tarshot')
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 159)  # normal damage is 79
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_dragondarts_does_double_damage(self):
        self.state.opponent.active.types = ['normal']
        bot_move = "dragondarts"
        opponent_move = "splash"
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 62)  # one hit would do 32
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_boltbeak_does_normal_damage_when_moving_second(self):
        self.state.self.active.speed = 1
        self.state.opponent.active.speed = 2
        bot_move = "boltbeak"
        opponent_move = "splash"
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 80)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_boltbeak_does_double_damage_when_moving_first(self):
        self.state.self.active.speed = 2
        self.state.opponent.active.speed = 1
        bot_move = "boltbeak"
        opponent_move = "splash"
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 158)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_fishious_rend_does_normal_damage_when_moving_second(self):
        self.state.self.active.speed = 1
        self.state.opponent.active.speed = 2
        bot_move = "fishiousrend"
        opponent_move = "splash"
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 53)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_fishious_rend_does_double_damage_when_moving_first(self):
        self.state.self.active.speed = 2
        self.state.opponent.active.speed = 1
        bot_move = "fishiousrend"
        opponent_move = "splash"
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 105)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_tackle_into_roughskin_causes_recoil(self):
        bot_move = "splash"
        opponent_move = "tackle"
        self.state.self.active.ability = 'roughskin'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.SELF, 35),
                    (constants.MUTATOR_HEAL, constants.OPPONENT, -18.5),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_courtchange_swaps_rocks(self):
        bot_move = "courtchange"
        opponent_move = "splash"
        self.state.self.side_conditions[constants.STEALTH_ROCK] = 1
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_SIDE_END, constants.SELF, constants.STEALTH_ROCK, 1),
                    (constants.MUTATOR_SIDE_START, constants.OPPONENT, constants.STEALTH_ROCK, 1),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_courtchange_does_not_swap_zero_value_side_condition(self):
        bot_move = "courtchange"
        opponent_move = "splash"
        self.state.self.side_conditions[constants.STEALTH_ROCK] = 1
        self.state.self.side_conditions[constants.SPIKES] = 0
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_SIDE_END, constants.SELF, constants.STEALTH_ROCK, 1),
                    (constants.MUTATOR_SIDE_START, constants.OPPONENT, constants.STEALTH_ROCK, 1),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_courtchange_swaps_rocks_and_spikes(self):
        bot_move = "courtchange"
        opponent_move = "splash"
        self.state.self.side_conditions[constants.STEALTH_ROCK] = 1
        self.state.opponent.side_conditions[constants.SPIKES] = 2
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_SIDE_END, constants.SELF, constants.STEALTH_ROCK, 1),
                    (constants.MUTATOR_SIDE_START, constants.OPPONENT, constants.STEALTH_ROCK, 1),
                    (constants.MUTATOR_SIDE_END, constants.OPPONENT, constants.SPIKES, 2),
                    (constants.MUTATOR_SIDE_START, constants.SELF, constants.SPIKES, 2),
                ],
                False
            )
        ]

        self.mutator.apply(expected_instructions[0].instructions)

        self.assertEqual(expected_instructions, instructions)

    def test_regular_damaging_move_with_speed_boost(self):
        bot_move = "tackle"
        opponent_move = "splash"
        self.state.self.active.ability = 'speedboost'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 25),
                    (constants.MUTATOR_BOOST, constants.SELF, constants.SPEED, 1)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_clangoroussoul(self):
        bot_move = "clangoroussoul"
        opponent_move = "splash"
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_BOOST, constants.SELF, constants.ATTACK, 1),
                    (constants.MUTATOR_BOOST, constants.SELF, constants.DEFENSE, 1),
                    (constants.MUTATOR_BOOST, constants.SELF, constants.SPECIAL_ATTACK, 1),
                    (constants.MUTATOR_BOOST, constants.SELF, constants.SPECIAL_DEFENSE, 1),
                    (constants.MUTATOR_BOOST, constants.SELF, constants.SPEED, 1),
                    (constants.MUTATOR_HEAL, constants.SELF, -69.33333333333333)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_clanorous_soul_fails_when_at_less_than_one_third_hp(self):
        bot_move = "clangoroussoul"
        opponent_move = "splash"
        self.state.self.active.hp = 1
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_boosting_move_with_speedboost(self):
        bot_move = "swordsdance"
        opponent_move = "splash"
        self.state.self.active.ability = 'speedboost'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_BOOST, constants.SELF, constants.ATTACK, 2),
                    (constants.MUTATOR_BOOST, constants.SELF, constants.SPEED, 1)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_speed_boosting_move_with_speedboost(self):
        bot_move = "dragondance"
        opponent_move = "splash"
        self.state.self.active.ability = 'speedboost'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_BOOST, constants.SELF, constants.ATTACK, 1),
                    (constants.MUTATOR_BOOST, constants.SELF, constants.SPEED, 1),
                    (constants.MUTATOR_BOOST, constants.SELF, constants.SPEED, 1),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_serenegrace(self):
        bot_move = "ironhead"
        opponent_move = "tackle"
        self.state.self.active.ability = 'serenegrace'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                0.6,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 99),
                    (constants.MUTATOR_APPLY_VOLATILE_STATUS, constants.OPPONENT, constants.FLINCH),
                    (constants.MUTATOR_REMOVE_VOLATILE_STATUS, constants.OPPONENT, constants.FLINCH),
                ],
                True
            ),
            TransposeInstruction(
                0.4,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 99),
                    (constants.MUTATOR_DAMAGE, constants.SELF, 35),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_serenegrace_on_paralyzed_pokemon(self):
        bot_move = "ironhead"
        opponent_move = "tackle"
        self.state.self.active.ability = 'serenegrace'
        self.state.opponent.active.status = constants.PARALYZED
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                0.6,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 99),
                    (constants.MUTATOR_APPLY_VOLATILE_STATUS, constants.OPPONENT, constants.FLINCH),
                    (constants.MUTATOR_REMOVE_VOLATILE_STATUS, constants.OPPONENT, constants.FLINCH),
                ],
                True
            ),
            TransposeInstruction(
                0.30000000000000004,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 99),
                    (constants.MUTATOR_DAMAGE, constants.SELF, 35),
                ],
                False
            ),
            TransposeInstruction(
                0.1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 99),
                ],
                True
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_fire_type_cannot_be_burned(self):
        bot_move = "willowisp"
        opponent_move = "splash"
        self.state.opponent.active.types = ['fire']
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_sheerforce_works_properly(self):
        bot_move = "earthpower"
        opponent_move = "splash"
        self.state.self.active.ability = 'sheerforce'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 62)  # 48 is normal damage. This move also usually has a secondary effect
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_burned_with_guts_doubles_damage(self):
        bot_move = "tackle"
        opponent_move = "splash"
        self.state.self.active.ability = 'guts'
        self.state.self.active.status = constants.BURN
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 37),  # 25 is regular damage
                    (constants.MUTATOR_DAMAGE, constants.SELF, 13)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_tintedlens_doubles_not_very_effective_damage(self):
        bot_move = "tackle"
        opponent_move = "splash"
        self.state.self.active.ability = 'tintedlens'
        self.state.opponent.active.types = ['rock']
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 24),  # 12 is regular damage when resisted
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_fire_type_cannot_be_burned_from_secondary(self):
        bot_move = "flamethrower"
        opponent_move = "splash"
        self.state.opponent.active.types = ['fire']
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 24)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_analytic_boosts_damage(self):
        bot_move = "tackle"
        opponent_move = "splash"
        self.state.self.active.ability = 'analytic'
        self.state.self.active.speed = 1
        self.state.opponent.active.speed = 2
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 33)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_poisoning_move_shows_poison_damage_on_opponents_turn(self):
        bot_move = "poisonjab"
        opponent_move = "tackle"
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                0.3,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 99),
                    (constants.MUTATOR_APPLY_STATUS, constants.OPPONENT, constants.POISON),
                    (constants.MUTATOR_DAMAGE, constants.SELF, 35),
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, self.state.opponent.active.maxhp * 0.125)
                ],
                False
            ),
            TransposeInstruction(
                0.7,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 99),
                    (constants.MUTATOR_DAMAGE, constants.SELF, 35),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_avalanche_into_switch_does_not_increase_avalanche_damage(self):
        bot_move = "avalanche"
        opponent_move = "switch yveltal"
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1.0,
                [
                    (constants.MUTATOR_SWITCH, constants.OPPONENT, 'aromatisse', 'yveltal'),
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 68)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_using_toxic_results_in_first_damage_to_be_one_sixteenth(self):
        bot_move = "toxic"
        opponent_move = "splash"
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                0.9,
                [
                    (constants.MUTATOR_APPLY_STATUS, constants.OPPONENT, constants.TOXIC),
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, int(self.state.opponent.active.maxhp / 16)),
                    (constants.MUTATOR_SIDE_START, constants.OPPONENT, constants.TOXIC_COUNT, 1),
                ],
                False
            ),
            TransposeInstruction(
                0.09999999999999998,
                [],
                False
            ),
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_previously_existing_toxic_results_in_correct_damage(self):
        bot_move = "splash"
        opponent_move = "splash"
        self.state.opponent.active.status = constants.TOXIC
        self.state.opponent.side_conditions[constants.TOXIC_COUNT] = 1
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, int(self.state.opponent.active.maxhp / 8)),
                    (constants.MUTATOR_SIDE_START, constants.OPPONENT, constants.TOXIC_COUNT, 1),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_switching_out_with_natural_cure_removes_status(self):
        bot_move = "switch xatu"
        opponent_move = "splash"
        self.state.self.active.status = constants.BURN
        self.state.self.active.ability = 'naturalcure'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_REMOVE_STATUS, constants.SELF, constants.BURN),
                    (constants.MUTATOR_SWITCH, constants.SELF, 'raichu', 'xatu'),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_darkaura_boosts_damage(self):
        bot_move = "pursuit"
        opponent_move = "splash"
        self.state.self.active.ability = 'darkaura'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 17),  # normally 12
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_stakeout_does_double_damage_versus_switch(self):
        bot_move = "tackle"
        opponent_move = "switch yveltal"
        self.state.self.active.ability = 'stakeout'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_SWITCH, constants.OPPONENT, 'aromatisse', 'yveltal'),
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 45),  # 26 damage normally
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_icescales_halves_special_damage(self):
        bot_move = "swift"
        opponent_move = "splash"
        self.state.opponent.active.ability = 'icescales'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 16),  # normally 32
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_icescales_does_not_halve_physical_damage(self):
        bot_move = "tackle"
        opponent_move = "splash"
        self.state.opponent.active.ability = 'icescales'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 25),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_pastelveil_prevents_poison(self):
        bot_move = "toxic"
        opponent_move = "splash"
        self.state.opponent.active.ability = 'pastelveil'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_punkrock_increases_sound_damage(self):
        bot_move = "boomburst"
        opponent_move = "splash"
        self.state.self.active.ability = 'punkrock'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 96),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_punkrock_decreases_sound_damage(self):
        bot_move = "boomburst"
        opponent_move = "splash"
        self.state.opponent.active.ability = 'punkrock'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 37),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_steelyspirit_boosts_steel_move(self):
        bot_move = "bulletpunch"
        opponent_move = "splash"
        self.state.self.active.ability = 'steelyspirit'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 75),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_steam_engine_boosts_speed_when_hit_by_water_move(self):
        bot_move = "surf"
        opponent_move = "splash"
        self.state.opponent.active.ability = 'steamengine'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 48),
                    (constants.MUTATOR_BOOST, constants.OPPONENT, constants.SPEED, 6),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_steamengine_does_not_overboost(self):
        bot_move = "surf"
        opponent_move = "splash"
        self.state.opponent.active.ability = 'steamengine'
        self.state.opponent.active.speed_boost = 4
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 48),
                    (constants.MUTATOR_BOOST, constants.OPPONENT, constants.SPEED, 2),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_switching_into_pkmn_with_screen_cleaner_removes_screens_for_both_sides(self):
        bot_move = "switch starmie"
        opponent_move = "splash"
        self.state.self.reserve['starmie'].ability = 'screencleaner'
        self.state.self.side_conditions[constants.REFLECT] = 1
        self.state.self.side_conditions[constants.LIGHT_SCREEN] = 1
        self.state.opponent.side_conditions[constants.REFLECT] = 1
        self.state.opponent.side_conditions[constants.AURORA_VEIL] = 1
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_SWITCH, constants.SELF, 'raichu', 'starmie'),
                    (constants.MUTATOR_SIDE_END, constants.SELF, constants.REFLECT, 1),
                    (constants.MUTATOR_SIDE_END, constants.OPPONENT, constants.REFLECT, 1),
                    (constants.MUTATOR_SIDE_END, constants.SELF, constants.LIGHT_SCREEN, 1),
                    (constants.MUTATOR_SIDE_END, constants.OPPONENT, constants.AURORA_VEIL, 1),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_pursuit_into_switch_causes_pursuit_to_happen_first_with_double_damage(self):
        bot_move = "pursuit"
        opponent_move = "switch yveltal"
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 24),  # normal damage is 12
                    (constants.MUTATOR_SWITCH, constants.OPPONENT, 'aromatisse', 'yveltal'),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_dying_when_being_pursuited(self):
        bot_move = "pursuit"
        opponent_move = "switch yveltal"
        self.state.opponent.active.hp = 1
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 1),

                    # this is technically wrong - the opponent would get the option to switch on the next turn.
                    # This doesn't matter in the eyes of the bot since they need to switch anyways
                    (constants.MUTATOR_SWITCH, constants.OPPONENT, 'aromatisse', 'yveltal'),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_opposite_pokemon_darkaura_boosts_damage(self):
        bot_move = "pursuit"
        opponent_move = "splash"
        self.state.opponent.active.ability = 'darkaura'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 17),  # normally 12
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_aurabreak_prevents_dark_aura(self):
        bot_move = "pursuit"
        opponent_move = "splash"
        self.state.self.active.ability = 'darkaura'
        self.state.opponent.active.ability = 'aurabreak'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 12),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_toxic_cannot_drop_below_0_hp(self):
        bot_move = "splash"
        opponent_move = "splash"
        self.state.opponent.active.status = constants.TOXIC
        self.state.opponent.active.hp = 1
        self.state.opponent.side_conditions[constants.TOXIC_COUNT] = 1
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 1),
                    (constants.MUTATOR_SIDE_START, constants.OPPONENT, constants.TOXIC_COUNT, 1),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_stealthrock_produces_correct_instruction(self):
        bot_move = "stealthrock"
        opponent_move = "splash"
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_SIDE_START, constants.OPPONENT, constants.STEALTH_ROCK, 1)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_solarbeam_does_not_do_damage_but_sets_volatile_status(self):
        bot_move = "solarbeam"
        opponent_move = "splash"
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_APPLY_VOLATILE_STATUS, constants.SELF, "solarbeam")
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_charged_solarbeam_executes_normally(self):
        bot_move = "solarbeam"
        opponent_move = "splash"
        self.state.self.active.volatile_status.add("solarbeam")
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 63)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_sun_does_not_require_solarbeam_charge(self):
        bot_move = "solarbeam"
        opponent_move = "splash"
        self.state.weather = constants.SUN
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 63)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_infiltrator_toxic_bypasses_sub(self):
        bot_move = "toxic"
        opponent_move = "splash"
        self.state.self.active.ability = 'infiltrator'
        self.state.opponent.active.volatile_status.add(constants.SUBSTITUTE)
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                0.9,
                [
                    (constants.MUTATOR_APPLY_STATUS, constants.OPPONENT, constants.TOXIC),
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 18),
                    (constants.MUTATOR_SIDE_START, constants.OPPONENT, constants.TOXIC_COUNT, 1),
                ],
                False
            ),
            TransposeInstruction(
                0.09999999999999998,
                [],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_poison_type_cannot_miss_toxic(self):
        bot_move = "toxic"
        opponent_move = "splash"
        self.state.self.active.types = ['poison']
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_APPLY_STATUS, constants.OPPONENT, constants.TOXIC),
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 18),
                    (constants.MUTATOR_SIDE_START, constants.OPPONENT, constants.TOXIC_COUNT, 1),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_fly_without_z_crystal_charges(self):
        bot_move = "fly"
        opponent_move = "splash"
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_APPLY_VOLATILE_STATUS, constants.SELF, "fly")
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_desolate_land_makes_water_moves_fail(self):
        bot_move = "surf"
        opponent_move = "splash"
        self.state.weather = constants.DESOLATE_LAND
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_stealthrock_produces_no_instructions_when_it_exists(self):
        bot_move = "stealthrock"
        opponent_move = "splash"
        self.state.opponent.side_conditions[constants.STEALTH_ROCK] = 1
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_spikes_goes_to_3_layers(self):
        bot_move = "spikes"
        opponent_move = "splash"
        self.state.opponent.side_conditions[constants.SPIKES] = 2
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_SIDE_START, constants.OPPONENT, constants.SPIKES, 1)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_reflect_halves_damage_when_used(self):
        bot_move = "reflect"  # bot is faster
        opponent_move = "tackle"
        self.state.opponent.side_conditions[constants.SPIKES] = 2
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_SIDE_START, constants.SELF, constants.REFLECT, 1),
                    (constants.MUTATOR_DAMAGE, constants.SELF, 17),  # non-reflect does 35
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_switch_into_toxicspikes_plus_damage(self):
        bot_move = "switch starmie"
        opponent_move = "tackle"
        self.state.self.side_conditions[constants.TOXIC_SPIKES] = 1
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_SWITCH, constants.SELF, "raichu", "starmie"),
                    (constants.MUTATOR_APPLY_STATUS, constants.SELF, constants.POISON),
                    (constants.MUTATOR_DAMAGE, constants.SELF, 24),  # tackle damage
                    (constants.MUTATOR_DAMAGE, constants.SELF, 28),  # poison damage
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_switch_into_toxicspikes_plus_setting_rocks_from_opponent(self):
        bot_move = "switch starmie"
        opponent_move = "stealthrock"
        self.state.self.side_conditions[constants.TOXIC_SPIKES] = 2
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_SWITCH, constants.SELF, "raichu", "starmie"),
                    (constants.MUTATOR_APPLY_STATUS, constants.SELF, constants.TOXIC),
                    (constants.MUTATOR_SIDE_START, constants.SELF, constants.STEALTH_ROCK, 1),
                    (constants.MUTATOR_DAMAGE, constants.SELF, 14),  # poison damage
                    (constants.MUTATOR_SIDE_START, constants.SELF, constants.TOXIC_COUNT, 1),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_spikes_into_rapid_spin_clears_the_spikes(self):
        bot_move = "spikes"
        opponent_move = "rapidspin"
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_SIDE_START, constants.OPPONENT, constants.SPIKES, 1),
                    (constants.MUTATOR_DAMAGE, constants.SELF, 43),
                    (constants.MUTATOR_SIDE_END, constants.OPPONENT, constants.SPIKES, 1),
                    (constants.MUTATOR_BOOST, constants.OPPONENT, constants.SPEED, 1)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_spikes_into_rapid_spin_does_not_clear_spikes_when_user_is_ghost_type(self):
        bot_move = "spikes"
        opponent_move = "rapidspin"

        self.state.self.active.types = ['ghost']

        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_SIDE_START, constants.OPPONENT, constants.SPIKES, 1),
                ],
                True
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_defog_works_even_if_defender_is_ghost(self):
        bot_move = "spikes"
        opponent_move = "defog"

        self.state.self.active.types = ['ghost']

        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_SIDE_START, constants.OPPONENT, constants.SPIKES, 1),
                    (constants.MUTATOR_SIDE_END, constants.OPPONENT, constants.SPIKES, 1),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_defog_removes_terrain(self):
        bot_move = "splash"
        opponent_move = "defog"
        self.state.field = constants.ELECTRIC_TERRAIN

        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_FIELD_END, constants.ELECTRIC_TERRAIN)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_defog_removes_terrain_and_spikes(self):
        bot_move = "splash"
        opponent_move = "defog"
        self.state.field = constants.ELECTRIC_TERRAIN
        self.state.self.side_conditions[constants.SPIKES] = 2

        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_FIELD_END, constants.ELECTRIC_TERRAIN),
                    (constants.MUTATOR_SIDE_END, constants.SELF, constants.SPIKES, 2)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_doubleironbash_does_double_damage(self):
        bot_move = "doubleironbash"
        opponent_move = "splash"

        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                0.3,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 149),
                    (constants.MUTATOR_APPLY_VOLATILE_STATUS, constants.OPPONENT, constants.FLINCH),
                    (constants.MUTATOR_REMOVE_VOLATILE_STATUS, constants.OPPONENT, constants.FLINCH),
                ],
                True
            ),
            TransposeInstruction(
                0.7,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 149)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_stamina_increases_defence_when_hit_with_damaging_move(self):
        bot_move = "tackle"
        opponent_move = "splash"

        self.state.opponent.active.ability = 'stamina'

        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 25),
                    (constants.MUTATOR_BOOST, constants.OPPONENT, constants.DEFENSE, 1),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_stamina_does_not_increase_defence_when_hit_with_status_move(self):
        bot_move = "charm"
        opponent_move = "splash"

        self.state.opponent.active.ability = 'stamina'

        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_BOOST, constants.OPPONENT, constants.ATTACK, -2),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_stealthrock_into_switch(self):
        bot_move = "stealthrock"
        opponent_move = "switch yveltal"
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_SWITCH, constants.OPPONENT, 'aromatisse', 'yveltal'),
                    (constants.MUTATOR_SIDE_START, constants.OPPONENT, constants.STEALTH_ROCK, 1)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_fainting_pokemon_does_not_move(self):
        self.state.opponent.active.hp = 1

        bot_move = "tackle"
        opponent_move = "tackle"
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    ('damage', 'opponent', 1),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_negative_boost_inflictions(self):
        bot_move = "crunch"
        opponent_move = "moonblast"
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                0.06,
                [
                    ('damage', 'opponent', 24),
                    ('boost', 'opponent', 'defense', -1),
                    ('damage', 'self', 119),
                    ('boost', 'self', 'special-attack', -1)
                ],
                False
            ),
            TransposeInstruction(
                0.13999999999999999,
                [
                    ('damage', 'opponent', 24),
                    ('boost', 'opponent', 'defense', -1),
                    ('damage', 'self', 119),
                ],
                False
            ),
            TransposeInstruction(
                0.24,
                [
                    ('damage', 'opponent', 24),
                    ('damage', 'self', 119),
                    ('boost', 'self', 'special-attack', -1)
                ],
                False
            ),
            TransposeInstruction(
                0.5599999999999999,
                [
                    ('damage', 'opponent', 24),
                    ('damage', 'self', 119),
                ],
                False
            ),
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_reflect_halves_physical_damage(self):
        bot_move = "tackle"
        opponent_move = "tackle"
        self.state.self.side_conditions[constants.REFLECT] = 1
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    ('damage', 'opponent', 25),
                    ('damage', 'self', 17)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_reflect_does_not_halve_special_damage(self):
        bot_move = "tackle"
        opponent_move = "fairywind"
        self.state.self.side_conditions[constants.REFLECT] = 1
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    ('damage', 'opponent', 25),
                    ('damage', 'self', 51)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_light_screen_halves_special_damage(self):
        bot_move = "tackle"
        opponent_move = "fairywind"
        self.state.self.side_conditions[constants.LIGHT_SCREEN] = 1
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    ('damage', 'opponent', 25),
                    ('damage', 'self', 25)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_rain_doubles_water_damage(self):
        bot_move = "surf"
        opponent_move = "tackle"
        self.state.weather = constants.RAIN
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    ('damage', 'opponent', 72),
                    ('damage', 'self', 35)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_rain_makes_hurricane_always_hit(self):
        bot_move = "hurricane"
        opponent_move = "splash"
        self.state.weather = constants.RAIN
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 59)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_sun_doubles_fire_damage(self):
        bot_move = "eruption"
        opponent_move = "tackle"
        self.state.weather = constants.SUN
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    ('damage', 'opponent', 119),
                    ('damage', 'self', 35)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_sand_properly_increses_special_defense_for_rock(self):
        bot_move = "surf"
        opponent_move = "splash"
        self.state.weather = constants.SAND
        self.state.opponent.active.types = ['rock']
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 64),
                    (constants.MUTATOR_DAMAGE, constants.SELF, 13),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_sand_does_not_increase_special_defense_for_ground(self):
        bot_move = "surf"
        opponent_move = "splash"
        self.state.weather = constants.SAND
        self.state.opponent.active.types = ['ground']
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 96),
                    (constants.MUTATOR_DAMAGE, constants.SELF, 13),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_lifeorb_gives_recoil(self):
        bot_move = "tackle"
        opponent_move = "tackle"
        self.state.self.active.item = 'lifeorb'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    ('damage', 'opponent', 33),
                    ('heal', 'self', -20.8),
                    ('damage', 'self', 35)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_choice_band_boosts_damage(self):
        bot_move = "tackle"
        opponent_move = "tackle"
        self.state.self.active.item = 'choiceband'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    ('damage', 'opponent', 37),
                    ('damage', 'self', 35)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_eviolite_reduces_damage(self):
        bot_move = "tackle"
        opponent_move = "tackle"
        self.state.self.active.item = 'eviolite'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    ('damage', 'opponent', 25),
                    ('damage', 'self', 24)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_rocky_helmet_hurts_attacker(self):
        bot_move = "tackle"
        opponent_move = "tackle"
        self.state.self.active.item = 'rockyhelmet'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    ('damage', 'opponent', 25),
                    ('damage', 'self', 35),
                    ('heal', 'opponent', -49.33333333333333)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_taunt_sets_taunt_status(self):
        bot_move = "taunt"
        opponent_move = "splash"
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_APPLY_VOLATILE_STATUS, constants.OPPONENT, constants.TAUNT)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_taunt_volatile_status_prevents_non_damaging_move(self):
        bot_move = "taunt"
        opponent_move = "calmmind"
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_APPLY_VOLATILE_STATUS, constants.OPPONENT, constants.TAUNT)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_taunt_volatile_status_does_not_prevent_damaging_move(self):
        bot_move = "taunt"
        opponent_move = "tackle"
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_APPLY_VOLATILE_STATUS, constants.OPPONENT, constants.TAUNT),
                    (constants.MUTATOR_DAMAGE, constants.SELF, 35)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_switch_into_ninetales_starts_sun_weather(self):
        bot_move = "switch ninetales"
        opponent_move = "splash"
        self.state.self.reserve['ninetales'] = Pokemon.from_state_pokemon_dict(StatePokemon("ninetales", 81).to_dict())
        self.state.self.reserve['ninetales'].ability = 'drought'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_SWITCH, 'self', self.state.self.active.id, 'ninetales'),
                    (constants.MUTATOR_WEATHER_START, constants.SUN, None)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_switch_into_politoed_starts_rain_weather(self):
        bot_move = "switch politoed"
        opponent_move = "splash"
        self.state.self.reserve['politoed'] = Pokemon.from_state_pokemon_dict(StatePokemon("politoed", 81).to_dict())
        self.state.self.reserve['politoed'].ability = 'drizzle'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_SWITCH, 'self', self.state.self.active.id, 'politoed'),
                    (constants.MUTATOR_WEATHER_START, constants.RAIN, None)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_switch_into_electricsurge_starts_terrain(self):
        bot_move = "switch tapukoko"
        opponent_move = "splash"
        self.state.self.reserve['tapukoko'] = Pokemon.from_state_pokemon_dict(StatePokemon("tapukoko", 81).to_dict())
        self.state.self.reserve['tapukoko'].ability = 'electricsurge'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_SWITCH, 'self', self.state.self.active.id, 'tapukoko'),
                    (constants.MUTATOR_FIELD_START, constants.ELECTRIC_TERRAIN, None)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_switch_into_psychicsurge_starts_terrain(self):
        bot_move = "switch tapulele"
        opponent_move = "splash"
        self.state.self.reserve['tapulele'] = Pokemon.from_state_pokemon_dict(StatePokemon("tapulele", 81).to_dict())
        self.state.self.reserve['tapulele'].ability = 'psychicsurge'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_SWITCH, 'self', self.state.self.active.id, 'tapulele'),
                    (constants.MUTATOR_FIELD_START, constants.PSYCHIC_TERRAIN, None)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_queenlymajesty_stops_priority_move(self):
        bot_move = "quickattack"
        opponent_move = "splash"
        self.state.opponent.active.ability = 'queenlymajesty'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_steelworker_boosts_steel_moves(self):
        bot_move = "heavyslam"
        opponent_move = "splash"
        self.state.opponent.active.types = ['normal']
        self.state.self.active.ability = 'steelworker'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 37)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    @mock.patch('showdown.engine.special_effects.moves.move_special_effect.pokedex')
    def test_heavyslam_damage_for_10_times_the_weight(self, pokedex_mock):
        # 10x the weight should result in 120 base-power
        fake_pokedex = {
            'pikachu': {
                'weight': 100
            },
            'pidgey': {
                'weight': 10
            }
        }
        pokedex_mock.__getitem__.side_effect = fake_pokedex.__getitem__

        bot_move = "heavyslam"
        opponent_move = "splash"
        self.state.self.active.types = ['normal']
        self.state.opponent.active.types = ['normal']
        self.state.self.active.id = 'pikachu'
        self.state.opponent.active.id = 'pidgey'

        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 74)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    @mock.patch('showdown.engine.special_effects.moves.move_special_effect.pokedex')
    def test_heavyslam_damage_for_4_times_the_weight(self, pokedex_mock):
        # 4x the weight should result in 100 base-power
        fake_pokedex = {
            'pikachu': {
                'weight': 100
            },
            'pidgey': {
                'weight': 25
            }
        }
        pokedex_mock.__getitem__.side_effect = fake_pokedex.__getitem__

        bot_move = "heavyslam"
        opponent_move = "splash"
        self.state.self.active.types = ['normal']
        self.state.opponent.active.types = ['normal']
        self.state.self.active.id = 'pikachu'
        self.state.opponent.active.id = 'pidgey'

        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 62)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    @mock.patch('showdown.engine.special_effects.moves.move_special_effect.pokedex')
    def test_heavyslam_damage_for_the_same_weight(self, pokedex_mock):
        # equal weight should result in 40 base-power
        fake_pokedex = {
            'pikachu': {
                'weight': 100
            },
            'pidgey': {
                'weight': 100
            }
        }
        pokedex_mock.__getitem__.side_effect = fake_pokedex.__getitem__

        bot_move = "heavyslam"
        opponent_move = "splash"
        self.state.self.active.types = ['normal']
        self.state.opponent.active.types = ['normal']
        self.state.self.active.id = 'pikachu'
        self.state.opponent.active.id = 'pidgey'

        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 25)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    @mock.patch('showdown.engine.special_effects.moves.move_special_effect.pokedex')
    def test_heatcrash_damage_for_the_same_weight(self, pokedex_mock):
        # 10x equal weight should result in 120 base-power
        fake_pokedex = {
            'pikachu': {
                'weight': 100
            },
            'pidgey': {
                'weight': 10
            }
        }
        pokedex_mock.__getitem__.side_effect = fake_pokedex.__getitem__

        bot_move = "heatcrash"
        opponent_move = "splash"
        self.state.self.active.types = ['normal']
        self.state.opponent.active.types = ['normal']
        self.state.self.active.id = 'pikachu'
        self.state.opponent.active.id = 'pidgey'

        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 74)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    @mock.patch('showdown.engine.special_effects.moves.move_special_effect.pokedex')
    def test_heatcrash_into_flashfire(self, pokedex_mock):
        # the defender has flashfire so no damage should be done, even with 10x the weight
        fake_pokedex = {
            'pikachu': {
                'weight': 100
            },
            'pidgey': {
                'weight': 10
            }
        }
        pokedex_mock.__getitem__.side_effect = fake_pokedex.__getitem__

        bot_move = "heatcrash"
        opponent_move = "splash"
        self.state.self.active.types = ['normal']
        self.state.opponent.active.types = ['normal']
        self.state.self.active.id = 'pikachu'
        self.state.opponent.active.id = 'pidgey'

        self.state.opponent.active.ability = 'flashfire'

        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_neuroforce_boosts_if_supereffective(self):
        bot_move = "machpunch"
        opponent_move = "splash"
        self.state.opponent.active.types = ['normal']
        self.state.self.active.ability = 'neuroforce'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 64)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_marvelscale_reduces_damage(self):
        bot_move = "tackle"
        opponent_move = "splash"
        self.state.opponent.active.types = ['normal']
        self.state.opponent.active.ability = 'marvelscale'
        self.state.opponent.active.status = constants.BURN
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 17),
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 18)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_marvelscale_does_not_reduce_special_damage(self):
        bot_move = "watergun"
        opponent_move = "splash"
        self.state.opponent.active.types = ['normal']
        self.state.opponent.active.ability = 'marvelscale'
        self.state.opponent.active.status = constants.BURN
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 22),
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 18)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_overcoat_protects_from_spore(self):
        bot_move = "spore"
        opponent_move = "splash"
        self.state.opponent.active.types = ['normal']
        self.state.opponent.active.ability = 'overcoat'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_unaware_ignore_defense_boost(self):
        bot_move = "tackle"
        opponent_move = "splash"
        self.state.opponent.active.types = ['normal']
        self.state.self.active.ability = 'unaware'
        self.state.opponent.active.defense_boost = 6
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 25)  # 25 is unboosted damage
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_unaware_ignore_special_defense_boost(self):
        bot_move = "watergun"
        opponent_move = "splash"
        self.state.opponent.active.types = ['normal']
        self.state.self.active.ability = 'unaware'
        self.state.opponent.active.special_defense_boost = 6
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 22)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_killing_a_pokemon_with_various_end_of_turn_action_items(self):
        bot_move = "return102"
        opponent_move = "splash"
        self.state.weather = constants.SAND
        self.state.opponent.active.types = ['normal']
        self.state.opponent.active.hp = 40
        self.state.opponent.active.item = 'leftovers'
        self.state.opponent.active.volatile_status.add(constants.LEECH_SEED)
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 40),
                    (constants.MUTATOR_DAMAGE, constants.SELF, 13)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_end_of_turn_instructions_execute_in_correct_order(self):
        bot_move = "splash"
        opponent_move = "splash"
        self.state.weather = constants.SAND
        self.state.opponent.active.types = ['normal']
        self.state.self.active.types = ['normal']
        self.state.self.active.item = 'leftovers'
        self.state.self.active.status = constants.POISON
        self.state.opponent.active.volatile_status.add(constants.LEECH_SEED)
        self.state.self.active.maxhp = 100
        self.state.self.active.hp = 50
        self.state.opponent.active.maxhp = 100
        self.state.opponent.active.hp = 50
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    # sand
                    (constants.MUTATOR_DAMAGE, constants.SELF, 6),
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 6),

                    # leftovers
                    (constants.MUTATOR_HEAL, constants.SELF, 6),

                    # poison
                    (constants.MUTATOR_DAMAGE, constants.SELF, 12),

                    # leechseed sap
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 12),
                    (constants.MUTATOR_HEAL, constants.SELF, 12)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_leftovers_healing(self):
        bot_move = "splash"
        opponent_move = "splash"
        self.state.self.active.hp = 1
        self.state.self.active.item = 'leftovers'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_HEAL, constants.SELF, 13)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_leftovers_healing_with_speedboost(self):
        bot_move = "splash"
        opponent_move = "splash"
        self.state.self.active.hp = 1
        self.state.self.active.item = 'leftovers'
        self.state.self.active.ability = 'speedboost'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_HEAL, constants.SELF, 13),
                    (constants.MUTATOR_BOOST, constants.SELF, constants.SPEED, 1)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_both_leftovers_healing(self):
        bot_move = "splash"
        opponent_move = "splash"
        self.state.self.active.hp = 1
        self.state.opponent.active.hp = 1
        self.state.self.active.item = 'leftovers'
        self.state.opponent.active.item = 'leftovers'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_HEAL, constants.SELF, 13),
                    (constants.MUTATOR_HEAL, constants.OPPONENT, 18),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_both_leftovers_healing_and_poison_damage(self):
        bot_move = "splash"
        opponent_move = "splash"
        self.state.self.active.hp = 1
        self.state.opponent.active.hp = 1
        self.state.self.active.item = 'leftovers'
        self.state.opponent.active.item = 'leftovers'
        self.state.opponent.active.status = constants.POISON
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_HEAL, constants.SELF, 13),
                    (constants.MUTATOR_HEAL, constants.OPPONENT, 18),
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 19),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_leftovers_has_no_effect_when_at_full_hp(self):
        bot_move = "splash"
        opponent_move = "splash"
        self.state.self.active.item = 'leftovers'
        self.state.opponent.active.item = 'leftovers'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_fainted_pokemon_gets_no_speedboost_or_leftovers_heal(self):
        bot_move = "splash"
        opponent_move = "splash"
        self.state.self.active.hp = 0
        self.state.self.active.item = 'leftovers'
        self.state.self.active.ability = 'speedboost'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_killing_a_pokemon_with_poisonheal(self):
        bot_move = "return102"
        opponent_move = "splash"
        self.state.opponent.active.types = ['normal']
        self.state.opponent.active.hp = 40
        self.state.opponent.active.status = constants.TOXIC
        self.state.opponent.active.ability = 'poisonheal'
        self.state.opponent.active.volatile_status.add(constants.LEECH_SEED)
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 40),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_killing_a_pokemon_with_poison(self):
        bot_move = "return102"
        opponent_move = "splash"
        self.state.opponent.active.types = ['normal']
        self.state.opponent.active.hp = 40
        self.state.opponent.active.status = constants.POISON
        self.state.opponent.active.volatile_status.add(constants.LEECH_SEED)
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 40),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_opponent_with_unaware_does_not_make_him_take_more_damage(self):
        bot_move = "tackle"
        opponent_move = "splash"
        self.state.opponent.active.types = ['normal']
        self.state.opponent.active.ability = 'unaware'  # now we set defenders ability to unaware. this shouldnt cause normal damage
        self.state.opponent.active.defense_boost = 6
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 7)  # 25 is unboosted damage
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_unaware_ignore_opponent_attack_boost(self):
        bot_move = "splash"
        opponent_move = "tackle"
        self.state.opponent.active.types = ['normal']
        self.state.self.active.ability = 'unaware'
        self.state.opponent.active.attack_boost = 6
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.SELF, 52)  # 202 is damage with +6
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_unaware_on_attacker_does_not_reduce_damage(self):
        bot_move = "splash"
        opponent_move = "tackle"
        self.state.opponent.active.types = ['normal']
        self.state.opponent.active.ability = 'unaware'
        self.state.opponent.active.attack_boost = 6
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.SELF, 202)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_overgrow_boosts_damage_below_one_third(self):
        bot_move = "vinewhip"
        opponent_move = "splash"
        self.state.opponent.active.types = ['normal']
        self.state.self.active.ability = 'overgrow'
        self.state.self.active.hp = 1
        self.state.self.active.maxhp = 4
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 42)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_swarm_boosts_damage_below_one_third(self):
        bot_move = "xscissor"
        opponent_move = "splash"
        self.state.opponent.active.types = ['normal']
        self.state.self.active.ability = 'swarm'
        self.state.self.active.hp = 1
        self.state.self.active.maxhp = 4
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 74)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_swarm_does_not_boost_when_at_half_health(self):
        bot_move = "xscissor"
        opponent_move = "splash"
        self.state.opponent.active.types = ['normal']
        self.state.self.active.ability = 'swarm'
        self.state.self.active.hp = 2
        self.state.self.active.maxhp = 4
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 49)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_shieldsdown_with_50_percent_can_be_burned(self):
        bot_move = "willowisp"
        opponent_move = "splash"
        self.state.opponent.active.types = ['normal']
        self.state.opponent.active.ability = 'shieldsdown'
        self.state.opponent.active.hp = 200
        self.state.opponent.active.maxhp = 400
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                0.85,
                [
                    (constants.MUTATOR_APPLY_STATUS, constants.OPPONENT, constants.BURN),
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 25),
                ],
                False
            ),
            TransposeInstruction(
                0.15000000000000002,
                [],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_galewings_increases_priority(self):
        bot_move = "bravebird"
        opponent_move = "tackle"
        self.state.opponent.active.types = ['normal']
        self.state.self.active.ability = 'galewings'
        self.state.self.active.speed = 1
        self.state.opponent.active.speed = 2
        self.state.self.active.hp = 400
        self.state.self.active.maxhp = 400
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 74),  # bot moves first even though it is slower
                    (constants.MUTATOR_DAMAGE, constants.SELF, 24),
                    (constants.MUTATOR_DAMAGE, constants.SELF, 52),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_galewings_does_not_increase_priority_when_hp_is_not_full(self):
        bot_move = "bravebird"
        opponent_move = "tackle"
        self.state.opponent.active.types = ['normal']
        self.state.self.active.ability = 'galewings'
        self.state.self.active.speed = 1
        self.state.opponent.active.speed = 2
        self.state.self.active.hp = 399
        self.state.self.active.maxhp = 400
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.SELF, 52),
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 74),
                    (constants.MUTATOR_DAMAGE, constants.SELF, 24),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_sturdy_prevents_ohko(self):
        bot_move = "splash"
        opponent_move = "tackle"
        self.state.opponent.active.types = ['normal']
        self.state.self.active.hp = 5
        self.state.self.active.maxhp = 5
        self.state.self.active.ability = 'sturdy'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.SELF, 4),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_sturdy_causes_no_damage_if_maxhp_is_1(self):
        bot_move = "splash"
        opponent_move = "tackle"
        self.state.opponent.active.types = ['normal']
        self.state.self.active.hp = 1
        self.state.self.active.maxhp = 1
        self.state.self.active.ability = 'sturdy'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.SELF, 0),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_sturdy_mon_can_be_killed_when_not_at_maxhp(self):
        bot_move = "splash"
        opponent_move = "tackle"
        self.state.opponent.active.types = ['normal']
        self.state.self.active.hp = 10
        self.state.self.active.maxhp = 100
        self.state.self.active.ability = 'sturdy'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.SELF, 10),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_justified_boosts_attack_versus_dark_move(self):
        bot_move = "splash"
        opponent_move = "knockoff"
        self.state.opponent.active.types = ['normal']
        self.state.self.active.ability = 'justified'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.SELF, 82),
                    (constants.MUTATOR_BOOST, constants.SELF, constants.ATTACK, 1),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_no_boost_from_non_damaging_dark_move(self):
        bot_move = "splash"
        opponent_move = "partingshot"
        self.state.opponent.active.types = ['normal']
        self.state.self.active.ability = 'justified'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_BOOST, constants.SELF, constants.ATTACK, -1),
                    (constants.MUTATOR_BOOST, constants.SELF, constants.SPECIAL_ATTACK, -1),
                    (constants.MUTATOR_SWITCH, constants.OPPONENT, 'aromatisse', 'yveltal')
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_infiltrator_goes_through_reflect(self):
        bot_move = "tackle"
        opponent_move = "splash"
        self.state.opponent.active.types = ['normal']
        self.state.opponent.side_conditions[constants.REFLECT] = 1
        self.state.self.active.ability = 'infiltrator'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 25),  # should be 12 with reflect up
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_secondary_poison_effect_with_shielddust(self):
        bot_move = "sludgebomb"
        opponent_move = "splash"
        self.state.opponent.active.types = ['normal']
        self.state.opponent.active.ability = 'shielddust'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 48),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_sleep_versus_sweetveil(self):
        bot_move = "spore"
        opponent_move = "splash"
        self.state.opponent.active.types = ['normal']
        self.state.opponent.active.ability = 'sweetveil'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_sleep_versus_vitalspirit(self):
        bot_move = "spore"
        opponent_move = "splash"
        self.state.opponent.active.types = ['normal']
        self.state.opponent.active.ability = 'vitalspirit'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_sandforce_with_steel_move_boosts_power(self):
        bot_move = "heavyslam"
        opponent_move = "splash"
        self.state.opponent.active.types = ['normal']
        self.state.self.active.ability = 'sandforce'
        self.state.weather = constants.SAND
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 33),
                    (constants.MUTATOR_DAMAGE, constants.SELF, 13),
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 18)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_sandforce_with_normal_move_has_no_boost(self):
        bot_move = "tackle"
        opponent_move = "splash"
        self.state.opponent.active.types = ['normal']
        self.state.self.active.ability = 'sandforce'
        self.state.weather = constants.SAND
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 25),
                    (constants.MUTATOR_DAMAGE, constants.SELF, 13),
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 18)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_sleep_versus_comatose(self):
        bot_move = "spore"
        opponent_move = "splash"
        self.state.opponent.active.types = ['normal']
        self.state.opponent.active.ability = 'comatose'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_quickfeet_boosts_speed(self):
        bot_move = "tackle"
        opponent_move = "tackle"
        self.state.opponent.active.types = ['normal']
        self.state.self.active.ability = 'quickfeet'
        self.state.self.active.status = constants.BURN
        self.state.self.active.speed = 100
        self.state.opponent.active.speed = 101
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 12),
                    (constants.MUTATOR_DAMAGE, constants.SELF, 52),
                    (constants.MUTATOR_DAMAGE, constants.SELF, 13),  # burn damage
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_triage_boosts_priority(self):
        bot_move = "drainingkiss"
        opponent_move = "tackle"
        self.state.opponent.active.types = ['normal']
        self.state.self.active.ability = 'triage'
        self.state.self.active.speed = 100
        self.state.opponent.active.speed = 101
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 27),
                    (constants.MUTATOR_HEAL, constants.SELF, 0),
                    (constants.MUTATOR_DAMAGE, constants.SELF, 52),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_draining_move_into_liquidooze(self):
        bot_move = "drainpunch"
        opponent_move = "splash"
        self.state.opponent.active.types = ['normal']
        self.state.opponent.active.ability = 'liquidooze'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 94),
                    (constants.MUTATOR_HEAL, constants.SELF, -47),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_innerfocus_prevents_flinching(self):
        bot_move = "ironhead"
        opponent_move = "splash"
        self.state.opponent.active.types = ['normal']
        self.state.opponent.active.ability = 'innerfocus'
        self.state.self.active.speed = 2
        self.state.opponent.active.speed = 1
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 49),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_defeatist_does_half_damage_at_less_than_half_health(self):
        bot_move = "tackle"
        opponent_move = "splash"
        self.state.opponent.active.types = ['normal']
        self.state.self.active.ability = 'defeatist'
        self.state.self.active.hp = 50
        self.state.self.active.maxhp = 100
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 13),  # does 25 normally
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_soundproof_immune_to_sound_move(self):
        bot_move = "boomburst"
        opponent_move = "splash"
        self.state.opponent.active.types = ['normal']
        self.state.opponent.active.ability = 'soundproof'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_soundproof_immune_to_partingshot(self):
        bot_move = "partingshot"
        opponent_move = "splash"
        self.state.opponent.active.types = ['normal']
        self.state.opponent.active.ability = 'soundproof'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_surgesurfer_boosts_speed(self):
        bot_move = "tackle"
        opponent_move = "tackle"
        self.state.opponent.active.types = ['normal']
        self.state.self.active.ability = 'surgesurfer'
        self.state.field = constants.ELECTRIC_TERRAIN
        self.state.self.active.speed = 100
        self.state.opponent.active.speed = 101
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 25),
                    (constants.MUTATOR_DAMAGE, constants.SELF, 52),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_weakarmor_activates_on_physical_move(self):
        bot_move = "tackle"
        opponent_move = "splash"
        self.state.opponent.active.types = ['normal']
        self.state.opponent.active.ability = 'weakarmor'
        self.state.field = constants.ELECTRIC_TERRAIN
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 25),
                    (constants.MUTATOR_BOOST, constants.OPPONENT, constants.DEFENSE, -1),
                    (constants.MUTATOR_BOOST, constants.OPPONENT, constants.SPEED, 2),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_weakarmor_does_not_activate_on_special_move(self):
        bot_move = "watergun"
        opponent_move = "splash"
        self.state.opponent.active.types = ['normal']
        self.state.opponent.active.ability = 'weakarmor'
        self.state.field = constants.ELECTRIC_TERRAIN
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 22),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_magmaarmor_prevents_frozen(self):
        bot_move = "icepunch"
        opponent_move = "splash"
        self.state.opponent.active.types = ['normal']
        self.state.opponent.active.ability = 'magmaarmor'
        self.state.field = constants.ELECTRIC_TERRAIN
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 47),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_quickfeet_boost_ignores_paralysis(self):
        bot_move = "tackle"
        opponent_move = "tackle"
        self.state.opponent.active.types = ['normal']
        self.state.self.active.ability = 'quickfeet'
        self.state.self.active.status = constants.PARALYZED
        self.state.self.active.speed = 100
        self.state.opponent.active.speed = 101
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                0.75,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 25),
                    (constants.MUTATOR_DAMAGE, constants.SELF, 52),
                ],
                False
            ),
            TransposeInstruction(
                0.25,
                [
                    (constants.MUTATOR_DAMAGE, constants.SELF, 52),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_secondary_poison_effect_with_immunity(self):
        bot_move = "sludgebomb"
        opponent_move = "splash"
        self.state.opponent.active.types = ['normal']
        self.state.opponent.active.ability = 'immunity'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 48),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_partingshot_into_defiant_boosts_attack_by_4(self):
        bot_move = "partingshot"
        opponent_move = "splash"
        self.state.opponent.active.types = ['normal']
        self.state.opponent.active.ability = 'defiant'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_BOOST, constants.OPPONENT, constants.ATTACK, 3),
                    (constants.MUTATOR_BOOST, constants.OPPONENT, constants.SPECIAL_ATTACK, -1),
                    (constants.MUTATOR_SWITCH, constants.SELF, 'raichu', 'xatu')
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_memento_into_defiant(self):
        bot_move = "memento"
        opponent_move = "splash"
        self.state.opponent.active.types = ['normal']
        self.state.opponent.active.ability = 'defiant'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_BOOST, constants.OPPONENT, constants.ATTACK, 2),
                    (constants.MUTATOR_BOOST, constants.OPPONENT, constants.SPECIAL_ATTACK, -2),
                    (constants.MUTATOR_HEAL, constants.SELF, -208)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_moonblast_secondary_into_defiant(self):
        bot_move = "moonblast"
        opponent_move = "splash"
        self.state.opponent.active.types = ['normal']
        self.state.opponent.active.ability = 'defiant'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                0.3,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 50),
                    (constants.MUTATOR_BOOST, constants.OPPONENT, constants.SPECIAL_ATTACK, -1),
                    (constants.MUTATOR_BOOST, constants.OPPONENT, constants.ATTACK, 2),
                ],
                False
            ),
            TransposeInstruction(
                0.7,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 50),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_switching_into_intimidate_into_defiant(self):
        bot_move = "switch xatu"
        opponent_move = "splash"
        self.state.opponent.active.types = ['normal']
        self.state.self.reserve['xatu'].ability = 'intimidate'
        self.state.opponent.active.ability = 'defiant'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_SWITCH, constants.SELF, 'raichu', 'xatu'),
                    (constants.MUTATOR_BOOST, constants.OPPONENT, constants.ATTACK, 1),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_thunderwave_into_limber(self):
        bot_move = "thunderwave"
        opponent_move = "splash"
        self.state.opponent.active.types = ['normal']
        self.state.opponent.active.ability = 'limber'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_thunderwave_into_ground_type(self):
        bot_move = "thunderwave"
        opponent_move = "splash"
        self.state.opponent.active.types = ['ground']
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_bodyslam_into_ground_type(self):
        bot_move = "bodyslam"
        opponent_move = "splash"
        self.state.opponent.active.types = ['ground']
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                0.3,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 53),
                    (constants.MUTATOR_APPLY_STATUS, constants.OPPONENT, constants.PARALYZED)
                ],
                False
            ),
            TransposeInstruction(
                0.7,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 53),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_protean_changes_types_before_doing_damage(self):
        bot_move = "surf"
        opponent_move = "splash"
        self.state.self.active.types = ['water', 'grass']
        self.state.self.active.ability = 'protean'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_CHANGE_TYPE, constants.SELF, ['water'], ['water', 'grass']),
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 72),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_protean_causes_attack_to_have_stab(self):
        bot_move = "surf"
        opponent_move = "splash"
        self.state.self.active.types = ['normal']
        self.state.self.active.ability = 'protean'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_CHANGE_TYPE, constants.SELF, ['water'], ['normal']),
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 72),  # non-STAB surf does 48 damage
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_no_type_change_instruction_if_there_are_no_types_to_change(self):
        bot_move = "surf"
        opponent_move = "splash"
        self.state.self.active.types = ['water']
        self.state.self.active.ability = 'protean'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 72),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_no_type_change_instruction_if_user_gets_flinched(self):
        bot_move = "surf"
        opponent_move = "ironhead"
        self.state.self.active.speed = 1
        self.state.opponent.active.speed = 2
        self.state.self.active.types = ['normal']
        self.state.self.active.ability = 'protean'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                0.3,
                [
                    (constants.MUTATOR_DAMAGE, constants.SELF, 68),
                    (constants.MUTATOR_APPLY_VOLATILE_STATUS, constants.SELF, constants.FLINCH),
                    (constants.MUTATOR_REMOVE_VOLATILE_STATUS, constants.SELF, constants.FLINCH),
                ],
                True
            ),
            TransposeInstruction(
                0.7,
                [
                    (constants.MUTATOR_DAMAGE, constants.SELF, 68),
                    (constants.MUTATOR_CHANGE_TYPE, constants.SELF, ['water'], ['normal']),
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 72),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_there_is_a_type_change_instruction_if_a_protean_user_misses_due_to_accuracy(self):
        bot_move = "hydropump"
        opponent_move = "splash"
        self.state.self.active.types = ['normal']
        self.state.self.active.ability = 'protean'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                0.8,
                [
                    (constants.MUTATOR_CHANGE_TYPE, constants.SELF, ['water'], ['normal']),
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 88),
                ],
                False
            ),
            TransposeInstruction(
                0.19999999999999996,
                [
                    (constants.MUTATOR_CHANGE_TYPE, constants.SELF, ['water'], ['normal']),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_non_damaging_move_causes_type_change_instruction(self):
        bot_move = "spikes"
        opponent_move = "splash"
        self.state.self.active.types = ['normal']
        self.state.self.active.ability = 'protean'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_CHANGE_TYPE, constants.SELF, ['ground'], ['normal']),
                    (constants.MUTATOR_SIDE_START, constants.OPPONENT, constants.SPIKES, 1)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_using_ground_move_with_libero_makes_pokemon_immune_to_electric_move(self):
        bot_move = "earthquake"
        opponent_move = "thunderwave"
        self.state.self.active.types = ['water', 'grass']
        self.state.self.active.ability = 'protean'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_CHANGE_TYPE, constants.SELF, ['ground'], ['water', 'grass']),
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 94),
                ],
                True
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_infestation_starts_volatile_status(self):
        bot_move = "infestation"
        opponent_move = "splash"
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 6),
                    (constants.MUTATOR_APPLY_VOLATILE_STATUS, constants.OPPONENT, constants.PARTIALLY_TRAPPED),
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 37)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_hustle(self):
        bot_move = "tackle"
        opponent_move = "splash"
        self.state.self.active.ability = 'hustle'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                0.8,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 37)
                ],
                False
            ),
            TransposeInstruction(
                0.19999999999999996,
                [],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_ironfist(self):
        bot_move = "machpunch"
        opponent_move = "splash"
        self.state.self.active.ability = 'ironfist'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 15)  # normal damage is 12
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_noguard(self):
        bot_move = "stoneedge"
        opponent_move = "splash"
        self.state.self.active.ability = 'noguard'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 62)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_refrigerate(self):
        bot_move = "tackle"
        opponent_move = "splash"
        self.state.self.active.ability = 'refrigerate'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 30)  # normal damage is 25
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_scrappy_hits_ghost(self):
        bot_move = "tackle"
        opponent_move = "splash"
        self.state.self.active.ability = 'scrappy'
        self.state.opponent.active.types = ['ghost']
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 25)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_strongjaw(self):
        bot_move = "bite"
        opponent_move = "splash"
        self.state.self.active.ability = 'strongjaw'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                0.3,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 28),  # normal damage is 18
                    (constants.MUTATOR_APPLY_VOLATILE_STATUS, constants.OPPONENT, constants.FLINCH),
                    (constants.MUTATOR_REMOVE_VOLATILE_STATUS, constants.OPPONENT, constants.FLINCH)

                ],
                True
            ),
            TransposeInstruction(
                0.7,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 28)  # normal damage is 18
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_technician(self):
        bot_move = "bulletpunch"
        opponent_move = "splash"
        self.state.self.active.ability = 'technician'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 75),  # normal damage is 51

                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_toughclaws(self):
        bot_move = "tackle"
        opponent_move = "splash"
        self.state.self.active.ability = 'toughclaws'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 33),  # normal damage is 25

                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_gorillatactics_boost_damage(self):
        bot_move = "tackle"
        opponent_move = "splash"
        self.state.self.active.ability = 'gorillatactics'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 37),  # normal damage is 25

                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_hugepower(self):
        bot_move = "tackle"
        opponent_move = "splash"
        self.state.self.active.ability = 'hugepower'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 49),  # normal damage is 25

                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_reckless(self):
        bot_move = "doubleedge"
        opponent_move = "splash"
        self.state.self.active.ability = 'reckless'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 89),  # normal damage is 74
                    (constants.MUTATOR_DAMAGE, constants.SELF, 29)

                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_parentalbond(self):
        bot_move = "tackle"
        opponent_move = "splash"
        self.state.self.active.ability = 'parentalbond'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 32),  # normal damage is 25

                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_sapsipper_with_leechseed(self):
        bot_move = "leechseed"
        opponent_move = "splash"
        self.state.opponent.active.ability = 'sapsipper'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_BOOST, constants.OPPONENT, constants.ATTACK, 1)

                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_sapsipper_with_leafblade(self):
        bot_move = "leafblade"
        opponent_move = "splash"
        self.state.opponent.active.ability = 'sapsipper'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_BOOST, constants.OPPONENT, constants.ATTACK, 1)

                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_thickfat(self):
        bot_move = "fusionflare"
        opponent_move = "splash"
        self.state.opponent.active.ability = 'thickfat'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 27)  # normal damage is 53

                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_contact_with_fluffy(self):
        bot_move = "tackle"
        opponent_move = "splash"
        self.state.opponent.active.ability = 'fluffy'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 13)  # normal damage is 25

                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_furcoat(self):
        bot_move = "tackle"
        opponent_move = "splash"
        self.state.opponent.active.ability = 'furcoat'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 13)  # normal damage is 25

                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_motordrive(self):
        bot_move = "hiddenpowerelectric60"
        opponent_move = "splash"
        self.state.opponent.active.ability = 'motordrive'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_BOOST, constants.OPPONENT, constants.SPEED, 1)

                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_voltabsorb(self):
        bot_move = "hiddenpowerelectric60"
        opponent_move = "splash"
        self.state.opponent.active.ability = 'voltabsorb'
        self.state.opponent.active.hp = 95
        self.state.opponent.active.maxhp = 100
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_HEAL, constants.OPPONENT, 5)

                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_stormdrain(self):
        bot_move = "watergun"
        opponent_move = "splash"
        self.state.opponent.active.ability = 'stormdrain'
        self.state.opponent.active.hp = 95
        self.state.opponent.active.maxhp = 100
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_BOOST, constants.OPPONENT, constants.SPECIAL_ATTACK, 1)

                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_fire_with_fluffy(self):
        bot_move = "fusionflare"
        opponent_move = "splash"
        self.state.opponent.active.ability = 'fluffy'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 105)  # normal damage is 53

                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_shieldsdown_with_25_percent_can_be_burned(self):
        bot_move = "willowisp"
        opponent_move = "splash"
        self.state.opponent.active.types = ['normal']
        self.state.opponent.active.ability = 'shieldsdown'
        self.state.opponent.active.hp = 100
        self.state.opponent.active.maxhp = 400
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                0.85,
                [
                    (constants.MUTATOR_APPLY_STATUS, constants.OPPONENT, constants.BURN),
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 25),
                ],
                False
            ),
            TransposeInstruction(
                0.15000000000000002,
                [],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_shieldsdown_with_75_percent_cannot_be_burned(self):
        bot_move = "willowisp"
        opponent_move = "splash"
        self.state.opponent.active.types = ['normal']
        self.state.opponent.active.ability = 'shieldsdown'
        self.state.opponent.active.hp = 3
        self.state.opponent.active.maxhp = 4
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1.0,
                [],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_blaze_boosts_damage_below_one_third(self):
        bot_move = "ember"
        opponent_move = "splash"
        self.state.opponent.active.types = ['normal']
        self.state.self.active.ability = 'blaze'
        self.state.self.active.hp = 1
        self.state.self.active.maxhp = 4
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                0.1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 32),
                    (constants.MUTATOR_APPLY_STATUS, constants.OPPONENT, constants.BURN),
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 18),
                ],
                False
            ),
            TransposeInstruction(
                0.9,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 32),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_torrent_boosts_damage_below_one_third(self):
        bot_move = "watergun"
        opponent_move = "splash"
        self.state.opponent.active.types = ['normal']
        self.state.self.active.ability = 'torrent'
        self.state.self.active.hp = 1
        self.state.self.active.maxhp = 4
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 32),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_using_move_with_choice_item_locks_other_moves(self):
        bot_move = "tackle"
        opponent_move = "splash"
        self.state.self.active.moves = [
            {constants.ID: 'tackle', constants.DISABLED: False},
            {constants.ID: 'thunderwave', constants.DISABLED: False},
            {constants.ID: 'coil', constants.DISABLED: False},
            {constants.ID: 'sandattack', constants.DISABLED: False}
        ]
        self.state.self.active.item = 'choicescarf'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 25),
                    (constants.MUTATOR_DISABLE_MOVE, constants.SELF, 'thunderwave'),
                    (constants.MUTATOR_DISABLE_MOVE, constants.SELF, 'coil'),
                    (constants.MUTATOR_DISABLE_MOVE, constants.SELF, 'sandattack'),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_gorilla_tactics_locks_other_moves_even_without_choice_item(self):
        bot_move = "tackle"
        opponent_move = "splash"
        self.state.self.active.moves = [
            {constants.ID: 'tackle', constants.DISABLED: False},
            {constants.ID: 'thunderwave', constants.DISABLED: False},
            {constants.ID: 'coil', constants.DISABLED: False},
            {constants.ID: 'sandattack', constants.DISABLED: False}
        ]
        self.state.self.active.item = None
        self.state.self.active.ability = 'gorillatactics'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 37),
                    (constants.MUTATOR_DISABLE_MOVE, constants.SELF, 'thunderwave'),
                    (constants.MUTATOR_DISABLE_MOVE, constants.SELF, 'coil'),
                    (constants.MUTATOR_DISABLE_MOVE, constants.SELF, 'sandattack'),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_gorilla_tactics_with_choice_item_locks_moves(self):
        bot_move = "tackle"
        opponent_move = "splash"
        self.state.self.active.moves = [
            {constants.ID: 'tackle', constants.DISABLED: False},
            {constants.ID: 'thunderwave', constants.DISABLED: False},
            {constants.ID: 'coil', constants.DISABLED: False},
            {constants.ID: 'sandattack', constants.DISABLED: False}
        ]
        self.state.self.active.item = 'choicescarf'
        self.state.self.active.ability = 'gorillatactics'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 37),
                    (constants.MUTATOR_DISABLE_MOVE, constants.SELF, 'thunderwave'),
                    (constants.MUTATOR_DISABLE_MOVE, constants.SELF, 'coil'),
                    (constants.MUTATOR_DISABLE_MOVE, constants.SELF, 'sandattack'),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_opponent_using_move_with_choice_item_locks_other_moves(self):
        bot_move = "splash"
        opponent_move = "tackle"
        self.state.opponent.active.moves = [
            {constants.ID: 'tackle', constants.DISABLED: False},
            {constants.ID: 'thunderwave', constants.DISABLED: False},
            {constants.ID: 'coil', constants.DISABLED: False},
            {constants.ID: 'sandattack', constants.DISABLED: False}
        ]
        self.state.opponent.active.item = 'choicescarf'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.SELF, 35),
                    (constants.MUTATOR_DISABLE_MOVE, constants.OPPONENT, 'thunderwave'),
                    (constants.MUTATOR_DISABLE_MOVE, constants.OPPONENT, 'coil'),
                    (constants.MUTATOR_DISABLE_MOVE, constants.OPPONENT, 'sandattack'),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_opponent_using_move_with_choice_item_locks_non_disabled_moves(self):
        bot_move = "splash"
        opponent_move = "tackle"
        self.state.opponent.active.moves = [
            {constants.ID: 'tackle', constants.DISABLED: False},
            {constants.ID: 'thunderwave', constants.DISABLED: True},  # disabled already
            {constants.ID: 'coil', constants.DISABLED: False},
            {constants.ID: 'sandattack', constants.DISABLED: True}  # disabled already
        ]
        self.state.opponent.active.item = 'choicescarf'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.SELF, 35),
                    (constants.MUTATOR_DISABLE_MOVE, constants.OPPONENT, 'coil'),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_already_disabled_moves_are_not_disabled(self):
        bot_move = "tackle"
        opponent_move = "splash"
        self.state.self.active.moves = [
            {constants.ID: 'tackle', constants.DISABLED: False},
            {constants.ID: 'thunderwave', constants.DISABLED: True},
            {constants.ID: 'coil', constants.DISABLED: True},
            {constants.ID: 'sandattack', constants.DISABLED: False}
        ]
        self.state.self.active.item = 'choicescarf'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 25),
                    (constants.MUTATOR_DISABLE_MOVE, constants.SELF, 'sandattack'),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_using_outrage_locks_other_moves(self):
        bot_move = "outrage"
        opponent_move = "splash"
        self.state.self.active.moves = [
            {constants.ID: 'outrage', constants.DISABLED: False},
            {constants.ID: 'thunderwave', constants.DISABLED: False},
            {constants.ID: 'coil', constants.DISABLED: False},
            {constants.ID: 'sandattack', constants.DISABLED: False}
        ]
        self.state.self.active.item = 'choicescarf'
        self.state.opponent.active.types = ['normal']
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 74),
                    (constants.MUTATOR_DISABLE_MOVE, constants.SELF, 'thunderwave'),
                    (constants.MUTATOR_DISABLE_MOVE, constants.SELF, 'coil'),
                    (constants.MUTATOR_DISABLE_MOVE, constants.SELF, 'sandattack'),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_switch_move_with_choice_item(self):
        bot_move = "switch xatu"
        opponent_move = "splash"
        self.state.self.active.moves = [
            {constants.ID: 'outrage', constants.DISABLED: False},
            {constants.ID: 'thunderwave', constants.DISABLED: False},
            {constants.ID: 'coil', constants.DISABLED: False},
            {constants.ID: 'sandattack', constants.DISABLED: False}
        ]
        self.state.self.active.item = 'choicescarf'
        self.state.opponent.active.types = ['normal']
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_SWITCH, constants.SELF, 'raichu', 'xatu')
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_switching_out_unlocks_locked_moves(self):
        bot_move = "switch xatu"
        opponent_move = "splash"
        self.state.self.active.moves = [
            {constants.ID: 'tackle', constants.DISABLED: False, constants.CURRENT_PP: 10},
            {constants.ID: 'thunderwave', constants.DISABLED: True, constants.CURRENT_PP: 10},
            {constants.ID: 'coil', constants.DISABLED: True, constants.CURRENT_PP: 10},
            {constants.ID: 'sandattack', constants.DISABLED: True, constants.CURRENT_PP: 10}
        ]
        self.state.self.active.item = 'choicescarf'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_ENABLE_MOVE, constants.SELF, 'thunderwave'),
                    (constants.MUTATOR_ENABLE_MOVE, constants.SELF, 'coil'),
                    (constants.MUTATOR_ENABLE_MOVE, constants.SELF, 'sandattack'),
                    (constants.MUTATOR_SWITCH, constants.SELF, 'raichu', 'xatu'),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_tanglinghair_drops_speed(self):
        bot_move = "tackle"
        opponent_move = "splash"
        self.state.opponent.active.types = ['normal']
        self.state.opponent.active.ability = 'tanglinghair'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 25),
                    (constants.MUTATOR_BOOST, constants.SELF, constants.SPEED, -1),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_cottondown_drops_speed(self):
        bot_move = "tackle"
        opponent_move = "splash"
        self.state.opponent.active.types = ['normal']
        self.state.opponent.active.ability = 'cottondown'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 25),
                    (constants.MUTATOR_BOOST, constants.SELF, constants.SPEED, -1),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_cottondown_drops_speed_for_non_contact_move(self):
        bot_move = "surf"
        opponent_move = "splash"
        self.state.opponent.active.types = ['normal']
        self.state.opponent.active.ability = 'cottondown'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 48),
                    (constants.MUTATOR_BOOST, constants.SELF, constants.SPEED, -1),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_vcreate_into_tanglinghair_drops_stats_correctly(self):
        bot_move = "vcreate"
        opponent_move = "splash"
        self.state.opponent.active.types = ['normal']
        self.state.opponent.active.ability = 'tanglinghair'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                0.95,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 111),
                    (constants.MUTATOR_BOOST, constants.SELF, constants.SPEED, -2),
                    (constants.MUTATOR_BOOST, constants.SELF, constants.DEFENSE, -1),
                    (constants.MUTATOR_BOOST, constants.SELF, constants.SPECIAL_DEFENSE, -1),
                ],
                False
            ),
            TransposeInstruction(
                0.050000000000000044,
                [],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_switch_into_grassysurge_starts_terrain(self):
        bot_move = "switch tapulele"
        opponent_move = "splash"
        self.state.self.reserve['tapulele'] = Pokemon.from_state_pokemon_dict(StatePokemon("tapulele", 81).to_dict())
        self.state.self.reserve['tapulele'].ability = 'grassysurge'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_SWITCH, 'self', self.state.self.active.id, 'tapulele'),
                    (constants.MUTATOR_FIELD_START, constants.GRASSY_TERRAIN, None)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_switch_into_mistysurge_starts_terrain(self):
        bot_move = "switch tapulele"
        opponent_move = "splash"
        self.state.self.reserve['tapulele'] = Pokemon.from_state_pokemon_dict(StatePokemon("tapulele", 81).to_dict())
        self.state.self.reserve['tapulele'].ability = 'mistysurge'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_SWITCH, 'self', self.state.self.active.id, 'tapulele'),
                    (constants.MUTATOR_FIELD_START, constants.MISTY_TERRAIN, None)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_switch_into_politoed_does_not_start_rain_weather_when_desolate_land_is_active(self):
        bot_move = "switch politoed"
        opponent_move = "splash"
        self.state.weather = constants.DESOLATE_LAND
        self.state.self.reserve['politoed'] = Pokemon.from_state_pokemon_dict(StatePokemon("politoed", 81).to_dict())
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_SWITCH, 'self', self.state.self.active.id, 'politoed'),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_switch_into_politoed_does_not_start_rain_weather_when_rain_is_already_active(self):
        bot_move = "switch politoed"
        opponent_move = "splash"
        self.state.weather = constants.DESOLATE_LAND
        self.state.self.reserve['politoed'] = Pokemon.from_state_pokemon_dict(StatePokemon("politoed", 81).to_dict())
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_SWITCH, 'self', self.state.self.active.id, 'politoed'),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_switch_in_with_dauntless_shield_causes_defense_to_raise(self):
        bot_move = "switch xatu"
        opponent_move = "splash"
        self.state.self.reserve['xatu'].ability = 'dauntlessshield'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_SWITCH, 'self', self.state.self.active.id, 'xatu'),
                    (constants.MUTATOR_BOOST, constants.SELF, constants.DEFENSE, 1)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_switch_in_with_intrepid_sword_causes_attack_to_raise(self):
        bot_move = "switch xatu"
        opponent_move = "splash"
        self.state.self.reserve['xatu'].ability = 'intrepidsword'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_SWITCH, 'self', self.state.self.active.id, 'xatu'),
                    (constants.MUTATOR_BOOST, constants.SELF, constants.ATTACK, 1)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_switch_into_intimidate_causes_opponent_attack_to_lower(self):
        bot_move = "switch xatu"
        opponent_move = "splash"
        self.state.self.reserve['xatu'].ability = 'intimidate'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_SWITCH, 'self', self.state.self.active.id, 'xatu'),
                    (constants.MUTATOR_UNBOOST, constants.OPPONENT, constants.ATTACK, 1)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_innerfocus_immune_to_intimidate(self):
        bot_move = "switch xatu"
        opponent_move = "splash"
        self.state.self.reserve['xatu'].ability = 'intimidate'
        self.state.opponent.active.ability = 'innerfocus'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_SWITCH, 'self', self.state.self.active.id, 'xatu'),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_dousedrive_makes_waterabsorb_activate(self):
        bot_move = "technoblast"
        opponent_move = "splash"
        self.state.self.active.item = 'dousedrive'
        self.state.opponent.active.ability = 'waterabsorb'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_airballoon_makes_immune(self):
        bot_move = "tackle"
        opponent_move = "earthquake"
        self.state.self.active.item = 'airballoon'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    ('damage', 'opponent', 25)
                ],
                True
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_weaknesspolicy_activates_on_super_effective_damage(self):
        bot_move = "machpunch"
        opponent_move = "splash"
        self.state.opponent.active.item = 'weaknesspolicy'
        self.state.opponent.active.types = ['normal']
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 51),
                    (constants.MUTATOR_BOOST, constants.OPPONENT, constants.ATTACK, 2),
                    (constants.MUTATOR_BOOST, constants.OPPONENT, constants.SPECIAL_ATTACK, 2),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_weaknesspolicy_does_not_activate_on_standard_damage(self):
        bot_move = "tackle"
        opponent_move = "splash"
        self.state.opponent.active.item = 'weaknesspolicy'
        self.state.opponent.active.types = ['normal']
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 25)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_weaknesspolicy_does_not_activate_on_resisted_damage(self):
        bot_move = "tackle"
        opponent_move = "splash"
        self.state.opponent.active.item = 'weaknesspolicy'
        self.state.opponent.active.types = ['rock']
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 12)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_weaknesspolicy_does_not_activate_on_status_move(self):
        bot_move = "willowisp"
        opponent_move = "splash"
        self.state.opponent.active.item = 'weaknesspolicy'
        self.state.opponent.active.types = ['grass']
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                0.85,
                [
                    (constants.MUTATOR_APPLY_STATUS, constants.OPPONENT, constants.BURN),
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 18)
                ],
                False
            ),
            TransposeInstruction(
                0.15000000000000002,
                [],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_memories_change_multiattack_type(self):
        bot_move = "multiattack"
        opponent_move = "splash"
        self.state.self.active.item = 'bugmemory'
        self.state.opponent.active.types = ['grass']
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1.0,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 149)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_memories_change_multiattack_type_to_not_very_effective(self):
        bot_move = "multiattack"
        opponent_move = "splash"
        self.state.self.active.item = 'watermemory'
        self.state.opponent.active.types = ['grass']
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1.0,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 37)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_inflicting_with_leechseed_produces_sap_instruction(self):
        bot_move = "leechseed"
        opponent_move = "splash"
        self.state.opponent.active.maxhp = 100
        self.state.self.active.maxhp = 100
        self.state.self.active.hp = 50
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_APPLY_VOLATILE_STATUS, constants.OPPONENT, constants.LEECH_SEED),
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 12),
                    (constants.MUTATOR_HEAL, constants.SELF, 12)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_leechseed_sap_does_not_overheal(self):
        bot_move = "leechseed"
        opponent_move = "splash"
        self.state.opponent.active.maxhp = 100
        self.state.self.active.maxhp = 100
        self.state.self.active.hp = 95
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_APPLY_VOLATILE_STATUS, constants.OPPONENT, constants.LEECH_SEED),
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 12),
                    (constants.MUTATOR_HEAL, constants.SELF, 5)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_leechseed_sap_into_removing_protect_side_condition(self):
        bot_move = "leechseed"
        opponent_move = "splash"
        self.state.opponent.active.maxhp = 100
        self.state.self.active.maxhp = 100
        self.state.self.active.hp = 50
        self.state.opponent.side_conditions[constants.PROTECT] = 1
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_APPLY_VOLATILE_STATUS, constants.OPPONENT, constants.LEECH_SEED),
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 12),
                    (constants.MUTATOR_HEAL, constants.SELF, 12),
                    (constants.MUTATOR_SIDE_END, constants.OPPONENT, constants.PROTECT, 1)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_using_roost_with_choice_item(self):
        bot_move = "roost"
        opponent_move = "tackle"
        self.state.self.active.moves = [
            {constants.ID: "tackle", constants.DISABLED: False, constants.CURRENT_PP: 10},
            {constants.ID: "stringshot", constants.DISABLED: False, constants.CURRENT_PP: 10},
            {constants.ID: "roost", constants.DISABLED: False, constants.CURRENT_PP: 10},
        ]
        self.state.self.active.item = 'choicescarf'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_APPLY_VOLATILE_STATUS, constants.SELF, 'roost'),
                    (constants.MUTATOR_DAMAGE, constants.SELF, 35),
                    (constants.MUTATOR_REMOVE_VOLATILE_STATUS, constants.SELF, 'roost'),
                    (constants.MUTATOR_DISABLE_MOVE, constants.SELF, 'tackle'),
                    (constants.MUTATOR_DISABLE_MOVE, constants.SELF, 'stringshot'),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_using_sunnyday_sets_the_weather(self):
        bot_move = "sunnyday"
        opponent_move = "splash"
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_WEATHER_START, constants.SUN, self.state.weather)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_using_trick_swaps_items_with_opponent(self):
        self.state.self.active.item = 'leftovers'
        self.state.opponent.active.item = 'lifeorb'
        bot_move = "trick"
        opponent_move = "splash"
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_CHANGE_ITEM, constants.SELF, 'lifeorb', 'leftovers'),
                    (constants.MUTATOR_CHANGE_ITEM, constants.OPPONENT, 'leftovers', 'lifeorb'),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_trick_fails_against_z_crystal(self):
        self.state.self.active.item = 'leftovers'
        self.state.opponent.active.item = 'iciumz'
        bot_move = "trick"
        opponent_move = "splash"
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_trick_fails_against_silvally_with_memory(self):
        self.state.self.active.item = 'leftovers'
        self.state.opponent.active.item = 'steelmemory'
        self.state.opponent.active.id = 'silvallysteel'
        bot_move = "trick"
        opponent_move = "splash"
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_trick_fails_on_opponent_with_substitute(self):
        self.state.self.active.item = 'leftovers'
        self.state.opponent.active.item = 'lifeorb'
        self.state.opponent.active.volatile_status.add(constants.SUBSTITUTE)
        bot_move = "trick"
        opponent_move = "splash"
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_trick_succeeds_when_user_is_behind_substitute(self):
        self.state.self.active.item = 'leftovers'
        self.state.opponent.active.item = 'lifeorb'
        self.state.self.active.volatile_status.add(constants.SUBSTITUTE)
        bot_move = "trick"
        opponent_move = "splash"
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_CHANGE_ITEM, constants.SELF, 'lifeorb', 'leftovers'),
                    (constants.MUTATOR_CHANGE_ITEM, constants.OPPONENT, 'leftovers', 'lifeorb'),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_trick_switches_no_item(self):
        self.state.self.active.item = None
        self.state.opponent.active.item = 'lifeorb'
        bot_move = "trick"
        opponent_move = "splash"
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_CHANGE_ITEM, constants.SELF, 'lifeorb', None),
                    (constants.MUTATOR_CHANGE_ITEM, constants.OPPONENT, None, 'lifeorb'),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_double_no_item_produces_no_instructions(self):
        self.state.self.active.item = None
        self.state.opponent.active.item = None
        bot_move = "trick"
        opponent_move = "splash"
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_opponent_move_locks_when_choicescarf_is_tricked(self):
        self.state.self.active.item = 'choicescarf'
        self.state.opponent.active.item = 'lifeorb'
        bot_move = "trick"
        opponent_move = "tackle"
        self.state.opponent.active.moves = [
            {constants.ID: 'tackle', constants.DISABLED: False},
            {constants.ID: 'thunderwave', constants.DISABLED: False},
            {constants.ID: 'coil', constants.DISABLED: False},
            {constants.ID: 'sandattack', constants.DISABLED: False}
        ]
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_CHANGE_ITEM, constants.SELF, 'lifeorb', 'choicescarf'),
                    (constants.MUTATOR_CHANGE_ITEM, constants.OPPONENT, 'choicescarf', 'lifeorb'),
                    (constants.MUTATOR_DAMAGE, constants.SELF, 35),
                    (constants.MUTATOR_DISABLE_MOVE, constants.OPPONENT, 'thunderwave'),
                    (constants.MUTATOR_DISABLE_MOVE, constants.OPPONENT, 'coil'),
                    (constants.MUTATOR_DISABLE_MOVE, constants.OPPONENT, 'sandattack'),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_switcheroo_behaves_the_same_as_trick(self):
        self.state.self.active.item = 'choicescarf'
        self.state.opponent.active.item = 'lifeorb'
        bot_move = "switcheroo"
        opponent_move = "tackle"
        self.state.opponent.active.moves = [
            {constants.ID: 'tackle', constants.DISABLED: False},
            {constants.ID: 'thunderwave', constants.DISABLED: False},
            {constants.ID: 'coil', constants.DISABLED: False},
            {constants.ID: 'sandattack', constants.DISABLED: False}
        ]
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_CHANGE_ITEM, constants.SELF, 'lifeorb', 'choicescarf'),
                    (constants.MUTATOR_CHANGE_ITEM, constants.OPPONENT, 'choicescarf', 'lifeorb'),
                    (constants.MUTATOR_DAMAGE, constants.SELF, 35),
                    (constants.MUTATOR_DISABLE_MOVE, constants.OPPONENT, 'thunderwave'),
                    (constants.MUTATOR_DISABLE_MOVE, constants.OPPONENT, 'coil'),
                    (constants.MUTATOR_DISABLE_MOVE, constants.OPPONENT, 'sandattack'),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_bot_moves_are_not_locked_when_a_choice_item_is_tricked(self):
        self.state.self.active.item = 'choicescarf'
        self.state.opponent.active.item = 'lifeorb'
        bot_move = "trick"
        opponent_move = "splash"
        self.state.self.active.moves = [
            {constants.ID: 'trick', constants.DISABLED: False},
            {constants.ID: 'thunderwave', constants.DISABLED: False},
            {constants.ID: 'coil', constants.DISABLED: False},
            {constants.ID: 'sandattack', constants.DISABLED: False}
        ]
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_CHANGE_ITEM, constants.SELF, 'lifeorb', 'choicescarf'),
                    (constants.MUTATOR_CHANGE_ITEM, constants.OPPONENT, 'choicescarf', 'lifeorb'),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_using_sunnyday_changes_the_weather_from_rain(self):
        bot_move = "sunnyday"
        opponent_move = "splash"
        self.state.weather = constants.RAIN
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_WEATHER_START, constants.SUN, self.state.weather)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_using_raindance_sets_the_weather(self):
        bot_move = "raindance"
        opponent_move = "splash"
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_WEATHER_START, constants.RAIN, self.state.weather)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_using_raindance_sets_the_weather_correctly_as_a_second_move(self):
        bot_move = "raindance"
        opponent_move = "bulletpunch"
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.SELF, 17),
                    (constants.MUTATOR_WEATHER_START, constants.RAIN, self.state.weather)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_fainted_pkmn_doesnt_move(self):
        bot_move = "raindance"
        opponent_move = "bulletpunch"
        self.state.self.active.hp = 1
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.SELF, 1),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_has_no_effect_when_weather_is_already_active(self):
        bot_move = "raindance"
        opponent_move = "splash"
        self.state.weather = constants.RAIN
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_paralyzed_pokemon_reacts_properly_to_weather(self):
        bot_move = "raindance"
        opponent_move = "splash"
        self.state.self.active.status = constants.PARALYZED
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                0.75,
                [
                    (constants.MUTATOR_WEATHER_START, constants.RAIN, None)
                ],
                False
            ),
            TransposeInstruction(
                0.25,
                [],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_using_trickroom_sets_trickroom(self):
        bot_move = "trickroom"
        opponent_move = "splash"
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_TOGGLE_TRICKROOM,)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_does_not_work_through_flinched(self):
        bot_move = "raindance"
        opponent_move = "ironhead"
        self.state.self.active.speed = 1
        self.state.opponent.active.speed = 2
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                0.3,
                [
                    (constants.MUTATOR_DAMAGE, constants.SELF, 34),
                    (constants.MUTATOR_APPLY_VOLATILE_STATUS, constants.SELF, constants.FLINCH),
                    (constants.MUTATOR_REMOVE_VOLATILE_STATUS, constants.SELF, constants.FLINCH),
                ],
                True
            ),
            TransposeInstruction(
                0.7,
                [
                    (constants.MUTATOR_DAMAGE, constants.SELF, 34),
                    (constants.MUTATOR_WEATHER_START, constants.RAIN, self.state.weather)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_faster_pkmn_does_not_flinch(self):
        bot_move = "raindance"
        opponent_move = "ironhead"
        self.state.self.active.speed = 2
        self.state.opponent.active.speed = 1
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [

                    (constants.MUTATOR_WEATHER_START, constants.RAIN, self.state.weather),
                    (constants.MUTATOR_DAMAGE, constants.SELF, 34),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_double_weather_move_sets_weathers_properly(self):
        bot_move = "raindance"
        opponent_move = "sandstorm"
        self.state.self.active.speed = 1
        self.state.opponent.active.speed = 2
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_WEATHER_START, constants.SAND, None),
                    (constants.MUTATOR_WEATHER_START, constants.RAIN, constants.SAND)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_using_sandstorm_sets_the_weather(self):
        bot_move = "sandstorm"
        opponent_move = "splash"
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_WEATHER_START, constants.SAND, self.state.weather),
                    (constants.MUTATOR_DAMAGE, constants.SELF, 13),
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 18),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_sand_causes_correct_damage_to_kill(self):
        bot_move = "splash"
        opponent_move = "splash"
        self.state.weather = constants.SAND
        self.state.self.active.hp = 1
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.SELF, 1),
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 18),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_hail_causes_correct_damage_to_kill(self):
        bot_move = "splash"
        opponent_move = "splash"
        self.state.weather = constants.HAIL
        self.state.self.active.hp = 1
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.SELF, 1),
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 18),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_using_hail_sets_the_weather(self):
        bot_move = "hail"
        opponent_move = "splash"
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_WEATHER_START, constants.HAIL, self.state.weather),
                    (constants.MUTATOR_DAMAGE, constants.SELF, 13),
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 18),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_using_sunnyday_in_heavyrain_does_not_change_weather(self):
        bot_move = "sunnyday"
        opponent_move = "splash"
        self.state.weather = constants.HEAVY_RAIN
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_using_sunnyday_into_solarbeam_causes_solarbeam_to_not_charge(self):
        bot_move = "sunnyday"
        opponent_move = "solarbeam"
        self.state.self.active.speed = 2
        self.state.opponent.active.speed = 1
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_WEATHER_START, constants.SUN, self.state.weather),
                    (constants.MUTATOR_DAMAGE, constants.SELF, 99)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_using_protect_adds_volatile_status_and_side_condition(self):
        bot_move = "protect"
        opponent_move = "splash"
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_APPLY_VOLATILE_STATUS, constants.SELF, constants.PROTECT),
                    (constants.MUTATOR_REMOVE_VOLATILE_STATUS, constants.SELF, constants.PROTECT),
                    (constants.MUTATOR_SIDE_START, constants.SELF, constants.PROTECT, 1)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_rocky_helmet_and_rough_skin_do_not_activate_on_protect(self):
        bot_move = "protect"
        opponent_move = "tackle"
        self.state.self.active.ability = "roughskin"
        self.state.self.active.item = "rockyhelmet"
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_APPLY_VOLATILE_STATUS, constants.SELF, constants.PROTECT),
                    (constants.MUTATOR_REMOVE_VOLATILE_STATUS, constants.SELF, constants.PROTECT),
                    (constants.MUTATOR_SIDE_START, constants.SELF, constants.PROTECT, 1)
                ],
                True
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_baneful_bunker_has_the_same_effect_as_protect(self):
        bot_move = "banefulbunker"
        opponent_move = "willowisp"
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_APPLY_VOLATILE_STATUS, constants.SELF, constants.BANEFUL_BUNKER),
                    (constants.MUTATOR_REMOVE_VOLATILE_STATUS, constants.SELF, constants.BANEFUL_BUNKER),
                    (constants.MUTATOR_SIDE_START, constants.SELF, constants.PROTECT, 1)
                ],
                True
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_spiky_shield_has_the_same_effect_as_protect(self):
        bot_move = "spikyshield"
        opponent_move = "willowisp"
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_APPLY_VOLATILE_STATUS, constants.SELF, constants.SPIKY_SHIELD),
                    (constants.MUTATOR_REMOVE_VOLATILE_STATUS, constants.SELF, constants.SPIKY_SHIELD),
                    (constants.MUTATOR_SIDE_START, constants.SELF, constants.PROTECT, 1)
                ],
                True
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_spiky_shield_into_non_contact_move(self):
        bot_move = "spikyshield"
        opponent_move = "earthquake"
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_APPLY_VOLATILE_STATUS, constants.SELF, constants.SPIKY_SHIELD),
                    (constants.MUTATOR_REMOVE_VOLATILE_STATUS, constants.SELF, constants.SPIKY_SHIELD),
                    (constants.MUTATOR_SIDE_START, constants.SELF, constants.PROTECT, 1)
                ],
                True
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_spiky_shield_into_contact_move(self):
        bot_move = "spikyshield"
        opponent_move = "tackle"
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_APPLY_VOLATILE_STATUS, constants.SELF, constants.SPIKY_SHIELD),
                    (constants.MUTATOR_HEAL, constants.OPPONENT, -37),
                    (constants.MUTATOR_REMOVE_VOLATILE_STATUS, constants.SELF, constants.SPIKY_SHIELD),
                    (constants.MUTATOR_SIDE_START, constants.SELF, constants.PROTECT, 1)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_spiky_shield_does_not_work_when_user_has_protect_side_condition(self):
        bot_move = "spikyshield"
        opponent_move = "tackle"
        self.state.self.side_conditions[constants.PROTECT] = 1
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.SELF, 35),
                    (constants.MUTATOR_SIDE_END, constants.SELF, constants.PROTECT, 1)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_spiky_shield_into_crash_attack(self):
        bot_move = "spikyshield"
        opponent_move = "highjumpkick"
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_APPLY_VOLATILE_STATUS, constants.SELF, constants.SPIKY_SHIELD),
                    (constants.MUTATOR_HEAL, constants.OPPONENT, -185),
                    (constants.MUTATOR_REMOVE_VOLATILE_STATUS, constants.SELF, constants.SPIKY_SHIELD),
                    (constants.MUTATOR_SIDE_START, constants.SELF, constants.PROTECT, 1)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_non_contact_move_with_banefulbunker(self):
        bot_move = "banefulbunker"
        opponent_move = "earthquake"
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_APPLY_VOLATILE_STATUS, constants.SELF, constants.BANEFUL_BUNKER),
                    (constants.MUTATOR_REMOVE_VOLATILE_STATUS, constants.SELF, constants.BANEFUL_BUNKER),
                    (constants.MUTATOR_SIDE_START, constants.SELF, constants.PROTECT, 1)
                ],
                True
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_crash_move_with_banefulbunker(self):
        bot_move = "banefulbunker"
        opponent_move = "highjumpkick"
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_APPLY_VOLATILE_STATUS, constants.SELF, constants.BANEFUL_BUNKER),
                    (constants.MUTATOR_APPLY_STATUS, constants.OPPONENT, constants.POISON),
                    (constants.MUTATOR_HEAL, constants.OPPONENT, -148),
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 37),
                    (constants.MUTATOR_REMOVE_VOLATILE_STATUS, constants.SELF, constants.BANEFUL_BUNKER),
                    (constants.MUTATOR_SIDE_START, constants.SELF, constants.PROTECT, 1)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_baneful_bunker_cannot_be_used_when_protect_is_in_the_side_conditions(self):
        bot_move = "banefulbunker"
        opponent_move = "earthquake"
        self.state.self.side_conditions[constants.PROTECT] = 1
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.SELF, 170),
                    (constants.MUTATOR_SIDE_END, constants.SELF, constants.PROTECT, 1)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_baneful_bunker_with_contact_move_causes_poison(self):
        bot_move = "banefulbunker"
        opponent_move = "tackle"
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_APPLY_VOLATILE_STATUS, constants.SELF, constants.BANEFUL_BUNKER),
                    (constants.MUTATOR_APPLY_STATUS, constants.OPPONENT, constants.POISON),
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 37),
                    (constants.MUTATOR_REMOVE_VOLATILE_STATUS, constants.SELF, constants.BANEFUL_BUNKER),
                    (constants.MUTATOR_SIDE_START, constants.SELF, constants.PROTECT, 1)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_only_first_protect_actives(self):
        bot_move = "protect"
        opponent_move = "protect"
        self.state.self.active.speed = 2  # bot is faster - only its protect should activate
        self.state.opponent.active.speed = 1
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_APPLY_VOLATILE_STATUS, constants.SELF, constants.PROTECT),
                    (constants.MUTATOR_REMOVE_VOLATILE_STATUS, constants.SELF, constants.PROTECT),
                    (constants.MUTATOR_SIDE_START, constants.SELF, constants.PROTECT, 1)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_protect_cannot_be_used_when_it_exists_as_a_side_condition(self):
        bot_move = "protect"
        opponent_move = "splash"
        self.state.self.side_conditions[constants.PROTECT] = 1
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_SIDE_END, constants.SELF, constants.PROTECT, 1)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_willowisp_misses_versus_protect(self):
        bot_move = "protect"
        opponent_move = "willowisp"
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_APPLY_VOLATILE_STATUS, constants.SELF, constants.PROTECT),
                    (constants.MUTATOR_REMOVE_VOLATILE_STATUS, constants.SELF, constants.PROTECT),
                    (constants.MUTATOR_SIDE_START, constants.SELF, constants.PROTECT, 1)
                ],
                True
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_protect_does_not_stop_weather_damage(self):
        bot_move = "protect"
        opponent_move = "splash"
        self.state.weather = constants.SAND
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_APPLY_VOLATILE_STATUS, constants.SELF, constants.PROTECT),
                    (constants.MUTATOR_DAMAGE, constants.SELF, 13),
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 18),
                    (constants.MUTATOR_REMOVE_VOLATILE_STATUS, constants.SELF, constants.PROTECT),
                    (constants.MUTATOR_SIDE_START, constants.SELF, constants.PROTECT, 1)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_protect_does_not_stop_status_damage(self):
        bot_move = "protect"
        opponent_move = "splash"
        self.state.self.active.status = constants.BURN
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_APPLY_VOLATILE_STATUS, constants.SELF, constants.PROTECT),
                    (constants.MUTATOR_DAMAGE, constants.SELF, 13),
                    (constants.MUTATOR_REMOVE_VOLATILE_STATUS, constants.SELF, constants.PROTECT),
                    (constants.MUTATOR_SIDE_START, constants.SELF, constants.PROTECT, 1)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_protect_behind_a_sub_works(self):
        bot_move = "protect"
        opponent_move = "splash"
        self.state.self.active.volatile_status.add(constants.SUBSTITUTE)
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_APPLY_VOLATILE_STATUS, constants.SELF, constants.PROTECT),
                    (constants.MUTATOR_REMOVE_VOLATILE_STATUS, constants.SELF, constants.PROTECT),
                    (constants.MUTATOR_SIDE_START, constants.SELF, constants.PROTECT, 1)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_protect_does_not_stop_leechseed_damage(self):
        bot_move = "protect"
        opponent_move = "splash"
        self.state.self.active.volatile_status.add(constants.LEECH_SEED)
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_APPLY_VOLATILE_STATUS, constants.SELF, constants.PROTECT),
                    (constants.MUTATOR_DAMAGE, constants.SELF, 26),
                    (constants.MUTATOR_HEAL, constants.OPPONENT, 0),
                    (constants.MUTATOR_REMOVE_VOLATILE_STATUS, constants.SELF, constants.PROTECT),
                    (constants.MUTATOR_SIDE_START, constants.SELF, constants.PROTECT, 1)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_protect_into_hjk_causes_crash_damage(self):
        bot_move = "protect"
        opponent_move = "highjumpkick"
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_APPLY_VOLATILE_STATUS, constants.SELF, constants.PROTECT),
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, self.state.opponent.active.maxhp * 0.5),
                    (constants.MUTATOR_REMOVE_VOLATILE_STATUS, constants.SELF, constants.PROTECT),
                    (constants.MUTATOR_SIDE_START, constants.SELF, constants.PROTECT, 1)
                ],
                True
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_protect_and_hjk_interaction_when_protect_was_previously_used(self):
        bot_move = "protect"
        opponent_move = "highjumpkick"
        self.state.self.side_conditions[constants.PROTECT] = 1
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                0.9,
                [
                    (constants.MUTATOR_DAMAGE, constants.SELF, 110),
                    (constants.MUTATOR_SIDE_END, constants.SELF, constants.PROTECT, 1)
                ],
                False
            ),
            TransposeInstruction(
                0.09999999999999998,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, self.state.opponent.active.maxhp * 0.5),
                    (constants.MUTATOR_SIDE_END, constants.SELF, constants.PROTECT, 1)
                ],
                True
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_using_non_protect_move_causes_protect_side_condition_to_be_removed(self):
        bot_move = "splash"
        opponent_move = "splash"
        self.state.self.side_conditions[constants.PROTECT] = 1
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_SIDE_END, constants.SELF, constants.PROTECT, 1)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_having_protect_volatile_status_causes_tackle_to_miss(self):
        bot_move = "protect"
        opponent_move = "tackle"
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_APPLY_VOLATILE_STATUS, constants.SELF, constants.PROTECT),
                    (constants.MUTATOR_REMOVE_VOLATILE_STATUS, constants.SELF, constants.PROTECT),
                    (constants.MUTATOR_SIDE_START, constants.SELF, constants.PROTECT, 1),
                ],
                True
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_stealthrock_is_unaffected_by_protect(self):
        bot_move = "protect"
        opponent_move = "stealthrock"
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_APPLY_VOLATILE_STATUS, constants.SELF, constants.PROTECT),
                    (constants.MUTATOR_SIDE_START, constants.SELF, constants.STEALTH_ROCK, 1),
                    (constants.MUTATOR_REMOVE_VOLATILE_STATUS, constants.SELF, constants.PROTECT),
                    (constants.MUTATOR_SIDE_START, constants.SELF, constants.PROTECT, 1),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_move_without_protect_flag_goes_through_protect(self):
        bot_move = "protect"
        opponent_move = "feint"
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_APPLY_VOLATILE_STATUS, constants.SELF, constants.PROTECT),
                    (constants.MUTATOR_DAMAGE, constants.SELF, 26),
                    (constants.MUTATOR_REMOVE_VOLATILE_STATUS, constants.SELF, constants.PROTECT),
                    (constants.MUTATOR_SIDE_START, constants.SELF, constants.PROTECT, 1),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_magicguard_does_not_take_leechseed_damage(self):
        bot_move = "splash"
        opponent_move = "splash"
        self.state.opponent.active.ability = 'magicguard'
        self.state.opponent.active.volatile_status.add(constants.LEECH_SEED)
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_waterbubble_doubles_water_damage(self):
        bot_move = "watergun"
        opponent_move = "splash"
        self.state.self.active.ability = 'waterbubble'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [(constants.MUTATOR_DAMAGE, constants.OPPONENT, 43)],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_waterbubble_halves_fire_damage(self):
        bot_move = "eruption"
        opponent_move = "splash"
        self.state.opponent.active.ability = 'waterbubble'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [(constants.MUTATOR_DAMAGE, constants.OPPONENT, 40)],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_waterbubble_prevents_burn(self):
        bot_move = "willowisp"
        opponent_move = "splash"
        self.state.opponent.active.ability = 'waterbubble'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_magicguard_does_not_take_poison_damage(self):
        bot_move = "splash"
        opponent_move = "splash"
        self.state.opponent.active.ability = 'magicguard'
        self.state.opponent.active.status = constants.POISON
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_galvanize_boosts_normal_move_to_give_it_stab(self):
        bot_move = "tackle"
        opponent_move = "splash"
        self.state.self.active.ability = 'galvanize'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 45)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_galvanize_boosts_normal_move_without_stab(self):
        bot_move = "tackle"
        opponent_move = "splash"
        self.state.self.active.ability = 'galvanize'
        self.state.self.active.types = ['normal']
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 30)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_leechseed_does_not_sap_when_dead(self):
        bot_move = "splash"
        opponent_move = "tackle"
        self.state.opponent.active.volatile_status.add(constants.LEECH_SEED)
        self.state.opponent.active.maxhp = 100
        self.state.self.active.maxhp = 100
        self.state.self.active.hp = 1
        self.state.opponent.active.speed = 2
        self.state.self.active.speed = 1
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.SELF, 1)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_misty_terrain_blocks_status(self):
        bot_move = "splash"
        opponent_move = "spore"
        self.state.field = constants.MISTY_TERRAIN
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_misty_terrain_does_not_block_status_on_ungrounded_pkmn(self):
        bot_move = "splash"
        opponent_move = "spore"
        self.state.self.active.types = ['flying']
        self.state.field = constants.MISTY_TERRAIN
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_APPLY_STATUS, constants.SELF, constants.SLEEP)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_waking_up_produces_wake_up_instruction(self):
        bot_move = "tackle"
        opponent_move = "splash"
        self.state.self.active.status = constants.SLEEP
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                0.33,
                [
                    (constants.MUTATOR_REMOVE_STATUS, constants.SELF, constants.SLEEP),
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 25)
                ],
                False
            ),
            TransposeInstruction(
                0.6699999999999999,
                [],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_thawing_produces_thaw_instruction(self):
        bot_move = "tackle"
        opponent_move = "splash"
        self.state.self.active.status = constants.FROZEN
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                0.2,
                [
                    (constants.MUTATOR_REMOVE_STATUS, constants.SELF, constants.FROZEN),
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 25)
                ],
                False
            ),
            TransposeInstruction(
                0.8,
                [],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_using_scald_while_frozen_always_thaws_user(self):
        bot_move = "scald"
        opponent_move = "splash"
        self.state.self.active.status = constants.FROZEN
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                0.3,
                [
                    (constants.MUTATOR_REMOVE_STATUS, constants.SELF, constants.FROZEN),
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 43),
                    (constants.MUTATOR_APPLY_STATUS, constants.OPPONENT, constants.BURN),
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 18)
                ],
                False
            ),
            TransposeInstruction(
                0.7,
                [
                    (constants.MUTATOR_REMOVE_STATUS, constants.SELF, constants.FROZEN),
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 43),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_using_flareblitz_move_while_frozen_always_thaws_user(self):
        bot_move = "flareblitz"
        opponent_move = "splash"
        self.state.self.active.status = constants.FROZEN
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                0.1,
                [
                    (constants.MUTATOR_REMOVE_STATUS, constants.SELF, constants.FROZEN),
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 74),
                    (constants.MUTATOR_DAMAGE, constants.SELF, 24),
                    (constants.MUTATOR_APPLY_STATUS, constants.OPPONENT, constants.BURN),
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 18)
                ],
                False
            ),
            TransposeInstruction(
                0.9,
                [
                    (constants.MUTATOR_REMOVE_STATUS, constants.SELF, constants.FROZEN),
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 74),
                    (constants.MUTATOR_DAMAGE, constants.SELF, 24),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_being_hit_by_fire_move_while_frozen_always_thaws(self):
        bot_move = "splash"
        opponent_move = "eruption"
        self.state.self.active.speed = 1
        self.state.opponent.active.speed = 2
        self.state.self.active.status = constants.FROZEN
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.SELF, 123),
                    (constants.MUTATOR_REMOVE_STATUS, constants.SELF, constants.FROZEN)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_being_hit_by_fire_move_while_slower_while_frozen_always_thaws(self):
        bot_move = "splash"
        opponent_move = "eruption"
        self.state.self.active.status = constants.FROZEN
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_REMOVE_STATUS, constants.SELF, constants.FROZEN),
                    (constants.MUTATOR_DAMAGE, constants.SELF, 123),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_ice_type_cannot_be_frozen(self):
        bot_move = "icebeam"
        opponent_move = "splash"
        self.state.opponent.active.types = ['ice']
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 24),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_cannot_be_frozen_in_harsh_sunlight(self):
        bot_move = "icebeam"
        opponent_move = "splash"
        self.state.weather = constants.DESOLATE_LAND
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 48),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_frozen_pokemon_versus_switch(self):
        bot_move = "splash"
        opponent_move = "switch yveltal"
        self.state.self.active.status = constants.FROZEN
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                0.2,
                [
                    (constants.MUTATOR_SWITCH, constants.OPPONENT, 'aromatisse', 'yveltal'),
                    (constants.MUTATOR_REMOVE_STATUS, constants.SELF, constants.FROZEN),
                ],
                False
            ),
            TransposeInstruction(
                0.8,
                [
                    (constants.MUTATOR_SWITCH, constants.OPPONENT, 'aromatisse', 'yveltal'),
                ],
                True
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_painsplit_properly_splits_health(self):
        bot_move = "painsplit"
        opponent_move = "splash"
        self.state.self.active.hp = 50
        self.state.opponent.active.hp = 100
        self.state.self.active.maxhp = 100
        self.state.opponent.active.maxhp = 100
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 25),
                    (constants.MUTATOR_HEAL, constants.SELF, 25),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_painsplit_does_not_overheal(self):
        bot_move = "painsplit"
        opponent_move = "splash"
        self.state.self.active.hp = 50
        self.state.self.active.maxhp = 100
        self.state.opponent.active.hp = 500
        self.state.opponent.active.maxhp = 500
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 225),
                    (constants.MUTATOR_HEAL, constants.SELF, 50),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_painsplit_does_not_overheal_enemy(self):
        bot_move = "painsplit"
        opponent_move = "splash"
        self.state.self.active.hp = 500
        self.state.self.active.maxhp = 500
        self.state.opponent.active.hp = 50
        self.state.opponent.active.maxhp = 100
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, -50),
                    (constants.MUTATOR_HEAL, constants.SELF, -225),
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_icebeam_into_scald(self):
        bot_move = "icebeam"
        opponent_move = "scald"
        self.state.self.active.speed = 2
        self.state.opponent.active.speed = 1
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                0.03,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 48),
                    (constants.MUTATOR_APPLY_STATUS, constants.OPPONENT, constants.FROZEN),
                    (constants.MUTATOR_REMOVE_STATUS, constants.OPPONENT, constants.FROZEN),
                    (constants.MUTATOR_DAMAGE, constants.SELF, 66),
                    (constants.MUTATOR_APPLY_STATUS, constants.SELF, constants.BURN),
                    (constants.MUTATOR_DAMAGE, constants.SELF, 13)
                ],
                False
            ),
            TransposeInstruction(
                0.06999999999999999,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 48),
                    (constants.MUTATOR_APPLY_STATUS, constants.OPPONENT, constants.FROZEN),
                    (constants.MUTATOR_REMOVE_STATUS, constants.OPPONENT, constants.FROZEN),
                    (constants.MUTATOR_DAMAGE, constants.SELF, 66),
                ],
                True
            ),
            TransposeInstruction(
                0.27,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 48),
                    (constants.MUTATOR_DAMAGE, constants.SELF, 66),
                    (constants.MUTATOR_APPLY_STATUS, constants.SELF, constants.BURN),
                    (constants.MUTATOR_DAMAGE, constants.SELF, 13)
                ],
                False
            ),
            TransposeInstruction(
                0.63,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 48),
                    (constants.MUTATOR_DAMAGE, constants.SELF, 66),
                ],
                True
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_electric_terrain_blocks_sleep(self):
        bot_move = "splash"
        opponent_move = "spore"
        self.state.field = constants.ELECTRIC_TERRAIN
        self.state.opponent.active.maxhp = 100
        self.state.self.active.maxhp = 100
        self.state.self.active.hp = 50
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_skill_link_increases_tailslap_damage(self):
        bot_move = "tailslap"
        opponent_move = "splash"
        self.state.self.active.ability = 'skilllink'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                0.85,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 77),
                ],
                False
            ),
            TransposeInstruction(
                0.15000000000000002,
                [],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_pre_existing_leechseed_produces_sap_instruction(self):
        bot_move = "tackle"
        opponent_move = "splash"
        self.state.opponent.active.volatile_status.add("leechseed")
        self.state.opponent.active.maxhp = 100
        self.state.opponent.active.hp = 100
        self.state.self.active.maxhp = 100
        self.state.self.active.hp = 50
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 25),
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 12),
                    (constants.MUTATOR_HEAL, constants.SELF, 12)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_pre_existing_leechseed_produces_sap_instruction_with_one_health_after_damage(self):
        bot_move = "tackle"
        opponent_move = "splash"
        self.state.opponent.active.volatile_status.add("leechseed")
        self.state.opponent.active.hp = 26
        self.state.opponent.active.maxhp = 100
        self.state.self.active.maxhp = 100
        self.state.self.active.hp = 50
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 25),
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 1),
                    (constants.MUTATOR_HEAL, constants.SELF, 1)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_double_zap_cannon(self):
        bot_move = "zapcannon"
        opponent_move = "zapcannon"

        # raichu's default ability should be lightningrod
        self.state.self.active.ability = None
        # Raichu is electric type and can't as such get paralyzed
        self.state.self.active.types = ["ghost", "grass"]

        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                0.1875,
                [
                    ('damage', 'opponent', 63),
                    ('apply_status', 'opponent', 'par'),
                    ('damage', 'self', 49),
                    ('apply_status', 'self', 'par')
                ],
                False
            ),
            TransposeInstruction(
                0.3125,
                [
                    ('damage', 'opponent', 63),
                    ('apply_status', 'opponent', 'par'),
                ],
                True
            ),
            TransposeInstruction(
                0.25,
                [
                    ('damage', 'self', 49),
                    ('apply_status', 'self', 'par')
                ],
                False
            ),
            TransposeInstruction(
                0.25,
                [],
                True
            ),
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_thunder_produces_all_states(self):
        bot_move = "thunder"
        opponent_move = "splash"
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                0.21,
                [
                    ('damage', 'opponent', 88),
                    ('apply_status', 'opponent', 'par'),
                ],
                False
            ),
            TransposeInstruction(
                0.48999999999999994,
                [
                    ('damage', 'opponent', 88),
                ],
                False
            ),
            TransposeInstruction(
                0.30000000000000004,
                [
                ],
                False
            ),
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_thunder_produces_all_states_with_damage_rolls_accounted_for(self):
        config.damage_calc_type = "min_max_average"
        bot_move = "thunder"
        opponent_move = "splash"
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                0.06999999999999999,
                [
                    ('damage', 'opponent', 88),
                    ('apply_status', 'opponent', 'par'),
                ],
                False
            ),
            TransposeInstruction(
                0.1633333333333333,
                [
                    ('damage', 'opponent', 88),
                ],
                False
            ),
            TransposeInstruction(
                0.30000000000000004,
                [
                ],
                False
            ),
            TransposeInstruction(
                0.06999999999999999,
                [
                    ('damage', 'opponent', 81),
                    ('apply_status', 'opponent', 'par'),
                ],
                False
            ),
            TransposeInstruction(
                0.1633333333333333,
                [
                    ('damage', 'opponent', 81),
                ],
                False
            ),
            TransposeInstruction(
                0.06999999999999999,
                [
                    ('damage', 'opponent', 96),
                    ('apply_status', 'opponent', 'par'),
                ],
                False
            ),
            TransposeInstruction(
                0.1633333333333333,
                [
                    ('damage', 'opponent', 96),
                ],
                False
            ),
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_flinching_move_versus_secondary_effect_produces_three_states(self):
        bot_move = "ironhead"
        opponent_move = "moonblast"
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                0.3,
                [
                    ('damage', 'opponent', 99),
                    ('apply_volatile_status', 'opponent', 'flinch'),
                    ('remove_volatile_status', 'opponent', 'flinch')
                ],
                True
            ),
            TransposeInstruction(
                0.21,
                [
                    ('damage', 'opponent', 99),
                    ('damage', 'self', 119),
                    ('boost', 'self', 'special-attack', -1),
                ],
                False
            ),
            TransposeInstruction(
                0.48999999999999994,
                [
                    ('damage', 'opponent', 99),
                    ('damage', 'self', 119),
                ],
                False
            ),
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_switch_flying_into_earthquake(self):
        bot_move = "switch xatu"
        opponent_move = "earthquake"
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    ('switch', 'self', 'raichu', 'xatu'),
                ],
                True
            ),
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_thousandarrows_versus_ungrounded_pokemon_hits(self):
        bot_move = "thousandarrows"
        opponent_move = "splash"
        self.state.opponent.active.types = ['flying']
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 56),
                    (constants.MUTATOR_APPLY_VOLATILE_STATUS, constants.OPPONENT, 'smackdown'),
                ],
                False
            ),
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_thousandarrows_versus_levitate_hits(self):
        bot_move = "thousandarrows"
        opponent_move = "splash"
        self.state.opponent.active.ability = 'levitate'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 56),
                    (constants.MUTATOR_APPLY_VOLATILE_STATUS, constants.OPPONENT, 'smackdown'),
                ],
                False
            ),
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_thousandarrows_versus_airballoon_hits(self):
        bot_move = "thousandarrows"
        opponent_move = "splash"
        self.state.opponent.active.item = 'airballoon'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 56),
                    (constants.MUTATOR_APPLY_VOLATILE_STATUS, constants.OPPONENT, 'smackdown'),
                ],
                False
            ),
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_magnetrise_versus_earthquake(self):
        bot_move = "earthquake"
        opponent_move = "magnetrise"
        self.state.opponent.active.speed = 2
        self.state.self.active.speed = 1
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_APPLY_VOLATILE_STATUS, constants.OPPONENT, 'magnetrise'),
                ],
                True
            ),
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_roost_volatilestatus_is_removed_at_end_of_turn(self):
        bot_move = "splash"
        opponent_move = "roost"
        self.state.opponent.active.speed = 2
        self.state.self.active.speed = 1
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_APPLY_VOLATILE_STATUS, constants.OPPONENT, 'roost'),
                    (constants.MUTATOR_REMOVE_VOLATILE_STATUS, constants.OPPONENT, 'roost'),
                ],
                False
            ),
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_roost_volatilestatus_makes_ground_move_hit_flying_type(self):
        bot_move = "earthquake"
        opponent_move = "roost"
        self.state.opponent.active.types = ['flying', 'ghost']
        self.state.opponent.active.speed = 2
        self.state.self.active.speed = 1
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_APPLY_VOLATILE_STATUS, constants.OPPONENT, 'roost'),
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 62),
                    (constants.MUTATOR_REMOVE_VOLATILE_STATUS, constants.OPPONENT, 'roost'),
                ],
                False
            ),
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_roost_volatilestatus_makes_ground_move_hit_pure_flying_type(self):
        bot_move = "earthquake"
        opponent_move = "roost"
        self.state.opponent.active.types = ['flying']
        self.state.opponent.active.speed = 2
        self.state.self.active.speed = 1
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_APPLY_VOLATILE_STATUS, constants.OPPONENT, 'roost'),
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 62),
                    (constants.MUTATOR_REMOVE_VOLATILE_STATUS, constants.OPPONENT, 'roost'),
                ],
                False
            ),
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_thousandarrows_versus_double_type_does_not_change_the_original_type_list(self):
        bot_move = "thousandarrows"
        opponent_move = "splash"
        self.state.opponent.active.types = ['flying', 'ground']
        get_all_state_instructions(self.mutator, bot_move, opponent_move)

        self.assertEqual(['flying', 'ground'], self.state.opponent.active.types)

    def test_flinching_as_second_move_does_not_produce_extra_state(self):
        bot_move = "switch xatu"
        opponent_move = "ironhead"
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    ('switch', 'self', 'raichu', 'xatu'),
                    ('damage', 'self', 52),
                ],
                False
            ),
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_attack_into_healing_produces_one_state(self):
        bot_move = "tackle"
        opponent_move = "recover"
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    ('damage', 'opponent', 25),
                    ('heal', 'opponent', 25),
                ],
                False
            ),
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_lifedew_healing(self):
        bot_move = "lifedew"
        opponent_move = "splash"
        self.state.self.active.hp -= 25
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_HEAL, constants.SELF, 25),
                ],
                False
            ),
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_morningsun_in_sunlight(self):
        bot_move = "morningsun"
        opponent_move = "splash"
        self.state.self.active.hp = 1
        self.state.self.active.maxhp = 100
        self.state.weather = constants.SUN
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_HEAL, constants.SELF, (2/3) * 100),
                ],
                False
            ),
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_morningsun_in_sand(self):
        bot_move = "morningsun"
        opponent_move = "splash"
        self.state.self.active.hp = 1
        self.state.self.active.maxhp = 100
        self.state.weather = constants.SAND
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_HEAL, constants.SELF, (1/4) * 100),
                    (constants.MUTATOR_DAMAGE, constants.SELF, 6),
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 18),
                ],
                False
            ),
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_shoreup_in_sand(self):
        bot_move = "shoreup"
        opponent_move = "splash"
        self.state.self.active.hp = 1
        self.state.self.active.maxhp = 100
        self.state.weather = constants.SAND
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_HEAL, constants.SELF, (2/3) * 100),
                    (constants.MUTATOR_DAMAGE, constants.SELF, 6),
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 18),
                ],
                False
            ),
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_attack_into_healing_with_multiple_attack_damage_rolls(self):
        config.damage_calc_type = "min_max_average"
        bot_move = "tackle"
        opponent_move = "recover"
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1 / 3,
                [
                    ('damage', 'opponent', 25),
                    ('heal', 'opponent', 25),
                ],
                False
            ),
            TransposeInstruction(
                1 / 3,
                [
                    ('damage', 'opponent', 28),
                    ('heal', 'opponent', 28),
                ],
                False
            ),
            TransposeInstruction(
                1 / 3,
                [
                    ('damage', 'opponent', 23),
                    ('heal', 'opponent', 23),
                ],
                False
            ),
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_fainted_pokemon_cannot_heal(self):
        self.state.opponent.active.hp = 1

        bot_move = "tackle"
        opponent_move = "recover"
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    ('damage', 'opponent', 1),
                ],
                False
            ),
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_switch_into_rocks_does_neutral_damage(self):
        self.state.opponent.side_conditions[constants.STEALTH_ROCK] = 1

        bot_move = "splash"
        opponent_move = "switch toxapex"
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    ('switch', 'opponent', 'aromatisse', 'toxapex'),
                    ('damage', 'opponent', 24.125),
                ],
                False
            ),
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_switch_into_rock_does_no_damage_with_heavy_duty_boots(self):
        self.state.opponent.side_conditions[constants.STEALTH_ROCK] = 1

        bot_move = "splash"
        opponent_move = "switch toxapex"
        self.state.opponent.reserve['toxapex'].item = 'heavydutyboots'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_SWITCH, constants.OPPONENT, 'aromatisse', 'toxapex'),
                ],
                False
            ),
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_switch_into_spike_does_no_damage_with_heavy_duty_boots(self):
        self.state.opponent.side_conditions[constants.SPIKES] = 2

        bot_move = "splash"
        opponent_move = "switch toxapex"
        self.state.opponent.reserve['toxapex'].item = 'heavydutyboots'
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_SWITCH, constants.OPPONENT, 'aromatisse', 'toxapex'),
                ],
                False
            ),
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_stealthrock_into_magicbounce_properly_reflects(self):
        self.state.self.active.ability = 'magicbounce'
        bot_move = "splash"
        opponent_move = "stealthrock"
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_SIDE_START, constants.OPPONENT, constants.STEALTH_ROCK, 1),
                ],
                False
            ),
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_magic_bounced_stealthrock_doesnt_exceed_one_level(self):
        self.state.self.active.ability = 'magicbounce'
        bot_move = "splash"
        opponent_move = "stealthrock"
        self.state.opponent.side_conditions[constants.STEALTH_ROCK] = 1
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [],
                False
            ),
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_double_earthquake_with_double_levitate_does_nothing(self):
        self.state.self.active.ability = 'levitate'
        self.state.opponent.active.ability = 'levitate'

        bot_move = "earthquake"
        opponent_move = "earthquake"
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                ],
                True
            ),
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_earthquake_hits_into_levitate_when_user_has_moldbreaker(self):
        self.state.self.active.ability = 'moldbreaker'
        self.state.opponent.active.ability = 'levitate'

        bot_move = "earthquake"
        opponent_move = "splash"
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 62)
                ],
                False
            ),
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_earthquake_hits_into_levitate_when_user_has_turboblaze(self):
        self.state.self.active.ability = 'turboblaze'
        self.state.opponent.active.ability = 'levitate'

        bot_move = "earthquake"
        opponent_move = "splash"
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 62)
                ],
                False
            ),
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_fire_move_hits_flashfire_pokemon_when_user_has_moldbreaker(self):
        self.state.self.active.ability = 'moldbreaker'
        self.state.opponent.active.ability = 'flashfire'

        bot_move = "eruption"
        opponent_move = "splash"
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 79)
                ],
                False
            ),
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_rocks_can_be_used_versus_magic_bounce_when_user_has_moldbreaker(self):
        self.state.self.active.ability = 'moldbreaker'
        self.state.opponent.active.ability = 'magicbounce'

        bot_move = "stealthrock"
        opponent_move = "splash"
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1,
                [
                    (constants.MUTATOR_SIDE_START, constants.OPPONENT, constants.STEALTH_ROCK, 1)
                ],
                False
            ),
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_paralyzed_pokemon_produces_two_states_when_trying_to_attack(self):
        self.state.self.active.status = constants.PARALYZED
        bot_move = "tackle"
        opponent_move = "tackle"
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                0.75,
                [
                    ('damage', 'opponent', 25),
                    ('damage', 'self', 35),

                ],
                False
            ),
            TransposeInstruction(
                0.25,
                [
                    ('damage', 'self', 35)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_removes_flinch_status_when_pokemon_faints(self):
        bot_move = "rockslide"
        opponent_move = "splash"

        self.state.opponent.active.hp = 44

        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                0.27,
                [
                    (constants.DAMAGE, constants.OPPONENT, 44),
                    (constants.MUTATOR_APPLY_VOLATILE_STATUS, constants.OPPONENT, constants.FLINCH),
                    (constants.MUTATOR_REMOVE_VOLATILE_STATUS, constants.OPPONENT, constants.FLINCH)
                ],
                True
            ),
            TransposeInstruction(
                0.63,
                [
                    (constants.DAMAGE, constants.OPPONENT, 44)

                ],
                False
            ),
            TransposeInstruction(
                0.09999999999999998,
                [],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_explosion_kills_the_user(self):
        bot_move = "explosion"
        opponent_move = "crunch"

        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1.0,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 154),
                    (constants.MUTATOR_HEAL, constants.SELF, -208.0),
                    (constants.MUTATOR_DAMAGE, constants.SELF, 0)
                ],
                True
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_closecombat_kills_and_reduces_stats(self):
        bot_move = "closecombat"
        opponent_move = "tackle"

        self.state.opponent.active.hp = 4.84

        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1.0,
                [
                    (constants.MUTATOR_DAMAGE, constants.OPPONENT, 4.84),
                    (constants.MUTATOR_BOOST, constants.SELF, constants.DEFENSE, -1),
                    (constants.MUTATOR_BOOST, constants.SELF, constants.SPECIAL_DEFENSE, -1)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_willowisp_on_flashfire(self):
        bot_move = "willowisp"
        opponent_move = "splash"
        self.state.opponent.active.ability = 'flashfire'

        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1.0,
                [],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_ground_immune_to_thunderwave(self):
        self.state.opponent.active.types = ['ground']
        bot_move = "thunderwave"
        opponent_move = "splash"

        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1.0,
                [],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)

    def test_electric_immune_to_thunderwave(self):
        bot_move = "thunderwave"
        opponent_move = "splash"
        self.state.opponent.active.types = ["electric"]
        instructions = get_all_state_instructions(self.mutator, bot_move, opponent_move)
        expected_instructions = [
            TransposeInstruction(
                1.0,
                [],
                False
            )
        ]

        self.assertEqual(expected_instructions, instructions)


class TestRemoveDuplicateInstructions(unittest.TestCase):
    def test_turns_two_identical_instructions_into_one(self):
        instruction1 = TransposeInstruction(
            0.5,
            [
                (constants.MUTATOR_DAMAGE, constants.SELF, 5)
            ],
            False
        )
        instruction2 = deepcopy(instruction1)
        duplicated_instructions = [
            instruction1,
            instruction2
        ]

        expected_instructions = [
            TransposeInstruction(
                1.0,
                [
                    (constants.MUTATOR_DAMAGE, constants.SELF, 5)
                ],
                False
            )
        ]

        instructions = remove_duplicate_instructions(duplicated_instructions)

        self.assertEqual(expected_instructions, instructions)

    def test_does_not_combine_when_instructions_are_different(self):
        instruction1 = TransposeInstruction(
            0.5,
            [
                (constants.MUTATOR_DAMAGE, constants.SELF, 5)
            ],
            False
        )
        instruction2 = TransposeInstruction(
            0.5,
            [
                (constants.MUTATOR_DAMAGE, constants.SELF, 6)
            ],
            False
        )
        duplicated_instructions = [
            instruction1,
            instruction2
        ]

        instructions = remove_duplicate_instructions(duplicated_instructions)

        self.assertEqual(duplicated_instructions, instructions)

    def test_combines_two_instructions_but_keeps_the_other(self):
        instructions = [
            TransposeInstruction(
                0.33,
                [
                    (constants.MUTATOR_DAMAGE, constants.SELF, 5)
                ],
                False
            ),
            TransposeInstruction(
                0.33,
                [
                    (constants.MUTATOR_DAMAGE, constants.SELF, 5)
                ],
                False
            ),
            TransposeInstruction(
                0.33,
                [
                    (constants.MUTATOR_DAMAGE, constants.SELF, 6)
                ],
                False
            )
        ]

        new_instructions = remove_duplicate_instructions(instructions)

        expected_instructions = [
            TransposeInstruction(
                0.66,
                [
                    (constants.MUTATOR_DAMAGE, constants.SELF, 5)
                ],
                False
            ),
            TransposeInstruction(
                0.33,
                [
                    (constants.MUTATOR_DAMAGE, constants.SELF, 6)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, new_instructions)

    def test_combines_multiple_duplicates(self):
        instructions = [
            TransposeInstruction(
                0.1,
                [
                    (constants.MUTATOR_DAMAGE, constants.SELF, 5)
                ],
                False
            ),
            TransposeInstruction(
                0.1,
                [
                    (constants.MUTATOR_DAMAGE, constants.SELF, 5)
                ],
                False
            ),
            TransposeInstruction(
                0.2,
                [
                    (constants.MUTATOR_DAMAGE, constants.SELF, 6)
                ],
                False
            ),
            TransposeInstruction(
                0.2,
                [
                    (constants.MUTATOR_DAMAGE, constants.SELF, 6)
                ],
                False
            ),
            TransposeInstruction(
                0.2,
                [
                    (constants.MUTATOR_DAMAGE, constants.SELF, 7)
                ],
                False
            ),
            TransposeInstruction(
                0.2,
                [
                    (constants.MUTATOR_DAMAGE, constants.SELF, 7)
                ],
                False
            )
        ]

        new_instructions = remove_duplicate_instructions(instructions)

        expected_instructions = [
            TransposeInstruction(
                0.2,
                [
                    (constants.MUTATOR_DAMAGE, constants.SELF, 5)
                ],
                False
            ),
            TransposeInstruction(
                0.4,
                [
                    (constants.MUTATOR_DAMAGE, constants.SELF, 6)
                ],
                False
            ),
            TransposeInstruction(
                0.4,
                [
                    (constants.MUTATOR_DAMAGE, constants.SELF, 7)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, new_instructions)

    def test_combines_two_instructions_but_keeps_many_others(self):
        instructions = [
            TransposeInstruction(
                0.2,
                [
                    (constants.MUTATOR_DAMAGE, constants.SELF, 5)
                ],
                False
            ),
            TransposeInstruction(
                0.2,
                [
                    (constants.MUTATOR_DAMAGE, constants.SELF, 5)
                ],
                False
            ),
            TransposeInstruction(
                0.1,
                [
                    (constants.MUTATOR_DAMAGE, constants.SELF, 6)
                ],
                False
            ),
            TransposeInstruction(
                0.2,
                [
                    (constants.MUTATOR_DAMAGE, constants.SELF, 7)
                ],
                False
            ),
            TransposeInstruction(
                0.3,
                [
                    (constants.MUTATOR_DAMAGE, constants.SELF, 8)
                ],
                False
            )
        ]

        new_instructions = remove_duplicate_instructions(instructions)

        expected_instructions = [
            TransposeInstruction(
                0.4,
                [
                    (constants.MUTATOR_DAMAGE, constants.SELF, 5)
                ],
                False
            ),
            TransposeInstruction(
                0.1,
                [
                    (constants.MUTATOR_DAMAGE, constants.SELF, 6)
                ],
                False
            ),
            TransposeInstruction(
                0.2,
                [
                    (constants.MUTATOR_DAMAGE, constants.SELF, 7)
                ],
                False
            ),
            TransposeInstruction(
                0.3,
                [
                    (constants.MUTATOR_DAMAGE, constants.SELF, 8)
                ],
                False
            )
        ]

        self.assertEqual(expected_instructions, new_instructions)


class TestUserMovesFirst(unittest.TestCase):
    def setUp(self):
        self.state = State(
                        Side(
                            Pokemon.from_state_pokemon_dict(StatePokemon("raichu", 73).to_dict()),
                            {
                                "xatu": Pokemon.from_state_pokemon_dict(StatePokemon("xatu", 81).to_dict()),
                                "starmie": Pokemon.from_state_pokemon_dict(StatePokemon("starmie", 81).to_dict()),
                                "gyarados": Pokemon.from_state_pokemon_dict(StatePokemon("gyarados", 81).to_dict()),
                                "dragonite": Pokemon.from_state_pokemon_dict(StatePokemon("dragonite", 81).to_dict()),
                                "hitmonlee": Pokemon.from_state_pokemon_dict(StatePokemon("hitmonlee", 81).to_dict()),
                            },
                            (0, 0),
                            defaultdict(lambda: 0)
                        ),
                        Side(
                            Pokemon.from_state_pokemon_dict(StatePokemon("aromatisse", 81).to_dict()),
                            {
                                "yveltal": Pokemon.from_state_pokemon_dict(StatePokemon("yveltal", 73).to_dict()),
                                "slurpuff": Pokemon.from_state_pokemon_dict(StatePokemon("slurpuff", 73).to_dict()),
                                "victini": Pokemon.from_state_pokemon_dict(StatePokemon("victini", 73).to_dict()),
                                "toxapex": Pokemon.from_state_pokemon_dict(StatePokemon("toxapex", 73).to_dict()),
                                "bronzong": Pokemon.from_state_pokemon_dict(StatePokemon("bronzong", 73).to_dict()),
                            },
                            (0, 0),
                            defaultdict(lambda: 0)
                        ),
                        None,
                        None,
                        False
                    )

        self.mutator = StateMutator(self.state)

    def test_bot_moves_first_when_move_priorities_are_the_same_and_it_is_faster(self):
        user = self.state.self
        opponent = self.state.opponent
        user_move = lookup_move('tackle')
        opponent_move = lookup_move('tackle')

        user.active.speed = 2
        opponent.active.speed = 1

        self.assertTrue(user_moves_first(self.state, user_move, opponent_move))

    def test_paralysis_reduces_speed_by_half(self):
        user = self.state.self
        opponent = self.state.opponent
        user_move = lookup_move('tackle')
        opponent_move = lookup_move('tackle')

        user.active.status = constants.PARALYZED

        user.active.speed = 10
        opponent.active.speed = 7

        self.assertFalse(user_moves_first(self.state, user_move, opponent_move))

    def test_opponent_moves_first_when_move_priorities_are_the_same_and_it_is_faster(self):
        user = self.state.self
        opponent = self.state.opponent
        user_move = lookup_move('tackle')
        opponent_move = lookup_move('tackle')

        user.active.speed = 1
        opponent.active.speed = 2

        self.assertFalse(user_moves_first(self.state, user_move, opponent_move))

    def test_priority_causes_slower_to_move_first(self):
        user = self.state.self
        opponent = self.state.opponent
        user_move = lookup_move('quickattack')
        opponent_move = lookup_move('tackle')

        user.active.speed = 1
        opponent.active.speed = 2

        self.assertTrue(user_moves_first(self.state, user_move, opponent_move))

    def test_both_using_priority_causes_faster_to_move_first(self):
        user = self.state.self
        opponent = self.state.opponent
        user_move = lookup_move('quickattack')
        opponent_move = lookup_move('quickattack')

        user.active.speed = 1
        opponent.active.speed = 2

        self.assertFalse(user_moves_first(self.state, user_move, opponent_move))

    def test_choice_scarf_causes_a_difference_in_effective_speed(self):
        user = self.state.self
        opponent = self.state.opponent
        user_move = lookup_move('tackle')
        opponent_move = lookup_move('tackle')

        user.active.item = 'choicescarf'
        user.active.speed = 5
        opponent.active.speed = 6

        self.assertTrue(user_moves_first(self.state, user_move, opponent_move))

    def test_tailwind_doubling_speed(self):
        user = self.state.self
        opponent = self.state.opponent
        user_move = lookup_move('tackle')
        opponent_move = lookup_move('tackle')

        user.side_conditions[constants.TAILWIND] = 1
        user.active.speed = 51
        opponent.active.speed = 100

        self.assertTrue(user_moves_first(self.state, user_move, opponent_move))

    def test_tailwind_at_0_does_not_boost(self):
        user = self.state.self
        opponent = self.state.opponent
        user_move = lookup_move('tackle')
        opponent_move = lookup_move('tackle')

        user.side_conditions[constants.TAILWIND] = 0
        user.active.speed = 51
        opponent.active.speed = 100

        self.assertFalse(user_moves_first(self.state, user_move, opponent_move))

    def test_switch_always_moves_first(self):
        user = self.state.self
        opponent = self.state.opponent
        user_move = "{} x".format(constants.SWITCH_STRING)
        opponent_move = lookup_move('quickattack')

        user.active.speed = 1
        opponent.active.speed = 2

        self.assertTrue(user_moves_first(self.state, user_move, opponent_move))

    def test_double_switch_results_in_faster_moving_first(self):
        user = self.state.self
        opponent = self.state.opponent
        user_move = "{} x".format(constants.SWITCH_STRING)
        opponent_move = "{} x".format(constants.SWITCH_STRING)

        user.active.speed = 1
        opponent.active.speed = 2

        self.assertFalse(user_moves_first(self.state, user_move, opponent_move))

    def test_prankster_results_in_status_move_going_first(self):
        user = self.state.self
        opponent = self.state.opponent
        user_move = lookup_move('willowisp')
        opponent_move = lookup_move('tackle')

        user.active.speed = 1
        opponent.active.speed = 2
        user.active.ability = 'prankster'

        self.assertTrue(user_moves_first(self.state, user_move, opponent_move))

    def test_quickattack_still_goes_first_when_user_has_prankster(self):
        user = self.state.self
        opponent = self.state.opponent
        user_move = lookup_move('willowisp')
        opponent_move = lookup_move('quickattack')

        user.active.speed = 1
        opponent.active.speed = 2
        user.active.ability = 'prankster'

        self.assertFalse(user_moves_first(self.state, user_move, opponent_move))

    def test_prankster_does_not_result_in_tackle_going_first(self):
        user = self.state.self
        opponent = self.state.opponent
        user_move = lookup_move('tackle')
        opponent_move = lookup_move('tackle')

        user.active.speed = 1
        opponent.active.speed = 2
        user.active.ability = 'prankster'

        self.assertFalse(user_moves_first(self.state, user_move, opponent_move))

    def test_trickroom_results_in_slower_pokemon_going_first(self):
        user = self.state.self
        opponent = self.state.opponent
        user_move = lookup_move('tackle')
        opponent_move = lookup_move('tackle')

        self.state.trick_room = True
        user.active.speed = 1
        opponent.active.speed = 2

        self.assertTrue(user_moves_first(self.state, user_move, opponent_move))

    def test_priority_move_goes_first_in_trickroom(self):
        user = self.state.self
        opponent = self.state.opponent
        user_move = lookup_move('tackle')
        opponent_move = lookup_move('quickattack')

        self.state.field = 'trickroom'
        user.active.speed = 1
        opponent.active.speed = 2

        self.assertFalse(user_moves_first(self.state, user_move, opponent_move))

    def test_pursuit_moves_second_when_slower(self):
        user = self.state.self
        opponent = self.state.opponent
        user_move = lookup_move('pursuit')
        opponent_move = lookup_move('tackle')

        user.active.speed = 1
        opponent.active.speed = 2

        self.assertFalse(user_moves_first(self.state, user_move, opponent_move))

    def test_pursuit_moves_first_when_opponent_is_switching(self):
        user = self.state.self
        opponent = self.state.opponent
        user_move = lookup_move('pursuit')
        opponent_move = 'switch yveltal'

        user.active.speed = 1
        opponent.active.speed = 2

        self.assertTrue(user_moves_first(self.state, user_move, opponent_move))

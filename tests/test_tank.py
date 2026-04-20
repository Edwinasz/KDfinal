import unittest
from ..tank import (
    Tank, HeavyTank, MediumTank, LightTank, TankDestroyer, SPG,
    WEIGHT_BY_TIER,
)


class TestTankValidation(unittest.TestCase):

    def test_valid_creation(self):
        t = HeavyTank(name="Tiger I", tier=7, nation="Germany")
        self.assertEqual(t.name, "Tiger I")
        self.assertEqual(t.tier, 7)
        self.assertEqual(t.nation, "Germany")

    def test_tier_too_low(self):
        with self.assertRaises(ValueError):
            HeavyTank(name="X", tier=0, nation="USSR")

    def test_tier_too_high(self):
        with self.assertRaises(ValueError):
            HeavyTank(name="X", tier=11, nation="USSR")

    def test_invalid_nation(self):
        with self.assertRaises(ValueError):
            HeavyTank(name="X", tier=5, nation="Narnia")

    def test_boundary_tier_1(self):
        t = LightTank(name="T-26", tier=1, nation="USSR")
        self.assertEqual(t.tier, 1)

    def test_boundary_tier_10(self):
        t = HeavyTank(name="IS-7", tier=10, nation="USSR")
        self.assertEqual(t.tier, 10)


class TestTankClass(unittest.TestCase):

    def test_heavy_tank_class(self):
        self.assertEqual(HeavyTank("X", 5, "USSR").tank_class, "Heavy")

    def test_medium_tank_class(self):
        self.assertEqual(MediumTank("X", 5, "USSR").tank_class, "Medium")

    def test_light_tank_class(self):
        self.assertEqual(LightTank("X", 5, "USSR").tank_class, "Light")

    def test_td_tank_class(self):
        self.assertEqual(TankDestroyer("X", 5, "USSR").tank_class, "TD")

    def test_spg_tank_class(self):
        self.assertEqual(SPG("X", 5, "USSR").tank_class, "SPG")


class TestTankWeights(unittest.TestCase):
    """Kiekviena poklasė turi savus dauginamojo koeficiento taisykles — testuojamos visos ribos."""

    # HeavyTank: visada 1.2x
    def test_heavy_weight_all_tiers(self):
        for tier in range(1, 11):
            expected = WEIGHT_BY_TIER[tier] * 1.2
            self.assertAlmostEqual(
                HeavyTank("X", tier, "USSR").matchmaking_weight(), expected,
                msg=f"HeavyTank tier {tier}",
            )

    # MediumTank: 1.2x nuo 9–10 lygio, 1.0x kitais atvejais
    def test_medium_weight_low_tiers(self):
        for tier in range(1, 9):
            expected = WEIGHT_BY_TIER[tier] * 1.0
            self.assertAlmostEqual(
                MediumTank("X", tier, "USSR").matchmaking_weight(), expected,
                msg=f"MediumTank tier {tier}",
            )

    def test_medium_weight_high_tiers(self):
        for tier in (9, 10):
            expected = WEIGHT_BY_TIER[tier] * 1.2
            self.assertAlmostEqual(
                MediumTank("X", tier, "USSR").matchmaking_weight(), expected,
                msg=f"MediumTank tier {tier}",
            )

    # LightTank: 1.2x nuo 5–8 lygio, 1.0x kitais atvejais
    def test_light_weight_outside_window(self):
        for tier in (1, 2, 3, 4, 9, 10):
            expected = WEIGHT_BY_TIER[tier] * 1.0
            self.assertAlmostEqual(
                LightTank("X", tier, "USSR").matchmaking_weight(), expected,
                msg=f"LightTank tier {tier}",
            )

    def test_light_weight_inside_window(self):
        for tier in range(5, 9):
            expected = WEIGHT_BY_TIER[tier] * 1.2
            self.assertAlmostEqual(
                LightTank("X", tier, "USSR").matchmaking_weight(), expected,
                msg=f"LightTank tier {tier}",
            )

    # TankDestroyer: 1.2x nuo 8 lygio, 1.0x kitais atvejais
    def test_td_weight_below_8(self):
        for tier in range(1, 8):
            expected = WEIGHT_BY_TIER[tier] * 1.0
            self.assertAlmostEqual(
                TankDestroyer("X", tier, "USSR").matchmaking_weight(), expected,
                msg=f"TD tier {tier}",
            )

    def test_td_weight_from_8(self):
        for tier in (8, 9, 10):
            expected = WEIGHT_BY_TIER[tier] * 1.2
            self.assertAlmostEqual(
                TankDestroyer("X", tier, "USSR").matchmaking_weight(), expected,
                msg=f"TD tier {tier}",
            )

    # SPG: visada 1.08x
    def test_spg_weight_all_tiers(self):
        for tier in range(1, 11):
            expected = WEIGHT_BY_TIER[tier] * 1.08
            self.assertAlmostEqual(
                SPG("X", tier, "USSR").matchmaking_weight(), expected,
                msg=f"SPG tier {tier}",
            )


class TestTankSerialization(unittest.TestCase):

    def test_to_dict_keys(self):
        t = HeavyTank("Tiger I", 7, "Germany")
        d = t.to_dict()
        self.assertEqual(set(d.keys()), {"name", "tier", "nation", "tank_class"})

    def test_to_dict_values(self):
        t = TankDestroyer("SU-100", 6, "USSR")
        d = t.to_dict()
        self.assertEqual(d["name"], "SU-100")
        self.assertEqual(d["tier"], 6)
        self.assertEqual(d["nation"], "USSR")
        self.assertEqual(d["tank_class"], "TD")

    def test_str_contains_name_and_tier(self):
        t = MediumTank("Panther", 7, "Germany")
        s = str(t)
        self.assertIn("Panther", s)
        self.assertIn("7", s)


if __name__ == "__main__":
    unittest.main()

import unittest

from mini_benchmark.pricing import calculate_cost, load_pricing, resolve_model_name


class PricingTests(unittest.TestCase):
    def test_resolve_alias(self) -> None:
        pricing = load_pricing()
        self.assertEqual(resolve_model_name("gpt-5-mini", pricing), "gpt-5.4-mini")

    def test_calculate_cost(self) -> None:
        usage = {
            "input_tokens": 1_000_000,
            "output_tokens": 100_000,
            "cache_read_tokens": 200_000,
            "cache_write_tokens": 0,
            "request_count": 1,
        }
        cost = calculate_cost("gpt-5.4", usage)
        self.assertEqual(cost["input_cost_usd"], 2.5)
        self.assertEqual(cost["cache_read_cost_usd"], 0.05)
        self.assertEqual(cost["output_cost_usd"], 1.5)
        self.assertEqual(cost["total_cost_usd"], 4.05)


if __name__ == "__main__":
    unittest.main()


import unittest

from mini_benchmark.pricing import calculate_cost, load_pricing, resolve_model_name


class PricingTests(unittest.TestCase):
    def test_resolve_alias(self) -> None:
        pricing = load_pricing()
        self.assertEqual(resolve_model_name("gpt-5-mini", pricing), "gpt-5.4-mini")
        self.assertEqual(resolve_model_name("claude-opus-4.6", pricing), "claude-opus-4.6")

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

    def test_calculate_cost_for_claude_opus_4_6(self) -> None:
        usage = {
            "input_tokens": 1_000_000,
            "output_tokens": 100_000,
            "cache_read_tokens": 200_000,
            "cache_write_tokens": 0,
            "request_count": 1,
        }
        cost = calculate_cost("claude-opus-4.6", usage)
        self.assertEqual(cost["input_cost_usd"], 5.0)
        self.assertEqual(cost["cache_read_cost_usd"], 0.1)
        self.assertEqual(cost["output_cost_usd"], 2.5)
        self.assertEqual(cost["total_cost_usd"], 7.6)


if __name__ == "__main__":
    unittest.main()

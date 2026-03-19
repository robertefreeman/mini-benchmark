import tempfile
import unittest
from pathlib import Path

from mini_benchmark.telemetry import parse_log_dir, parse_log_file


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "sample_copilot.log"


class TelemetryTests(unittest.TestCase):
    def test_parse_log_file(self) -> None:
        usage = parse_log_file(FIXTURE_PATH)
        self.assertEqual(usage["gpt-5.4"]["input_tokens"], 23209)
        self.assertEqual(usage["gpt-5.4"]["output_tokens"], 35)
        self.assertEqual(usage["gpt-5.4"]["cache_read_tokens"], 1536)
        self.assertEqual(usage["gpt-5.4"]["request_count"], 1)

    def test_parse_log_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "process-1.log"
            target.write_text(FIXTURE_PATH.read_text(encoding="utf-8"), encoding="utf-8")
            usage = parse_log_dir(Path(tmpdir))
        self.assertIn("gpt-5.4", usage)


if __name__ == "__main__":
    unittest.main()


"""Regression tests for CSV timestamps; all prices and timestamps are synthetic."""
import datetime as dt
import tempfile
import unittest
from pathlib import Path

from edgeguard_lab import load_market_csv


class CSVChronologyTests(unittest.TestCase):
    def load(self, times):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "synthetic_ohlc.csv"
            rows = ["time,open,high,low,close"]
            rows.extend(f"{stamp},100,102,99,101" for stamp in times)
            path.write_text("\n".join(rows) + "\n", encoding="utf-8")
            return load_market_csv(path)

    def prefix(self):
        start = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)
        return [(start + dt.timedelta(minutes=30 * i)).isoformat() for i in range(38)]

    def test_increasing_instants_accepted_even_when_strings_descend(self):
        times = self.prefix() + [
            "2026-01-02T14:00:00+02:00",  # 12:00 UTC
            "2026-01-02T13:00:00+00:00",  # 13:00 UTC
        ]
        self.assertEqual(len(self.load(times)), 40)

    def test_decreasing_instants_rejected_even_when_strings_ascend(self):
        times = self.prefix() + [
            "2026-01-02T14:00:00+00:00",  # 14:00 UTC
            "2026-01-02T15:00:00+02:00",  # 13:00 UTC
        ]
        with self.assertRaisesRegex(ValueError, "Fechas no ordenadas"):
            self.load(times)

    def test_duplicate_instants_with_different_offsets_rejected(self):
        times = self.prefix() + [
            "2026-01-02T14:00:00+00:00",
            "2026-01-02T16:00:00+02:00",
        ]
        with self.assertRaisesRegex(ValueError, "duplicadas"):
            self.load(times)

    def test_legacy_naive_timestamps_remain_supported(self):
        start = dt.datetime(2026, 1, 1)
        times = [(start + dt.timedelta(hours=i)).isoformat() for i in range(40)]
        self.assertEqual(len(self.load(times)), 40)


if __name__ == "__main__":
    unittest.main()

"""Malformed CSV inputs should fail with actionable row errors, not raw exceptions."""
import tempfile
import unittest
from pathlib import Path

import edgeguard_lab as lab


class IncompleteCsvRowTests(unittest.TestCase):
    def _read(self, row):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "incomplete.csv"
            lines = ["time,open,high,low,close"]
            lines.extend(
                f"2026-01-01T{i:02d}:00:00+00:00,100,102,98,101"
                for i in range(40)
            )
            lines[12] = row  # Data row 12; actual CSV line 13.
            path.write_text("\n".join(lines) + "\n", encoding="utf-8")
            return lab.load_market_csv(path)

    def test_missing_close_reports_row_number(self):
        with self.assertRaisesRegex(ValueError, "Fila CSV 13 inválida"):
            self._read("2026-01-01T11:00:00+00:00,100,102,98")

    def test_missing_timestamp_reports_row_number(self):
        with self.assertRaisesRegex(ValueError, "Fila CSV 13 inválida"):
            self._read(",100,102,98,101")

    def test_missing_open_reports_row_number(self):
        with self.assertRaisesRegex(ValueError, "Fila CSV 13 inválida"):
            self._read("2026-01-01T11:00:00+00:00,,102,98,101")


if __name__ == "__main__":
    unittest.main()

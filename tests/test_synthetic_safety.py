"""Regression checks for EDGEGUARD's synthetic-only safety guarantees."""
import datetime as dt
import tempfile
import unittest
from pathlib import Path

import edgeguard_lab as lab


class SyntheticSafetyTests(unittest.TestCase):
    def test_market_is_deterministic_and_ohlc_consistent(self):
        first = lab.synthetic_market(n=48, seed=17)
        self.assertEqual(first, lab.synthetic_market(n=48, seed=17))
        for bar in first:
            self.assertGreater(bar["low"], 0)
            self.assertLessEqual(bar["low"], min(bar["open"], bar["close"]))
            self.assertGreaterEqual(bar["high"], max(bar["open"], bar["close"]))

    def test_csv_rejects_duplicate_instant_with_different_utc_offset(self):
        start = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)
        rows = []
        for i in range(40):
            stamp = (start + dt.timedelta(hours=i)).isoformat()
            if i == 10:
                # 10:00 +01:00 is the same instant as previous 09:00 UTC.
                stamp = "2026-01-01T10:00:00+01:00"
            rows.append(f"{stamp},100,102,98,101")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "input.csv"
            path.write_text("time,open,high,low,close\n" + "\n".join(rows) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Fechas no ordenadas o duplicadas"):
                lab.load_market_csv(path)

    def test_csv_rejects_nonfinite_price(self):
        start = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)
        rows = []
        for i in range(40):
            close = "NaN" if i == 15 else "101"
            rows.append(f"{(start + dt.timedelta(hours=i)).isoformat()},100,102,98,{close}")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "input.csv"
            path.write_text("time,open,high,low,close\n" + "\n".join(rows) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Fila CSV"):
                lab.load_market_csv(path)

    def test_auditor_rejects_unreconciled_balance(self):
        account = lab.new_account()
        account["balance"] += 100
        report = lab.auditor(account, lab.metrics(account))
        self.assertFalse(report["passed"])
        self.assertIn("Conciliación de cuenta fallida", report["errors"])

    def test_public_report_explicitly_labels_synthetic_simulation(self):
        account = lab.new_account()
        metrics = lab.metrics(account)
        audit = lab.auditor(account, metrics)
        report = lab.writer(account, metrics, audit, {"status": "SIN_CAMBIO"})
        self.assertIn("SIMULACIÓN SOBRE PRECIOS SINTÉTICOS", report)
        self.assertIn("NO ES CUENTA DE BRÓKER", report)


if __name__ == "__main__":
    unittest.main()

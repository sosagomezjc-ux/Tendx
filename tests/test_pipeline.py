import csv, json, tempfile, unittest
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import edgeguard_lab as lab

class TestSystem(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bars=lab.synthetic_market(400)
        cls.account=lab.simulate(cls.bars,400)

    def test_seed_reproducibility(self):
        self.assertEqual(self.bars,lab.synthetic_market(400))
        self.assertNotEqual(self.bars,lab.synthetic_market(400,seed=2))

    def test_ohlc_correctness(self):
        for b in self.bars:
            self.assertGreaterEqual(b['high'],max(b['open'],b['close']))
            self.assertLessEqual(b['low'],min(b['open'],b['close']))

    def test_balances_reconcile(self):
        a=self.account;m=lab.metrics(a); report=lab.auditor(a,m)
        self.assertTrue(report['passed'],report['errors'])
        self.assertAlmostEqual(m['net_realized'],round(a['balance']-lab.INITIAL,2),places=2)

    def test_only_one_position(self):
        self.assertTrue(self.account['open_position'] is None or isinstance(self.account['open_position'],dict))
        for t in self.account['trades']: self.assertGreater(t['exit_bar'],t['entry_bar'])

    def test_risk_per_trade_limited(self):
        for trade in self.account['trades']:
            self.assertLessEqual(trade['planned_risk_cash'],trade['initial_equity']*.00501)

    def test_commission_in_profit(self):
        t=self.account['trades'][0]; direc=1 if t['side']=='BUY' else -1
        expected=direc*(t['exit_fill']-t['entry_fill'])*t['units']-t['entry_fee']-t['exit_fee']
        self.assertAlmostEqual(expected,t['net_pnl'],places=2)

    def test_audit_tamper_detected(self):
        a=json.loads(json.dumps(self.account));a['trades'][0]['net_pnl']+=101
        result=lab.auditor(a,lab.metrics(a))
        self.assertFalse(result['passed'])

    def test_missing_candles_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'x.csv'
            p.write_text('time,open,high,low,close\n2026-01-01,100,90,110,100\n',encoding='utf8')
            with self.assertRaises(ValueError): lab.load_market_csv(p)

    def test_synthetic_session_daily_count(self):
        self.assertLessEqual(self.account['trades_today'],self.account['config']['max_new_trades_per_day'])

    def test_bar_clock_advances(self):
        a=lab.simulate(self.bars,150)
        lab.process_bar(a,self.bars,150)
        self.assertEqual(a['bars_processed'],151)
        self.assertEqual(a['run_count'],(150-(lab.POLICY['slow']+2))+1)

    def test_no_entry_at_total_loss_limit(self):
        a=lab.new_account();i=a['bars_processed'];a['balance']=lab.INITIAL*.91
        a['daily_anchor']=a['balance'];a['snapshots']=[]
        lab.process_bar(a,self.bars,i)
        self.assertIsNone(a['open_position'])

    def test_publish_content_tells_truth(self):
        a=self.account;m=lab.metrics(a);aud=lab.auditor(a,m)
        post=lab.writer(a,m,aud,{'status':'SIN_CAMBIO'})
        self.assertIn('SINTÉTICOS',post)
        self.assertIn('NO ES CUENTA DE BRÓKER',post)

    def test_trade_conservation_with_mark(self):
        a=lab.new_account(); a['open_position']={'side':'BUY','units':1.,'entry_fill':100,
          'entry_fee':1.5}
        a['balance']=10000.
        self.assertLess(lab.mark_equity(a,100.),10000.)

    def test_walk_forward_never_updates_config(self):
        before=dict(self.account['config']); report=lab.researcher(self.bars)
        self.assertIn(report['status'],['SIN_CAMBIO','SUGERENCIA_SIN_AUTOAPLICACION','DATOS_INSUFICIENTES'])
        self.assertEqual(self.account['config'],before)

if __name__=='__main__':unittest.main()

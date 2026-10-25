#!/usr/bin/env python3
"""EDGEGUARD Autonomous Lab: transparent synthetic paper-trading + audit + reporting.
Only standard library. No brokerage account access or financial advice.
"""
from __future__ import annotations
import argparse, csv, datetime as dt, hashlib, html, json, math, random
from pathlib import Path

BASE = Path(__file__).resolve().parent
STATE = BASE / 'state/account.json'
OUT = BASE / 'results'
SITE = BASE / 'site'
INITIAL = 10000.0
SEED = 20261025
POLICY = {'fast': 7, 'slow': 24, 'risk_fraction': .005, 'daily_loss_limit': .03,
          'total_loss_limit': .08, 'max_new_trades_per_day': 2,
          'max_leverage': 2.0, 'reward_multiple': 1.7, 'max_bars_held': 9,
          'spread_bps': 3.0, 'slippage_bps': 2.0, 'commission_bps': 1.0}


def dump(path: Path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    target = path.with_suffix(path.suffix+'.tmp')
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf8')
    target.replace(path)


def synthetic_market(n=1200, seed=SEED):
    """Generated OHLC; not market quotes and not broker data."""
    rng = random.Random(seed)
    bars, p = [], 2075.0
    start = dt.datetime(2026, 1, 5, tzinfo=dt.timezone.utc)
    for i in range(n):
        regime = (i // 85) % 4
        drift = [0.0005, -0.0003, 0.0000, 0.0004][regime]
        vol = [0.0055, 0.0075, 0.011, 0.006][regime]
        op = p
        shock = rng.gauss(drift,vol) + (-.026 if i % 173 == 71 else 0)
        close = max(25, op*(1+shock))
        wick = abs(rng.gauss(0, vol*.45)) + .0007
        hi = max(op, close)*(1+wick)
        low = min(op, close)*(1-wick)
        bars.append({'index':i, 'time':(start+dt.timedelta(hours=4*i)).isoformat(),
                     'open':round(op,5),'high':round(hi,5),'low':round(low,5),'close':round(close,5)})
        p = close
    return bars


def load_market_csv(path):
    """User-supplied OHLC: input has no verified provenance; explicitly labeled."""
    rows=[]
    timestamps=[]
    with open(path, newline='', encoding='utf-8-sig') as f:
        for i,r in enumerate(csv.DictReader(f)):
            try:
                row={'index':i, 'time':r['time'], 'open':float(r['open']), 'high':float(r['high']),
                     'low':float(r['low']), 'close':float(r['close'])}
                if not all(math.isfinite(row[k]) and row[k]>0 for k in ['open','high','low','close']): raise ValueError('no finite price')
                if row['low']>min(row['open'],row['close']) or row['high']<max(row['open'],row['close']): raise ValueError('OHLC inconsistent')
                timestamp=dt.datetime.fromisoformat(row['time'].replace('Z','+00:00'))
                # Preserve legacy naive CSV timestamps by treating them as UTC.
                # Compare actual instants, not strings: ISO offsets can sort differently.
                if timestamp.tzinfo is None:
                    timestamp=timestamp.replace(tzinfo=dt.timezone.utc)
                timestamps.append(timestamp.astimezone(dt.timezone.utc))
            except (KeyError, ValueError, TypeError, AttributeError) as exc:
                raise ValueError(f'Fila CSV {i+2} inválida: {exc}') from exc
            rows.append(row)
    if len(rows)<40: raise ValueError('Se necesitan al menos 40 barras OHLC.')
    if any(timestamps[i]<=timestamps[i-1] for i in range(1,len(timestamps))):
        raise ValueError('Fechas no ordenadas o duplicadas.')
    return rows


def new_account():
    return {'schema': 'edgeguard.paper.v1', 'origin': 'SYNTHETIC_GENERATED',
            'equity_currency': 'USD_SIM', 'symbol':'XAUUSD-SIM', 'balance': INITIAL, 'initial_balance':INITIAL,
            'bars_processed': POLICY['slow']+2, 'open_position':None, 'daily_anchor':INITIAL,
            'daily_index':None, 'trades_today':0, 'trades':[], 'snapshots':[], 'events':[],
            'config':dict(POLICY), 'run_count':0}


def _sma(xs,n): return sum(xs[-n:])/n

def _atr(history, n=14):
    if len(history)<n+1: return history[-1]['close']*.008
    vals=[]
    for i in range(len(history)-n,len(history)):
        b=history[i]; prev=history[i-1]['close']
        vals.append(max(b['high']-b['low'],abs(b['high']-prev),abs(b['low']-prev)))
    return sum(vals)/len(vals)


def _signal(history,cfg):
    # Only COMPLETED bars, excludes the current bar; no look-ahead.
    if len(history)<cfg['slow']+2: return None
    close=[b['close'] for b in history]
    fast=_sma(close,cfg['fast']); slow=_sma(close,cfg['slow'])
    prior=close[-1]; threshold=.0008
    if fast>slow*(1+threshold) and prior>fast: return 'BUY'
    if fast<slow*(1-threshold) and prior<fast: return 'SELL'
    return None


def _price_with_cost(price, direction, side, cfg):
    # direction +1 long/-1 short; entry side +1 and exit side -1.
    adversarial = direction*side
    bps = cfg['spread_bps']/2 + cfg['slippage_bps']
    return price * (1+adversarial*bps/10000)


def mark_equity(account,price):
    pos=account['open_position']
    if not pos: return account['balance']
    direction=1 if pos['side']=='BUY' else -1
    mark=_price_with_cost(price,direction,-1,account['config'])
    close_fee=abs(pos['units']*mark)*account['config']['commission_bps']/10000
    return account['balance']+direction*(mark-pos['entry_fill'])*pos['units']-close_fee-pos['entry_fee']


def _close(account, bar, price, reason):
    p=account['open_position']; cfg=account['config']; direction=1 if p['side']=='BUY' else -1
    fill=_price_with_cost(price,direction,-1,cfg)
    exit_fee=abs(p['units']*fill)*cfg['commission_bps']/10000
    pnl=direction*(fill-p['entry_fill'])*p['units']-exit_fee-p['entry_fee']
    # Entry fee included only at close, ensuring realized PnL reconciles.
    account['balance']=round(account['balance']+pnl,8)
    trade={**p, 'exit_bar':bar['index'], 'exit_time':bar['time'],'exit_fill':round(fill,6),
           'exit_fee':round(exit_fee,8),'exit_reason':reason,'net_pnl':round(pnl,8),
           'balance_after':round(account['balance'],8)}
    account['trades'].append(trade)
    account['open_position']=None
    account['events'].append({'bar':bar['index'],'type':'CLOSE','reason':reason,'pnl':trade['net_pnl']})


def process_bar(account, bars, i):
    bar=bars[i]; cfg=account['config']
    day=i//6  # paper clock: six synthetic 4h bars per simulated day
    if account['daily_index'] != day:
        account['daily_index']=day; account['daily_anchor']=mark_equity(account,bar['open'])
        account['trades_today']=0
    p=account['open_position']
    if p:
        isbuy=p['side']=='BUY'
        stop_hit = bar['low']<=p['stop'] if isbuy else bar['high']>=p['stop']
        tp_hit = bar['high']>=p['take_profit'] if isbuy else bar['low']<=p['take_profit']
        # Conservative same-bar ambiguity: stop wins, never optimistic TP.
        if stop_hit: _close(account,bar,p['stop'],'STOP')
        elif tp_hit: _close(account,bar,p['take_profit'],'TAKE_PROFIT')
        elif i-p['entry_bar'] >= cfg['max_bars_held']: _close(account,bar,bar['close'],'TIME_EXIT')
    # New entry only if flat at bar start. Never enter and exit on the same bar:
    # bar OHLC cannot establish intrabar order sequence for new positions.
    if p is None and account['open_position'] is None:
        signal=_signal(bars[:i],cfg)
        current_equity=mark_equity(account,bar['open'])
        headroom_day=current_equity - account['daily_anchor']*(1-cfg['daily_loss_limit'])
        headroom_total=current_equity - INITIAL*(1-cfg['total_loss_limit'])
        if signal and account['trades_today'] < cfg['max_new_trades_per_day'] and headroom_day>0 and headroom_total>0:
            direction=1 if signal=='BUY' else -1
            entry=_price_with_cost(bar['open'],direction,1,cfg)
            distance=max(_atr(bars[:i])*1.1, entry*.002)
            stop=entry-direction*distance
            tp=entry+direction*distance*cfg['reward_multiple']
            max_per_unit = distance+(entry+abs(stop))*(cfg['spread_bps']/2+cfg['slippage_bps']+cfg['commission_bps'])/10000
            cash_risk=min(current_equity*cfg['risk_fraction'],headroom_day*.7,headroom_total*.7)
            units=min(cash_risk/max_per_unit, (current_equity*cfg['max_leverage'])/entry)
            if units>0.001:
                fee=abs(units*entry)*cfg['commission_bps']/10000
                account['open_position']={'entry_bar':i,'entry_time':bar['time'],'side':signal,
                    'entry_fill':round(entry,6),'entry_fee':round(fee,8),
                    'units':round(units,8),'stop':round(stop,6),'take_profit':round(tp,6),
                    'planned_risk_cash':round(cash_risk,6),'initial_equity':round(current_equity,6)}
                account['trades_today']+=1
                account['events'].append({'bar':i,'type':'OPEN','side':signal,'planned_risk_cash':round(cash_risk,5)})
    eq=mark_equity(account,bar['close'])
    account['snapshots'].append({'index':i, 'time':bar['time'],'balance':round(account['balance'],4),
                                 'equity':round(eq,4),'price':bar['close']})
    account['bars_processed']=i+1
    account['run_count']+=1
    account['events']=account['events'][-500:]
    account['snapshots']=account['snapshots'][-1200:]
    return account


def simulate(bars, upto=None, cfg=None):
    a=new_account()
    if cfg: a['config'].update(cfg)
    upto = upto or len(bars)
    for i in range(a['bars_processed'],min(upto,len(bars))): process_bar(a,bars,i)
    return a


def metrics(a):
    t=a['trades']; pnl=[x['net_pnl'] for x in t]
    wins=[x for x in pnl if x>0]; losses=[x for x in pnl if x<0]
    peak=INITIAL; dd=0
    for tr in t:
        peak=max(peak,tr['balance_after'])
        dd=max(dd,(peak-tr['balance_after'])/peak*100)
    score=sum(pnl)
    return {'trades':len(t),'wins':len(wins),'losses':len(losses),
       'net_realized':round(score,2),'balance':round(a['balance'],2),
       'equity_mark':round(a['snapshots'][-1]['equity'],2) if a['snapshots'] else INITIAL,
       'win_rate_pct':round(len(wins)/len(pnl)*100,2) if pnl else None,
       'profit_factor':round(sum(wins)/abs(sum(losses)),3) if losses else None,
       'max_closed_balance_drawdown_pct':round(dd,2),
       'open_position':a['open_position'] is not None}


def auditor(a,m):
    issues=[]
    if a['schema']!='edgeguard.paper.v1': issues.append('Esquema desconocido')
    prev=INITIAL
    for j,t in enumerate(a['trades']):
        side=1 if t['side']=='BUY' else -1
        expected=side*(t['exit_fill']-t['entry_fill'])*t['units']-t['entry_fee']-t['exit_fee']
        if abs(expected-t['net_pnl'])>.03: issues.append(f'P&L inconsistente orden {j}')
        prev+=t['net_pnl']
        if abs(prev-t['balance_after'])>.03: issues.append(f'Saldo inconsistente orden {j}')
        if t['planned_risk_cash']<=0 or t['planned_risk_cash']>t['initial_equity']*.0051:
            issues.append(f'Riesgo inicial excesivo en orden {j}')
        if t['exit_bar']<=t['entry_bar']: issues.append(f'Orden cronológica invalida en operación {j}')
    if abs(a['balance']-prev)>.03 or abs(m['net_realized']-round(a['balance']-INITIAL,2))>.03:
        issues.append('Conciliación de cuenta fallida')
    if any(not math.isfinite(s['equity']) or s['equity']<0 for s in a['snapshots']):
        issues.append('Equity imposible')
    if len(a['trades']) != m['trades']: issues.append('Número de operaciones inconsistente')
    return {'passed':not issues,'errors':issues,'checks':['conciliación de P&L','límites de riesgo de entrada',
      'coherencia temporal','balance y equity','integridad de operaciones'],
      'origin':a['origin'], 'timestamp_utc':dt.datetime.now(dt.timezone.utc).isoformat()}


def researcher(bars):
    """Champion/challenger offline, reports candidates only; never trades live or edits code."""
    if len(bars)<180:
        return {'status':'DATOS_INSUFICIENTES','proposed':None,
         'reason':'Sin muestra suficiente; no se ajusta estrategia.',
         'holdout_note':'No se usan barras futuras. No se extrapolan resultados.', 'trials':[]}
    split=int(len(bars)*.65)
    versions=[(7,24),(5,22),(10,32),(8,28)]
    trials=[]
    for fast,slow in versions:
        cfg={'fast':fast,'slow':slow}
        # Isolated evaluation: train/test segment, indicators get warmup bars only.
        train=simulate(bars[:split],cfg=cfg)
        test=simulate(bars[split-40:],cfg=cfg)
        te=metrics(test); tr=metrics(train)
        trials.append({'fast':fast,'slow':slow,'train':{'trades':tr['trades'],'net':tr['net_realized']},
             'holdout':{'trades':te['trades'],'net':te['net_realized'], 'dd_pct':te['max_closed_balance_drawdown_pct']}})
    baseline=next(t for t in trials if t['fast']==7 and t['slow']==24)
    eligible=[t for t in trials if t['holdout']['trades']>=8 and t['train']['trades']>=8]
    eligible.sort(key=lambda q:(q['holdout']['net']-q['holdout']['dd_pct']*25),reverse=True)
    best=eligible[0] if eligible else None
    can_propose=best and (best['fast'],best['slow'])!=(7,24) and best['holdout']['net']>baseline['holdout']['net']+100 and best['holdout']['dd_pct']<=baseline['holdout']['dd_pct']
    return {'status':'SUGERENCIA_SIN_AUTOAPLICACION' if can_propose else 'SIN_CAMBIO',
     'proposed':{'fast':best['fast'],'slow':best['slow']} if can_propose else None,
     'reason':'Las variantes se investigan offline. No son evidencia de ventaja futura; no se modifica la estrategia activa.',
     'holdout_note':'El test usa datos sintéticos no independientes económicamente de sus regímenes. No extrapolar.',
     'trials':trials}


def sha(payload): return hashlib.sha256(json.dumps(payload,sort_keys=True,ensure_ascii=False).encode('utf8')).hexdigest()


def writer(a,m,audit,research):
    now=dt.datetime.now(dt.timezone.utc).strftime('%d/%m/%Y %H:%M UTC')
    origin_warning=('SIMULACIÓN SOBRE PRECIOS SINTÉTICOS. NO ES CUENTA DE BRÓKER.' if a['origin']=='SYNTHETIC_GENERATED' else 'BACKTEST CON HISTORIAL OHLC APORTADO POR USUARIO, FUENTE NO VERIFICADA. NO SON ÓRDENES DE BRÓKER.')
    pnl=f"{m['net_realized']:+,.2f}"
    return (f"# Informe público EDGEGUARD — {now}\n\n"
      f"**{origin_warning}**\n\n"
      f"Agente operador: {m['trades']} operaciones simuladas cerradas; resultado realizado {pnl} USD_SIM. "
      f"Balance simulado {m['balance']:,.2f} USD_SIM. "
      f"Drawdown máximo de balance cerrado {m['max_closed_balance_drawdown_pct']} %. "
      f"Tasa de acierto {str(m['win_rate_pct'])+' %' if m['win_rate_pct'] is not None else 'n/d'}.\n\n"
      f"Agente auditor: {'APROBADO' if audit['passed'] else 'RECHAZADO'}. "
      f"Comprobaciones: {', '.join(audit['checks'])}.\n\n"
      f"Agente investigador: {research['status'].replace('_',' ').lower()}. "
      "La estrategia operativa no se modifica automáticamente.\n\n"
      "No es asesoramiento financiero ni una demostración de rentabilidad futura. "
      "La simulación incorpora spread, comisiones y deslizamiento aproximados, "
      "pero no reproduce todos los costes ni la microestructura de un mercado real.\n")


def render_site(a,m,audit,research,post):
    esc=html.escape
    hist=a['snapshots'][-220:]
    data=[s['equity'] for s in hist] or [INITIAL]
    mn=min(data); mx=max(data); width=900; height=235
    coords=[]
    for i,val in enumerate(data):
        x=round(i*width/max(1,len(data)-1),2)
        y=round(10+(mx-val)/max(.001,mx-mn)*(height-20),2)
        coords.append(f'{x},{y}')
    path=' '.join(coords)
    gains='+' if m['net_realized']>=0 else ''
    if m['trades']:
        rows='\n'.join('<tr><td>'+esc(t['exit_time'][:16])+'</td><td>'+esc(t['side'])+'</td><td>'+esc(t['exit_reason'])+'</td><td class="num">'+f"{t['net_pnl']:+.2f}"+'</td></tr>' for t in a['trades'][-20:][::-1])
    else: rows='<tr><td colspan="4">Todavía no hay operaciones cerradas</td></tr>'
    latest_post=esc(post).replace('\n','<br>')
    banner=('PRECIOS 100 % SINTÉTICOS' if a['origin']=='SYNTHETIC_GENERATED' else 'HISTÓRICO APORTADO SIN VERIFICAR')
    badge='AUDITORÍA OK' if audit['passed'] else 'AUDITORÍA FALLIDA'
    return f'''<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>EDGEGUARD Autonomous Lab · Demo</title><style>
:root{{--bg:#0a1221;--card:#121e31;--txt:#eff5ff;--dim:#9eafc6;--line:#26354b;--aqua:#5ce4cd;--amber:#ffd37d}}*{{box-sizing:border-box}}body{{font-family:Inter,system-ui,-apple-system,Segoe UI,sans-serif;background:var(--bg);color:var(--txt);margin:0}}.wrap{{max-width:1120px;margin:auto;padding:30px 20px 70px}}.top{{display:flex;align-items:center;justify-content:space-between;gap:10px;flex-wrap:wrap}}.logo{{font-weight:850;letter-spacing:.02em;font-size:23px}}.logo em{{font-style:normal;color:var(--aqua)}}.tag{{font-size:12px;display:inline-block;padding:6px 10px;border-radius:15px;background:#17394a;color:#83eedb;font-weight:700}}.warning{{border:1px solid #d19a38;background:#392b20;border-radius:12px;padding:14px 17px;color:#ffe2aa;margin-top:24px;font-weight:700}}h1{{font-size:clamp(26px,4vw,41px);line-height:1.1;max-width:730px;margin:25px 0 10px}}p{{color:var(--dim);line-height:1.6}}.muted{{color:var(--dim)}}.grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:13px;margin:24px 0}}.panel{{border:1px solid var(--line);background:var(--card);padding:19px;border-radius:14px}}.k{{color:var(--dim);font-size:12px;text-transform:uppercase;letter-spacing:.06em}}.v{{font-size:25px;font-weight:800;margin-top:9px;font-variant-numeric:tabular-nums}}h2{{font-size:20px;margin:30px 0 12px}}.section{{border:1px solid var(--line);background:var(--card);padding:20px;border-radius:14px}}svg{{width:100%;height:auto}}.axis{{fill:#8092aa;font-size:11px}}table{{width:100%;border-collapse:collapse;text-align:left;font-size:14px}}td,th{{border-bottom:1px solid var(--line);padding:12px 8px}}th{{color:var(--dim)}}.num{{text-align:right;font-variant-numeric:tabular-nums}}.cols{{display:grid;grid-template-columns:1fr 1fr;gap:14px}}.textblock{{font-size:13px;line-height:1.8;color:#d7e1f0}}.mini{{font-size:12px;color:var(--dim)}}a{{color:var(--aqua)}}@media(max-width:780px){{.grid{{grid-template-columns:repeat(2,1fr)}}.cols{{grid-template-columns:1fr}}}}@media(max-width:420px){{.grid{{grid-template-columns:1fr 1fr}}.v{{font-size:21px}}}}</style></head><body><div class="wrap">
<div class="top"><div class="logo">EDGEGUARD <em>AI</em> <span class="muted" style="font-size:13px">AUTONOMOUS LAB</span></div><span class="tag">{badge}</span></div>
<div class="warning">SIMULACIÓN / PAPER TRADING · {banner}. No hay cuenta, bróker, órdenes ni dinero real.</div>
<h1>Agentes que operan, auditan y publican un experimento de trading</h1><p>Demostración tecnológica auditable. Este entorno es una cuenta ficticia y no demuestra una ventaja financiera. Cada ciclo usa una nueva barra sintética y registra el resultado.</p>
<p class="mini">Símbolo ficticio: XAUUSD-SIM · no sigue la cotización real del oro</p><div class="grid"><div class="panel"><div class="k">Saldo simulado</div><div class="v">{m['balance']:,.2f}</div><div class="mini">USD_SIM</div></div><div class="panel"><div class="k">Resultado realizado</div><div class="v">{gains}{m['net_realized']:,.2f}</div><div class="mini">USD_SIM</div></div><div class="panel"><div class="k">Operaciones cerradas</div><div class="v">{m['trades']}</div><div class="mini">Simulación, no bróker</div></div><div class="panel"><div class="k">Drawdown balance</div><div class="v">{m['max_closed_balance_drawdown_pct']:.2f}%</div><div class="mini">No incluye DD intrabar</div></div></div>
<h2>Evolución de la equity simulada</h2><div class="section"><svg viewBox="0 0 920 255" role="img" aria-label="Evolución de equity de la cuenta ficticia"><line x1="10" y1="20" x2="910" y2="20" stroke="#253a4e"/><line x1="10" y1="245" x2="910" y2="245" stroke="#253a4e"/><polyline points="{path}" fill="none" stroke="#5ce4cd" stroke-width="2.4" transform="translate(10 0)"/><text x="10" y="14" class="axis">{mx:,.0f} USD_SIM</text><text x="10" y="252" class="axis">{mn:,.0f}</text></svg><div class="mini">Últimas {len(hist)} barras ficticias · Balance realizado ≠ equity marcada · Costes simulados</div></div>
<div class="cols"><section><h2>Últimas operaciones simuladas</h2><div class="section"><table><thead><tr><th>Cierre simulado</th><th>Lado</th><th>Salida</th><th class="num">P&L</th></tr></thead><tbody>{rows}</tbody></table></div></section>
<section><h2>Agentes autónomos</h2><div class="section"><p><b>01 Operador:</b> abre/cierra posiciones de papel bajo reglas fijas.</p><p><b>02 Auditor:</b> recalcula cada operación y detiene publicaciones ante errores.</p><p><b>03 Investigador:</b> compara variantes offline; jamás optimiza las operaciones reales.</p><p><b>04 Redactor:</b> construye informe y borrador de difusión con fuentes y advertencias.</p><div class="mini">Estrategia actual: SMA {a['config']['fast']}/{a['config']['slow']}. Propuesta de investigación: {research['status']}. No se ejecuta código modificado automáticamente.</div></div></section></div>
<h2>Último parte público</h2><div class="section textblock">{latest_post}</div>
<p class="mini">Origen: {esc(a['origin'])}. Barra sintética procesada: {a['bars_processed']}. Última actualización: {dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}. No son rendimientos verificables de mercado.</p></div></body></html>'''


def release(a,bars):
    m=metrics(a); audit=auditor(a,m)
    if not audit['passed']:
        dump(OUT/'qa_failed.json',audit)
        raise RuntimeError('Auditoría fallida: se cancela la publicación y el guardado del estado.')
    research=researcher(bars[:a['bars_processed']])
    post=writer(a,m,audit,research)
    pub={'kind':'SIMULATION_SYNTHETIC_NOT_BROKER' if a['origin']=='SYNTHETIC_GENERATED' else 'USER_IMPORTED_OHLC_UNVERIFIED_BACKTEST','results':m, 'audit':audit,
         'research':research,'processed_bars':a['bars_processed'],
         'policy_sha256':sha(a['config']), 'ledger_sha256':sha(a['trades'])}
    SITE.mkdir(parents=True,exist_ok=True)
    (SITE/'index.html').write_text(render_site(a,m,audit,research,post),encoding='utf8')
    (SITE/'latest_post.md').write_text(post,encoding='utf8')
    dump(SITE/'results.json',pub)
    dump(OUT/'audit.json',audit)
    dump(OUT/'research.json',research)
    dump(OUT/'trades.json',a['trades'])
    dump(STATE,a)
    (OUT/'BORRADOR_PUBLICACION.md').write_text(post,encoding='utf8')
    return pub


def main():
    parser=argparse.ArgumentParser(description='EDGEGUARD Autonomous Lab · SOLO simulación')
    parser.add_argument('command',choices=['demo','cycle','audit','research'])
    parser.add_argument('--bars',type=int,default=300,help='Número de barras simuladas para demo')
    parser.add_argument('--input-csv',type=str,default=None,help='CSV OHLC aportado manualmente; fuente sin verificar')
    args=parser.parse_args()
    bars=load_market_csv(args.input_csv) if args.input_csv else synthetic_market()
    if args.command=='demo':
        if args.bars < 40 or args.bars > len(bars): parser.error('Barras inválidas')
        a=simulate(bars,args.bars)
        if args.input_csv: a['origin']='HISTORICAL_OHLC_UPLOADED_UNVERIFIED'
        pub=release(a,bars)
    else:
        if not STATE.exists(): raise SystemExit('Primero ejecuta: python edgeguard_lab.py demo')
        a=json.loads(STATE.read_text(encoding='utf8'))
        if (a['origin']=='SYNTHETIC_GENERATED') != (args.input_csv is None):
            raise SystemExit('Origen de datos diferente al inicial. Es obligatorio mantener la misma fuente para continuar el expediente.')
        if args.command=='cycle':
            if a['bars_processed']>=len(bars): raise SystemExit('Se agotaron las barras: ampliar proveedor de datos autorizado.')
            process_bar(a,bars,a['bars_processed'])
            pub=release(a,bars)
        elif args.command=='audit':
            m=metrics(a); pub={'audit':auditor(a,m),'results':m}
            if not pub['audit']['passed']: raise SystemExit('Auditoría fallida')
        else: pub={'research':researcher(bars)}
    print(json.dumps(pub,ensure_ascii=False,indent=2)[:2500])

if __name__=='__main__': main()

#!/usr/bin/env python3
"""Optional LLM agents. Never control execution, publication or audit verdicts.
Uses OpenAI Responses API when API key supplied; otherwise leaves deterministic workflow intact.
"""
from __future__ import annotations
import datetime as dt, json, os, urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def ask_agent(role: str, metrics: dict) -> str:
    key=os.environ.get('OPENAI_API_KEY','')
    if not key: raise RuntimeError('Sin OPENAI_API_KEY: análisis de lenguaje omitido (modo 0 €).')
    instructions=("Eres el agente editorial de EDGEGUARD AI. "
      "Todo el conjunto es una simulación de operaciones de papel con precios sintéticos, NO un broker. "
      "No inventes datos, testimonios, estrategias rentables, usuarios ni resultados reales. "
      "No emitas consejos concretos de inversión, señales ni promesas. "
      "Usa únicamente las estadísticas recibidas. Dos párrafos en español, máximo 110 palabras. "
      "Si hay pérdidas, decláralas claramente. "
      f"Tu función es {role}. No puedes cambiar reglas, enviar órdenes ni publicar directamente.")
    request={'model':os.environ.get('EDGEGUARD_LLM_MODEL','gpt-4.1-mini'),
             'instructions':instructions,
             'input':json.dumps({'role':role,'fact_checkable_statistics':metrics},ensure_ascii=False),
             'max_output_tokens':320}
    http=urllib.request.Request('https://api.openai.com/v1/responses',
          data=json.dumps(request).encode('utf-8'),headers={'Authorization':f'Bearer {key}',
          'Content-Type':'application/json'},method='POST')
    with urllib.request.urlopen(http,timeout=40) as response:
        data=json.load(response)
    chunks=[c.get('text','') for output in data.get('output',[]) for c in output.get('content',[])
            if c.get('type')=='output_text']
    final='\n'.join(chunks).strip()
    if not final: raise RuntimeError('La API no devolvió texto utilizable.')
    return final

def run():
    p=ROOT/'site/results.json'
    if not p.exists(): raise SystemExit('Primero ejecuta la simulación.')
    data=json.loads(p.read_text())
    if not data['audit']['passed']: raise SystemExit('La auditoría no está aprobada; no se consulta el modelo.')
    public={'kind':data['kind'],'statistics':data['results'],'audit_passed':True}
    drafts=[]
    for role in ['analista de disciplina', 'redactor de contenido educativo']:
        try: drafts.append('### '+role+'\n\n'+ask_agent(role,public))
        except Exception as e:
            drafts.append('### '+role+'\n\nSin borrador generado: '+str(e).split(':')[0])
    out='''# BORRADORES IA · REQUIEREN REVISIÓN

SIMULACIÓN, NO RESULTADOS DE BRÓKER. No se publican automáticamente en redes sociales.

'''+ '\n\n'.join(drafts)+'\n'
    (ROOT/'results/IA_BORRADORES_PENDIENTES.md').write_text(out,encoding='utf-8')
    print('Borradores guardados; ninguna publicación social automática.')

if __name__=='__main__': run()

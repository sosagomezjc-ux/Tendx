# EDGEGUARD AI — Autonomous Lab

**Laboratorio experimental de trading en papel, con precios 100 % sintéticos.**
No es una cuenta de bróker ni muestra operaciones reales, no genera señales de inversión y no demuestra rentabilidad.

## Componentes

- Operador simulado: `edgeguard_lab.py`.
- Auditor de P&L, riesgos y consistencia.
- Investigador: evalúa variantes aisladas sin instalar automáticamente cambios.
- Redactor: genera la web y un borrador transparente; el módulo LLM es opcional.
- Supervisor: GitHub Actions comprueba el estado cada cinco minutos (cron no garantiza puntualidad).

## Ejecutar y comprobar

```bash
python -m unittest discover -s tests -v
python edgeguard_lab.py audit
```

GitHub Actions ejecuta las pruebas automáticamente al desplegar el código.
El laboratorio avanza una barra **ficticia** cuatro veces al día y publica los datos calculados dentro de `site/`.
El healthcheck de cinco minutos **no ejecuta operaciones**.

El sitio público con GitHub Pages necesita habilitar **Settings → Pages → Build and deployment → Source: GitHub Actions** y después definir la variable `ENABLE_PAGES=true`. No hay conexión con MT5 ni agentes de órdenes reales.

## Seguridad

No introducir claves ni historiales de clientes. No cambiar parámetros de trading o código en producción sin revisión independiente. Si el auditor detecta inconsistencias, se interrumpe la publicación.

Más detalles en [`docs/ACTIVACION.md`](docs/ACTIVACION.md) y [`docs/INTEGRACION_MT5.md`](docs/INTEGRACION_MT5.md).

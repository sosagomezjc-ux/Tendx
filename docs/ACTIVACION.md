# Activación sin pagar por más aplicaciones

1. Crear repositorio GitHub vacío (público si se desea usar Pages con el plan gratuito).
2. Subir el proyecto completo, incluyendo `.github/workflows/lab-24h.yml`. No subir claves ni historiales privados.
3. Abrir Actions > EDGEGUARD Autonomous Lab > Run workflow. Verificar resultado verde (los tests, la simulación y la auditoría deben aprobar).
4. La programación existente corre 4 veces al día (01:23, 07:23, 13:23, 19:23 UTC). La programación puede retrasarse.
5. Si se quiere web accesible por terceros, Settings > Pages > Source: GitHub Actions, y añadir variable de repositorio `ENABLE_PAGES` con valor `true` en Settings > Secrets and variables > Actions > Variables. Repetir Run workflow. La URL la proporciona GitHub; no se inventa.
6. Para añadir comentarios escritos por un LLM: crear secreto `OPENAI_API_KEY` y variable `USE_LLM_DRAFTS=true`, con presupuesto API controlado. El borrador no se publica automáticamente.
7. Detener la automatización: desactivar el workflow programado desde Actions (o borrar el cron). No se abren cuentas ni órdenes reales.

## Control de costes
- Python y reglas deterministas: 0 € en API.
- GitHub Actions/Pages: sujeto a límites de cada plan. No contratar VPS para esta simulación.
- La API de IA es opcional y de pago por uso.
- No usar datos o identidades de clientes dentro del repo público.

## Necesario para una cuenta demo MT5 real
El titular debe abrir y autorizar la cuenta demo con su bróker y conectar el terminal MT5 en un entorno compatible. No se debe simular esa creación ni almacenar contraseñas en este repositorio. GitHub Actions no dispone del terminal y no puede ejecutar órdenes por sí solo.

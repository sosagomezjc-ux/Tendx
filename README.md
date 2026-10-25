# EDGEGUARD AI — Autonomous Lab v0.3

**Estado:** simulador verificable funcionando localmente. No hay cuenta demo real de MetaTrader creada, no hay transacciones de bróker, no hay clientes ni publicaciones en redes hechas desde este chat.

## Qué hace la cadena autónoma

1. **Operador:** crea y actualiza una cuenta de papel de 10.000 USD_SIM, a partir de barras OHLC **sintéticas** de precio. Ejecuta órdenes solo en la simulación con spread, slippage y comisión aproximados.
2. **Auditor independiente:** recalcula P&L y saldo de cada operación, verifica riesgo de entrada, tiempos y consistencia. Si no aprueba, aborta el guardado y la publicación.
3. **Investigador:** compara versiones de la estrategia utilizando una partición cronológica. No altera el código ni la estrategia de producción sin una validación independiente.
4. **Redactor:** produce informe y web públicos que identifican claramente la simulación. Un agente LLM adicional puede preparar análisis y borradores cuando se configure una API key, pero no cambia cifras ni publica en redes directamente.
5. **Supervisor automático:** ejecuta pruebas antes de cada ciclo y puede repetirlas de forma programada usando GitHub Actions cuando se conecte un repositorio.

**Aviso:** Los resultados iniciales de la estrategia son **negativos** en los datos sintéticos. Esto no es un error de interfaz: la honestidad de las publicaciones es un requisito. Ninguna simulación certifica beneficios futuros. Una operativa demo de broker requerirá abrir y autorizar una cuenta demo en un terminal externo, verificar reglas y pasar pruebas específicas antes de permitir órdenes reales de demostración.

## Ejecutar en un ordenador

Con Python 3.10+ y sin instalar bibliotecas:

```bash
python -m unittest discover -s tests -v
python edgeguard_lab.py demo --bars 80
```

Abrir `site/index.html` con Chrome. Para una nueva ronda:

```bash
python edgeguard_lab.py cycle
python edgeguard_lab.py audit
```

Los archivos producidos están en `state/`, `site/` y `results/`. `site/index.html` es una página autónoma. Nunca contiene credenciales ni contraseñas.

## Automatizar 24/7 con pocas aplicaciones

Una sola plataforma externa: **GitHub**. Crea un repositorio nuevo y sube estos archivos (sin compartir claves); en la pestaña Actions activa `lab-24h.yml`. Se ejecutará 4 veces al día y también puede activarse manualmente. Para publicar automáticamente la web **del propio proyecto**, habilita Settings > Pages > Source: GitHub Actions y configura la variable de repositorio `ENABLE_PAGES=true`. La programación puede retrasarse o saltarse ciclos; no es infraestructura de baja latencia ni un terminal MT5 online permanente.

Para redacción opcional mediante IA: en GitHub crea un secreto `OPENAI_API_KEY`, define `USE_LLM_DRAFTS=true`, establece límites de gasto en tu proyecto de API. Se guardarán `results/IA_BORRADORES_PENDIENTES.md`, **no** se publicarán automáticamente como opiniones o testimonios. Sin API key, los 4 roles deterministas siguen operando con coste de modelo 0.

**GitHub Pages requiere repo público en plan GitHub Free**. El repositorio y los resultados de simulación serán visibles para terceros. No incluir información de clientes, cuentas, datos personales ni claves. Para repositorios privados y condiciones de uso, revisar el plan y los límites de Actions/Pages.

## Si importas precios OHLC por CSV

Ejemplo de columnas: `time,open,high,low,close` con fechas ISO ordenadas. `python edgeguard_lab.py demo --input-csv MIS_DATOS.csv --bars 360`. Por seguridad los CSV no están autenticados y los resultados se etiquetan como backtest con datos aportados, NO como cuenta bróker. Para continuar, hay que proporcionar **el mismo archivo** en todos los ciclos; no alterarlo durante el experimento.

## Restricciones esenciales

- No existe envío automático de órdenes a un bróker, ni cuenta demo externa, ni señales rentables demostradas.
- El simulador usa barras de 4h **inventadas**; una barra por ciclo programado no representa seis horas reales de mercado ni es backtest válido para predecir precios.
- Los límites simulados son una política de ejemplo, **no** reglas de ninguna firma de fondeo.
- El motor de simulación registra pérdidas, comisiones y drawdown, pero no reproduce garantías, ejecuciones parciales, gaps reales o series de ticks.
- Un LLM jamás valida aritmética ni aprueba cambios de trading. Propuestas de mejora quedan en cuarentena para validación humana si conectan con dinero o una cuenta externa.
- Publicación automática limitada a nuestro sitio, con avisos honestos. Las redes sociales requieren conexión y autorización de cuentas.

## Documentos
- `docs/ACTIVACION.md`: pasos mínimos para activar GitHub Actions.
- `docs/CRITERIOS_DE_MEJORA.md`: cómo evitar sobreajuste y qué mejora puede aprobarse automáticamente.
- `docs/INTEGRACION_MT5.md`: siguiente etapa: demo real de un broker, no disponible aún.
- `site/latest_post.md`: primera publicación generada automáticamente.
- `results/audit.json`: prueba reproducible de auditoría.

## Veredicto del ensayo de estrés previo

En 300 velas sintéticas y con la estrategia inalterada, el simulador perdió aproximadamente **800 USD_SIM** y alcanzó el límite máximo de caída del capital simulado del **8 %**. Ese resultado está conservado en `results/ENSAYO_ESTRES_300.json`. **La estrategia NO está aprobada como estrategia rentable.** La cuenta operativa de ejemplo empieza en 80 barras para que pueda observarse el comportamiento del circuito de automatización desde un punto temprano, no para elegir resultados favorables.

## Comprobaciones cada 5 minutos (opcional)

El workflow `.github/workflows/healthcheck-5m.yml` ejecuta pruebas y audita el libro simulado cada 5 minutos (mejor esfuerzo). No genera velas/operaciones ni cambia estrategias; si falla, GitHub muestra un workflow rojo. No se ejecutará hasta que este proyecto se haya subido con autorización de escritura. La programación puede sufrir retrasos. Mantener apagado si no se necesitan comprobaciones tan frecuentes.

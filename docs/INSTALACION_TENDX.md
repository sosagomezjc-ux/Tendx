# Instalación de EDGEGUARD AI en Tendx

Repositorio objetivo: https://github.com/sosagomezjc-ux/Tendx

## Estado actualizado (25-10-2026)

- Se autorizó la instalación GitHub de ChatGPT y se confirmó escritura en `sosagomezjc-ux/Tendx`.
- El repositorio se inicializó con un README, y el despliegue de los archivos del laboratorio está en curso.
- Tras publicar el código, GitHub Actions ejecuta pruebas y auditoría con cada `push` a `main`, además de los ciclos programados.
- GitHub Pages es opcional y requiere activación explícita de `ENABLE_PAGES=true`.

## Verificación después de instalar

1. En `Tendx`, abre la pestaña **Actions** y revisa los flujos de healthcheck y laboratorio.
2. Confirma que el healthcheck supera 14 pruebas y audita la cuenta sintética.
3. Comprueba que `site/results.json` identifica la procedencia `SIMULATION_SYNTHETIC_NOT_BROKER`.
4. Para publicar el sitio, configura Pages con origen GitHub Actions y variable `ENABLE_PAGES=true`.

## Método alternativo, sin permiso para ChatGPT

Con un ordenador y Git instalado:

```bash
# Descargar y descomprimir EDGEGUARD_AI_AGENTES_AUTONOMOS_v03_TENDX.zip
# Abrir una terminal dentro de la carpeta descomprimida y ejecutar:
git init
git branch -M main
git remote add origin https://github.com/sosagomezjc-ux/Tendx.git
git add .
git commit -m "Inicializar EDGEGUARD Autonomous Lab"
git push -u origin main
```

Si el repositorio tiene un README, clona primero el repositorio y copia el contenido del paquete sobre el clon, para preservar el commit existente. No uses `--force` para subirlo.

## Activación después de subir

1. Ve a la pestaña **Actions** del repositorio.
2. Abre el workflow **EDGEGUARD Autonomous Lab** y ejecuta **Run workflow** sobre `main`.
3. Comprueba que las pruebas sean verdes y que se actualicen `state/`, `results/` y `site/`.
4. Para publicar el sitio: **Settings > Pages > Source: GitHub Actions**. En **Settings > Secrets and variables > Actions > Variables**, crea `ENABLE_PAGES=true` y vuelve a ejecutar el workflow.
5. No publiques resultados como operaciones reales: los precios y operaciones del laboratorio son **sintéticos**.
6. No introduzcas contraseñas, credenciales de bróker, datos de clientes ni claves API en archivos versionados. Si se usa la API opcional, guarda `OPENAI_API_KEY` como secreto de Actions.

## Limitaciones

- El laboratorio es de **paper-trading sintético**. No abre cuentas demo de bróker ni envía operaciones MT5.
- GitHub Actions programado 4 veces diarias no constituye un terminal ni conexión continua a datos de mercado.
- No hay autoactualización arbitraria de estrategias, ya que requeriría controles de seguridad y validación de resultados fuera de muestra.

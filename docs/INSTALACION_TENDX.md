# Instalación de EDGEGUARD AI en Tendx

Repositorio objetivo: https://github.com/sosagomezjc-ux/Tendx

## Estado comprobado (25-10-2026)

- Repositorio público existente, pero sin contenido inicial.
- La integración de GitHub para ChatGPT devuelve `403 Resource not accessible by integration` al intentar crear un archivo.
- No se ha desplegado ni activado GitHub Actions o GitHub Pages.
- El paquete sí se ejecuta localmente y pasó 14 pruebas automatizadas.

## Método recomendado: autorizar escritura a ChatGPT

1. En GitHub, abre **Settings > Applications** y revisa las autorizaciones/instalaciones relacionadas con ChatGPT/GitHub. Si la autorización está limitada por repositorio, selecciona `sosagomezjc-ux/Tendx` y concede acceso al contenido del repositorio.
2. Si no aparece la integración, revisa **Settings > Plugins > GitHub** en ChatGPT y vuelve a conectarla con la cuenta correcta. Esta conexión debe permitir operaciones de escritura; no basta con leer repositorios.
3. En `Tendx`, si el repositorio sigue vacío, crea un archivo README desde la pestaña Code (Add file > Create new file, nombre `README.md`), lo que inicializa la rama `main`.
4. Comprueba que la integración pueda crear o actualizar un archivo. Después sube el proyecto completo respetando carpetas, especialmente `.github/workflows/lab-24h.yml`.

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

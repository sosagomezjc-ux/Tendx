# Protocolo de mejora autónoma responsable

## Lo que sí corrige automáticamente el sistema
- Detectar precios OHLC inválidos o fechas duplicadas antes de procesar.
- Conciliar todas las operaciones, comisiones y saldos.
- Detener y rechazar publicación cuando falla una auditoría.
- Comparar variantes como `SMA(5,22)`, `SMA(7,24)` y `SMA(10,32)` en histórico separado cronológicamente.
- Preparar borradores e informes usando únicamente métricas verificadas.

## Lo que NO debe hacer automáticamente
- Editar su propio código operativo en producción sin pruebas y revisión.
- Cambiar parámetros tras elegir el mejor resultado del mismo histórico (sobreajuste).
- Ejecutar operaciones reales o enviar órdenes a cuentas ajenas.
- Publicar afirmaciones sobre rendimientos en bróker cuando son simulaciones.
- Ocultar pérdidas o eliminar operaciones desfavorables para exhibir resultados atractivos.

## Reglas del ciclo de mejoras
1. Generar propuesta en `results/research.json`.
2. Evaluar contra una muestra de prueba cronológica no vista en entrenamiento, con fricciones incluidas.
3. Exigir número significativo de operaciones, drawdown contenido y beneficio neto ajustado por costes, además de estabilidad por periodos. Los resultados sintéticos no bastan.
4. Aplicar automáticamente solo correcciones de calidad de datos y fallos de interfaz que pasen QA; la política financiera queda estable salvo aprobación expresa.
5. Documentar versión, cambios, pruebas, motivos de rechazo y rollback.

**La publicación frecuente de una simulación no demuestra habilidad predictiva ni rentabilidad.** Las pruebas de utilidad comercial requieren participantes reales con consentimiento y una ventaja frente a herramientas existentes.

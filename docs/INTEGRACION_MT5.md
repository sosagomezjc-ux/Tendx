# Etapa MT5 de demostración real — aún no desplegada

El sistema actual crea una **cuenta ficticia de papel en código**, no una cuenta de MetaTrader. Para ejecutar órdenes en una demo auténtica hará falta:

1. Cuenta DEMO creada por el titular según las condiciones del bróker y terminal MT5 accesible en Windows.
2. Conector local que compruebe por programa el valor `account_info().trade_mode` e interrumpa cualquier ejecución cuando no sea `ACCOUNT_TRADE_MODE_DEMO`.
3. Bloqueo por defecto de toda escritura: la activación demo debe configurarse de forma explícita y ser revocable. Jamás reutilizar credenciales de cuentas reales.
4. Servidor/ordenador activo, vigilancia de conexión, horario de negociación, lotajes, márgenes, stop loss y slippage.
5. pruebas en datos demo del bróker con ventanas de mercado, conciliación de órdenes, posición/equity, errores y reconexiones; no confiar solo en P&L simulado.
6. Reglas y autorización para publicar resultados. Distinguir explícitamente demo broker, backtesting, precios sintéticos y resultados reales.

Documentación de MetaTrader 5: https://www.mql5.com/en/docs/python_metatrader5

**Decisión:** no incluimos `order_send` habilitado en el paquete porque todavía no conocemos broker, servidor, credenciales de demo ni reglas de ejecución. Ningún proceso conectado a dinero de terceros o real recibirá autorización automática desde GitHub.

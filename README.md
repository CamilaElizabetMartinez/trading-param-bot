# TRADING-PARAM-BOT
TRADING-PARAM-BOT es un bot de Telegram diseñado para modificar y monitorear parámetros de trading en tiempo real. Permite a los usuarios ajustar configuraciones críticas y obtener información sobre el estado actual de las operaciones de trading a través de comandos simples.

# Características
- Modificación dinámica de parámetros de trading.
- Monitoreo en tiempo real del estado de las operaciones.
- Acceso a logs y comprobaciones de salud del sistema.
- Interfaz fácil de usar a través de comandos de Telegram.

# Requisitos
- Token de bot de Telegram
- Python 3.7+

# Dependencias
Este proyecto utiliza principalmente módulos de la biblioteca estándar de Python. Sin embargo, requiere la instalación de algunas dependencias externas.

# Módulos externos requeridos
- requests

# Comandos disponibles
- /initialcapital -> Modifica el capital inicial
- /stoploss -> Modifica el stop loss
- /takeprofit -> Modifica el take profit
- /reservesl -> Modifica el reserva stop loss
- /currentparameters -> Muestra el valor actual de los parametros de trading de cada bot
- /typemarkettrade -> Indica si esta operando en SELL o BUY
- /isinmarket -> Informa si esta dentro o fuera de mercado 
- /logs -> Muestra los logs recientes
- /healthcheck -> Devuelve el id del proceso
- /help -> Muestra una lista de comandos disponibles 
- /cancel -> Cancela la conversacion actual

# Forma de levantarlo
- python3 trading_param_bot.py

# Seguridad
- Asegúrese de mantener su token de bot seguro y no lo comparta públicamente.

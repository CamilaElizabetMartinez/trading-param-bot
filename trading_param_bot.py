import datetime as dt
import datetime
import os
import json
import requests
import threading
import subprocess
import argparse
import time
import logging
from logging.handlers import RotatingFileHandler
from requests.exceptions import ConnectionError
import time

def setup_logging():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    log_dir = "logs"

    try:
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        log_file_name = datetime.datetime.now().strftime("%Y-%m-%d.log")
        log_file_path = os.path.join(log_dir, log_file_name)

        file_handler = RotatingFileHandler(
            log_file_path,
            maxBytes=1024 * 1024 * 10,  # 10 MB
            backupCount=10,
            encoding="utf-8"
        )
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

        logging.getLogger().addHandler(file_handler)
        logging.getLogger().addHandler(console_handler)

        logging.info(f"Inicio de la ejecución {datetime.datetime.now()}")
    except Exception as e:
        logging.error(f"Error al configurar el logger: {str(e)}")
        raise e

conversation_context = {}
commands_list = [
    "/initialcapital",
    "/stoploss",
    "/takeprofit",
    "/reservesl",
    "/typemarkettrade",
    "/isinmarket",
    "/currentparameters",
    "/logs",
    "/healthcheck",
    "/help",
    "/cancel"
]
commands_bots = [
    "/chilches",
    "/leader",
    "/follower",
]

def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("-env","--env", help="dev=testing prod=produccion", type=str, default="dev")
    args = parser.parse_args()
    return args

#Definir la ruta del archivo donde se almacenan los datos de configuración
def get_config_file_name(env):
    CONFIG_FILE_PATH = f'config/config.{env}.json'
    logging.info(f'Ruta del archivo de configuración: {CONFIG_FILE_PATH}')
    return CONFIG_FILE_PATH

def write_in_file(config_file_path,bot_settings):
    try:
        with open(config_file_path, 'w') as f:
            json.dump(bot_settings, f, indent=4)
    except Exception as e: 
        logging.error(f"Error al escribir en el archivo de configuración: {config_file_path}")
        logging.error(str(e))
        raise e 
    logging.info(f"Archivo de configuración actualizado en {config_file_path}")

#Función para leer la configuración del archivo.
def read_config(CONFIG_FILE_PATH):
    logging.info(f"Leer archivo de configuración: {CONFIG_FILE_PATH}")
    try:
        with open(CONFIG_FILE_PATH, 'r') as config_file:
            return json.load(config_file)
    except FileNotFoundError:
        logging.error(f"Archivo de configuración no encontrado: {CONFIG_FILE_PATH}")
        raise Exception("Config file not found.")

def find_bot_config(bot_name,update,chat_id):
    bot = next((bot for bot in config['bots'] if bot['name'] == bot_name), None)
    if not bot:
        send_message(update['message']['chat']['id'], f"No se ha encontrado configuracion para el {bot_name}")
        reset_conversation_context(chat_id)
    else:
        return bot
    
def handle_response_type_market_trade(update):
    chat_id = update['message']['chat']['id']
    selected_bot = update['message']['text']
    if chat_id in conversation_context and conversation_context[chat_id].get('waiting_for_bot'):
        conversation_context[chat_id]['bot_name'] = selected_bot
        bot_name = selected_bot[1:]
        bot_config = find_bot_config(bot_name,update,chat_id)

        if bot_config:
            config_file_path = bot_config.get('fileTypeMarketTrade')
            with open(config_file_path, 'r') as f:
                bot_settings = f.readlines()[1].strip()
                
            if bot_settings == 'buy':
                tipe_market_trade = 'SELL'
            elif bot_settings == 'sell':
                tipe_market_trade = 'BUY'
            
            send_message(chat_id, f"El bot {bot_name} se encuentra operando en {tipe_market_trade}")
            logging.info(f"Mensaje enviado al chat {chat_id}: El bot {bot_name} se encuentra operando en {tipe_market_trade}")
        else:
            handle_unknown_command_for_bots(chat_id, commands_bots)

        reset_conversation_context(chat_id)
    else:
        handle_unknown_command_for_bots(chat_id, commands_bots)

def handle_response_is_in_market(update):
    chat_id = update['message']['chat']['id']
    selected_bot = update['message']['text']
    if chat_id in conversation_context and conversation_context[chat_id].get('waiting_for_bot'):
        conversation_context[chat_id]['bot_name'] = selected_bot
        bot_name = selected_bot[1:]
        bot_config = find_bot_config(bot_name,update,chat_id)

        if bot_config:
            config_file_path = bot_config.get('fileIsInMarket')
            with open(config_file_path, 'r') as f:
                bot_settings = json.load(f)
            is_in_market = bot_settings.get('isInMarket', 'No disponible')

            if is_in_market == True:
                status_is_in_market = 'está dentro del mercado'
            elif is_in_market == False:
                status_is_in_market = 'está fuera del mercado'
            else:
                status_is_in_market = 'estado desconocido'
                
            send_message(chat_id, f"El bot {bot_name} {status_is_in_market}")
            logging.info(f"Mensaje enviado al chat {chat_id}:El bot {bot_name} ha detectado que {status_is_in_market}")
        else:
            handle_unknown_command_for_bots(chat_id, commands_bots)

        reset_conversation_context(chat_id)
    else:
        handle_unknown_command_for_bots(chat_id, commands_bots)
    
#Función para manejar el comando /healthcheck
def handle_healthcheck_response(update):
    logging.info(f"Procesando comando healthcheck:{update['message']['text']}")
    chat_id = update['message']['chat']['id']
    selected_bot = update['message']['text']
    if chat_id in conversation_context and conversation_context[chat_id].get('waiting_for_bot'):
        bot_name = selected_bot[1:]
        bot_config = find_bot_config(bot_name,update,chat_id)
        wallet = bot_config.get('wallet')
        
        if bot_name == "leader":
            pattern = "cruce-sma"
        elif bot_name == "follower":
            pattern = "torrox"
        elif bot_name == "chilches":
            pattern = "chilches"
        else:
            return []
        
        command = f"ps aux | grep -E 'aveos.*{pattern}.*python' | awk '{{print $2}}'"
        result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        pids = result.stdout.strip()
    
        # Responder según el resultado
        if pids:
            response_text = f"El proceso de {bot_name} con billetera {wallet} y PID {pids} está activo."
            logging.info(f"Respuesta de salud con PID activo: {response_text}")
        else:
            response_text = f"El proceso de {bot_name} con billetera {wallet} y PID {pids} no está activo."
            logging.info(f"Respuesta de salud sin PID activo: {response_text}")

        # Enviar la respuesta al usuario
        send_message(update['message']['chat']['id'], response_text)
        reset_conversation_context(chat_id)

def is_numeric_string(text):
    try:
        number = int(float(text))
        return number
    except ValueError:
        return False

def reset_conversation_context(chat_id):
    if exists_conversation(chat_id):
        del conversation_context[chat_id]
    else:
        send_message(f"No se encontró contexto de conversación para chat_id {chat_id}.")

def handle_unknown_command_for_bots(chat_id, commands_bots):
    message = "Comando no reconocido. Por favor, intenta de nuevo.\n" + "\n".join(commands_bots)
    send_message(chat_id, message)

def handle_unknown_command_for_list(chat_id, commands_list):
    commands_text = "Comando no reconocido. Por favor, intenta de nuevo.\n" + "\n".join(commands_list)
    send_message(chat_id, commands_text)

def handle_configuration_change(update, command):
    logging.info(f"Procesando comando de configuración: {command}")
    chat_id = update['message']['chat']['id']
    if command == '/initialcapital':
        message = "¿A cuál bot quieres cambiarle el Capital Inicial?\n" + "\n".join(commands_bots)
    elif command == '/stoploss':
        message = "¿A cuál bot quieres cambiarle el Stop Loss?\n" + "\n".join(commands_bots)
    elif command == '/takeprofit':
        message = "¿A cuál bot quieres cambiarle el Take Profit?\n" + "\n".join(commands_bots)
    elif command == '/reservesl':
        message = "¿A cuál bot quieres cambiarle la Reserva SL?\n" + "\n".join(commands_bots)

    send_message(chat_id, message)
    # Almacena el estado de la conversación
    conversation_context[chat_id] = {'waiting_for_bot': True, 'command': command}
    logging.info(f"Estado de conversación actualizado para chat {chat_id}: {conversation_context[chat_id]}{update}")

def handle_command_response(update):
    logging.info(f"Procesando respuesta del comando: {update['message']['text']}")
    chat_id = update['message']['chat']['id']
    command = update['message']['text']
    if chat_id in conversation_context and conversation_context[chat_id].get('waiting_for_bot'):
        if command in ['/leader','/follower']:
            bot_name = command
            # Procesa la respuesta y actualiza el contexto de la conversación
            conversation_context[chat_id]['bot_name'] = bot_name
            send_message(chat_id, "¿Cuál es el nuevo valor?")
            conversation_context[chat_id]['waiting_for_bot'] = False
            conversation_context[chat_id]['waiting_for_value'] = True
            logging.info(f"Respuesta procesada para chat {chat_id}: {bot_name}")
        else:
            handle_unknown_command_for_bots(chat_id, commands_bots)
       
def handle_command(update):
    logging.info(f"Procesando comando: {update['message']['text']}")
    chat_id = update['message']['chat']['id']
    command = update['message']['text']
    if command in commands_list:
        message = "Selecciona el nombre del bot \n" + "\n".join(commands_bots)
    else:
        message = "No se encontró ninguna configuración."

    send_message(chat_id,message)
    conversation_context[chat_id] = {'waiting_for_bot': True, 'command': command}
    logging.info(f"Estado de conversación actualizado para chat {chat_id}: {conversation_context[chat_id]}{update}")

def handle_logs_response(update):
    chat_id = update['message']['chat']['id']
    selected_bot = update['message']['text']
    
    logging.info(f"Procesando 'handle_logs_response' para chat {chat_id} con selección: {selected_bot}")

    if chat_id in conversation_context and conversation_context[chat_id].get('waiting_for_lines'):
        num_lines = int(selected_bot[1:])  # Convertir /20, /50, /100 a número
        log_file_path = conversation_context[chat_id].get('log_file_path')

        if log_file_path and os.path.isfile(log_file_path):
            with open(log_file_path, 'r') as log_file:
                lines = log_file.readlines()
                logging.info(f"Archivo de log leído, total líneas: {len(lines)}")
                if len(lines) < num_lines:
                    num_lines = len(lines)
                last_lines = lines[-num_lines:]
            response_text = f"Últimas {num_lines} líneas de {log_file_path}:\n{''.join(last_lines)}"
        else:
            response_text = f"No se ha encontrado el archivo de registro en la ruta: {log_file_path or 'desconocida'}"
            logging.warning(response_text)
                    
    elif chat_id in conversation_context and conversation_context[chat_id].get('waiting_for_bot'):
        bot_name = selected_bot[1:]
        bot_config = find_bot_config(bot_name,update,chat_id)
        folder_path = bot_config.get('folder')

        if bot_name == 'chilches':
            log_file_path = os.path.join(folder_path, '_console.log')    
        elif bot_name == 'leader':
            log_file_path = os.path.join(folder_path, 'TORROX-LEADER-AVEOS_console.log')
        elif bot_name == 'follower':
            log_file_path = os.path.join(folder_path, 'TORROX-FOLLOWER_console.log')
        else:
            send_message(update['message']['chat']['id'], f"No se ha encontrado archivo de regitro para el {bot_name}.")
            reset_conversation_context(chat_id)
            return
        
        # if not os.path.isfile(log_file_path):
        #     send_message(chat_id, f"No se ha encontrado archivo de registro para el {bot_name}.")
        #     reset_conversation_context(chat_id)
        #     return

        # Guardar la ruta del archivo de log en el contexto
        conversation_context[chat_id]['log_file_path'] = log_file_path
        conversation_context[chat_id]['waiting_for_lines'] = True
        send_message(chat_id, "Selecciona el número de líneas que deseas ver:\n/20\n/50\n/100")


def handle_current_parameters_response(update):
    chat_id = update['message']['chat']['id']
    selected_bot = update['message']['text']
    if chat_id in conversation_context and conversation_context[chat_id].get('waiting_for_bot'):
        conversation_context[chat_id]['bot_name'] = selected_bot
        bot_name = selected_bot[1:]
        bot_config = find_bot_config(bot_name,update,chat_id)

        if bot_config:
            config_file_path = bot_config.get('configFilePath')
            with open(config_file_path, 'r') as f:
                bot_settings = json.load(f)

            send_message(chat_id, f"Parámetros actuales para {bot_name}: \n{bot_settings}")
            logging.info(f"Mensaje enviado al chat {chat_id}: Parámetros actuales para {bot_name} con valor {bot_settings}")
        else:
            handle_unknown_command_for_bots(chat_id, commands_bots)

        reset_conversation_context(chat_id)
    else:
        handle_unknown_command_for_bots(chat_id, commands_bots)

def handle_value_update(update, value_type):
    logging.info(f"Procesando actualización de valor: {value_type}")
    chat_id = update['message']['chat']['id']
    text = update['message']['text']

    if chat_id in conversation_context and conversation_context[chat_id].get('waiting_for_value'):
        text_converted_int = int(text)
        new_value = text_converted_int
        bot_name = conversation_context[chat_id]['bot_name']
        bot_name = bot_name[1:]

        bot_config = find_bot_config(bot_name,update,chat_id)
        if bot_config:
            config_file_path = bot_config.get('configFilePath')

            with open(config_file_path, 'r') as f:
                bot_settings = json.load(f)

            if value_type == 'initialCapital':
                bot_settings['initialCapital'] = new_value
            elif value_type == 'stopLoss':
                bot_settings['stopLoss'] = new_value
            elif value_type == 'takeProfit':
                bot_settings['takeProfit'] = new_value
            elif value_type == 'slReserve': 
                bot_settings['slReserve'] = new_value

            write_in_file(config_file_path,bot_settings)
            reset_conversation_context(chat_id)
            
            send_message(chat_id, f"¡Listo! Se ha modificado el valor de {value_type} en {new_value} para {bot_name}")
            logging.info(f"Mensaje enviado al chat {chat_id}: ¡Listo! Se ha modificado el valor de {value_type} en {new_value} para {bot_name}")
            
def cancel_command(update):
    logging.info(f"Procesando comando cancelar: {update['message']['text']}")
    chat_id = update['message']['chat']['id']
    if exists_conversation(chat_id):
        reset_conversation_context(chat_id)
        send_message(chat_id, "La conversación ha sido cancelada.Por favor, intenta de nuevo")
        logging.info(f"Conversación cancelada para chat {chat_id}")
    else:
        send_message(chat_id, "No hay una conversación en curso para cancelar.")
        logging.info(f"No hay conversación en curso para cancelar en chat {chat_id}")

def help_command(chat_id):
    commands_text = "Comandos disponibles:\n" + "\n".join(commands_list)
    send_message(chat_id, commands_text)

def set_convesation_context(chat_id):
    conversation_context[chat_id] = {'waiting_for_bot': False,'command': None, 'bot_name': None}
    logging.info(f"Contexto de conversación establecido para chat {chat_id}: {conversation_context[chat_id]}")

def exists_conversation(chat_id):
    return chat_id in conversation_context

def handler_interaction_1(update,text, chat_id):
    logging.info(f"Procesando manejador de interaccion 1:{update['message']['text']}")
    if text.startswith('/healthcheck'):
        handle_command(update)
    elif text.startswith('/logs'):
        handle_command(update)
    elif text.startswith('/help'):
        help_command(chat_id)
    elif text.startswith('/cancel'):
        cancel_command(update)
    elif text.startswith('/currentparameters'):
        handle_command(update)
    elif text.startswith('/typemarkettrade'):
        handle_command(update)
    elif text.startswith('/isinmarket'):
        handle_command(update)
    elif text.startswith('/initialcapital'):
        handle_configuration_change(update, '/initialcapital')
    elif text.startswith('/stoploss'):
        handle_configuration_change(update, '/stoploss')
    elif text.startswith('/takeprofit'):
        handle_configuration_change(update, '/takeprofit')
    elif text.startswith('/reservesl'):
        handle_configuration_change(update, '/reservesl')
    else:
        handle_unknown_command_for_list(chat_id, commands_list)
        logging.info(f"Fin de la ejecucion interaccion 1:{update}")

def handler_interation_2(previous_command,update):
    logging.info(f"Procesando respuesta manejador de interaccion 2:{previous_command}")
    if previous_command == '/initialcapital':
        handle_command_response(update)
    elif previous_command == '/stoploss':
        handle_command_response(update)
    elif previous_command == '/takeprofit':
        handle_command_response(update)
    elif previous_command == '/reservesl':
        handle_command_response(update)
    elif previous_command == '/typemarkettrade':
        handle_response_type_market_trade(update)
    elif previous_command == '/isinmarket':
        handle_response_is_in_market(update)
    elif previous_command == '/currentparameters':
        handle_current_parameters_response(update)
    elif previous_command == '/healthcheck':
        handle_healthcheck_response(update)
    elif previous_command == '/logs':
        handle_logs_response(update)
    logging.info(f"Fin de la ejecucion interaccion 2:{update}")      

def handler_interaction_3(update,previous_command):
    logging.info(f"Procesando respuesta manejador de interaccion 3: {previous_command}")
    if previous_command == '/initialcapital':
        handle_value_update(update,'initialCapital')
    elif previous_command == '/stoploss':
        handle_value_update(update,'stopLoss')
    elif previous_command == '/takeprofit':
        handle_value_update(update,'takeProfit')
    elif previous_command == '/reservesl':
        handle_value_update(update,'slReserve')
    logging.info(f"Fin de la ejecucion interaccion 3: {update}")

def is_interaction_2(previous_command):
    return previous_command in commands_list

def is_interaction_3(bot_name):
    return bot_name in commands_bots

# Función para enviar un mensaje al usuario.
def send_message(chat_id, text):
    url = f'https://api.telegram.org/bot{config["token"]}/sendMessage'
    params = {'chat_id': chat_id, 'text': text}
    requests.post(url, json=params)

# Función para manejar actualizaciones.
def handle_updates(update):
    if 'message' in update and 'text' in update['message']:
        text = update['message']['text']
        chat_id = update['message']['chat']['id']

        if text in '/cancel':
            cancel_command(update)
            return

        if exists_conversation(chat_id):
            # Obtener el contexto de la conversación
            context = conversation_context[chat_id]
            # Determinar el comando ejecutado anteriormente
            previous_command = context.get('command')
            bot_name = context.get('bot_name')

            if is_interaction_3(bot_name):
                if is_numeric_string(text):
                    handler_interaction_3(update,previous_command)
                else:
                    set_convesation_context(chat_id)
                    handle_unknown_command_for_bots(chat_id, commands_bots)

            if is_interaction_2(previous_command):
                handler_interation_2(previous_command,update)
            else:
                set_convesation_context(chat_id)
                handle_unknown_command_for_list(chat_id, commands_list)

        else:
            handler_interaction_1(update,text,chat_id)

# Función para obtener el mayor update_id actual
def get_max_update_id(config):
    url = f'https://api.telegram.org/bot{config["token"]}/getUpdates'
    response = requests.get(url)
    updates = response.json().get('result', [])
    return max([update['update_id'] for update in updates], default=None)

# Función para obtener actualizaciones
def get_updates(config,offset=None):
    MAX_RETRIES = 5
    RETRY_DELAY = 5
    for attempt in range(MAX_RETRIES):
        try:
            url = f'https://api.telegram.org/bot{config["token"]}/getUpdates'
            params = {'offset': offset, 'timeout': 60}
            response = requests.get(url, params=params)

            if response.status_code == 200:
                updates = response.json().get('result')
                if updates:
                    # Encuentre el update_id más alto y agregue 1 para obtener el siguiente desplazamiento
                    next_offset = max(update['update_id'] for update in updates) + 1
                    logging.info(f"Obtenidas {len(updates)} actualizaciones, próximo offset: {next_offset}")
                    return updates, next_offset
            return [], offset
        except ConnectionError as e:
            connection_error_msg =(f"Error de conexión. Reintentando en {RETRY_DELAY} segundos...")
            logging.info(connection_error_msg)
            time.sleep(RETRY_DELAY)
            RETRY_DELAY *= 2
    else:
        error_msg = "Se alcanzó el número máximo de reintentos. No se pudieron obtener las actualizaciones."
        logging.error(error_msg)
        raise Exception(error_msg)
    
# Función para manejar actualizaciones en un hilo separado
def handle_updates_in_thread(config):
    # Obtén el mayor update_id actual para establecer el offset inicial
    offset = get_max_update_id(config) + 1 if get_max_update_id(config) else None
    while True:
        try:
            updates, offset = get_updates(config,offset)
            for update in updates:
                handle_updates(update)
        except Exception as e:
            logging.error(f"Error al procesar las actualizaciones{e}", exc_info=True)   
            time.sleep(1)   

# Ejecución principal
if __name__ == '__main__':
    setup_logging()
    args = parse_arguments()
    CONFIG_FILE_PATH = get_config_file_name(args.env)
    config = read_config(CONFIG_FILE_PATH)
    # Inicia un hilo para manejar actualizaciones de forma asincrónica
    update_thread = threading.Thread(target=handle_updates_in_thread, args=(config,))
    update_thread.start()

    while True:
        pass  # Mantén el programa principal en ejecución
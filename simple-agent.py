# 01 - Importar librerias
import os
from typing import Any
from pathlib import Path
from dotenv import load_dotenv
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.ai.projects.models import CodeInterpreterTool, FunctionTool, ToolSet
from functions.compound_interest import CompoundInterest

# 02 - Cargar las variables de entorno y conexion a Azure AI Projects
# Requiere hacer az login en la terminal
load_dotenv()

project_connection_string = os.getenv("AI_PROJECT_CONNECTION_STRING")
agent_model = os.getenv("CHAT_MODEL")

project_client = AIProjectClient.from_connection_string(
    conn_str=project_connection_string, 
    credential=DefaultAzureCredential()
)

# 03 - Asignación de funciones de usuario
user_functions = {CompoundInterest.calculate_future_value}

# 04 - Creación y uso del agente
with project_client:
    #04a - Definición de herramientas del agente
    code_interpreter = CodeInterpreterTool()
    functions = FunctionTool(functions=user_functions)

    toolset = ToolSet()
    toolset.add(code_interpreter)
    toolset.add(functions)

    #04b - Definición del agente
    agent_name = "Product Support Agent"
    agent_instructions = "You are a product support agent that helps users with product-related queries. " \
    "You can use code interpreter to generate and save text, image files if the user asks for it" \
    " and you can also use given functions for calculations. Use default parameters for functions if not specified by the user. " 

    product_agent = project_client.agents.create_agent(
        model=agent_model,
        name=agent_name,
        instructions=agent_instructions,
        toolset=toolset
    )
    print(f"Agente creado, ID: {product_agent.id}")

    # 04c - Crear un hilo de conversación para el agente
    agent_thread = project_client.agents.create_thread()
    print(f"Hilo creado, ID: {agent_thread.id}")

    # 04d - Enviar un mensaje (petición) al agente

    #user_prompt = "Tengo 2 productos, " \
    #"iPhone a USD 200 por 3 meses y Laptop HP en 500 USD en un solo pago, " \
    #"¿cuál es más caro? " \
    #"Primero responde la pregunta. " \
    #"Luego, genera un reporte donde expliques el razonamiento, guárdalo en el archivo reporte-productos.md. " \
    #"Finalmente, crea una gráfica de barras donde muestres el total a pagar por producto y guárdala como costo-total.png." \
    #"Utiliza colores en tono pastel para la gráfica."
    user_prompt = "Cual es la evolución del valor futuro de un producto que hoy cuesta 100 pesos mes a mes durante 5 meses a una tasa del 3% mensual" \
    "Responde la pregunta calculando el valor en cada mes utilizando la función proporcionada. " \
    "Luego, genera un reporte donde expliques el razonamiento, muestra la evolución del valor mes a mes en una tabla y guárdalo en el archivo reporte-producto.md. " \
    "Finalmente, genera una gráfica de línea donde muestres cómo va evolucionando el valor del producto mes a mes en el plazo utilizado, guárdala como costo-producto.png." \

    # 04e - Enviar el mensaje al agente en el hilo de conversación
    user_message = project_client.agents.create_message(
        thread_id=agent_thread.id,
        role="user",
        content=user_prompt,
    )
    print(f"Se creó el mensaje, ID: {user_message.id}")

    # 04f - Procesar el mensaje y obtener la respuesta del agente
    run = project_client.agents.create_and_process_run(
        thread_id=agent_thread.id, 
        assistant_id=product_agent.id)
    print(f"Ejecución finalizada, status: {run.status}")

    if run.status == "failed":
        # Si el error es "Rate limit is exceeded.", incrementa el límite de tokens
        print(f"Ejecución fallida. Error: {run.last_error}")
    
    # 04g - Mostrar la respuesta del agente
    messages = project_client.agents.list_messages(thread_id=agent_thread.id)
    #print(f"Respuestas del agente: ")
    #print(f"---Lista de Mensajes: {messages} ---")

    print(f"--- Respuesta concreta del agente ---")
    for message in reversed(messages['data']):
        if message.get('role') == 'assistant':
            for content in message.get('content', []):
                if content.get('type') == 'text':
                    print(f"    Agente: {content['text']['value']}")

    # 04h - Guardar los archivos generados por el agente
    for file_path_annotation in messages.file_path_annotations:
        file_name = Path(file_path_annotation.text).name
        project_client.agents.save_file(
            file_id=file_path_annotation.file_path.file_id, 
            file_name=file_name)
        print(f"Archivo guardado en: {Path.cwd() / file_name}")
    
    # 04i - Eliminar el agente
    project_client.agents.delete_agent(product_agent.id)
    print("Agente eliminado.")    
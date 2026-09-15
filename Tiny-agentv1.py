import json
import os
from datetime import datetime

from openai import OpenAI


# ---------------------------------------------------------
# 1. Initialisation du client OpenAI
# ---------------------------------------------------------

# La clé doit être définie dans la variable d'environnement :
# export OPENAI_API_KEY="..."
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])


# ---------------------------------------------------------
# 2. Nos outils Python
#
# Ce sont de simples fonctions.
# Le LLM ne les exécute PAS directement.
# Il demande à notre programme de les exécuter.
# ---------------------------------------------------------

def get_current_time():
    """Retourne l'heure actuelle."""
    return datetime.now().strftime("%H:%M:%S")


def multiply(a, b):
    """Multiplie deux nombres."""
    return a * b


# ---------------------------------------------------------
# 3. Description des outils pour le LLM
#
# On explique au modèle :
# - le nom de l'outil
# - ce qu'il fait
# - les paramètres qu'il accepte
# ---------------------------------------------------------

TOOLS = [
    {
        "type": "function",
        "name": "get_current_time",
        "description": "Retourne l'heure actuelle.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "type": "function",
        "name": "multiply",
        "description": "Multiplie deux nombres.",
        "parameters": {
            "type": "object",
            "properties": {
                "a": {
                    "type": "number",
                    "description": "Premier nombre",
                },
                "b": {
                    "type": "number",
                    "description": "Deuxième nombre",
                },
            },
            "required": ["a", "b"],
        },
    },
]


# ---------------------------------------------------------
# 4. Dispatcher
#
# C'est lui qui fait le lien entre :
#
#     nom demandé par le LLM
#
# et
#
#     vraie fonction Python
# ---------------------------------------------------------

def execute_tool(name, arguments):

    if name == "get_current_time":
        return get_current_time()

    if name == "multiply":
        return multiply(
            arguments["a"],
            arguments["b"],
        )

    return f"Outil inconnu : {name}"


# ---------------------------------------------------------
# 5. Notre agent
# ---------------------------------------------------------

def run_agent(user_message):

    # Historique de travail de l'agent
    messages = [
        {
            "role": "user",
            "content": user_message,
        }
    ]

    while True:

        # -------------------------------------------------
        # On demande au LLM quoi faire
        # -------------------------------------------------

        response = client.responses.create(
            model="gpt-5.6-luna",

            instructions="""
            Tu es un petit agent expérimental.

            Réponds directement lorsque tu connais la réponse.

            Si un outil est nécessaire, utilise-le.
            """,

            tools=TOOLS,
            input=messages,
        )

        # On conserve les éléments produits par le modèle
        # pour le tour suivant.
        messages.extend(response.output)

        tool_called = False

        # -------------------------------------------------
        # On regarde si le LLM demande l'utilisation
        # d'un outil.
        # -------------------------------------------------

        for item in response.output:

            if item.type != "function_call":
                continue

            tool_called = True

            print(f"\n[AGENT] Outil demandé : {item.name}")

            # Arguments envoyés par le LLM
            arguments = json.loads(item.arguments)

            print(f"[AGENT] Arguments : {arguments}")

            # -------------------------------------------------
            # Exécution REELLE de la fonction Python
            # -------------------------------------------------

            result = execute_tool(
                item.name,
                arguments,
            )

            print(f"[AGENT] Résultat : {result}")

            # -------------------------------------------------
            # On renvoie le résultat au LLM
            # -------------------------------------------------

            messages.append(
                {
                    "type": "function_call_output",
                    "call_id": item.call_id,
                    "output": str(result),
                }
            )

        # -------------------------------------------------
        # Aucun outil demandé :
        # le LLM a terminé son travail.
        # -------------------------------------------------

        if not tool_called:
            return response.output_text


# ---------------------------------------------------------
# 6. Petit terminal interactif
# ---------------------------------------------------------

print("Tiny Agent")
print("Tape 'quit' pour quitter.\n")

while True:

    question = input("Vous : ")

    if question.lower() == "quit":
        break

    answer = run_agent(question)

    print("\nAgent :", answer)
    print()
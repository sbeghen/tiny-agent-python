import json
import os
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


# ---------------------------------------------------------
# 1. Initialisation du client OpenAI
# ---------------------------------------------------------

# La clé API doit être définie dans l'environnement :
#
# export OPENAI_API_KEY="..."
#
client = OpenAI(
    api_key=os.environ["OPENAI_API_KEY"]
)


# ---------------------------------------------------------
# 2. TOOL : récupérer une page web
#
# Le rôle du tool est uniquement de donner une capacité
# supplémentaire à notre agent :
#
# "Je peux récupérer le contenu d'une URL."
#
# La méthode d'analyse sera définie plus tard
# dans notre skill.
# ---------------------------------------------------------

def fetch_url(url):
    """
    Récupère les informations principales d'une page web.
    """

    response = requests.get(
        url,
        timeout=10,
        headers={
            "User-Agent": "TinyAgent/2.0"
        }
    )

    # Déclenche une erreur Python si la page
    # retourne une erreur HTTP : 404, 500, etc.
    response.raise_for_status()

    # BeautifulSoup transforme le HTML en structure
    # facilement exploitable.
    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )

    # On retire quelques éléments inutiles
    # pour notre analyse.
    for tag in soup(
        ["script", "style", "noscript"]
    ):
        tag.decompose()

    # TITLE
    title = (
        soup.title.get_text(" ", strip=True)
        if soup.title
        else None
    )

    # META DESCRIPTION
    meta = soup.find(
        "meta",
        attrs={"name": "description"}
    )

    meta_description = (
        meta.get("content")
        if meta
        else None
    )

    # H1
    h1 = [
        tag.get_text(" ", strip=True)
        for tag in soup.find_all("h1")
    ]

    # H2
    h2 = [
        tag.get_text(" ", strip=True)
        for tag in soup.find_all("h2")
    ]

    # Texte visible de la page
    text = " ".join(
        soup.stripped_strings
    )

    # On limite volontairement la quantité
    # de texte envoyée au LLM.
    text = text[:12000]

    return {
        "url": response.url,
        "status_code": response.status_code,
        "title": title,
        "meta_description": meta_description,
        "h1": h1,
        "h2": h2[:20],
        "text": text,
    }


# ---------------------------------------------------------
# 3. Description du tool pour le LLM
#
# Comme dans la V1 :
#
# cette partie N'EXECUTE PAS fetch_url().
#
# Elle explique simplement au modèle
# qu'un outil existe.
# ---------------------------------------------------------

TOOLS = [
    {
        "type": "function",
        "name": "fetch_url",
        "description": (
            "Récupère les informations principales "
            "et le contenu d'une page web."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": (
                        "URL complète de la page web "
                        "à récupérer."
                    ),
                }
            },
            "required": ["url"],
        },
    }
]


# ---------------------------------------------------------
# 4. Dispatcher
#
# Le LLM demande :
#
# fetch_url(...)
#
# Mais c'est notre programme Python
# qui exécute réellement la fonction.
# ---------------------------------------------------------

def execute_tool(name, arguments):

    if name == "fetch_url":
        return fetch_url(
            arguments["url"]
        )

    return {
        "error": f"Outil inconnu : {name}"
    }


# ---------------------------------------------------------
# 5. Chargement d'une skill
#
# Une skill est ici simplement un fichier Markdown.
#
# Exemple :
#
# skills/
# └── audit-page/
#     └── SKILL.md
# ---------------------------------------------------------

def load_skill(name):
    """
    Charge le fichier SKILL.md correspondant.
    """

    path = (
        Path("skills")
        / name
        / "SKILL.md"
    )

    if not path.exists():
        raise FileNotFoundError(
            f"Skill introuvable : {path}"
        )

    return path.read_text(
        encoding="utf-8"
    )


# ---------------------------------------------------------
# 6. Notre agent
# ---------------------------------------------------------

def run_agent(
    user_message,
    skill_name=None
):

    # -----------------------------------------------------
    # Mémoire de travail minimale
    #
    # Comme dans la V1, messages contient
    # tout ce qui se passe pendant CETTE tâche.
    #
    # Cette mémoire disparaît lorsque run_agent()
    # se termine.
    # -----------------------------------------------------

    messages = [
        {
            "role": "user",
            "content": user_message,
        }
    ]

    # Instructions générales de l'agent.
    instructions = """
Tu es un petit agent expérimental.

Réponds directement lorsque tu disposes
déjà des informations nécessaires.

Si tu dois récupérer le contenu d'une page web,
utilise l'outil fetch_url.

N'invente pas les informations absentes.
"""

    # -----------------------------------------------------
    # Si une skill est demandée,
    # on charge son contenu.
    # -----------------------------------------------------

    if skill_name:

        skill = load_skill(
            skill_name
        )

        # Puis on ajoute la méthode au contexte du LLM.
        instructions += f"""

Une skill spécialisée est active.

Applique cette méthode pour réaliser la tâche.

--- SKILL ---

{skill}

--- FIN SKILL ---
"""

    # -----------------------------------------------------
    # Boucle agentique
    # -----------------------------------------------------

    while True:

        # On demande au LLM quoi faire.
        response = client.responses.create(
            model="gpt-5.6-luna",
            instructions=instructions,
            tools=TOOLS,
            input=messages,
        )

        # -------------------------------------------------
        # Mémoire de travail
        #
        # On conserve la réponse du modèle
        # pour le prochain tour.
        # -------------------------------------------------

        messages.extend(
            response.output
        )

        tool_called = False

        # -------------------------------------------------
        # On inspecte ce que le modèle a demandé.
        # -------------------------------------------------

        for item in response.output:

            # Si ce n'est pas un appel de tool,
            # on passe au suivant.
            if item.type != "function_call":
                continue

            tool_called = True

            print(
                f"\n[AGENT] Outil demandé : "
                f"{item.name}"
            )

            # Les arguments arrivent sous forme JSON.
            arguments = json.loads(
                item.arguments
            )

            print(
                f"[AGENT] Arguments : "
                f"{arguments}"
            )

            # -------------------------------------------------
            # Exécution réelle du tool Python
            # -------------------------------------------------

            try:

                result = execute_tool(
                    item.name,
                    arguments,
                )

            except Exception as error:

                result = {
                    "error": str(error)
                }

            print(
                "[AGENT] Résultat récupéré."
            )

            # -------------------------------------------------
            # On renvoie le résultat au LLM.
            #
            # Il pourra l'observer au prochain tour
            # du while True.
            # -------------------------------------------------

            messages.append(
                {
                    "type": "function_call_output",
                    "call_id": item.call_id,
                    "output": json.dumps(
                        result,
                        ensure_ascii=False,
                    ),
                }
            )

        # -------------------------------------------------
        # Si aucun outil n'est demandé,
        # on considère que le modèle a terminé.
        # -------------------------------------------------

        if not tool_called:
            return response.output_text


# ---------------------------------------------------------
# 7. Terminal interactif
# ---------------------------------------------------------

print()
print("Tiny Agent V2")
print("------------------------------")
print()
print("Sans skill :")
print("Analyse https://example.com")
print()
print("Avec skill :")
print("/audit-page Analyse https://example.com")
print()
print("Tape 'quit' pour quitter.")
print()


while True:

    question = input("Vous : ")

    if question.lower() == "quit":
        break

    skill_name = None

    # -----------------------------------------------------
    # Pour cette version pédagogique,
    # l'activation de la skill est explicite.
    #
    # On ne fait PAS encore de sélection automatique.
    # -----------------------------------------------------

    if question.startswith(
        "/audit-page "
    ):

        skill_name = "audit-page"

        question = question.removeprefix(
            "/audit-page "
        ).strip()

    # Exécution de l'agent.
    answer = run_agent(
        question,
        skill_name=skill_name,
    )

    print()
    print("Agent :")
    print(answer)
    print()
import os
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .rag_engine import answer_question
from django.shortcuts import render
import subprocess
from pathlib import Path

@csrf_exempt
def ask(request):
    """
    Lida com requisições POST (JSON) e GET para responder à pergunta de um usuário.
    Sempre retorna 'resposta' como string.
    """
    if request.method == "POST":
        try:
            if request.content_type == "application/json":
                data = json.loads(request.body)
                pergunta = data.get("pergunta", "")
            else:
                pergunta = request.POST.get("pergunta", "")

            if not pergunta:
                return JsonResponse({"erro": "Pergunta vazia"}, status=400)

            # resposta pode ser dict (com 'resposta' e 'fontes') ou string
            resposta = answer_question(pergunta)

            if isinstance(resposta, dict):
                return JsonResponse({
                    "pergunta": pergunta,
                    "resposta": resposta.get("resposta", ""),
                    "fontes": resposta.get("fontes", [])
                })
            else:
                return JsonResponse({
                    "pergunta": pergunta,
                    "resposta": str(resposta),
                    "fontes": []
                })

        except Exception as e:
            return JsonResponse({"erro": str(e)}, status=400)

    return JsonResponse({"erro": "Use POST (JSON) ou GET (?q=...)"}, status=400)


def chat_interface(request):
    """
    Gerencia a interface de chat para a aplicação chatbot.

    Esta view controla a conversa entre o usuário e o chatbot, armazenando as mensagens na sessão.
    Suporta limpar a conversa e gerar respostas do bot para as perguntas do usuário.
    """
    if "messages" not in request.session:
        request.session["messages"] = []

    messages = request.session["messages"]
    thinking = False

    if request.method == "POST":
        if "clear" in request.POST:
            # botão limpar conversa
            request.session["messages"] = []
            messages = []
        else:
            pergunta = request.POST.get("pergunta")
            if pergunta:
                # adiciona pergunta do usuário
                messages.append({"sender": "user", "text": pergunta})
                request.session["messages"] = messages
                thinking = True

                # gera resposta do bot
                resposta = answer_question(pergunta)
                messages.append({"sender": "bot", "text": str(resposta)})
                request.session["messages"] = messages

    return render(
        request,
        "chatbot/chat.html",
        {"messages": messages, "thinking": thinking}
    )


from crawler import crawler_exec

def update_news(request):
    try:
        test_mode = request.GET.get("teste") == "1"
        query = "notícias recentes sobre educação na Região Integrada de Desenvolvimento do Distrito Federal e Entorno (RIDE-DF)"
        artigos = crawler_exec.executar_coleta(query, test_mode=test_mode)

        return JsonResponse({
            "status": "sucesso",
            "modo_teste": test_mode,
            "qtde_artigos": len(artigos),
            "artigos": artigos if test_mode else [a["titulo"] for a in artigos],
        })

    except Exception as e:
        return JsonResponse({
            "status": "erro",
            "mensagem": str(e)
        })
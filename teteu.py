import os
import sqlite3
import subprocess
import requests
from openai import OpenAI
from RestrictedPython import compile_restricted, safe_globals
import chardet
import glob
import cohere
from deep_translator import GoogleTranslator
from github import Github
from win10toast import ToastNotifier
import readline
import nbformat as nbf

# Substitua a configuração da API key:
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
if not client.api_key:
    raise ValueError("API Key da OpenAI não encontrada. Verifique a variável de ambiente 'OPENAI_API_KEY'.")

modelo_gpt = "gpt-3.5-turbo"

# 📦 Banco de Dados SQLite
con = sqlite3.connect('teteu.db')
cur = con.cursor()

# Cria tabela se não existir
cur.execute('''
    CREATE TABLE IF NOT EXISTS historico (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        comando TEXT,
        resposta TEXT
    )
''')
con.commit()

def obter_contexto(limite=5):
    cur.execute('SELECT comando, resposta FROM historico ORDER BY id DESC LIMIT ?', (limite,))
    registros = cur.fetchall()
    # Inverter para ordem cronológica
    return registros[::-1]

# Função para conversar com o GPT (atualizada para openai>=1.0.0)
def perguntar_ao_gpt(prompt, contexto_limite=5):
    try:
        mensagens = []
        # Adiciona contexto das últimas interações
        contexto = obter_contexto(contexto_limite)
        for comando, resposta in contexto:
            mensagens.append({"role": "user", "content": comando})
            mensagens.append({"role": "assistant", "content": resposta})
        # Adiciona a nova pergunta com personalidade
        prompt_personalizado = (
            "Você é o TETEU, um assistente de programação divertido, que responde de forma descontraída e amigável, "
            "usando gírias brasileiras quando possível. "
            "Seja claro, didático e incentive o usuário a aprender. "
            f"Pergunta do usuário: {prompt}"
        )
        mensagens.append({"role": "user", "content": prompt_personalizado})

        resposta = client.chat.completions.create(
            model=modelo_gpt,
            messages=mensagens,
            temperature=0.7,
            max_tokens=1500
        )
        texto = resposta.choices[0].message.content.strip()
        return texto
    except Exception as e:
        if "insufficient_quota" in str(e):
            return "⚠️ Sua cota da OpenAI acabou. Verifique seu plano e billing em https://platform.openai.com/account/usage"
        return f"Erro ao acessar OpenAI: {e}"

# ⚙️ Função para executar código Python de forma segura
def executar_codigo(codigo):
    try:
        byte_code = compile_restricted(codigo, '<string>', 'exec')
        exec(byte_code, safe_globals.copy())
    except Exception as e:
        print(f"Erro ao executar: {e}")

# 📜 Mostrar histórico
def mostrar_historico(limite=10):
    cur.execute('SELECT id, comando, resposta FROM historico ORDER BY id DESC LIMIT ?', (limite,))
    registros = cur.fetchall()
    if registros:
        for r in registros[::-1]:
            print(f"\n🆔 {r[0]} — Comando: {r[1]}\nResposta: {r[2]}")
    else:
        print("📭 Histórico vazio.")

# 🔍 Buscar no histórico
def buscar_no_historico(termo):
    cur.execute("SELECT id, comando, resposta FROM historico WHERE comando LIKE ? OR resposta LIKE ? ORDER BY id", 
                (f"%{termo}%", f"%{termo}%"))
    resultados = cur.fetchall()
    if resultados:
        for r in resultados:
            print(f"\n🆔 {r[0]} — Comando: {r[1]}\nResposta: {r[2]}")
    else:
        print(f"🔍 Nada encontrado para '{termo}'.")

def mostrar_ajuda():
    print("""
Comandos disponíveis:
- sair: Encerra o programa
- exec <codigo>: Executa código Python
- historico: Mostra as últimas interações
- buscar <termo>: Busca no histórico
- limpar_historico: Limpa todo o histórico
- exportar_historico: Exporta o histórico para um arquivo
- modelo <nome>: Troca o modelo GPT (ex: modelo gpt-4)
- explica <codigo>: Explica detalhadamente um código Python
- resuma <texto>: Resume um texto longo
- erro <mensagem>: Explica um erro de Python e como resolver
- corrija <codigo>: Sugere melhorias e corrige um código Python
- quiz: Recebe uma pergunta de múltipla escolha sobre programação
- desafio: Recebe um desafio de programação para praticar
- materiais: Sugere materiais gratuitos para aprender Python
- ajuda: Mostra esta mensagem de ajuda
""")

def limpar_historico():
    cur.execute('DELETE FROM historico')
    con.commit()
    print("🧹 Histórico limpo com sucesso!")

def exportar_historico():
    cur.execute('SELECT id, comando, resposta FROM historico ORDER BY id')
    registros = cur.fetchall()
    if registros:
        with open("historico_teteu.txt", "w", encoding="utf-8") as f:
            for r in registros:
                f.write(f"ID: {r[0]}\nComando: {r[1]}\nResposta: {r[2]}\n{'-'*40}\n")
        print("📤 Histórico exportado para 'historico_teteu.txt'.")
    else:
        print("📭 Histórico vazio, nada para exportar.")

def exportar_para_notebook():
    cur.execute('SELECT comando, resposta FROM historico ORDER BY id')
    registros = cur.fetchall()
    nb = nbf.v4.new_notebook()
    cells = []
    for comando, resposta in registros:
        cells.append(nbf.v4.new_markdown_cell(f"**Comando:** `{comando}`\n\n**Resposta:**\n{resposta}"))
    nb['cells'] = cells
    with open("historico_teteu.ipynb", "w", encoding="utf-8") as f:
        nbf.write(nb, f)
    print("📓 Histórico exportado para 'historico_teteu.ipynb'.")

def explicar_codigo(codigo):
    prompt = f"Explique detalhadamente o que faz o seguinte código Python:\n\n{codigo}"
    return perguntar_ao_gpt(prompt)

def resumir_texto(texto):
    prompt = f"Resuma o texto a seguir em poucas linhas, de forma clara e objetiva:\n\n{texto}"
    return perguntar_ao_gpt(prompt)

def explicar_erro(erro):
    prompt = f"Explique o seguinte erro de Python e como resolvê-lo:\n\n{erro}"
    return perguntar_ao_gpt(prompt)

def corrigir_codigo(codigo):
    prompt = f"Revise o seguinte código Python, aponte erros e sugira melhorias:\n\n{codigo}"
    return perguntar_ao_gpt(prompt)

def sugerir_materiais():
    prompt = "Sugira materiais gratuitos para aprender Python, como sites, vídeos e livros."
    return perguntar_ao_gpt(prompt)

def quiz_programacao():
    prompt = (
        "Crie uma pergunta de múltipla escolha sobre programação Python, "
        "com 4 alternativas e indique a correta no final."
    )
    return perguntar_ao_gpt(prompt)

def desafio_programacao():
    prompt = (
        "Me proponha um desafio simples de programação em Python para iniciantes, "
        "explique o que deve ser feito e mostre a solução ao final."
    )
    return perguntar_ao_gpt(prompt)

def explicar_biblioteca(nome):
    prompt = f"Explique para que serve a biblioteca Python '{nome}' e mostre um exemplo de uso."
    return perguntar_ao_gpt(prompt)

def buscar_stackoverflow(pergunta):
    url = "https://api.stackexchange.com/2.3/search/advanced"
    params = {
        "order": "desc",
        "sort": "relevance",
        "q": pergunta,
        "site": "stackoverflow",
        "accepted": True,
        "answers": 1
    }
    resp = requests.get(url, params=params)
    data = resp.json()
    if data["items"]:
        titulo = data["items"][0]["title"]
        link = data["items"][0]["link"]
        return f"Encontrei isso no Stack Overflow:\n{titulo}\n{link}"
    else:
        return "Nenhuma resposta encontrada no Stack Overflow."

import subprocess
import os

def analisar_codigo(codigo):
    with open("temp_code.py", "w", encoding="utf-8") as f:
        f.write(codigo)
    resultados = []
    try:
        # Flake8
        flake8 = subprocess.run(["flake8", "temp_code.py"], capture_output=True, text=True)
        if flake8.stdout:
            resultados.append(f"⚠️ Flake8 encontrou problemas:\n{flake8.stdout}")
        else:
            resultados.append("✅ Flake8: Nenhum problema encontrado.")

        # Pylint
        pylint = subprocess.run(
            ["pylint", "temp_code.py", "--disable=all", "--enable=errors,warnings"],
            capture_output=True, text=True
        )
        if pylint.stdout and "Your code has been rated" not in pylint.stdout:
            resultados.append(f"⚠️ Pylint encontrou problemas:\n{pylint.stdout}")
        else:
            resultados.append("✅ Pylint: Nenhum problema encontrado.")

        # Mypy (opcional, se usar type hints)
        mypy = subprocess.run(["mypy", "temp_code.py"], capture_output=True, text=True)
        if mypy.stdout and "Success" not in mypy.stdout:
            resultados.append(f"⚠️ Mypy encontrou problemas de tipos:\n{mypy.stdout}")
        else:
            resultados.append("✅ Mypy: Tipos corretos ou não utilizados.")

        # Black (sugestão de formatação)
        black = subprocess.run(["black", "--check", "temp_code.py"], capture_output=True, text=True)
        if "would reformat" in black.stdout:
            resultados.append("💡 Black: O código pode ser melhor formatado. Use o Black para padronizar.")
        else:
            resultados.append("✅ Black: O código já está bem formatado.")
    finally:
        if os.path.exists("temp_code.py"):
            os.remove("temp_code.py")
    return "\n\n".join(resultados)

def sugerir_projetos(nivel="iniciante"):
    prompt = f"Me sugira 3 ideias de projetos em Python para o nível {nivel}, com breve descrição de cada."
    return perguntar_ao_gpt(prompt)

def revisar_com_gpt(codigo):
    prompt = (
        "Analise o seguinte código Python, explique os principais erros encontrados, "
        "mostre exemplos de código corrigido quando possível e sugira melhorias de clareza, performance e boas práticas:\n\n"
        f"{codigo}"
    )
    return perguntar_ao_gpt(prompt)

# 🧠 Loop principal do TETEU
def teteu_loop():
    global modelo_gpt
    print("🤖 TETEU IA — Assistente de Código")
    print("Comandos: 'sair', 'exec <codigo>', 'historico', 'buscar <termo>'")

    while True:
        comando = input(">>> ")

        if comando.lower() == 'sair':
            print("Tchau! 👋")
            break

        elif comando.lower().startswith('exec'):
            codigo = comando[5:]
            executar_codigo(codigo)
            print("Código executado.")
            continue

        elif comando.lower() == 'historico':
            texto_hist = mostrar_historico_interface()
            print(texto_hist)
            continue

        elif comando.lower().startswith('buscar'):
            termo = comando[7:].strip()
            if termo:
                buscar_no_historico(termo)
            else:
                print("⚠️ Informe um termo para buscar. Exemplo: buscar print")
            continue

        elif comando.lower() == 'ajuda':
            mostrar_ajuda()
            continue

        elif comando.lower() == 'limpar_historico':
            limpar_historico()
            print("🧹 Histórico limpo com sucesso!")
            continue

        elif comando.lower() == 'exportar_historico':
            exportar_historico()
            print("Histórico exportado para 'historico_teteu.txt'.")
            continue

        elif comando.lower() == 'exportar_para_notebook':
            exportar_para_notebook()
            print("Histórico exportado para 'historico_teteu.ipynb'.")
            continue

        elif comando.lower().startswith('modelo'):
            novo_modelo = comando[7:].strip()
            if novo_modelo:
                modelo_gpt = novo_modelo
                print(f"🤖 Modelo alterado para: {modelo_gpt}")
            else:
                print("⚠️ Informe o nome do modelo. Exemplo: modelo gpt-4")
            continue

        elif comando.lower().startswith('explica'):
            codigo = comando[8:]
            explicacao = perguntar_todas_ias(f"Explique detalhadamente o que faz o seguinte código Python:\n\n{codigo}")
            print(f"\nTETEU 🤖 {explicacao}")
            cur.execute('INSERT INTO historico (comando, resposta) VALUES (?, ?)', (comando, explicacao))
            con.commit()
            continue

        elif comando.lower().startswith('resuma'):
            texto = comando[7:]
            resumo = resumir_texto(texto)
            print(f"\nTETEU 🤖 {resumo}")
            cur.execute('INSERT INTO historico (comando, resposta) VALUES (?, ?)', (comando, resumo))
            con.commit()
            continue

        elif comando.lower().startswith('erro'):
            erro = comando[5:]
            explicacao = explicar_erro(erro)
            print(f"\nTETEU 🤖 {explicacao}")
            cur.execute('INSERT INTO historico (comando, resposta) VALUES (?, ?)', (comando, explicacao))
            con.commit()
            continue

        elif comando.lower() == 'quiz':
            quiz = quiz_programacao()
            print(f"\nTETEU 🤖 {quiz}")
            cur.execute('INSERT INTO historico (comando, resposta) VALUES (?, ?)', (comando, quiz))
            con.commit()
            continue

        elif comando.lower() == 'desafio':
            desafio = desafio_programacao()
            print(f"\nTETEU 🤖 {desafio}")
            cur.execute('INSERT INTO historico (comando, resposta) VALUES (?, ?)', (comando, desafio))
            con.commit()
            continue

        elif comando.lower().startswith('corrija'):
            codigo = comando[7:]
            correcao = corrigir_codigo(codigo)
            print(f"\nTETEU 🤖 {correcao}")
            cur.execute('INSERT INTO historico (comando, resposta) VALUES (?, ?)', (comando, correcao))
            con.commit()
            continue

        elif comando.lower() == 'materiais':
            materiais = sugerir_materiais()
            print(f"\nTETEU 🤖 {materiais}")
            cur.execute('INSERT INTO historico (comando, resposta) VALUES (?, ?)', (comando, materiais))
            con.commit()
            continue

        elif comando.lower().startswith('stackoverflow'):
            pergunta = comando[13:].strip()
            resposta = buscar_stackoverflow(pergunta)
            print(f"\nTETEU 🤖 {resposta}")
            cur.execute('INSERT INTO historico (comando, resposta) VALUES (?, ?)', (comando, resposta))
            con.commit()
            continue

        elif comando.lower().startswith('biblioteca'):
            nome = comando[11:].strip()
            explicacao = explicar_biblioteca(nome)
            print(f"\nTETEU 🤖 {explicacao}")
            cur.execute('INSERT INTO historico (comando, resposta) VALUES (?, ?)', (comando, explicacao))
            con.commit()
            continue

        elif comando.lower().startswith('analisar'):
            codigo = comando[8:].strip()
            analise = analisar_codigo(codigo)
            print(f"\nTETEU 🤖 {analise}")
            try:
                revisao = revisar_com_gpt(codigo)
                print(f"\nTETEU 🤖 Sugestão GPT:\n{revisao}")
                resposta_final = analise + "\n\nSugestão GPT:\n" + revisao
            except Exception as e:
                print("\nTETEU 🤖 Não foi possível acessar o GPT para revisão. Mostrando apenas análise automática.")
                resposta_final = analise
            cur.execute('INSERT INTO historico (comando, resposta) VALUES (?, ?)', (comando, resposta_final))
            con.commit()
            continue

        elif comando.lower().startswith('projetos'):
            nivel = comando[8:].strip() or "iniciante"
            sugestoes = sugerir_projetos(nivel)
            print(f"\nTETEU 🤖 {sugestoes}")
            cur.execute('INSERT INTO historico (comando, resposta) VALUES (?, ?)', (comando, sugestoes))
            con.commit()
            continue

        else:
            print("🤖 TETEU: Não entendi esse comando. Digite 'ajuda' para ver as opções.")

def limpar_arquivos_temporarios(padrao="temp_code*.py"):
    for arquivo in glob.glob(padrao):
        try:
            os.remove(arquivo)
        except Exception as e:
            print(f"Não foi possível remover {arquivo}: {e}")

# 🚀 Rodar
if __name__ == "__main__":
    try:
        teteu_loop()
    finally:
        limpar_arquivos_temporarios()
        con.close()

def perguntar_ao_cohere(prompt):
    try:
        co = cohere.Client(os.getenv("COHERE_API_KEY"))  # Ou coloque sua chave direto aqui
        resposta = co.generate(
            model='command',  # ou 'command-light'
            prompt=prompt,
            max_tokens=300
        )
        return resposta.generations[0].text.strip()
    except Exception as e:
        return f"Erro Cohere: {e}"

def perguntar_ao_huggingface(prompt):
    try:
        API_URL = "https://api-inference.huggingface.co/models/bigscience/bloomz-560m"  # Você pode trocar por outro modelo!
        headers = {"Authorization": f"Bearer {os.getenv('HF_API_KEY')}"}
        payload = {"inputs": prompt}
        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        resposta = response.json()
        # Alguns modelos retornam uma lista, outros um dicionário
        if isinstance(resposta, list) and resposta and "generated_text" in resposta[0]:
            return resposta[0]["generated_text"].strip()
        elif isinstance(resposta, dict) and "error" in resposta:
            return f"Erro Hugging Face: {resposta['error']}"
        else:
            return str(resposta)
    except Exception as e:
        return f"Erro Hugging Face: {e}"

def perguntar_todas_ias(prompt, contexto_limite=5):
    respostas = []

    # OpenAI GPT
    try:
        resposta_gpt = perguntar_ao_gpt(prompt, contexto_limite)
        if resposta_gpt and not resposta_gpt.startswith("⚠️ Sua cota da OpenAI acabou"):
            respostas.append("🤖 GPT:\n" + resposta_gpt)
    except Exception:
        pass

    # Cohere
    try:
        prompt_en = traduzir_para_ingles(prompt)
        resposta_cohere = perguntar_ao_cohere(prompt_en)
        if resposta_cohere and not "quota" in str(resposta_cohere).lower():
            respostas.append("🟣 Cohere:\n" + resposta_cohere)
    except Exception:
        pass

    # Hugging Face
    try:
        prompt_en = traduzir_para_ingles(prompt)
        resposta_hf = perguntar_ao_huggingface(prompt_en)
        if resposta_hf and not "quota" in str(resposta_hf).lower():
            respostas.append("🤗 Hugging Face:\n" + resposta_hf)
    except Exception:
        pass

    if respostas:
        return "\n\n".join(respostas)
    else:
        return "Nenhuma IA pôde responder no momento (todas atingiram o limite ou houve erro)."

def traduzir_para_ingles(texto):
    try:
        return GoogleTranslator(source='pt', target='en').translate(texto)
    except Exception:
        return texto

def baixar_repositorio_github(url):
    try:
        g = Github()
        repo_name = url.split("github.com/")[1]
        repo = g.get_repo(repo_name)
        arquivos = repo.get_contents("")
        for arquivo in arquivos:
            print(arquivo.name)
    except Exception as e:
        print(f"Erro ao baixar repositório: {e}")

def notificar(texto):
    toaster = ToastNotifier()
    toaster.show_toast("TETEU IA", texto, duration=5)

def mostrar_historico_interface(limite=10):
    cur.execute('SELECT id, comando, resposta FROM historico ORDER BY id DESC LIMIT ?', (limite,))
    registros = cur.fetchall()
    if registros:
        texto = ""
        for r in registros[::-1]:
            texto += f"\n🆔 {r[0]} — Comando: {r[1]}\nResposta: {r[2]}\n"
        return texto
    else:
        return "📭 Histórico vazio."

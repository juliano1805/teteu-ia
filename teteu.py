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

cur.execute('''
    CREATE TABLE IF NOT EXISTS ranking (
        nome TEXT PRIMARY KEY,
        pontos INTEGER DEFAULT 0,
        quizzes INTEGER DEFAULT 0
    )
''')
con.commit()

usuario = input("Digite seu nome para o ranking: ")
cur.execute('INSERT OR IGNORE INTO ranking (nome) VALUES (?)', (usuario,))
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
- exportar_para_notebook: Exporta o histórico para Jupyter Notebook
- modelo <nome>: Troca o modelo GPT (ex: modelo gpt-4)
- explica <codigo>: Explica detalhadamente um código Python
- resuma <texto>: Resume um texto longo
- erro <mensagem>: Explica um erro de Python e como resolver
- corrija <codigo>: Sugere melhorias e corrige um código Python
- quiz: Recebe uma pergunta de múltipla escolha sobre programação
- desafio: Recebe um desafio de programação para praticar
- ranking: Mostra o ranking de pontuação dos quizzes
- corrigir_exercicio <codigo_do_aluno> <gabarito>: Corrige automaticamente um exercício comparando com o gabarito
- explica_erro <mensagem de erro>: Explica o erro de execução do Python
- mini_projeto <tema>: Cria um mini-projeto guiado em etapas
- desafio_diario: Recebe um desafio de programação para o dia
- entrevista: Simula uma entrevista técnica de Python
- conceito <tema>: Explica um conceito de Python de forma didática
- materiais: Sugere materiais gratuitos para aprender Python
- materiais_personalizados <tema>: Sugere materiais gratuitos sobre um tema específico
- curva_aprendizado: Mostra sua evolução em quizzes e pontos
- exercicios_online <tema>: Sugere exercícios online gratuitos sobre um tema
- debug <codigo>: Simula a execução passo a passo de um código Python
- stackoverflow <pergunta>: Busca respostas no Stack Overflow
- biblioteca <nome>: Explica para que serve uma biblioteca Python e mostra exemplo
- analisar <codigo>: Analisa o código com linters e IA
- projetos <nível>: Sugere ideias de projetos por nível (iniciante, intermediário, avançado)
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

    def comando_ajuda():
        mostrar_ajuda()

    def comando_historico():
        print(mostrar_historico_interface())

    comandos = {
        "ajuda": comando_ajuda,
        "historico": comando_historico,
        # ...adicione os outros comandos
    }

    while True:
        comando = input(">>> ").strip().lower()
        if comando in comandos:
            comandos[comando]()
        else:
            print("🤖 TETEU: Não entendi esse comando. Digite 'ajuda' para ver as opções.")

def mostrar_ranking():
    cur.execute('SELECT nome, pontos, quizzes FROM ranking ORDER BY pontos DESC, quizzes DESC')
    for i, (nome, pontos, quizzes) in enumerate(cur.fetchall(), 1):
        print(f"{i}º {nome} — {pontos} pontos ({quizzes} quizzes)")

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

def atualizar_pontuacao(nome, pontos_ganhos):
    cur.execute('UPDATE ranking SET pontos = pontos + ?, quizzes = quizzes + 1 WHERE nome = ?', (pontos_ganhos, nome))
    con.commit()

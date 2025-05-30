# teteu-ia
---

# 🤖 TETEU IA — Assistente de Código Multiplataforma

TETEU é um assistente de programação em Python que integra múltiplas IAs (OpenAI, Cohere, Hugging Face) para responder perguntas, analisar códigos, sugerir projetos, explicar erros, exportar histórico e muito mais — tudo pelo terminal.

---

## ✨ Funcionalidades

- **Respostas inteligentes**: Usa APIs de OpenAI, Cohere e Hugging Face para responder dúvidas de programação.
- **Análise automática de código**: Integra linters (flake8, pylint, mypy, black) para revisão e sugestões de melhoria.
- **Banco de dados local**: Histórico de interações salvo em SQLite, com busca e exportação.
- **Exportação para Jupyter Notebook**: Gere um notebook com todo o histórico de perguntas e respostas.
- **Tradução automática**: Prompts traduzidos para inglês para melhor performance das IAs.
- **Ranking e gamificação**: Sistema de pontos e ranking para quizzes.
- **Funcionalidades extras**: 
  - Sugestão de projetos
  - Quizzes e desafios
  - Correção automática de exercícios
  - Explicação de erros de execução
  - Mini-projetos guiados
  - Desafio diário
  - Simulador de entrevistas técnicas
  - Explicação de conceitos
  - Sugestão de materiais personalizados
  - Análise de curva de aprendizado
  - Sugestão de exercícios online
  - Modo debug (execução passo a passo)
  - Integração com Stack Overflow e GitHub
  - Notificações no Windows

---

## 🚀 Como rodar

1. **Clone o repositório e instale as dependências:**
   ```sh
   pip install -r requirements.txt
   ```

2. **Configure as variáveis de ambiente com suas chaves de API:**
   - `OPENAI_API_KEY`
   - `COHERE_API_KEY`
   - `HF_API_KEY`

3. **Execute o programa:**
   ```sh
   python teteu.py
   ```

---

## 🕹️ Exemplos de uso

- `explica print("Olá Mundo")` — Explica um código Python
- `corrija for i in range(5) print(i)` — Sugere melhorias e corrige código
- `projetos intermediario` — Sugere ideias de projetos
- `quiz` — Recebe uma pergunta de múltipla escolha
- `historico` — Mostra as últimas interações
- `exportar_para_notebook` — Exporta o histórico para Jupyter Notebook
- `corrigir_exercicio <codigo_do_aluno> <gabarito>` — Corrige automaticamente um exercício
- `explica_erro <mensagem de erro>` — Explica um erro de execução do Python
- `mini_projeto <tema>` — Cria um mini-projeto guiado em etapas
- `desafio_diario` — Recebe um desafio de programação para o dia
- `entrevista` — Simula uma entrevista técnica de Python
- `conceito <tema>` — Explica um conceito de Python de forma didática
- `materiais_personalizados <tema>` — Sugere materiais gratuitos sobre um tema específico
- `curva_aprendizado` — Mostra sua evolução em quizzes e pontos
- `exercicios_online <tema>` — Sugere exercícios online gratuitos sobre um tema
- `debug <codigo>` — Simula a execução passo a passo de um código Python

---

## 💡 Meu papel no projeto

Desenvolvi este projeto **individualmente**, contando com o auxílio de ferramentas de IA como o GitHub Copilot para acelerar o desenvolvimento, solucionar dúvidas e aprimorar o código.  
Implementei, adaptei e testei todas as funcionalidades, além de integrar diferentes APIs e ferramentas Python.  
Durante o processo, aprimorei meus conhecimentos em APIs de IA, automação de testes, integração de ferramentas Python e organização de projetos.

---

## 🛠️ Tecnologias e bibliotecas

- Python 3.10+
- [OpenAI API](https://platform.openai.com/)
- [Cohere API](https://cohere.com/)
- [Hugging Face Inference API](https://huggingface.co/inference-api)
- SQLite, nbformat, deep-translator, win10toast, flake8, pylint, mypy, black, RestrictedPython, requests, github

---

## 📄 Licença

Projeto acadêmico/experimental. Uso livre para fins de estudo.

---

## 📝 NOTA DE ATUALIZAÇÃO — Versão 2.0

- Sistema de ranking e pontuação para quizzes
- Correção automática de exercícios (`corrigir_exercicio`)
- Explicação de erros de execução (`explica_erro`)
- Mini-projetos guiados (`mini_projeto`)
- Desafio diário de programação (`desafio_diario`)
- Simulador de entrevistas técnicas (`entrevista`)
- Explicação de conceitos de Python (`conceito`)
- Sugestão de materiais personalizados (`materiais_personalizados`)
- Análise de curva de aprendizado (`curva_aprendizado`)
- Sugestão de exercícios online (`exercicios_online`)
- Modo debug: simulação passo a passo de código (`debug`)
- Integração com Stack Overflow e GitHub
- Exportação do histórico para Jupyter Notebook
- Notificações no Windows
- Diversas melhorias de usabilidade e organização do código

---

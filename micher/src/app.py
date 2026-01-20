####### CARREGAR DADOS #####
import os
import json
import pandas as pd
import subprocess
import streamlit as st

# BASE_DIR aponta para a raiz do projeto (uma pasta acima de src)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# CONFIGURAÇÕES
MODELO = "gpt-oss"
MAX_TOKENS = 300  # limite de tokens, apenas para referência

# CARREGAR ARQUIVOS JSON E CSV
perfil = json.load(open(os.path.join(BASE_DIR, 'data', 'perfil_investidor.json'), encoding='utf-8'))
transacoes = pd.read_csv(os.path.join(BASE_DIR, 'data', 'transacoes.csv'))
historico = pd.read_csv(os.path.join(BASE_DIR, 'data', 'historico_atendimento.csv'))
produtos = json.load(open(os.path.join(BASE_DIR, 'data', 'produtos_financeiros.json'), encoding='utf-8'))

### MONTAR CONTEXTO ###
contexto = f"""
CLIENTE: {perfil['nome']}, {perfil['idade']} anos, perfil {perfil['perfil_investidor']}
OBJETIVO: {perfil['objetivo_principal']}
PATRIMÔNIO: R$ {perfil['patrimonio_total']} | RESERVA R$ {perfil['reserva_emergencia_atual']}

TRANSAÇÕES RECENTES:
{transacoes.to_string(index=False)}

ATENDIMENTOS ANTERIORES:
{historico.to_string(index=False)}

PRODUTOS DISPONÍVEIS:
{json.dumps(produtos, indent=2, ensure_ascii=False)}
"""

### SYSTEM PROMPT ###
SYSTEM_PROMPT = """Você é o Micher, um educador financeiro amigável e didático.

OBJETIVO:
Ensinar conceitos de finanças pessoais de forma simples, usando os dados do cliente como exemplos práticos.

REGRAS:
1- Nunca recomente investimentos específicos - apenas explique como funciona
2- Use os dados fornecidos para exemplos personalizados
3- Linguagem simples, como se explicasse para um amigo
4- Se não souber algo, admita: "Não tenho essa informação, mas posso explicar..."
5- Sempre pergunte se o cliente entendeu
[CONTEXTO: USO DA BASE DE CONHECIMENTO]
"""

### FUNÇÃO PARA CHAMAR OLLAMA VIA CLI ###
def perguntar(msg):
    """
    Chama o modelo Ollama local usando a CLI, adaptado para a versão sem '--prompt'.
    """
    prompt = f"{SYSTEM_PROMPT}\n\nCONTEXTO DO CLIENTE:\n{contexto}\n\nPergunta: {msg}"
    try:
        result = subprocess.run(
            ["ollama", "run", MODELO, prompt],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode != 0:
            return f"Erro ao executar Ollama CLI: {result.stderr.strip()}"
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        return "O Ollama demorou muito para responder."
    except Exception as e:
        return f"Ocorreu um erro ao chamar Ollama: {e}"


### INTERFACE STREAMLIT ###
st.set_page_config(page_title="Micher - Educador Financeiro", page_icon="👨‍🎓")

st.title("👨‍🎓 Sou Micher, seu educador Financeiro")

# Inicializa o histórico de chat no Streamlit
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Input do usuário
if pergunta_usuario := st.chat_input("Sua dúvida sobre finanças..."):
    st.session_state.chat_history.append({"role": "user", "message": pergunta_usuario})
    with st.spinner("Gerando resposta..."):
        resposta = perguntar(pergunta_usuario)
        st.session_state.chat_history.append({"role": "assistant", "message": resposta})

# Exibir histórico
for chat in st.session_state.chat_history:
    if chat["role"] == "user":
        st.chat_message("user").write(chat["message"])
    else:
        st.chat_message("assistant").write(chat["message"])

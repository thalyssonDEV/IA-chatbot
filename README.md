# NexusBot 🤖

NexusBot é um projeto de chatbot inteligente e multifuncional, desenvolvido com Python e o framework FastAPI. Ele utiliza o poder do modelo de IA generativa `gemini-1.5-flash-latest` da Google para fornecer respostas coesas e contextuais, tanto para texto quanto para imagens.

## 🚀 Como Executar Localmente

Siga estes passos para rodar o projeto na sua máquina local.

### 1. Pré-requisitos

* **Python 3.8+**
* **Git**

### 2. Instalação

Abra seu terminal e siga os comandos abaixo:

```bash
# 1. Clone o repositório do projeto
git clone [https://github.com/thalyssonDEV/nexusbot.git](https://github.com/thalyssonDEV/nexusbot.git)

# 2. Navegue para a pasta do projeto
cd nexusbot

# 3. (Recomendado) Crie e ative um ambiente virtual
python -m venv venv
# No Windows:
# .\venv\Scripts\activate
# No macOS/Linux:
# source venv/bin/activate

# 4. Instale todas as dependências necessárias
pip install -r requirements.txt
```

3. Configuração
A aplicação precisa da sua chave da API do Google Gemini para funcionar.

Na raiz do projeto, crie um arquivo chamado .env.

Dentro deste arquivo, adicione sua chave no seguinte formato:

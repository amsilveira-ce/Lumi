# Lumi 🌟 - Elder Care AI Assistant

**AI-Powered Elder Companion with Voice Interface, Safety Monitoring & Smart Calendar**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![React 18](https://img.shields.io/badge/react-18-blue.svg)](https://reactjs.org/)
[![Google Gemini](https://img.shields.io/badge/Gemini-AI-orange.svg)](https://ai.google.dev/)
[![A2A Protocol](https://img.shields.io/badge/A2A-Protocol-green.svg)](https://a2a-protocol.github.io/)

> **Empowering elders with AI companionship that remembers, understands, and protects.**

Lumi is an intelligent elder care system that combines conversational AI powered by Google Gemini with real-time safety monitoring, voice interface, smart calendar, and emergency intervention capabilities.

---

## 🎯 Key Features

### 🤖 **Multi-Agent AI System**
- **Orchestrator** - Coordena todos os agentes e roteamento de mensagens
- **Safety Agent** - Detecta crises e situações de emergência com IA
- **Conversation Agent** - Respostas empáticas via Google Gemini
- **Memory Agent** - Gerenciamento inteligente de contexto

### 🗣️ **Complete Voice Interface**
- **Speech-to-Text** - Reconhecimento de voz em português (Web Speech API)
- **Text-to-Speech** - Respostas faladas automaticamente
- **Elder-Friendly Controls** - Botões grandes, feedback visual claro
- **Real-time Transcription** - Veja o que você está dizendo enquanto fala

### 📅 **Smart Calendar (MCP)**
- Adicionar, editar e remover eventos
- Lembretes configuráveis
- Visualização de eventos futuros
- Integração com agentes via Model Context Protocol

### 🛡️ **Intelligent Safety Monitoring**
- **3-Tier Risk Assessment**:
  - 🟢 SAFE - Conversação normal
  - 🟡 MEDIUM - Angústia emocional, confusão
  - 🔴 HIGH - Emergência médica (quedas, dor no peito, etc.)
- **Automatic Response** - Notificação de contatos, intervenção de crise
- **Pattern Detection** - Detecta problemas recorrentes

### 🧠 **Powered by Google Gemini**
- Compreensão contextual avançada
- Respostas naturais e empáticas
- Classificação de risco inteligente
- Memória de conversas

---

## 🚀 Quick Start

### Pré-requisitos

- Python 3.11+
- Node.js 16+
- Chave de API do Google Gemini ([Obter aqui](https://aistudio.google.com/apikey))
- Chrome ou Edge (para funcionalidades de voz)

### Instalação Rápida

```bash
# 1. Clone o repositório
git clone <seu-repositorio>
cd Lumi

# 2. Configure o Backend
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac ou venv\Scripts\activate no Windows
pip install -r requirements.txt

# 3. Configure variáveis de ambiente
cp .env.example .env
# Edite .env e adicione sua GEMINI_API_KEY

# 4. Configure o Frontend
cd ../frontend
npm install
```

### Execução (Linux/Mac)

```bash
# Iniciar todos os agentes (um comando!)
./start_agents.sh

# Em outro terminal, iniciar o frontend
cd frontend
npm start
```

### Execução Manual

Veja o guia completo em [SETUP.md](SETUP.md)

---

## 🎮 Como Usar

1. **Acesse** `http://localhost:3000`
2. **Navegue** entre modos usando o botão "🔄 Switch to..."
3. **Mode Conversation:**
   - Clique em "🔇 Voz Desligada" para ativar voz
   - Use "🎤 Falar" para capturar sua voz
   - Ouça respostas automaticamente
   - Digite mensagens normalmente se preferir

---

## 🏗️ Arquitetura

```
┌─────────────────────────────────────────────┐
│         React Frontend (Port 3000)          │
│   • Voice Input (STT)                       │
│   • Voice Output (TTS)                      │
│   • Elder-Friendly UI                       │
└──────────────────┬──────────────────────────┘
                   │ A2A JSONRPC
                   ▼
┌─────────────────────────────────────────────┐
│         ORCHESTRATOR (Port 8082)            │
│   Context-First Routing & Coordination      │
└───┬─────────┬──────────┬─────────────┬─────┘
    │         │          │             │
    ▼         ▼          ▼             ▼
┌────────┐ ┌────────┐ ┌────────┐ ┌──────────┐
│ Safety │ │ Conver │ │ Memory │ │ Calendar │
│ Agent  │ │ sation │ │ Agent  │ │   Tool   │
│ (8080) │ │ (8081) │ │ (8083) │ │  (MCP)   │
└────┬───┘ └────┬───┘ └────┬───┘ └────┬─────┘
     │          │          │          │
     └──────────┴──────────┴──────────┘
                    │
                    ▼
            Google Gemini API
```

### Three-Layer Context System

1. **Conversation Context** - Últimas conversas com timestamps
2. **Active Topics** - Tópicos atuais com nível de confiança
3. **User State** - Perfil, preferências, estado emocional

Isso permite que o sistema:
- Lembre o nome do seu neto
- Saiba quando você tomou remédio
- Detecte padrões de solidão
- Forneça respostas personalizadas

---

## 🛠️ Tech Stack

### Backend
- **Python 3.11+**
- **Google Gemini AI** - LLM principal
- **A2A Protocol** - Comunicação entre agentes
- **MCP** - Model Context Protocol para ferramentas
- **Starlette/Uvicorn** - ASGI server

### Frontend
- **React 18** - Framework UI
- **TypeScript** - Type safety
- **Web Speech API** - STT & TTS
- **Tailwind CSS** - Styling
- **Lucide Icons** - Ícones

---

## 📂 Estrutura do Projeto

```
Lumi/
├── backend/
│   ├── src/
│   │   ├── orchestrator/         # Coordenador principal
│   │   ├── safety/               # Detecção de crises
│   │   ├── conversation_agent/   # Geração de respostas (Gemini)
│   │   ├── memory_agent/         # Gestão de contexto
│   │   └── calendar_tool/        # Calendário MCP
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ConversationMode.tsx  # Interface principal
│   │   │   ├── ChatPanel.tsx
│   │   │   ├── WidgetPanel.tsx
│   │   │   └── widgets/              # Widgets dinâmicos
│   │   └── hooks/
│   │       ├── useVoiceInput.ts      # Hook STT
│   │       ├── useTextToSpeech.ts    # Hook TTS
│   │       └── useOnboardingAgent.ts # Cliente A2A
│   └── package.json
│
├── start_agents.sh       # Inicia todos os agentes (Linux/Mac)
├── stop_agents.sh        # Para todos os agentes
├── README.md             # Este arquivo
└── SETUP.md              # Guia detalhado de configuração
```

---

## 🎓 Documentação

- **[README.md](README.md)** ← Você está aqui
- **[SETUP.md](SETUP.md)** - Guia completo de configuração e uso
- **[backend/.env.example](backend/.env.example)** - Variáveis de ambiente

---

## 🎯 Demo Scenarios

### Scenario 1: Conversação por Voz
```
[Usuário clica em "🎤 Falar"]
User: "Olá, como está o tempo hoje?"
→ Transcrição aparece em tempo real
→ Gemini gera resposta empática
→ Resposta é falada automaticamente
```

### Scenario 2: Emergência Médica
```
User: "Estou sentindo dor no peito"
→ Safety Agent: Risk Level HIGH
→ Orchestrator: Aciona protocolo de emergência
→ UI: Mostra EmergencyAlert com contatos
→ Actions: Notifica familiares automaticamente
```

### Scenario 3: Gerenciamento de Calendário
```
User: "Adicionar consulta médica amanhã às 14h"
→ Calendar Tool: Cria evento
→ Reminder: 1 hora antes
→ Agent: "Consulta agendada! Vou lembrá-lo 1 hora antes."
```

---

## 🔮 Roadmap

### ✅ Fase 1 (Completo)
- ✅ Migração para Google Gemini
- ✅ Interface de voz completa (STT + TTS)
- ✅ Ferramenta de calendário MCP
- ✅ Sistema multi-agente funcionando

### 🚧 Fase 2 (Próxima)
- [ ] Integração completa do calendário com agentes
- [ ] Persistência em banco de dados
- [ ] Suporte a múltiplos usuários
- [ ] Dashboard para cuidadores

### 🔜 Fase 3 (Futuro)
- [ ] App mobile (React Native)
- [ ] Integração com Google Calendar
- [ ] Detecção de emoções por voz
- [ ] Suporte multilíngue

---

## 🤝 Contribuindo

1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/NovaFuncionalidade`)
3. Commit suas mudanças (`git commit -m 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/NovaFuncionalidade`)
5. Abra um Pull Request

---

## 📝 Licença

Este projeto é privado e proprietário.

---

## 🙏 Agradecimentos

- **Google** - Gemini AI API
- **Anthropic** - A2A Protocol
- **Comunidade Open Source** - Frameworks e ferramentas

---

## 📞 Suporte

Para dúvidas ou problemas:
1. Consulte [SETUP.md](SETUP.md)
2. Verifique os logs em `logs/`
3. Abra uma issue no repositório

---

<div align="center">

**🌟 Desenvolvido com ❤️ para melhorar o cuidado com idosos**

*"Tecnologia que cuida, não complica"*

[🚀 Começar](SETUP.md) | [📖 Documentação](SETUP.md)

</div>

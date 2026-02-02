# TTS com Gemini 2.5 Flash - Implementação Oficial

## ✅ Implementação Baseada no Código Oficial do Google

Sistema de Text-to-Speech usando **gemini-2.5-flash-preview-tts** seguindo exatamente a documentação e código oficial do Google.

## 🎯 Modelo e Configuração

### Modelo
- **gemini-2.5-flash-preview-tts** - Modelo oficial para TTS do Gemini

### Formato de Áudio
- **Input**: Texto simples
- **Output**: PCM raw (audio/L16;rate=24000)
- **Conversão**: Automática para WAV para reprodução
- **Qualidade**: 16-bit, 24kHz, Mono

## 🎭 Vozes Disponíveis

Baseado no código oficial do Google:

1. **Puck** (padrão) - Voz natural e amigável
2. **Charon** - Voz mais profunda
3. **Kore** - Voz feminina suave
4. **Fenrir** - Voz masculina forte
5. **Aoede** - Voz melodiosa
6. **Zephyr** - Voz suave e calorosa (do exemplo oficial)

## 📝 API Key

Configurada em `.env`:
```bash
GEMINI_API_KEY=AIzaSyAQhkXikoBQWXb0PrfklcWO-ap_SFPkJFY
```

## 🚀 Como Funciona

1. Envia requisição com `responseModalities: ['audio']`
2. Gemini processa e gera áudio PCM raw
3. Recebe base64 do áudio em `inlineData`
4. Converte PCM para WAV (adiciona header WAV)
5. Salva temporariamente e reproduz

## 💻 Uso no Código

### Básico

```dart
final ttsService = GeminiTTSService();

// Voz padrão (Puck)
await ttsService.speak("Olá, como posso ajudar você?");

// Voz específica
await ttsService.speak("Prazer em conhecê-lo!", voiceName: "Kore");
```

### Chat com IA

```dart
// Gerar resposta e falar
final model = GeminiConfig.model;
final response = await model.generateContent([
  Content.text("Como você está?")
]);

await ttsService.speak(response.text);
```

### Múltiplas Frases

```dart
await ttsService.speakWithPauses([
  "Encontrei aquelas fotos do Leo.",
  "Elas estão no álbum de família.",
  "Vamos ligar para ele agora?"
],
  pauseDuration: Duration(milliseconds: 800),
  voiceName: "Aoede"
);
```

### Ver Vozes Disponíveis

```dart
print(GeminiTTSService.availableVoices);
// [Puck, Charon, Kore, Fenrir, Aoede, Zephyr]
```

## 🔧 Estrutura da Requisição

Seguindo o código oficial Python:

```json
{
  "contents": [
    {
      "role": "user",
      "parts": [
        {"text": "Texto para falar"}
      ]
    }
  ],
  "generationConfig": {
    "temperature": 1.0,
    "responseModalities": ["audio"],
    "speechConfig": {
      "voiceConfig": {
        "prebuiltVoiceConfig": {
          "voiceName": "Puck"
        }
      }
    }
  }
}
```

## 🔍 Debug / Logs

O serviço imprime logs detalhados:

```
Requesting Gemini TTS with model: gemini-2.5-flash-preview-tts
Voice: Puck
Text: Olá, como posso ajudar você?
Response status: 200
Found audio data with mime type: audio/L16;rate=24000
Audio decoded: 245760 bytes
Converted to WAV: 245804 bytes
Audio saved to: /tmp/gemini_tts_1234567890.wav
```

## 🎯 Conversão PCM → WAV

Implementação baseada no código oficial:

1. **Parse do mime type**: Extrai bits per sample e sample rate
2. **Cria header WAV**: 44 bytes seguindo formato RIFF/WAVE
3. **Combina header + dados**: Arquivo WAV completo pronto para reprodução

```dart
// Exemplo de mime type
"audio/L16;rate=24000"
// L16 = 16 bits per sample
// rate=24000 = 24kHz sample rate
```

## 📊 Vantagens do TTS Gemini

| Recurso | Gemini TTS | TTS Tradicional |
|---------|-----------|-----------------|
| **Contextual** | ✅ Entende contexto | ❌ |
| **Entonação** | ✅ Dinâmica | ⚠️ Fixa |
| **Naturalidade** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Integração IA** | ✅ Mesma API | ❌ |
| **Vozes** | 6 humanizadas | Varia |
| **Qualidade** | 24kHz PCM | Varia |

## ⚠️ Troubleshooting

### Erro 404 - Model not found

Certifique-se de usar: `gemini-2.5-flash-preview-tts`

### Erro 400 - Invalid request

Verifique o formato da requisição:
- `responseModalities` deve ser `["audio"]` (minúsculo)
- `voiceName` deve ser uma das vozes válidas

### No audio data in response

O modelo pode não ter gerado áudio. A resposta completa é impressa no console para debug.

### Áudio não reproduz

1. Verifique se o arquivo WAV foi criado
2. Confirme que tem permissão de escrita em `/tmp`
3. Teste com texto simples primeiro

## 🚀 Exemplo Completo de Chat com TTS

```dart
// Serviço completo: pergunta → resposta → fala
Future<void> chatComTTS(String pergunta) async {
  // 1. Gerar resposta com Gemini
  final model = GeminiConfig.model;
  final response = await model.generateContent([
    Content.text(pergunta)
  ]);

  final resposta = response.text ?? 'Desculpe, não consegui gerar uma resposta.';

  // 2. Falar a resposta com TTS
  final ttsService = GeminiTTSService();
  await ttsService.speak(resposta, voiceName: 'Kore');

  print('Pergunta: $pergunta');
  print('Resposta: $resposta');
}

// Uso
await chatComTTS('Qual é a capital do Brasil?');
```

## 📚 Código Fonte Oficial

Implementação baseada em:
- [Exemplo Python oficial do Google](https://ai.google.dev/gemini-api/docs/audio)
- [Documentação Gemini Audio API](https://ai.google.dev/gemini-api/docs/audio)

## 🎯 Diferenças do Código Python

| Python | Dart/Flutter |
|--------|--------------|
| `generate_content_stream` | `generateContent` (não-streaming) |
| Salva WAV diretamente | Converte PCM → WAV |
| `google-genai` SDK | HTTP direto |
| Suporte multi-speaker | Single speaker |

## 🔮 Próximos Passos

### Streaming (Future)
```dart
// Reproduzir enquanto gera (quando implementar)
await ttsService.speakStreaming(text);
```

### Multi-Speaker (Future)
```dart
// Múltiplos falantes em uma conversa
await ttsService.speakMultiSpeaker({
  'Speaker 1': {'text': 'Olá!', 'voice': 'Zephyr'},
  'Speaker 2': {'text': 'Oi!', 'voice': 'Puck'}
});
```

### Cache de Áudio
```dart
// Cache de frases comuns
final cache = AudioCache();
await cache.speakCached('Olá, como posso ajudar?');
```

## ✅ Status de Implementação

- ✅ Modelo correto: gemini-2.5-flash-preview-tts
- ✅ Formato de requisição: Seguindo código oficial
- ✅ 6 vozes disponíveis
- ✅ Conversão PCM → WAV
- ✅ Reprodução de áudio
- ✅ Integração na UI
- ✅ Tratamento de erros
- ✅ Debug logging

## 🎤 Teste Agora

**Recarregue a página** (Ctrl+R ou Cmd+R) e clique no ícone de alto-falante! 🔊

O TTS está usando **SOMENTE o Gemini** com o modelo oficial correto!

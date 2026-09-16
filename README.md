# 🤖 Obsidian Gemini Bot

Este projeto é um Bot do Telegram integrado à inteligência artificial do Google (Gemini) e atua como um assistente RAG (Retrieval-Augmented Generation) para um "Segundo Cérebro" no Obsidian.

## 🛠️ Tecnologias Usadas
- **Python**: Linguagem principal do projeto.
- **`python-telegram-bot`**: Biblioteca para a comunicação com a API do Telegram.
- **Gemini API (`google-generativeai`)**: Inteligência artificial responsável por processar as mensagens (texto e áudio) e gerar as respostas. Usamos o modelo `gemini-3.5-flash` por ser nativamente multimodal e ultra-rápido.
- **VBScript & Batch Script**: Utilizados para garantir a inicialização invisível (background) do bot no Windows (`.vbs` na pasta Startup).

## ⚙️ Como as tecnologias foram integradas
1. O bot atua via *Long Polling*, aguardando ativamente mensagens do usuário autenticado no Telegram.
2. Sempre que uma mensagem (texto ou voz) chega, o bot varre a pasta local do Obsidian (lendo todos os arquivos `.md`).
3. Todo esse texto, junto com a mensagem do usuário (ou o arquivo `.ogg` no caso de áudio), é injetado no prompt do Gemini.
4. O Gemini foi configurado utilizando o recurso de `response_schema` (Roteamento via JSON) para obrigatoriamente decidir se a intenção do usuário é **salvar uma nota** ou **fazer uma pergunta**.
5. Se for nota, o bot faz um append no arquivo final. Se for pergunta, ele responde no próprio chat do Telegram consultando o contexto.

## ⚠️ Principais Problemas Enfrentados e Soluções
- **Problema de Sincronização do Google Drive:** 
  - **Causa:** O Google Drive nem sempre monta o disco virtual `G:\` no exato momento que o Windows liga, o que causava falha no script de inicialização caso o bot tentasse ler a pasta do Obsidian que ainda não estava lá.
  - **Solução:** A pasta do projeto (código-fonte) foi migrada de dentro do Drive para o disco local (`C:\Users\mathe\Desktop\pastas - trabalho\Obsidian_Gemini_Bot`). Adicionalmente, foi colocada uma lógica de verificação `if not vault_path.exists()` no código Python para avisar o usuário amigavelmente caso o disco `G:\` ainda não esteja montado ao receber uma mensagem.
- **Modelo Gemini Descontinuado:**
  - **Causa:** O modelo inicialmente pensado (`gemini-1.5-flash`) não estava mais disponível ou compatível com a API no contexto do SDK.
  - **Solução:** Atualizamos rapidamente a chamada para `gemini-3.5-flash`, o que trouxe a vantagem adicional de possuir suporte nativo para leitura e interpretação direta de arquivos de áudio sem depender de bibliotecas externas de Speech-to-Text.

import os
import asyncio
import json
from pathlib import Path
import ollama
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN", "")
ALLOWED_USER_ID = int(os.getenv("ALLOWED_USER_ID", 0))
OBSIDIAN_VAULT = r"g:\Meu Drive\Obsidian Vault"
vault_path = Path(OBSIDIAN_VAULT)

ollama_client = ollama.Client(host='http://127.0.0.1:11434')

# ================= FERRAMENTAS DO AGENTE =================

def search_notes(query: str) -> str:
    """Busca notas no cofre do Obsidian que contenham a palavra-chave especificada (case-insensitive).
    Retorna uma lista de caminhos e nomes de arquivos encontrados.
    """
    if not vault_path.exists():
        return "Erro: O disco G: não está montado ou acessível."
        
    resultados = []
    query_lower = query.lower()
    for filepath in vault_path.rglob('*.md'):
        if any(ignored in filepath.parts for ignored in ['.obsidian', '.gemini', '.agents']):
            continue
        # Busca no nome do arquivo
        if query_lower in filepath.name.lower():
            resultados.append(str(filepath.relative_to(vault_path)))
            continue
        # Busca no conteudo
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                if query_lower in f.read().lower():
                    resultados.append(str(filepath.relative_to(vault_path)))
        except Exception:
            pass
            
    if not resultados:
        return f"Nenhuma nota encontrada contendo: '{query}'"
    
    return "Notas encontradas:\n" + "\n".join(resultados[:20]) # max 20 resultados

def read_note(filename: str) -> str:
    """Lê o conteúdo completo de uma nota específica. 
    Passe o caminho relativo ou apenas o nome do arquivo com a extensão .md (ex: 'Estudos.md').
    """
    if not vault_path.exists():
        return "Erro: Cofre inacessível."
        
    target_path = vault_path / filename
    if target_path.exists() and target_path.is_file():
        try:
            with open(target_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            return f"Erro ao ler arquivo: {e}"
            
    # Fallback: busca por nome
    for filepath in vault_path.rglob(filename if filename.endswith('.md') else f"{filename}.md"):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return f"--- {filepath.relative_to(vault_path)} ---\n" + f.read()
        except Exception as e:
            pass
            
    return f"Nota '{filename}' não encontrada."

def write_note(filename: str, content: str) -> str:
    """Cria uma NOVA nota ou SOBRESCREVE uma existente com o conteúdo especificado.
    'filename' deve incluir a extensão .md (ex: 'ideias.md').
    """
    if not filename.endswith('.md'):
        filename += '.md'
    target_path = vault_path / filename
    try:
        # Se contiver subpastas, tenta criar
        target_path.parent.mkdir(parents=True, exist_ok=True)
        with open(target_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Nota '{filename}' criada/sobrescrita com sucesso."
    except Exception as e:
        return f"Erro ao escrever nota: {e}"

def append_note(filename: str, content: str) -> str:
    """Adiciona texto ao final de uma nota existente.
    Ideal para adicionar itens a uma lista de tarefas, diário ou lembretes.
    """
    if not filename.endswith('.md'):
        filename += '.md'
    # Busca a nota pra garantir que acerta o caminho
    target_path = vault_path / filename
    if not target_path.exists():
        for filepath in vault_path.rglob(filename):
            target_path = filepath
            break
            
    try:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        with open(target_path, 'a', encoding='utf-8') as f:
            f.write("\n" + content + "\n")
        return f"Conteúdo adicionado ao final da nota '{target_path.name}'."
    except Exception as e:
        return f"Erro ao adicionar na nota: {e}"

AVAILABLE_TOOLS = {
    'search_notes': search_notes,
    'read_note': read_note,
    'write_note': write_note,
    'append_note': append_note
}

# ================= TELEGRAM HANDLERS =================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id != ALLOWED_USER_ID:
        return

    if not update.message.text:
        await update.message.reply_text("⚠️ Por favor, envie apenas texto.")
        return

    msg_temporaria = await update.message.reply_text("Processando com Inteligência (Agentic Mode)... ⏳")
    
    system_prompt = (
        "Você é o assistente inteligente do Obsidian (Segundo Cérebro) do Matheus. "
        "Você tem acesso direto aos arquivos do usuário através de ferramentas (tools). "
        "Você DEVE usar as ferramentas sempre que o usuário pedir para buscar informações, ler notas ou salvar novas anotações. "
        "Não invente informações. Se o usuário pedir algo sobre as anotações dele, sempre USE a ferramenta `search_notes` primeiro, "
        "e depois `read_note` para ler o conteúdo. Se o usuário quiser criar uma nota, use `write_note` ou `append_note`. "
        "Após usar as ferramentas necessárias, responda de forma natural em português o que você fez ou encontrou."
    )
    
    messages = [
        {'role': 'system', 'content': system_prompt},
        {'role': 'user', 'content': update.message.text}
    ]

    try:
        # Loop de Agente
        while True:
            response = await asyncio.to_thread(
                ollama_client.chat,
                model='qwen2.5-coder:7b',
                messages=messages,
                tools=[search_notes, read_note, write_note, append_note]
            )
            
            message = response['message']
            messages.append(message)
            
            if not message.get('tool_calls'):
                break # A IA não quer mais usar ferramentas, respondeu texto final
                
            for tool_call in message['tool_calls']:
                func_name = tool_call['function']['name']
                args = tool_call['function']['arguments']
                
                print(f"Executando ferramenta: {func_name} com args: {args}")
                
                if func_name in AVAILABLE_TOOLS:
                    try:
                        result = AVAILABLE_TOOLS[func_name](**args)
                    except Exception as e:
                        result = f"Error execution tool: {e}"
                else:
                    result = f"Tool {func_name} not found."
                
                messages.append({
                    'role': 'tool',
                    'content': str(result),
                    'name': func_name
                })
                
        final_response = message.get('content', "Feito!")
        if not final_response or not final_response.strip():
            final_response = "Ação concluída com sucesso no seu cofre!"
            
        await update.message.reply_text(f"🧠 {final_response}")
        
    except Exception as e:
        await update.message.reply_text(f"❌ Ocorreu um erro: {e}")
    finally:
        await context.bot.delete_message(chat_id=update.message.chat_id, message_id=msg_temporaria.message_id)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id == ALLOWED_USER_ID:
        await update.message.reply_text("Bot Agentic iniciado! Você pode pedir para eu pesquisar, ler ou criar anotações no seu Obsidian.")

def main():
    print("Iniciando Bot...")
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    try:
        asyncio.get_event_loop()
    except RuntimeError:
        asyncio.set_event_loop(asyncio.new_event_loop())

    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()

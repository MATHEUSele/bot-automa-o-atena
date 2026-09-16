Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "g:\Meu Drive\Obsidian Vault\Projetos\bot-automa-o-atena"
WshShell.Run ".\.venv\Scripts\pythonw.exe bot.py", 0
Set WshShell = Nothing

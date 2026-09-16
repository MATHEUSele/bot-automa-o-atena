Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "C:\Users\mathe\Desktop\pastas - trabalho\Obsidian_Gemini_Bot"
WshShell.Run "pythonw.exe bot.py", 0
Set WshShell = Nothing

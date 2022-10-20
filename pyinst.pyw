import sys, os
import tkinter as tk
from tkinter import filedialog

print(
    """
=======================================
Create a .exe file from a Python Script
=======================================

Select the Python script you want to create the .exe from:

""")

root = tk.Tk()
root.withdraw()

file = filedialog.askopenfilename(initialdir = "./", title = "Select file", filetypes = ((".py files","*.py"),
                                                                                         (".pyw files","*.pyw"),
                                                                                         (".spec","*.spec")))

if file == "." or file == None:
    sys.exit()

if file.endswith('.pyw'):
    #NORMAL
    cmd = ('pyinstaller.exe --windowed --onefile --hidden-import "babel.numbers" ' + '"' + file + '"')
    os.system(cmd)

elif file.endswith('.py'):
    #NORMAL
    cmd = ('pyinstaller.exe --onefile ' + '"' + file + '"')
    os.system(cmd)

elif file.endswith('.spec'):
    cmd = ('pyinstaller.exe ' + '"' + file + '"')
    os.system(cmd)

os.system('pause')
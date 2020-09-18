# Kickstart a gamestream session with a fixed resolution and game launcher
import win32api
import win32.lib.win32con as win32con
import win32gui
import pywintypes
import pyautogui
import subprocess
import psutil
import os
import sys
from time import sleep

# Window enumeration handler function per https://www.blog.pythonlibrary.org/2014/10/20/pywin32-how-to-bring-a-window-to-front/
def windowEnumerationHandler(hwnd, top_windows):
    top_windows.append((hwnd, win32gui.GetWindowText(hwnd)))

# Target resolution for gamestream environment
gamestream_width = sys.argv[1]
gamestream_height = sys.argv[2]

# Set resolution to target
print("Switching resolution to {0}x{1}".format(gamestream_width, gamestream_height))
devmode = pywintypes.DEVMODEType()
devmode.PelsWidth = int(gamestream_width)
devmode.PelsHeight = int(gamestream_height)
devmode.Fields = win32con.DM_PELSWIDTH | win32con.DM_PELSHEIGHT
win32api.ChangeDisplaySettings(devmode, 0)

# Minimize all windows
print("Minimizing windows")
pyautogui.hotkey('winleft', 'd')

# Start JoyToKey if installed
j2k_path = 'C:\Program Files (x86)\JoyToKey\JoyToKey.exe'
if os.path.exists(j2k_path):
    print("Launching JoyToKey")
    j2k = True
    if "JoyToKey.exe" in (p.name() for p in psutil.process_iter()):
        os.system('taskkill /f /im JoyToKey.exe')
    subprocess.Popen(j2k_path)

# Start game launcher
print("Launching Playnite")
playnite_exe = os.path.join(os.getenv('LOCALAPPDATA'), 'Playnite', 'Playnite.FullscreenApp.exe')
subprocess.Popen(playnite_exe)

# Move mouse cursor into the lower-right corner to pseudo-hide it
pyautogui.FAILSAFE = False
pyautogui.moveTo(9999, 9999, duration = 0)

# Focus playnite in the foreground
results = []
top_windows = []
playnite_focused = False
while not playnite_focused:
    win32gui.EnumWindows(windowEnumerationHandler, top_windows)
    for i in top_windows:
        if "playnite" in i[1].lower():
            print("Focusing Playnite")
            win32gui.ShowWindow(i[0],5)
            win32gui.SetForegroundWindow(i[0])
            playnite_focused = True
            break
    sleep(1)

# Watch for termination of Playnite to return to the system's original configuration
print("Watching for Playnite to close")
while True:
    if "Playnite.FullscreenApp.exe" in (p.name() for p in psutil.process_iter()):
        sleep(3)
    else:
        break

# Kill joy2key
if j2k:
    if "JoyToKey.exe" in (p.name() for p in psutil.process_iter()):
        print("Terminating joy2key.")
        os.system('taskkill /f /im JoyToKey.exe')

# Kill gamestream
print("Terminating GameStream session.")
if "nvstreamer.exe" in (p.name() for p in psutil.process_iter()):
    os.system('taskkill /f /im nvstreamer.exe')

# Restore original resolution
print('Restoring original resolution.')
win32api.ChangeDisplaySettings(None, 0)

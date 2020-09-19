# Kickstart a gamestream session with a fixed resolution and game launcher
import win32api
import win32.lib.win32con as win32con
import win32gui
import pywintypes
import pyautogui
import configparser
import subprocess
import psutil
import os
import sys
from time import sleep

# Window enumeration handler function per https://www.blog.pythonlibrary.org/2014/10/20/pywin32-how-to-bring-a-window-to-front/
def windowEnumerationHandler(hwnd, top_windows):
    top_windows.append((hwnd, win32gui.GetWindowText(hwnd)))

# Define a default config file to write if we're missing one
config_filename = 'gamestream_launchpad_cfg.ini'
default_config = """[LAUNCHER]
# The path to your Playnite.FullscreenApp.exe
launcher_path = %%LOCALAPPDATA%%\Playnite\Playnite.FullscreenApp.exe

[BACKGROUND]
# List as many exe's as you want here. They will run at the start of the GameStream session and be killed at the end.
background_exe_1 = C:\Program Files (x86)\JoyToKey\JoyToKey.exe
# background_exe_2 = C:\WINDOWS\system32\mspaint.exe

[SETTINGS]
# Set debug = 1 to leave a window running after gamestream to see error messages from GSLP
debug = 0
sleep_on_exit = 0
"""

# Write the default config
if not os.path.exists(config_filename):
    with open(config_filename, 'w') as out_file:
        out_file.write(default_config)

# Parse the config file
config = configparser.ConfigParser()
config.read(config_filename)
cfg_launcher = config['LAUNCHER'].get('launcher_path', r'%LOCALAPPDATA%\Playnite\Playnite.FullsreenApp.exe')
cfg_bg_paths = config['BACKGROUND']
cfg_settings = config['SETTINGS']
debug = cfg_settings.get('debug', '0')
sleep_on_exit = cfg_settings.get('sleep_on_exit', '0')

# Target resolution for gamestream environment
try:
    gamestream_width = sys.argv[1]
    gamestream_height = sys.argv[2]
except IndexError:
    print("Error parsing host resolution arguments. Did you mean to run one of the .bat launcher scripts?")
    print("Usage: gamestream_launchpad.exe 1920 1080")
    sys.exit(1)

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

# Start background programs, if they're available
for path in cfg_bg_paths:
    expanded_path = os.path.expandvars(cfg_bg_paths[path])
    if os.path.exists(expanded_path):
        print("Launching", expanded_path)
        exec_name = os.path.basename(expanded_path)
        # Kill the process first if it's already running
        if exec_name in (p.name() for p in psutil.process_iter()):
            os.system('taskkill /f /im ' + exec_name)
        # Start the process
        subprocess.Popen(expanded_path)

# Kill leftover game launchers
launcher_exec_name = os.path.basename(cfg_launcher)
if launcher_exec_name in (p.name() for p in psutil.process_iter()):
    os.system('taskkill /f /im ' + launcher_exec_name)

# Specific case for alternate versions of Playnite
if "Playnite" in launcher_exec_name:
    if "Playnite.FullscreenApp.exe" in (p.name() for p in psutil.process_iter()):
        os.system('taskkill /f /im ' + "Playnite.FullscreenApp.exe")
    if "Playnite.DesktopApp.exe" in (p.name() for p in psutil.process_iter()):
        os.system('taskkill /f /im ' + "Playnite.DesktopApp.exe")

# Start game launcher
print("Starting game launcher")
launcher_exe = os.path.expandvars(cfg_launcher)
subprocess.Popen(launcher_exe)

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

# Terminate background programs, if they're available
for path in cfg_bg_paths:
    expanded_path = os.path.expandvars(cfg_bg_paths[path])
    if os.path.exists(expanded_path):
        exec_name = os.path.basename(expanded_path)
        print("Terminating", exec_name)
        if exec_name in (p.name() for p in psutil.process_iter()):
            os.system('taskkill /f /im ' + exec_name)

# Kill gamestream
print("Terminating GameStream session.")
if "nvstreamer.exe" in (p.name() for p in psutil.process_iter()):
    os.system('taskkill /f /im nvstreamer.exe')

# Restore original resolution
print('Restoring original resolution.')
win32api.ChangeDisplaySettings(None, 0)

if sleep_on_exit == '1':
# Put computer to sleep
    print("Going to sleep")
    os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")

if debug == '1':
    # Leave window open for debugging
    input("Paused for debug review. Press Enter key to close.")

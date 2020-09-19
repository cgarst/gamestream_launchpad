# GameStream Launchpad 🚀

![](demo.gif)

GameStream Launchpad (GSLP) orchestrates an optimized environment for NVIDIA GameStream connections through NVIDIA Shield hardware and/or [Moonlight](https://github.com/moonlight-stream) clients. By running GSLP as a "game" through Moonlight or SHIELD instead of selecting games directly, it improves the GameStream experience with the following ideas:

 1. Launches a controller-optimized launcher that automatically displays all installed games from all stores (Steam, Origin, Epic, Xbox GamePass, etc).
 2. Automatically set a specific resolution on the host during the session.
 3. Automatically end the GameStream session and revert the host resolution when exiting the launcher.
 4. Specify custom background processes that only live during the GameStream session, such as a global controller remappings program.
 
By default, this configuration uses [Playnite](https://github.com/JosefNemec/Playnite) fullscreen mode as the launcher. Additional launchers can be supported by request.

## Basic Setup
 1. Install [Playnite](https://github.com/JosefNemec/Playnite) and configure it to your liking.
 2. Download the latest [release](https://github.com/cgarst/gamestream_launchpad/releases/) and extract the files somewhere.
 3. Open GeForce experience and navigate to Settings > SHIELD > ADD.
 4. In the file picker, select the `.bat` script with the resolution you want your computer to have during the GameStream.
 
## Customization
A non-default Playnite path and/or custom background programs can be defined in `gamestream_launchpad_cfg.ini`. The config's included example launches [JoyToKey](https://joytokey.net/en/), which would allow you to map additional button mapping/combo functions. Some ideas for controller remapping would be to map to Shift-Tab for Steam overlay, Win-G for Xbox gamebar, Win-Alt-PrintScr for screenshot, or Win key for cutscene pauses.

The config file supports an unlimited number of background processes, paths defined with environment variables, or just regular absolute paths. A debug mode can also be enabled here which will leave the console window running to check the output after a session.

```
[LAUNCHER]
# The path to your Playnite.FullscreenApp.exe
launcher_path = %%LOCALAPPDATA%%\Playnite\Playnite.FullscreenApp.exe

[BACKGROUND]
# List as many exe's as you want here. They will run at the start of the GameStream session and be killed at the end.
background_exe_1 = C:\Program Files (x86)\JoyToKey\JoyToKey.exe
# background_exe_2 = C:\WINDOWS\system32\mspaint.exe

[SETTINGS]
# Set debug = 1 to leave a window running after gamestream to see error messages from GSLP
debug = 0
```

## Resolution Recommendations
In most cases, the ideal resolution is the one closest to your client system running Moonlight or the NVIDIA app. Make sure to set the client-side streaming quality option at or above the resolution used by GSLP. A resolution can only be set when your system already supports it. However, custom resolutions can be added through the NVIDIA Control Panel's "Change resolution" settings. Additionally, you can still run a 1440p or 4k stream on a system with a 1080p monitor by enabling DSR Factors in the NVIDIA Control Panel's "Manage 3D Settings" globals.

## Development

### Developer Dependencies
 1. Install [Python 3.8](https://www.python.org/) for Windows, ensuring that you select "Add Python to PATH" during installation.
 2. Install [pipenv](https://pypi.org/project/pipenv/) via `pip install pipenv`.

### Developer Setup
 1. Clone this repo.
 2. In the repo directory, run `pipenv install` to setup the Python environment.
 3. Ensure that things are working by running `pipenv run gamestream_launchpad.py 1280 720` and closing Playnite.
 4. Build the exe with `build.bat`


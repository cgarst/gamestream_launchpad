# GameStream Launchpad 🚀

![](demo.gif)

GameStream Launchpad orchestrates an optimized environment for NVIDIA GameStream connections through NVIDIA Shield hardware and/or [Moonlight](https://github.com/moonlight-stream) clients. It improves the GameStream experience with the following ideas:

 1. Launch the session with a controller-optimized game launcher that automatically displays all installed games from all stores (Steam, Origin, Epic, Xbox GamePass, etc).
 2. Automatically set a specific resolution on the host during the session.
 3. Automatically end the GameStream session and revert the host resolution when exiting the launcher.
 4. Enable optional global controller remappings that only exist during the GameStream session.
 
By default, this configuration uses [Playnite](https://github.com/JosefNemec/Playnite) fullscreen mode as the launcher and [JoyToKey](https://joytokey.net/en/) as the optional controller remapper. However it should work with anything.

## Setup
 1. Install [Playnite](https://github.com/JosefNemec/Playnite) and configure it to your liking.
 2. (Optional) Install [JoyToKey](https://joytokey.net/en/) if you want this program to launch it so that your controller can have additional button mapping/combo functions.
 3. Download the latest [release](https://github.com/cgarst/gamestream_launchpad/releases/) and extract the files somewhere.
 4. Open GeForce experience and navigate to Settings > SHIELD > ADD.
 5. In the file picker, select the `.bat` script with the resolution you want your computer to have during the GameStream.

## Development

### Developer Dependencies
 1. Install [Python 3.8](https://www.python.org/) for Windows, ensuring that you select "Add Python to PATH" during installation.
 2. Install [pipenv](https://pypi.org/project/pipenv/) via `pip install pipenv`.

### Developer Setup
 1. Clone this repo.
 2. In the repo directory, run `pipenv install` to setup the Python environment.
 3. Ensure that things are working by running `pipenv run gamestream_launchpad.py 1280 720` and closing Playnite.
 4. Build the exe with `build.bat`


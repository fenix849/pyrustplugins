# pyrustplugins 
pyrustplugins is currently a work in progress and only partially implimented.

## Installation

### Linux
```
python3 -m venv /opt/pyrustplugins
cd /opt/pyrustplugins
source bin/activate
python3 m pip install -r requirements.txt
```
You should now edit config.py and set your appkey, you can also customize cache directoty, log and config files if desired.
For the next step You will need your pterodactyl instance_uri and api bearer the latter of which is generated from <instance_uri>/account/api.
```
python3 rustplugins.py -i <instance_uri> <apibearer>
```

### Windows
Ensure python 3.7+ is installed from https://www.python.org/downloads/windows/
```
python3 -m venv ~\appdata\local\pyrustplugins
cd ~\appdata\local\pyrustplugins
sciprts\activate.bat
python3 -m pip install -r requirements.txt
```
You should now edit config.py and set your appkey, you can also customize cache directoty, log and config files if desired.
For the next step You will need your pterodactyl instance_uri and api bearer the latter of which is generated from <instance_uri>/account/api.
```
python3 rustplugins.py -i <instance_uri> <apibearer>

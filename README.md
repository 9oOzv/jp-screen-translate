Show kana an translation for japanese text under cursor

**On Linux**
```bash
python3 -m venv venv
. ven/bin/activate
pip install -r requirements.txt
pip install jamdict-data
python translator.py
```

Probably need to install tesseract with the japanese options. I dont know. I am currently running this on windows. Maybe your distro has a package.

**On Windows** 

Install tesseract `https://github.com/tesseract-ocr/tesseract` with the japanese options. Use the 3rd party binaries or whatever. Either use the standard install location or set the environment variable `TESSERACT_PATH` to the location of the tesseract executable.

```cmd
<wherever your python.exe is> -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
pip install jamdict-data
python translator.py
```


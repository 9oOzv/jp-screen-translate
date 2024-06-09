Show kana an translation for japanese text under cursor

**On Linux**

May or may not work. I have not tested on linux yet.

```bash
python3 -m venv venv
. ven/bin/activate
pip install -r requirements.txt
pip install easyocr # If you want to use easyocr
pip install pytesseract # If you want to use pytesseract
python app.py (gui|cli)
```

* If using Tesseract for OCR, it needs to be installed separately.
  * [https://tesseract-ocr.github.io/tessdoc/Installation.html#ubuntu](https://tesseract-ocr.github.io/tessdoc/Installation.html#ubuntu)
  * Check the options for japanese language.


**On Windows** 

* If using Tesseract for OCR, it needs to be installed separately.
  * [https://tesseract-ocr.github.io/tessdoc/Installation.html#windows](https://tesseract-ocr.github.io/tessdoc/Installation.html#windows)
  * Check the options for japanese language.
  * Either use the installer default path or set the environment variable `TESSERACT_PATH` to the location of the tesseract executable.
    * The `TESSERACT_PATH`, if you install tesseract in non-standard location, may or may not work. I have not tested it.

```cmd
<wherever your python.exe is> -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
pip install easyocr # If you want to use easyocr
pip install pytesseract # If you want to use pytesseract
python app.py (gui|cli)
```

**Commands**

```bash
python app.py cli # Print translations to the console
python app.py gui # Show a tooltip following the cursor
python app.py --help # Show help
python app.py <command> --help # Show help
```


**CUDA**

For speed, install torch with cuda support as described at [https://pytorch.org/get-started/locally/](https://pytorch.org/get-started/locally/)

Not sure if the old torch needs to be uninstalled first. Maybe need to run `pip uninstall torch` first.

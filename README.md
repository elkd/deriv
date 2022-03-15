# Deriv Bot

Deriv (formerly Binary.com) is an online trading platform. This repo uses Playwright to automate some common operations on the website (deriv.com). Most work here is used by a client, I'm making some parts of the codebase available since I so far can't find great resources for learning Playwright's Python API. Selenium has been the go-to for Browser Automation with Python for years.

So strictly, this repo isn't about Deriv, it's rather a demonstration of what you can do with Playwright beyond Pytest hello world examples 🤖🤖

## Installation

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install the requirements.

```bash
pip install -r requirements.txt
playwright install
```
For the UI, PysimpleGUI/TKinter is used, Python for Windows comes bundled with Tkinter. For Linux users, installing TKinter will be something like
```bash
sudo apt-get install python3-tk
```
 

## Usage

```python
python trade.py
```

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.


## License
[MIT](https://choosealicense.com/licenses/mit/)

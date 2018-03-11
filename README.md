# MeetNGo

## Usage

### Instructions
Before doing anything, you should probably edit the email templates.

First place the files *Questionnaire Filleul.csv* and *Questionnaire Parrain-Marraine.csv* into the MeetNGo folder. Then run *meetngo.py* and follow the instruction :wink:

### Requirements
To run the program, you will need a recent version of Python (at least 3.5).

If you are on Windows and you don't have Python installed properly, you can follow these instructions (this will not affect the rest of you're computer).

- Download python's [Windows x86-64 embeddable zip file](https://www.python.org/ftp/python/3.6.4/python-3.6.4-embed-amd64.zip).
- Move the zip file inside the MeetNGo folder.
- Right-click on it and choose *Extract All...*.

Now that you have a local Python, let's create way to launch the program.

- Create a new text document and write `START %CD%\python-3.6.4-embed-amd64\python.exe %CD%\meetngo.py` inside.
- Rename this file `RUN.cmd`. Windows should warn you that *the file might become unusable*, accept. If Windows doesn't tell you anything, you should retry with file extentions enabled (View > File name extensions).

To run the program, you can now double-click on the file you just created, it will run *meetngo.py*.

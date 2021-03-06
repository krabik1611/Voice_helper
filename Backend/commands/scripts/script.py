from threading import Thread
from queue import Queue
from datetime import datetime
import win32api
import os
import pandas as pd
import numpy as np
import sys
import traceback
from cleantext import clean
import pdfplumber
import glob
import re
status = np.array(['работа','дефект','наряд','резерв'])
queue = Queue()

class FindInPDF(Thread):
        def __init__(self,path,text,result):
            super(FindInPDF,self).__init__()
            self.path = path
            self.text = text
            self.result = result

        def run(self):
            text1 = readPDF(self.path)
            if re.findall(self.text,text1,flags=re.IGNORECASE):
                self.result.append(self.path)
            queue.task_done()


class Find_file(Thread):
    def __init__(self,drive,file_name):
        Thread.__init__(self)
        self.drive = drive
        self.file_name = file_name
        self.list_dirs = []

    def run(self):
        self.list_dirs = list(os.walk(self.drive))
        for info in self.list_dirs:
            for i in info[-1]:
                if self.file_name.lower() in i.lower():
                    self.result = info[0]+ "\\" + self.file_name
                    break
            try:
                print(self.result)
                break
            except:
                continue
        queue.task_done()


def date_time():
    date = datetime.now()
    date_now = {
        'year': date.year,
        'month': date.month,
        'day': date.day,
        'hour': date.hour,
        'minute': date.minute,
        'second': date.second
    }
    
    return f"{date.year}-{date.month}-{date.day} {date.hour}:{date.minute}:{date.second}"

def helloworld(a, b):
    print("hello world", a, b)


def startbrowser():
    os.system("start www.google.com")
    return 0

def weather():
    from requests import  get
    try:
        r = get("http://ipinfo.io").json()
        city = r["city"]
        key = "b5db848c6f1317ccddf157a8c3d8112e"
        r = get(f"http://api.openweathermap.org/data/2.5/weather?q={city}&units=metric&appid={key}&lang=ru").json()
        answer = r["main"]
        answer.update(r["weather"][0])
        # print(answer)
        string_answ = f"Температура: {answer['temp']}, Чувствуется как: {answer['feels_like']}, Давление: {answer['pressure']}"
        return string_answ
    except Exception as err:
        e = sys.exc_info()[2]
        tbinfo = traceback.format_tb(e)[0]
        print(err,"\n",tbinfo,)
        return 1

def launchProgramm(program:str):
    programs = {
        "explorer":["проводник","мой компьютер","explorer"],
        "browser":["браузер","сайт росатома"]
    }
    try:
        if program in programs["explorer"] :
            program = "explorer"
        elif program in programs["browser"] :
            program = "https://rosatom.ru/"
        os.system(f"start {program}")
        return 0
    except Exception as err:
        e = sys.exc_info()[2]
        tbinfo = traceback.format_tb(e)[0]
        print(err,"\n",tbinfo,)
        return 1

def xls_analysis(command,path='./xls'):
    global status
    dict_all = {}
    try:
        for info in os.walk(path):
            for xls_name in info[-1]:
                try:
                    #dict_spisok = {}
                    xls = pd.read_html(info[0]+'/'+xls_name)
                    df = pd.DataFrame(xls[0])
                    df.columns = df.loc[0,:].to_list()
                    df = df.loc[1:,:].reset_index(drop=True)
                    df = df.loc[:1,:]
                    df['Состояние'] = pd.Series()
                    df['Состояние'] = np.random.choice(len(status),len(df))
                    if 'список' in command:
                        dict_spisok = {'Столбцы':['Описание',"Состояние"]}
                        desc = df['Описание'].to_dict()
                        status = df['Состояние'].to_dict()
                        for i in desc:
                            dict_spisok.update({i:[desc[i],status[i]]})
                    dict_all.update({info[0]+'/'+xls_name:dict_spisok})
                except Exception as err:
                    e = sys.exc_info()[2]
                    tbinfo = traceback.format_tb(e)[0]
                    print(err,"\n",tbinfo,)
                    continue
        return dict_all
    except Exception as err:
        e = sys.exc_info()[2]
        tbinfo = traceback.format_tb(e)[0]
        print(err,"\n",tbinfo,)
        return 1


def find_file_on_fs(file_name,path=''):
    if path == '':
        drives = win32api.GetLogicalDriveStrings()
        drives = drives.split('\000')[:-1] 
    else:
        drives = [path]
    dict_drives = {}
    try:
        some = ""
        if type(file_name) == list:
            for i in file_name:
                some += i
                if file_name.index(i) == len(file_name)-1:
                    pass
                else:
                    some += '\n'
        else:
            some = file_name
        for path in drives:
            dict_drives.update({path:Find_file(path,some)})
            queue.put(dict_drives[path].start())
    except Exception as err:
        e = sys.exc_info()[2]
        tbinfo = traceback.format_tb(e)[0]
        print(err,"\n",tbinfo,)
        return 1

    queue.join()

    list_files = []
    for path in drives:
        try:
            list_files.append(dict_drives[path].result)
        except:
            continue

    dict_files = {file_name:list_files}

    return dict_files


def readPDF(path:str):
    try:
        if path.lower().endswith(".pdf"):
            with pdfplumber.open(path) as pdf:
                if (len(pdf.pages)):
                    text = " ".join([
                        page.extract_text() or " " for page in pdf.pages if page
                    ])
            clear_text = clean(text, lang='ru', lower=False, to_ascii=False)
            return clear_text

        else:
            return 1
    
    except Exception as err:
        e = sys.exc_info()[2]
        tbinfo = traceback.format_tb(e)[0]
        print(err,"\n",tbinfo,)
        return 1



def findInPDF(text,path):
    try:
        files = [
            glob.glob(os.path.join(folder[0],"*.pdf"))
            for folder in os.walk(path)
            if glob.glob(os.path.join(folder[0],"*.pdf"))
        ][0]
        result = []
        for file in files:
            thread = FindInPDF(file,text,result)
            queue.put(thread.start())
        
        queue.join()
        if result:
            return result 
    except Exception as err:
        e = sys.exc_info()[2]
        tbinfo = traceback.format_tb(e)[0]
        print(err,"\n",tbinfo,)
        return 1  

    


if __name__ == "__main__":
    # readPDF("D:\\project\\Voice_helper\\Backend\\HackAtom_Data\\pdf_material\\01.pdf")
    findInPDF("касается отсека аварийной выгрузки отработавших","D:\\project\\Voice_helper\\Backend\\HackAtom_Data\\")


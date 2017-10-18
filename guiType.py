import datetime
import os
import platform
import time
import tkinter as tkr
from tkinter import (Button, Entry, Frame, Label, Listbox, PhotoImage,
                     Scrollbar, Tk, Toplevel)

import ioServ
import osk

root = Tk()
nuWin = None

# *F=frame, *S=scroll, *L=list, *B=button, *T=label, *E=entry
nameL = infoT = None

# root.config(bg='#000000')
root.title('PhyxtGears1720io')
root.geometry('800x600')  # 1024x768
if platform.system() != 'Windows' and platform.system() != 'Darwin':
    root.attributes('-fullscreen', True)
'''
NOTES:
  tabs for each team (FLL and FIRST)
  show hours in list.
  REORGANIZE IT ALL
'''

opts = ioServ.loadOpts()

try:
    os.mkdir(opts['pathTime'])
except:  # DO NOT USE BARE EXCEPT
    pass

ioServ.mkfile(opts['usernameFile'])


def makeNewUserWindow():  # new user window
    global root, nuWin

    nuWin = Toplevel(root)
    nuWin.title('Create new user')
    # nuWin.geometry('460x160')

    inputF = Frame(nuWin)
    buttnF = Frame(nuWin)
    vkeyF = Frame(nuWin, pady=8)

    Label(inputF, text='Fullname: ', font='Courier 14').grid(sticky=tkr.E, padx=2, pady=2)
    Label(inputF, text='Username: ', font='Courier 14').grid(sticky=tkr.E, padx=2, pady=2)

    nuFullE = Entry(inputF, font='Courier 18', width=42)  # full name textbox
    nuUserE = Entry(inputF, font='Courier 18', width=42)  # username  textbox

    def setVK(choice):
        if choice == 1:
            vkey.attach = nuFullE
        elif choice == 2:
            vkey.attach = nuUserE
    nuFullE.bind('<FocusIn>', lambda e: setVK(1))
    nuUserE.bind('<FocusIn>', lambda e: setVK(2))

    nuFullE.grid(row=0, column=1)
    nuUserE.grid(row=1, column=1)
    inputF.pack()

    nuErrT = Label(nuWin, font='Courier 14', text='', fg='red')  # if theres an error with the name (ie name exists or not a real name) show on screen
    nuErrT.pack()

    def finishNewUser():
        errmsg, user, full = 'None', nuUserE.get(), nuFullE.get()

        if user == '' or full == '':
            errmsg = 'Err: All boxes must be filled'
        elif ioServ.checkNameDB(full):
            errmsg = 'Err: Fullname already exists.'
        elif ioServ.checkNameDB(user):
            errmsg = 'Err: Username already exists.'

        if errmsg == 'None':
            ioServ.addNameDB(full, user)  # todo: add job options
            refreshListboxes()
            nuWin.destroy()
        else:
            nuErrT.config(text=errmsg, fg='red')

    finB = Button(buttnF, text='Create User', font='Courier 14', fg='blue', width=16, command=finishNewUser)
    canB = Button(buttnF, text='Cancel',      font='Courier 14', fg='red',  width=16, command=nuWin.destroy)
    finB.grid(row=0, column=1)
    canB.grid(row=0, column=0)
    buttnF.pack()

    vkey = osk.vk(parent=vkeyF, attach=nuFullE)  # on screen alphabet keyboard
    vkeyF.pack()


def refreshListboxes(n=None):
    global nameL, infoT
    select = nameL.curselection()
    nameL.delete(0, tkr.END)
    ioServ.sortUsernameList()

    nameIO = ''
    typeIO = 'N'

    for line in open(opts['usernameFile']):
        nameIO = line.strip().split('|')[0]
        try:
            with open(opts['pathTime'] + nameIO.replace(' ', '') + '.txt', 'r+') as f:
                typeIO = f.readlines()[-1][0]  # iolist.insert(END, f.readlines()[-1][0])
        except:  # DO NOT USE BARE EXCEPT
            typeIO = 'N'
        nameL.insert(tkr.END, nameIO + ' ' * (35 - len(nameIO)) + typeIO)

    if select:
        nameL.see(select[0])


def ioSign(c):
    global nameL, infoT
    if len(nameL.curselection()) == 0:
        infoT.config(text='Nothing Selected!', fg='orange')
        return
    theNow = datetime.now()
    nameIO = nameL.get(nameL.curselection()[0])[:-1]
    timeIO = time.strftime(opts['ioForm'])
    autoClocked = False

    ioServ.mkfile(opts['pathTime'] + nameIO.replace(' ', '') + '.txt')  # make file if it doesn't exist

    readFile = open(opts['pathTime'] + nameIO.replace(' ', '') + '.txt', 'r+')
    lines = [line.strip() for line in readFile]
    inTimeFrame = datetime.strptime(lines[-1][4:], opts['ioForm']) < theNow < theNow.replace(hour=4, minute=30, second=0, microsecond=0)
    if lines and lines[-1][0] == 'a' and c == 'o' and inTimeFrame:
        # RECOVERING AUTOCLOCKOUT
        with open(opts['pathTime'] + nameIO.replace(' ', '') + '.txt', 'w+') as f:
            f.write('\n'.join(lines[:-1]) + '\n' + c + ' | ' + timeIO + '\n')
        # note for future annoucement system: have annoucements over phone system annoucing the time till autoclockout cutoff
        # ie: "it is 4:00am, 1 hour till autoclockout cutoff. please be sure to sign out and sign back in to get the hours."
        infoT.config(text=nameIO.split()[0] + ' signed out proper!', fg='Green')
    elif lines and lines[-1][0] in 'ioa':
        # DOUBLE SIGN IN/OUT
        if c == 'i':
            infoT.config(text=nameIO.split()[0] + ' is already signed in!', fg='orange')
        elif c == 'o':
            if lines[-1][0] == 'o':
                infoT.config(text=nameIO.split()[0] + ' is already signed out!', fg='orange')
            elif lines[-1][0] == 'a':
                infoT.config(text=nameIO.split()[0] + ' was auto-signed out!', fg='orange')
    elif not lines and c == 'o':
        # NEVER SIGNED IN BEFORE
        infoT.config(text=nameIO.split()[0] + ' has never signed in!', fg='orange')
    else:
        # NORMAL SIGN IN/OUT
        with open(opts['pathTime'] + nameIO.replace(' ', '') + '.txt', 'a+') as f:
            f.write(c + ' | ' + timeIO + '\n')
        hours = str(round(ioServ.calcTotalTime(nameIO.replace(' ', '')) / 60 / 60, 2))
        if c == 'i':
            infoT.config(text=nameIO.split()[0] + ' signed in! ' + hours + ' hours.', fg='Green')
        elif c == 'o':
            infoT.config(text=nameIO.split()[0] + ' signed out! ' + hours + ' hours.', fg='Red')
        # note for out signio: even if there is an issue one signout, show an error but still log the out. this was robby's idea.
    readFile.close()

    refreshListboxes()


def confirmQuit():  # quit program window with passcode protection
    global root, opts
    qtWin = Toplevel(root)
    qtWin.title('Quit?')
    Label(qtWin, text='Enter AdminPass\nto quit.', font='Courier 16 bold').pack(pady=2)
    passEntry = Entry(qtWin, font='Courier 14', width=10, show='*')
    passEntry.pack(pady=2)

    def areYouSure():
        if passEntry.get() == opts['adminPass']:
            root.destroy()

    buttonF = Frame(qtWin)
    quitit = Button(buttonF, text='Quit',  font='Courier 14 bold', fg='red', command=areYouSure)
    cancit = Button(buttonF, text='Cancel', font='Courier 14 bold', fg='blue', command=qtWin.destroy)
    quitit.grid(column=0, row=0)
    cancit.grid(column=1, row=0)
    buttonF.pack(pady=2)
    vnum = osk.vn(parent=qtWin, attach=passEntry)


def main():
    # *F = frame, *S = scroll, *L = list, *B = button, *T = text
    global nameL, infoT
    listF = Frame(root)
    listS = Scrollbar(listF, orient=tkr.VERTICAL)
    nameL = Listbox(listF, selectmode=tkr.SINGLE, yscrollcommand=listS.set, font='Courier 18')
    nameL.config(width=36, height=20)
    listS.config(command=nameL.yview, width=52)

    listS.pack(side=tkr.RIGHT, fill=tkr.Y)
    nameL.pack(side=tkr.LEFT, fill=tkr.BOTH, expand=1)
    listF.pack(side=tkr.LEFT, padx=12)

    logo1720 = PhotoImage(file='assets/logo.gif')
    Label(root, text='PhyxtGears1720io', font='Courier 12').pack(pady=4)
    Label(root, image=logo1720).pack()

    ioF = Frame(root)
    iIOB = Button(ioF, text='IN',  font='Courier 16 bold', bg='green', fg='white', command=lambda: ioSign('i'), width=12, height=2)
    oIOB = Button(ioF, text='OUT', font='Courier 16 bold', bg='red',  fg='white',   command=lambda: ioSign('o'), width=12, height=2)
    infoT = Label(ioF, text='', font='Courier 16 bold', height=6, wraplength=192, justify=tkr.CENTER)
    newB = Button(ioF, text='New User', font='Courier 16 bold', bg='blue', fg='white', command=makeNewUserWindow, width=12, height=2)

    iIOB.pack(pady=4)
    oIOB.pack(pady=4)
    infoT.pack()
    newB.pack(pady=4)
    ioF.pack()

    Button(text='QUIT', font='Courier 16 bold', height=1, fg='red', command=confirmQuit).pack(side=tkr.RIGHT, padx=12)

    refreshListboxes()

    root.mainloop()


if __name__ == '__main__':
    main()

from ipaddress import IPv4Address, AddressValueError
from os import listdir, getcwd
from os.path import getsize, isfile
from random import randint
from threading import Thread
from time import sleep
from tkinter import *

import socket
import struct
from tkinter import filedialog


# define variables used in multiple methods
class univ():
    filenames = None
    selectedFile = None
    selectFileDrop = None
    ipAddrEntry: Entry = None
    portEntry: Entry = None
    invalidIpCnt = 0
    invalidPortCnt = 0
    ip = None
    sock = None
    conn = None
    port = None
    addr = None


# button click methods

def sendClick():
    sendRecvBody.forget()
    loadPickFileBody()

def recvClick():
    sendRecvBody.forget()
    loadEnterIpBody()

def sendFileClick():
    if univ.selectedFile.get() != "Select File":
        univ.filenames = [univ.selectedFile.get()]
    
    if univ.filenames:
        pickFileBody.forget()

        univ.ip = socket.gethostbyname(socket.gethostname())
        univ.port = 15120 + randint(0, 9)
        univ.addr = (univ.ip, univ.port)

        thread = Thread(target=listenForConnection)
        thread.daemon = True
        thread.start()
        loadViewIpBody()

def recvFileClick():
    validIp = False
    try:
        ipAddr = IPv4Address(univ.ipAddrEntry.get())
        validIp = True
    except AddressValueError:
        univ.invalidIpCnt += 1

        if univ.invalidIpCnt == 1:
            titleLabel.config(text="Enter a Valid IP Address")
        elif univ.invalidIpCnt == 2:
            titleLabel.config(text="Enter a VALID IP Address")
        elif univ.invalidIpCnt == 3:
            titleLabel.config(font=("Segoe UI", 18))
        elif univ.invalidIpCnt == 4:
            titleLabel.config(fg= "red")
        else:
            root.destroy()

    if validIp:
        if univ.invalidPortCnt == 0:
            titleLabel.config(fg= "black", font=("Segoe UI", 9))

        try:
            port = int(univ.portEntry.get())
        except ValueError:
            univ.invalidPortCnt += 1

            if univ.invalidPortCnt == 1:
                titleLabel.config(text="Enter a Valid Port Number")
            elif univ.invalidPortCnt == 2:
                titleLabel.config(text="Enter a VALID Port Number")
            elif univ.invalidPortCnt == 3:
                titleLabel.config(font=("Segoe UI", 18))
            elif univ.invalidPortCnt == 4:
                titleLabel.config(fg= "red")
            else:
                root.destroy()
            
            return

        univ.ip = str(ipAddr)
        univ.port = port
        univ.addr = (univ.ip, univ.port)

        thread = Thread(target=connectToServer)
        thread.daemon = True
        thread.start()

def openFileDialog():
    files = filedialog.askopenfilenames(initialdir=getcwd(), title="Select Files", filetypes=[("All files", "*.*")])
    if files:
        univ.filenames = files
        titleLabel.config(text="Files Selected")

# load screens methods to send file

def loadSendRecvBody():
    titleLabel.config(text="Send or Receive?")
    titleFrame.pack()

    sendButton = Button(sendRecvBody, text="Send", padx=20, pady=10, command=sendClick)
    sendButton.place(relx=0.5, rely=0.3, anchor=CENTER)

    recvButton = Button(sendRecvBody, text="Receive", padx=13, pady=10, command=recvClick)
    recvButton.place(relx=0.5, rely=0.7, anchor=CENTER)

    sendRecvBody.pack()

def loadPickFileBody():
    titleLabel.config(text="Select Files to Send")
    titleFrame.pack()

    files = [file for file in listdir() if isfile(file)]
    univ.selectedFile = StringVar(value="Select File")

    univ.selectFileDrop = OptionMenu(pickFileBody, univ.selectedFile, *files)
    univ.selectFileDrop.config(width=20)
    univ.selectFileDrop.place(relx=0.4, rely=0.3, anchor=CENTER)

    browseFileButton = Button(pickFileBody, text="Browse", padx=1, pady=2, command=openFileDialog)
    browseFileButton.place(relx=0.8, rely=0.3, anchor=CENTER)

    sendFileButton = Button(pickFileBody, text="Send Files", padx=13, pady=10, command=sendFileClick)
    sendFileButton.place(relx=0.5, rely=0.7, anchor=CENTER)

    pickFileBody.pack()

def loadViewIpBody():
    titleLabel.config(text="Enter IP on Other Device")
    titleFrame.pack()

    ipLabel = Label(viewIpBody, text="Local IP: " + univ.ip)
    ipLabel.place(relx=0.5, rely=0.3, anchor=CENTER)

    portLabel = Label(viewIpBody, text="Port: " + str(univ.port))
    portLabel.place(relx=0.5, rely=0.7, anchor=CENTER)

    viewIpBody.pack()

def loadSendFileBody():
    titleLabel.config(text="Sending File")
    titleFrame.pack()

    percent = 0
    percentLabel = Label(sendFileBody, text=str(percent) + "% complete")
    percentLabel.place(relx=0.5, rely=0.3, anchor=CENTER)

    sendFileBody.pack()

    numFiles = len(univ.filenames)

    univ.conn.send(numFiles.to_bytes(1, "big"))

    for i in range(numFiles):
        if numFiles > 1:
            titleLabel.config(text="Sending File "+ str(i+1) + "/" + str(numFiles))

        totalSize = getsize(univ.filenames[i])
        remSize = totalSize
        metadata = trimFileName(univ.filenames[i]) + "\_()_/" + str(totalSize)
        print(metadata)
        univ.conn.send(struct.pack("!H", len(metadata)))
        univ.conn.send(metadata.encode(FORMAT))
        buffSize = univ.conn.getsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF)

        file = open(univ.filenames[i], "rb")
        while remSize > 0:
            data = file.read(min(buffSize, remSize))

            univ.conn.send(data)
            
            remSize -= len(data)
            percent = float(totalSize-remSize)/totalSize*100
            percentLabel.config(text='{:.1f}'.format(percent) + "% complete")
        file.close()

    univ.conn.close()
    univ.sock.close()
    sleep(3)
    root.destroy()

def trimFileName(fileName: str) -> str:
    if "/" in fileName:
        return fileName[fileName.rfind("/")+1:]
    return fileName

# load screen methods to receive file

def loadEnterIpBody():
    titleLabel.config(text="Enter IP Address and Port Number")
    titleFrame.pack()

    univ.ipAddrEntry = Entry(enterIpBody, width=16)
    univ.ipAddrEntry.insert(0, socket.gethostbyname(socket.gethostname()))
    univ.ipAddrEntry.place(relx=0.5, rely=0.1, anchor=CENTER)

    univ.portEntry = Entry(enterIpBody, width=16)
    univ.portEntry.insert(0, "15120")
    univ.portEntry.place(relx=0.5, rely=0.4, anchor=CENTER)

    recvFileButton = Button(enterIpBody, text="Receive Files", padx=13, pady=10, command=recvFileClick)
    recvFileButton.place(relx=0.5, rely=0.8, anchor=CENTER)

    enterIpBody.pack()

def loadRecvFileBody():
    titleLabel.config(text="Receiving File")
    titleFrame.pack()

    percent = 0
    percentLabel = Label(recvFileBody, text=str(percent) + "% complete")
    percentLabel.place(relx=0.5, rely=0.3, anchor=CENTER)

    recvFileBody.pack()

    numFiles = int.from_bytes(univ.sock.recv(1), "big")

    for i in range(numFiles):
        if numFiles > 1:
            titleLabel.config(text="Receiving File " + str(i+1) + "/" + str(numFiles))
        
        metaSize = int.from_bytes(univ.sock.recv(2), "big")
        metadata = univ.sock.recv(metaSize).decode(FORMAT).split("\_()_/")
        name = metadata[0]
        totalSize = int(metadata[1])
        remSize = totalSize

        while isfile(name):
            name = renameFile(name)
        file = open(name, "wb")
        buffSize = univ.sock.getsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF)

        while remSize > 0:
            data = univ.sock.recv(min(buffSize, remSize))

            file.write(data)

            remSize -= len(data)
            percent = float(totalSize-remSize)/totalSize*100
            percentLabel.config(text='{:.1f}'.format(percent) + "% complete")
        file.close()
    
    univ.sock.close()
    sleep(3)
    root.destroy()

# file renaming helper method
def renameFile(fileName: str) -> str:
    if "." in fileName:
        i = fileName.rfind(".")
    else:
        i = len(fileName)
    return fileName[:i] + "v2" + fileName[i:]
    

# connection helper methods

def listenForConnection():
    univ.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    univ.sock.bind(univ.addr)
    univ.sock.listen()

    univ.conn, _ = univ.sock.accept()
    viewIpBody.forget()
    loadSendFileBody()

def connectToServer():
    univ.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    univ.sock.connect(univ.addr)
    enterIpBody.forget()
    loadRecvFileBody()


# file send constants
FORMAT = "utf-8"

# begin main code
root = Tk()

root.title("File Transfer GUI")
root.minsize(300,300)
root.maxsize(300,300)

titleFrame = Frame(root, width=300, height=50)
titleLabel = Label(titleFrame, text="")
titleLabel.place(relx=0.5, rely=0.5, anchor=CENTER)

# main screen
sendRecvBody = Frame(root, width=300, height=200)

# send screens
pickFileBody = Frame(root, width=300, height=200)
viewIpBody = Frame(root, width=300, height=200)
sendFileBody = Frame(root, width=300, height=200)

# recv screens
enterIpBody = Frame(root, width=300, height=200)
recvFileBody = Frame(root, width=300, height=200)

loadSendRecvBody()

root.mainloop()
#!/usr/bin/python
#coding:utf8
#python 2.7.6

import threading
import socket
import time
import os
import sys
import signal
from readline import get_line_buffer
BUFSIZE = 1024
BACKPORT = 7789     #状态监听端口
CHATPORT = 7788     #聊天信息发送窗口
# START = '>>'
# INIT = '>>'
users = {}
ips = {} 
#起到双向字典的作用，ip和name互相映射

class Cmd():
    START = '>> '
    INIT = '>> '
    outmutex = threading.Lock()

    @classmethod
    def output_with_rewrite(self, msg):
        if self.outmutex.acquire(1):
            sys.stdout.write('\r'+' '*(len(get_line_buffer())+len(self.START))+'\r')
            print msg
            sys.stdout.write(self.START+get_line_buffer())
            sys.stdout.flush()
            self.outmutex.release()
    
    @classmethod
    def output(self, msg):
        if self.outmutex.acquire(1):
            print msg
            self.outmutex.release()

    @classmethod
    def set_start(self, start):
        self.START = start

    @classmethod
    def reset_start(self):
        self.START = self.INIT

class UserList():
    def __init__(self):
        self.users = {}
        self.ips = {}
        self.mutex = threading.Lock()

    def add_user(self, name, ip):
        if self.mutex.acquire(1):
            self.users[name] = ip
            self.ips[ip] = name
            self.mutex.release()

    def has_ip(self, ip):
        ret = False
        if self.mutex.acquire(1):
            ret = ip in self.ips
            self.mutex.release()
        return ret

    def clear(self):
        if self.mutex.acquire(1):
            self.users.clear()
            self.ips.clear()
            self.mutex.release()

    def del_by_ip(self, ip):
        if self.mutex.acquire(1):
            del self.users[ips[ip]]
            del self.ips[ip]
            self.mutex.release()

    def get_users(self):
        users = []
        if self.mutex.acquire(1):
            for key in self.users:
                users += key
            self.mutex.release()
        return users

#数据处理类（消息封装、分解）
class Data(): 
    def gettime(self):
        return time.strftime('%Y-%m-%d %H:%M', time.localtime(time.time()))

    def getip(self):
        ip = os.popen("/sbin/ifconfig | grep 'inet addr' | awk '{print $2}'").read()
        ip = ip[ip.find(':')+1:ip.find('\n')]
        return ip

    def handlebc(self, data):
        data = data[5:]
        res = data.split('#opt:')
        return res

    def makebc(self, name, switch):
        data = 'name:%s#opt:%d' % (name, switch)
        return data

    def handlechat(self, data):
        msg = '\n' + self.gettime() + '\n' +'from '+ data + '\n'
        return msg

    def makechat(self, data, name):
        return name + ':' + data

#后台监听类
class Back(threading.Thread): 
    def __init__(self, user_list):
        threading.Thread.__init__(self)
        self.data = Data()
        self.user_list = user_list
        self.addrb = ('255.255.255.255', BACKPORT)
        self.addrl = ('', BACKPORT)
        self.name = socket.gethostname()
        self.name = "jieb"
        self.ip = self.data.getip()
        self.thread_stop = False

    def status(self, name, switch):
        if switch == 0:
            status = 'offline'
        elif switch == 1:
            status = 'online'
        #用来处理输入过程中被线程返回消息打乱的情况
        Cmd.print_with_rewrite('[status]' + name + ' ' + status)

    def broadcast(self, switch):
        bsock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        bsock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        data = self.data.makebc(self.name, switch)
        bsock.sendto(data, self.addrb)
        bsock.close()

    def response(self, addr, switch):
        rsock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        data = self.data.makebc(self.name, switch)
        rsock.sendto(data, (addr, BACKPORT))
        rsock.close()

    def check(self):
        # self.user_list.clear()
        if usermutex.acquire():
            ips.clear()
            users.clear()
            usermutex.release()
        self.broadcast(1)

    def run(self):
        lsock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        lsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        lsock.bind(self.addrl)
        self.broadcast(1)
        while not self.thread_stop:
            data, addr = lsock.recvfrom(BUFSIZE)
            datalist = self.data.handlebc(data)
            if usermutex.acquire(1):
                if datalist[1] == '0':
                    if ips.has_key(addr[0]):
                        if anoun == 1:
                            self.status(datalist[0], 0)
                        # self.user_list.del_by_ip(addr[0])
                        del ips[addr[0]]
                        del users[datalist[0]]
                elif datalist[1] == '1':
                    if anoun == 1 and datalist[0] != self.name:
                        self.status(datalist[0], 1)
                    # self.user_list.add_user(datalist[0], addr[0])
                    users[datalist[0]] = addr[0]
                    ips[addr[0]] = datalist[0]
                    self.response(addr[0], 2)
                elif datalist[1] == '2':
                    if anoun == 1 and datalist[0] != self.name:
                        self.status(datalist[0], 1)
                    # self.user_list.add_user(datalist[0], addr[0])
                    users[datalist[0]] = addr[0]
                    ips[addr[0]] = datalist[0]
                usermutex.release()
        lsock.close()
    def stop(self):
        self.broadcast(0)
        self.thread_stop = True

#聊天类
class Listen(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.addr = ('', CHATPORT)
        self.name = socket.getfqdn(socket.gethostname())
        self.data = Data()
        self.thread_stop = False

    def ack(self, addr):#to be added 用来确认消息报的接受
        return

    def run(self):
        lsock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        lsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        lsock.bind(self.addr)
        while not self.thread_stop:
            data, addr = lsock.recvfrom(BUFSIZE)
            msg = self.data.handlechat(data)
            Cmd.output_with_rewrite(msg)
        lsock.close()
    def stop(self):
        self.thread_stop = True

#启动入口类
class Start(): 
    def __init__(self, user_list):
        self.name = socket.getfqdn(socket.gethostname())
        self.user_list
        self.data = Data()
        self.listen = Listen()
        self.back = Back(user_list)
        print '*******   iichats   ********'
        print '     Written by Kevince     \n'
        print 'This is ' + self.name
        print self.data.gettime()+'\n'

    #帮助信息
    def helpinfo(self):     
        helps = "use ':' to use options\n" + \
                "\t:exit\t\t\texit iichats\n" + \
                "\t:list\t\t\tlist online users\n" + \
                "\t:quit\t\t\tquit the chat mode\n" + \
                "\t:chat [hostname]\tchatting to someone\n" + \
                "\t:set status [on|off]\tturn on/of status alarms\n"
        Cmd.output(helps)

    def refresh(self):
        out = '\n******Onlinelist******\n'
        # users = user_list.get_users()
        for key in users:
            out += key + "\n"
        out += '**********************\n'
        Cmd.output(out)

    def chatting(self):
        csock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        Cmd.output("use ':help' to get help information")

        name = ''
        address = ''
        global anoun
        global START
        while True:
            arg = raw_input(Cmd.START)
            if arg[0:5] == ':quit' and Cmd.START != Cmd.INIT:
                name = ''
                address = ''
                Cmd.reset_start()
            elif arg[0] == ':' and Cmd.START == Cmd.INIT:
                if arg[1:] == 'exit':
                    break
                elif arg[1:5] == 'list':
                    self.refresh()
                    continue
                elif arg[1:12] == 'set status ':
                    if arg[12:] == 'on':
                        anoun = 1
                    elif arg[12:] == 'off':
                        anoun = 0
                    continue
                elif arg[1:5] == 'help':
                    self.helpinfo()
                    continue
                elif arg[1:6] == 'check':
                    self.back.check()
                    print 'checking the list...'
                    time.sleep(3)
                    self.refresh()
                elif arg[1:6] == 'chat ':
                    name = arg[6:]
                    if usermutex.acquire(1):
                        userlist = users.keys()
                        usermutex.release()
                    if name not in userlist:
                        Cmd.output('this host does not exist')
                        continue
                    address = (users.get(name), CHATPORT)
                    Cmd.output('now chatting to ' + name+ \
                            " ,use ':quit' to quit CHAT mode")
                    Cmd.set_start(name + Cmd.INIT)
                else:
                    Cmd.output("invalid input, use ':help' to get some info")
            else:
                if not len(address):
                    Cmd.output("you can CHAT to someone, or use ':help'")
                    continue
                data = arg
                msg = self.data.makechat(data, self.name)
                csock.sendto(msg, address)
        csock.close()
    def start(self):
        self.back.setDaemon(True)
        self.back.start()
        self.listen.setDaemon(True)
        self.listen.start()
        self.chatting()
        self.back.stop()
        self.listen.stop()
        sys.exit()

usermutex = threading.Lock()
# outmutex = threading.Lock()
#控制status on和off的情况
anoun = 1
def main():
    user_list = UserList()
    s = Start(user_list)
    s.start()

# 20160769 Park Ho Yeon
#

from socket import *
import time
import threading
import sys

#set target server socket
serverName = 'nsl2.cau.ac.kr'
serverPort = 50769
answerLock = threading.Lock()
answerLock.acquire()
disconnectFlag = False
startTime=0

clientVersion='1.0'

#recieve part, it need to run thread
def recvMessage(clientSocket):

    global disconnectFlag
    
    while True:
    
        #recieve
        modifiedMessage = clientSocket.recv(2048)
        
        #response time end
        responseTime = int((time.time()-startTime)*10000)/10
        
        #check recieved message(terminated)
        if modifiedMessage.decode() == '':
            print('Info: Server is terminated. Press Enter key to exit')
            disconnectFlag=True
            break
            
        serverCommand=modifiedMessage.decode()[0].encode()
        
        #answer to client(unlock chat)
        if serverCommand== b'\x01':
            #print result
            printMessage = modifiedMessage.decode()[1:]
            print(printMessage)
            answerLock.release()
            
        #recieve anytime
        if serverCommand == b'\x02':
            #print result
            printMessage = modifiedMessage.decode()[1:]
            print(printMessage)
            
        #disconnected from server message
        if serverCommand == b'\x03':
            printMessage = modifiedMessage.decode()[1:]
            print(printMessage)
            print('Press Enter key to exit')
            disconnectFlag=True
            if(answerLock.locked()):
                answerLock.release()
            break
            
        #rtt output
        if serverCommand == b'\x06':
            print('Round trip time: '+str(responseTime)+' ms')
            answerLock.release()
            
        #initializeMessage
        if serverCommand == b'\x10':
            recvSplit=modifiedMessage.decode()[1:].split('\\')
            welcomeMessage=recvSplit[0]+str(gethostbyname(serverName))+recvSplit[1]
            print(welcomeMessage)
        
            
        

#try before command 5 OR KeyboardInterrupt is happened, OR get some problem
try:
    #set client socket
    clientSocket = socket(AF_INET, SOCK_STREAM)
    clientSocket.connect((serverName, serverPort))
    print("The client is running on port", clientSocket.getsockname()[1])
    
    #wrong argument input
    if not len(sys.argv) == 2:
        print('wrong command line, you must set only 1 argument to use your ID')
        sys.exit()
    
    clientID=sys.argv[1]
    
    #sent ID infomation to server
    iniBytes=bytearray(b'\x11')
    initializeMessage=clientID
    iniBytes.extend(initializeMessage.encode())
    clientSocket.send(iniBytes)

    #new thread to recv message
    threading._start_new_thread(recvMessage, (clientSocket,))

    while True:

        #chatting on
        chatting = input()

        if disconnectFlag:
            break

        if not chatting:
            continue
        
        
        #command case    
        if chatting[0]=='\\':
            commandSplit=chatting.split(' ')
            
            if commandSplit[0]=='\\list':
                command=b'\x02'
            elif commandSplit[0]=='\\dm':
                command=b'\x03'
                targetID=commandSplit[1]
            elif commandSplit[0]=='\\ex':
                command=b'\x04'
                targetID=commandSplit[1]
            elif commandSplit[0]=='\\quit':
                command=b'\x00'
                clientSocket.send(command)
                print('\ngg~')
                break
            elif commandSplit[0]=='\\ver':
                command=b'\x05'
            
            elif commandSplit[0]=='\\rtt':
                command=b'\x06'
                
            else:
                print('invalid command')
                continue
        else:#normal case
            command=b'\x01'

        #Create sendlist
        sendList=''
        #chatting case
        if command==b'\x01':
            sendList += chatting
        if command==b'\x03' or command == b'\x04':
            sendList += targetID+'\\'
            for counter in range(len(commandSplit[2:])):
                if counter == 0:
                    sendList+=commandSplit[2]
                else:
                    sendList += ' ' +commandSplit[2+counter]
            
        #version case
        if command==b'\x05':
            sendList += str(clientVersion)

        #response time start
        startTime=time.time()
        
        sendbytes=bytearray(command)
        sendbytes.extend(sendList.encode())

        #send list
        clientSocket.send(sendbytes)
        
        #lock before answer is comming
        if not (command==b'\x01'
        or command==b'\x03'
        or command==b'\x04'):
            answerLock.acquire()
        
        

#catch if KeyboardInterrupt is happened
except KeyboardInterrupt:
    print('\ngg~')

#catch if server transport is gotten problem    
except Exception as e:
    print('\nTransport has some problem, please check and try it again.')
    print('Error: ' + str(e))
    
    

clientSocket.close()

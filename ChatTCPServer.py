# 20160769 Park Ho Yeon
#

from socket import *
import time
import threading

#set start time
start = time.time()

#set server socket
serverPort = 50769
serverSocket = socket(AF_INET, SOCK_STREAM)
serverSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
serverSocket.bind(('', serverPort))
serverSocket.listen(1)
connectionList=list()
set_ID = 1
num_of_client = 0
listLock = threading.Lock()
serverVersion='1.0'


print("The server is ready to receive on port", serverPort)

#function that broadcast
def brdCst(message):
    byteSend=bytearray(b'\x02')
    byteSend.extend(message.encode())
    if connectionList:
        for target in connectionList:
            target[2].send(byteSend)
    
#function that broadcast with except member
def brdCst_except(message, except_list):

    byteSend=bytearray(b'\x02')
    byteSend.extend(message.encode())
    if connectionList:
        for target in connectionList:
            except_flag=False
            for counter in range(len(except_list)):
                if(target[0]==except_list[counter]):
                    except_flag=True
                    break
            if except_flag:
                continue
            target[2].send(byteSend)



#function that control thread
def handle_client(connectionSocket, clientAddress, client_ID):

    listLock.acquire()

    global num_of_client
    global connectionList
    
    except_list=list()
    except_list.append(client_ID) 
    #initiate id value and broadcasting
    try:
        num_of_client += 1
        connectionList.append([client_ID, clientAddress, connectionSocket])
    finally:
        listLock.release()
    
    counterStr=''
    
    counterStr+='You are '+str(num_of_client)
    if(num_of_client==1):
        counterStr+='st user'
    elif (num_of_client==2):
        counterStr+='nd user'
    elif (num_of_client==3):
        counterStr+='rd user'
    else:
        counterStr+='th user'
    
    #initiate message
    welcomeBytes=bytearray(b'\x10')
    welcomeMessage='welcome '+client_ID+' to CAU network class chat room at '+'\\'+' '+str(serverPort)+'. '+counterStr+'\n'
    welcomeBytes.extend(welcomeMessage.encode())
    connectionSocket.send(welcomeBytes)
    
    
    broadMessage=client_ID+' joined. There are '+str(num_of_client)+' users connected'
    print(broadMessage)
    
    #call broadcast thread
    brdCst_except(broadMessage, except_list)
    
    
    while True:
        #receive client message
        recvList = connectionSocket.recv(2048)
        #detect if client is terminated
        if recvList.decode() == '':
            break
        
        #decode command and print what is command
        command = recvList.decode()[0].encode()
        recvMessage=recvList.decode()[1:]
        
        
        #detect is there wrong words
        finder=recvMessage.upper()
        if not finder.find('i hate professor'.upper()) == -1:
            banBytes=bytearray(b'\x03')
            banned='you write wrong word! you are banned!'
            banBytes.extend(banned.encode())
            connectionSocket.send(banBytes)
            banMessage=client_ID+' write wrong words! '+client_ID+' is banned!'
            brdCst_except(banMessage, except_list)
            break

        
        #check message that it is no problem(just check [0])
        if (command != b'\x01'  #normal
        and command != b'\x02'  #list
        and command != b'\x03'  #dm
        and command != b'\x04'  #ex
        and command != b'\x05'  #ver
        and command != b'\x06'  #rtt
        and command != b'\x00'):#quit
            print('Recieve message has problem')
            errorBytes=bytearray(b'\x01')
            errorMessage = 'Server get unexpected message, please send it again'
            errorBytes.extend(errorMessage.encode())
            connectionSocket.send(errorBytes)
            continue
        
        #debugging
        print('Command '+str(command))

        #if command is q(clent is terminated normally)
        if command == b'\x00':
            break
        
        #chatting case
        if command == b'\x01':#normal
            normalMessage=client_ID+'> '+recvMessage
            brdCst_except(normalMessage, except_list)
            continue
        if command == b'\x03' or command == b'\x04':#dm or ex
            targetSplit=recvMessage.split('\\')
            targetID=targetSplit[0]
            #check that id is existence
            trg_flag=False
            for trg in connectionList:
                if trg[0]==targetID:
                    trg_flag=True
                    break
            if not trg_flag:
                errorBytes=bytearray(b'\x02')
                errorMessage = 'target '+targetID+' is no here. please check it again'
                errorBytes.extend(errorMessage.encode())
                connectionSocket.send(errorBytes)
                continue
            
            msg=''
            #extract word
            for counter in range(len(targetSplit[1:])):
                if counter == 0:
                    msg+=targetSplit[1]
                else:
                    msg+='\\'+targetSplit[1+counter]
            
            #separate DM and EX
            if command == b'\x03':#dm
                for trg in connectionList:
                    if trg[0]==targetID:
                        dBytes=bytearray(b'\x02')
                        dMessage='from: '+client_ID+'> '+msg
                        dBytes.extend(dMessage.encode())
                        trg[2].send(dBytes)
            if command ==b'\x04':#ex
                except_list.append(targetID)
                eMessage=client_ID+'> '+msg
                brdCst_except(eMessage, except_list)
                except_list.remove(targetID)
            continue
        
        #list case        
        if command == b'\x02':
            listLock.acquire()
            try:
                listBytes=bytearray(b'\x01')
                list_str=''
                if connectionList:
                    for client in connectionList:
                        list_str += str(client[0])+': '+str(client[1])+'\n'
                listBytes.extend(list_str.encode())
                connectionSocket.send(listBytes)
            finally:
                listLock.release()
            continue
        
        #version case
        if command == b'\x05':
            verBytes=bytearray(b'\x01')
            versionMessage = 'Server version= '+str(serverVersion)+'\n'
            versionMessage += 'Client version= '+recvMessage
            verBytes.extend(versionMessage.encode())
            connectionSocket.send(verBytes)
            
        #rtt case
        if command == b'\x06':
            rttBytes = b'\x06'
            connectionSocket.send(rttBytes)
        
    #break then close
    listLock.acquire()
    #finish this thread after broadcast
    try:
        num_of_client -= 1
        for close_trg in connectionList:
            if close_trg[0]==client_ID:
                connectionList.remove(close_trg)
                break
        broadMessage = client_ID+' is disconnected. There are '+str(num_of_client)+' users in the chat room.'
        print(broadMessage)
    finally:
        listLock.release()
    brdCst(broadMessage)
    connectionSocket.close()

#try before KeyboardInterrupt is happened
try:
    
    is_sameID=False
    
    while True:
        #set connection socket
        (connectionSocket, clientAddress) = serverSocket.accept()
        print('Connection requested from', clientAddress)
        
        
        #if new client over 8
        if(num_of_client>=8):
            rejectionBytes=bytearray(b'\x03')
            rejectionMessage='chatting room full. cannot connect'
            rejectionBytes.extend(rejectionMessage.encode())
            connectionSocket.send(rejectionBytes)
            connectionSocket.close()
            print('connection refused')
            continue
            
            
        initiation = connectionSocket.recv(2048)
        
        #error case
        if(initiation.decode()==''):
            print('client has some problem, connection is disconnected')
            continue
        
        if(initiation.decode()[0].encode()==b'\x11'):
            tempID=initiation.decode()[1:]
        else:
            rejectionBytes=bytearray(b'\x03')
            rejectionMessage='receive nickname has some problem, please restart again'
            rejectionBytes.extend(rejectionMessage.encode())
            connectionSocket.send(rejectionBytes)
            connectionSocket.close()
            print('connection refused')
        
        #if already same id
        for connectedID in connectionList:
            if connectedID[0]==tempID:
                rejectionBytes=bytearray(b'\x03')
                rejectionMessage='that nickname is already used by another user. cannot connect'
                rejectionBytes.extend(rejectionMessage.encode())
                connectionSocket.send(rejectionBytes)
                connectionSocket.close()
                print('connection refused')
                is_sameID=True
                break
        if is_sameID:
           is_sameID=False
           continue
        
        
        #start new thread
        threading._start_new_thread(handle_client, (connectionSocket, clientAddress, tempID))
#catch if KeyboardInterrupt is happened
except KeyboardInterrupt:
    print('\nBye bye~')
except Exception as e:
    print('Transport has problem, please check and try it again.')
    print('Error: ' + str(e))
finally:
    if connectionList:
        for close_socket in connectionList:
            if close_socket[2]:
                close_socket[2].close()
    serverSocket.close()
    exit();

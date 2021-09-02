# 20160769 Park Ho Yeon
#

from socket import *
from random import *
import sys
import time
import threading

#node ip address and port number
node1=('nsl2.cau.ac.kr', 20769)
node2=('nsl2.cau.ac.kr', 30769)
node3=('nsl2.cau.ac.kr', 40769)
node4=('nsl2.cau.ac.kr', 50769)
#header type
headToConnection=b'\x01'
headToNormalMessage=b'\x02'
headToACK=b'\x03'
headToFAIL=b'\x04'
headToALIVE=b'\x05'
headToClosed=b'\x00'

#node initiate
leftNode=list()
rightNode=list()

connectWishList=list()#connectWishList
connectedList=list()#for send list
AliveList=list()#for alive
deadList=list()#for stop to running alive
failedList=list()#for connection request test

#message storage
cacheList=list()

#initiate variables
portType=0
p2pPort=0
p2pSocket = socket(AF_INET, SOCK_DGRAM)
nowconnection=0
seqnum=randrange(99999) #give random value on seqnum, so avoid if start same node but not conflict same seqnum
starting=seqnum
nickname=''
IPAddress = 'nsl2.cau.ac.kr'
initTimeout=5
aliveTimeout=5
p2pVersion='1.1'

#--------------------------method--------------------------#

def connection_request_send():
    connectionRequest=bytearray(headToConnection)
    #send message in connectWishList
    for target in connectWishList:
        p2pSocket.sendto(connectionRequest,(target[0],target[1]))
    
def sendAll(message):
    #send all connected Node
    for target in connectedList:
        p2pSocket.sendto(message, target)
        
def sendAllExcept(message, exceptNode):
    #send all connected Node except one node
    for target in connectedList:
        if target==exceptNode:
            continue
        p2pSocket.sendto(message, target)
    
def recv_continue():
    print('receiving ready.')
    while True:
        (recvMessage, recvAddress)=p2pSocket.recvfrom(1024)
            
        header=recvMessage.decode()[0].encode()
        
        if header == headToConnection: #only headtype
            if not recvAddress in connectedList:
                if len(connectedList) >=2: #already max
                    print('sys: this node already has maximum connection, we cannot connected anymore!')
                    AckOrFailMessage=bytearray(headToFAIL)
                elif not ((recvAddress[0]==leftNode[0] and recvAddress[1]==leftNode[1]) or (recvAddress[0]==rightNode[0] and recvAddress[1]==rightNode[1])): #invalid peer node
                    print(recvAddress)
                    print(leftNode)
                    print(rightNode)
                    print('sys: '+str(recvAddress)+' node is invalid neighbor')
                    AckOrFailMessage=bytearray(headToFAIL)
                else:
                    connectedList.append(recvAddress)
                    threading._start_new_thread(aliveControll, (recvAddress,))                    
                    AckOrFailMessage=bytearray(headToACK)
                    fromNode=[recvAddress[0], recvAddress[1]]
                    if fromNode in connectWishList:
                        connectWishList.remove(fromNode)
                p2pSocket.sendto(AckOrFailMessage, recvAddress)
            
        if header == headToNormalMessage: #headtype-sourceNodeAddress-seqnum-Message
        
            sourceAddress=list()
            MsgSeqnum=0
            
            extractMessage=recvMessage.decode()[1:]
            targetSplit=extractMessage.split('\\')
            sourceIP = targetSplit[0]
            sourcePort = int(targetSplit[1])
            MsgSeqnum = int(targetSplit[2])
            
            sourceAddress.append(sourceIP)
            sourceAddress.append(sourcePort)
            
            if gethostbyname(IPAddress) == sourceAddress[0] and p2pPort == sourceAddress[1]:
                print('sys: send message is run arround, please check message or network again')
                continue 
            
            is_same=False
                
            for searching in cacheList: #searching that is same message comming
                if sourceAddress == searching[0] and MsgSeqnum == searching[1]: #same message
                    is_same=True
                    break #discard
                
            if(is_same):#discard if same seqnum at same source is already
                continue
                
            cmpMessage=list()
            cmpMessage.append(sourceAddress)#source port
            cmpMessage.append(MsgSeqnum)#seqnum
            cmpMessage.append(recvAddress)
            cacheList.append(cmpMessage)
                
            msg=''
               
            for counter in range(len(targetSplit[3:])):
               if counter == 0:
                   msg+=targetSplit[3]
                   
               else:
                   msg+='\\'+targetSplit[3+counter]
                  
            print(msg)
                
            sendAllExcept(recvMessage, recvAddress)
            
        if header == headToACK: #only headtype
            fromNode=[recvAddress[0], recvAddress[1]]
            if fromNode in connectWishList: #receive only it is wishlist(=before this program send connectionRequest)
                connectedList.append(recvAddress) 
                threading._start_new_thread(aliveControll, (recvAddress,)) 
                connectWishList.remove(fromNode) #remove this node in wish list
                broadMessage=str(gethostbyname(IPAddress))+'\\'+str(p2pPort)+'\\'+str(starting)+'\\'+nickname+'['+str()+str(gethostbyname(IPAddress))+', '+str(p2pPort)+'] has joined this P2P chatting network!'
                sendBytearray=bytearray(headToNormalMessage)
                sendBytearray.extend(broadMessage.encode())
                p2pSocket.sendto(sendBytearray, recvAddress)

                
        if header == headToFAIL: #only headtype
            print('sys: '+str(recvAddress)+' connection is failed')
            failedList.append(recvAddress) #add to failedList, but not remove this node in connectWishList.(when version up, we can use connectWishList to request again)
        if header == headToALIVE:
            AliveList.append(recvAddress)
        if header == headToClosed: #only headtype
            if recvAddress in connectedList:
                connectedList.remove(recvAddress)
                deadList.append(recvAddress)
                
            
            
            
    
    
def aliveControll(targetNode):
    count = 0
    aliveCheckMSG=bytearray(headToALIVE)
    while True:
        p2pSocket.sendto(aliveCheckMSG, targetNode)
        time.sleep(aliveTimeout)
        if targetNode in AliveList:
            count = 0
        else:
            count += 1
        
        while targetNode in AliveList:
            AliveList.remove(targetNode)
        
        if count >=2: # if equal or more than second timeout
            print('sys: '+str(targetNode)+ ' is disconnected')
            connectedList.remove(targetNode)
            break
        elif targetNode in deadList: # when node is dead
            while targetNode in deadList:
                deadList.remove(targetNode)
            break #finish this loop
    
def connectionTimeout():
    time.sleep(initTimeout)
    for tempNode in connectWishList: #not yet connected
        convertNode=(tempNode[0],tempNode[1])
        if not tempNode in failedList: #even not receive failed message
            print('sys: '+str(tempNode)+ ' connection failed, timed out')
        
    connectWishList.clear()
#--------------------------main start--------------------------#

#argv check
if not len(sys.argv) == 3:
    print('wrong command line, you must set only 2 argument to use port type and your Nickname')
    sys.exit()
    
#import port type
try:
    portType = int(sys.argv[1])
except ValueError:
    print('port type has error, please try it again')
    sys.exit()

if portType<1 or portType>4:
    print('it doesn\'t support that type, please write 1 to 4')
    sys.exit()
    
#set Nickname
nickname=sys.argv[2]

#set P2P socket
if portType == 1:
    p2pPort=node1[1]
elif portType == 2:
    p2pPort=node2[1]
elif portType == 3:
    p2pPort=node3[1]
elif portType == 4:
    p2pPort=node4[1]
    
p2pSocket.bind(('', p2pPort))

#set left & right
if portType == 1:
    leftNode.append(gethostbyname(node4[0]))
    leftNode.append(node4[1])
    rightNode.append(gethostbyname(node2[0]))
    rightNode.append(node2[1])
elif portType == 2:
    leftNode.append(gethostbyname(node1[0]))
    leftNode.append(node1[1])
    rightNode.append(gethostbyname(node3[0]))
    rightNode.append(node3[1])
elif portType == 3:
    leftNode.append(gethostbyname(node2[0]))
    leftNode.append(node2[1])
    rightNode.append(gethostbyname(node4[0]))
    rightNode.append(node4[1])    
elif portType == 4:
    leftNode.append(gethostbyname(node3[0]))
    leftNode.append(node3[1])
    rightNode.append(gethostbyname(node1[0]))
    rightNode.append(node1[1])
    
print('The P2P node is ready to receive on port '+str(p2pPort)+', its nickname: '+nickname)

#try before KeyboardInterrupt is happened
try:
    #append left node and right node to connectWishList
    connectWishList.append(leftNode)
    connectWishList.append(rightNode)
    
    connection_request_send() # send connectionRequest
    threading._start_new_thread(connectionTimeout, ()) #thread that check timed out on.
    
    threading._start_new_thread(recv_continue, ())
    
    seqnum+=1
    
    while True:
        #chatting on
        chatting = input()
        if chatting=='':
            continue
        sendMessage=''
        
        #command case    
        if chatting[0]=='\\':
            commandSplit=chatting.split(' ')
            if commandSplit[0]=='\\connection':
                if (len(connectedList) == 0):
                    print('no any connected peer node')
                else:
                    print(connectedList)
            elif commandSplit[0]=='\\help':
                print('----------------------command list----------------------')
                print('\\connection: show the <IP, port> list of connected peers')
                print('\\help: show help message, including list of commands')
                print('\\quit: disconnect from network, and quit')
            elif commandSplit[0]=='\\quit':
                print('\nBye bye~')
                break
            else:
                print('sys: wrong command, if you need to help, please write\"\\help\" to know command.')
        else:
            if (len(connectedList) == 0):
                print('no any connected peer node')
                continue
                
            
            sendMessage=str(gethostbyname(IPAddress))+'\\'+str(p2pPort)+'\\'+str(seqnum)+'\\'+nickname+'> '+chatting
            sendBytearray=bytearray(headToNormalMessage)
            sendBytearray.extend(sendMessage.encode())
            sendAll(sendBytearray)
            seqnum+=1
            
                

#catch if KeyboardInterrupt is happened
except KeyboardInterrupt:
    print('\nBye bye~')
except Exception as e:
    print('Transport has problem, please check and try it again.')
    print('Error: ' + str(e))
finally:
    broadMessage=str(gethostbyname(IPAddress))+'\\'+str(p2pPort)+'\\'+str(seqnum)+'\\'+nickname+'['+str()+str(gethostbyname(IPAddress))+', '+str(p2pPort)+'] has disconnected this P2P chatting network.'
    ByeBA=bytearray(headToNormalMessage)
    ByeBA.extend(broadMessage.encode())
    sendAll(ByeBA)
    sendBytearray=bytearray(headToClosed)
    sendAll(sendBytearray)
    p2pSocket.close()
    exit();

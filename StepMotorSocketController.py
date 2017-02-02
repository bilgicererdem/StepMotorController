import socket 
import sys  
import subprocess 
import RPi.GPIO as GPIO
import time
from threading import Thread
import numpy as np
import cv2
import os

GPIO.setwarnings(False) 
GPIO.cleanup()
GPIO.setmode(GPIO.BCM)
coil_A_1_pin = 23
coil_A_2_pin = 24
coil_B_1_pin = 4
coil_B_2_pin = 17

GPIO.setup(coil_A_1_pin, GPIO.OUT)
GPIO.setup(coil_A_2_pin, GPIO.OUT)
GPIO.setup(coil_B_1_pin, GPIO.OUT)
GPIO.setup(coil_B_2_pin, GPIO.OUT)

seq = [[1,0,1,0],
	[0,1,1,0],
	[0,1,0,1],
	[1,0,0,1]]

seq_rev=[[1,0,0,1],
	[0,1,0,1],
	[0,1,1,0],
	[1,0,1,0]]

def trd():
   global durum
   global sy
   while(True):
	if durum == 2:
		setStep(seq_rev[sy%4][0],seq_rev[sy%4][1],seq_rev[sy%4][2],seq_rev[sy%4][3])
		sy=sy+1
		sy=sy%4
		time.sleep(0.01)
		setStep(0,0,0,0)
		time.sleep(delay)

	elif durum == 1:
		setStep(seq[sy%4][0],seq[sy%4][1],seq[sy%4][2],seq[sy%4][3])
		sy=sy+1
		sy=sy%4
		time.sleep(0.01)
		setStep(0,0,0,0)
		time.sleep(delay)
	elif durum == 0:
		setStep(0,0,0,0)
		time.sleep(0.01)
	time.sleep(0.1)
def setStep(w1, w2, w3, w4):
	GPIO.output(coil_A_1_pin, w1)
	GPIO.output(coil_A_2_pin, w2)
	GPIO.output(coil_B_1_pin, w3)
	GPIO.output(coil_B_2_pin, w4)
global durum
global sy
global delay
global cm
durum=0
sy=0
delay = 0.15
os.system('sudo modprobe bcm2835-v4l2')
durum=0
sy=0
cm=0
w=480
h=320
my_camera = cv2.VideoCapture(0)
my_camera.set(3,w)
my_camera.set(4,h)
time.sleep(2)
def cmr():
  global cm
  global durum
  while (True):
   if cm == 1:
    success, image = my_camera.read()
    image = cv2.flip(image,-1)
    image = cv2.GaussianBlur(image,(5,5),0)

    image_HSV = cv2.cvtColor(image,cv2.COLOR_BGR2HSV)
    lower_pink = np.array([21,100,100])
    upper_pink = np.array([31,255,255])
    mask = cv2.inRange(image_HSV,lower_pink,upper_pink)
    mask = cv2.GaussianBlur(mask,(5,5),0)

    # findContours returns a list of the outlines of the white shapes in the mask (and a heirarchy that we shall ignore)            
    contours, hierarchy = cv2.findContours(mask,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)

    # If we have at least one contour, look through each one and pick the biggest
    if len(contours)>0:
        largest = 0
        area = 0
        for i in range(len(contours)):
            # get the area of the ith contour
            temp_area = cv2.contourArea(contours[i])
            # if it is the biggest we have seen, keep it
            if temp_area > area:
                area = temp_area
                largest = i
        # Compute the coordinates of the center of the largest contour
        coordinates = cv2.moments(contours[largest])
        target_x = int(coordinates['m10']/coordinates['m00'])
        target_y = int(coordinates['m01']/coordinates['m00'])
        # Pick a suitable diameter for our target (grows with the contour)
        diam = int(np.sqrt(area)/4)
        # draw on a target
	#cv2.putText(image,"KEDI"+str(target_x)+","+str(target_y),(target_x,target_y),cv2.FONT_HERSHEY_PLAIN,1,[255,255,255]) 
        
	print(target_x)
	if target_x<150 and target_x>1:
		durum=1
	elif target_x>350 and target_x<479:
		durum=2
	elif target_x>=150 and target_x<=350:
		durum=0
	
	cv2.circle(image,(target_x,target_y),diam,(0,255,0),1)
        cv2.line(image,(target_x-2*diam,target_y),(target_x+2*diam,target_y),(0,255,0),1)     
	cv2.line(image,(target_x,target_y-2*diam),(target_x,target_y+2*diam),(0,255,0),1)
    else:
	durum=0
	time.sleep(0.01)
   # cv2.imshow('View',image)
   else:
	time.sleep(0.01)
#thread.start_new_thread(cmr,())
#thread.start_new_thread(trd,())
t1 = Thread(target = trd)
t1.setDaemon(True)
t1.start()
t2 = Thread(target = cmr)
t2.setDaemon(True)
t2.start()

print 'Cihazlarin Baglanmasi Bekleniyor...' 
def sckt():
   global durum
   global delay
   s=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
   #HOST = socket.gethostbyname(socket.gethostname()) 
   HOST="192.168.42.1"
   PORT=8000
   try:
      s.bind((HOST, PORT)) 
   except socket.error as msg:
      print 'Baglanti Hatasi : ' + str(msg[0]) + ' Hata: ' + msg[1]
      sys.exit()
     
   s.listen(2) 
   print 'Cihazlarin Baglanmasi Bekleniyor...' 
   while 1:
    baglanti, adres = s.accept()
    mn = baglanti.recv(1024)
    global cm
    metin=mn.split(" ")
    if metin[1] == 'bt':
		durum=2
		baglanti.sendall("sol\n")
    if metin[1] == 'btt':
		durum=1
    		baglanti.sendall("sag\n")
    if metin[1] == "bos":
		durum=0
		setStep(0,0,0,0)
		baglanti.sendall("bos\n")  
    if metin[0] == "sld":
		delay=float(int(metin[1])*0.0985/100)
		#delay=float(metin[1]*0.0985)/100
		baglanti.sendall("ps\n")
    if metin[0] == "kamera":
		
		if metin[1] == "ac":
			cm=1
		else:
			cm=0
		
		baglanti.sendall(str(cm)+"\n")
    else:
	baglanti.sendall("pisi\n")    
if __name__ == "__main__":
	import thread
	thread.start_new_thread(sckt,())
	while True:
		 x = raw_input ("DURUM:")

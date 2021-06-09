#-------------------------------------------------------------------
# Project: Motion Detector
# Author: Joshua McCarty
# Date: 5/22/2021
# Description: Detect motion, sound an alarm, turn on light,
# take image and video, send email.
#-------------------------------------------------------------------



#-------------------------------------------------------------------
# Imports and Initializations
#-------------------------------------------------------------------
import datetime
from time import sleep

# import for camera
from picamera import PiCamera 
import subprocess

# import for light trigger and motion sensor
import RPi.GPIO as GPIO

# imports for sound
from pygame import mixer
mixer.init()
import random

# imports for email
import smtplib
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.application import MIMEApplication
from email import encoders



#-------------------------------------------------------------------
# Global Variables
#-------------------------------------------------------------------
camera = PiCamera() # assign camera module on raspi
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)
GPIO.setup(7, GPIO.IN)      #Read output from PIR motion sensor
GPIO.setup(11, GPIO.OUT)    #LED output pin

# email send and recieve addresses and password
email_user = "EMAIL ADDRESS"
email_password = "PASSWORD"
email_send = "EMAIL ADDRESS"

# times for operation 
startTime = datetime.time(12, 00, 00, 0) # 20:00 (8:00) PM
stopTime = datetime.time(8, 00, 00, 0) # 8:00 AM
midNightUp = datetime.time(23, 59, 59, 999999)
midNightDown = datetime.time(0, 00, 00, 0)



#-------------------------------------------------------------------
# searchMotion()
#-------------------------------------------------------------------
def searchMotion():
    i=GPIO.input(7)

    if i==0:                 #When output from motion sensor is LOW
        print "No intruders",i
        sleep(0.1)
        return False
    
    elif i==1:               #When output from motion sensor is HIGH
        print "Intruder detected",i
        sleep(0.1)
        return True



#-------------------------------------------------------------------
# checkTime()
#-------------------------------------------------------------------
def checkTime():
    
    currentTime = datetime.datetime.now().time()

    if (startTime <= currentTime) and (midNightUp >= currentTime):
        return True
    if midNightDown < currentTime and stopTime >= currentTime:
        return True

    if startTime > currentTime and stopTime < currentTime:
        return False



#-------------------------------------------------------------------
# startVideo()
#-------------------------------------------------------------------
def startVideo():
    subprocess.call('rm video.h264', shell=True)
    #camera.resolution = (1920, 1080)
    camera.rotation = 180
    camera.framerate = 25
    camera.start_preview()
    camera.start_recording('/home/pi/Desktop/video.h264')
    print('Video Recording')



#-------------------------------------------------------------------
# soundAlarm()
#-------------------------------------------------------------------
def soundAlarm():
    # randomly generates a number between 0 and 4 and then selects appropriate sound clip
    for x in range(5):
        selection = random.randint(0,4)
    
    if selection == 0: 
        sound = mixer.Sound('sound1.wav') # sound must be a .wav file
        sound.play()
    if selection == 1: 
        sound = mixer.Sound('sound2.wav')
        sound.play()
    if selection == 2: 
        sound = mixer.Sound('sound3.wav')
        sound.play()
    if selection == 3: 
        sound = mixer.Sound('sound4.wav')
        sound.play()
    if selection == 4: 
        sound = mixer.Sound('sound5.wav')
        sound.play()
    print('Alarm Activated')



#-------------------------------------------------------------------
# takePicture()
#-------------------------------------------------------------------
def takePicture():
    camera.start_preview()
    for i in range(5):
        sleep(0.5)
        camera.capture('/home/pi/Desktop/image%s.jpg' % i)
    camera.stop_preview()
    print('Images Captured')



#-------------------------------------------------------------------
# stopVideo()
#-------------------------------------------------------------------
def stopVideo():
    camera.stop_recording()
    camera.stop_preview()
    
    # convert video from .h264 to .mp4
    subprocess.call('rm video.mp4', shell=True)
    subprocess.call('MP4Box -add video.h264 video.mp4', shell=True)
    print('End Recording')



#-------------------------------------------------------------------
# sendEmail()
#-------------------------------------------------------------------
def sendEmail():
    # creates the email subject
    subject = "Motion Detected | %s" % masterTime

    msg = MIMEMultipart()
    msg["From"] = email_user
    msg["To"] = email_send
    msg["Subject"] = subject

    # adds email text
    body = "Motion has been detected on %s! " % masterTime
    msg.attach(MIMEText(body,"plain"))

    # adds (5) images to email named image0.jpg-image4.jpg
    for i in range(5):
        attachment = 'image%s.jpg' % i 
        fp = open(attachment, 'rb')                                                    
        img = MIMEImage(fp.read())
        fp.close()
        img.add_header('Content-Disposition','attachment',filename='image%s_' % i + masterTime + '.jpg')
        msg.attach(img)

    # adds video to email
    attachment = 'video.mp4'
    fp = open(attachment, 'rb')                                                    
    vid = MIMEApplication(fp.read(),_subtype=".mp4")
    fp.close()
    vid.add_header('Content-Disposition','attachment',filename='video_' + masterTime + '.mp4')
    msg.attach(vid) #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

    # contancts gmail
    text = msg.as_string()
    server = smtplib.SMTP("smtp.gmail.com",587)
    server.starttls()
    server.login(email_user,email_password)

    # sends and quits email
    server.sendmail(email_user,email_send,msg.as_string())
    server.quit()

    print('Email Sent')



#-------------------------------------------------------------------
# Main
#-------------------------------------------------------------------
going = True
while(going):

    if (checkTime() == True) and (searchMotion() == True):

        masterTime = datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S') # records the time of the initial motion detection

        startVideo() # begins recording a video
    
        sleep(5) # waits 5 seconds

        GPIO.output(11, 1)  #Turn ON LED, closes relay to turn on light

        soundAlarm() # begins making noises
     
        takePicture() # takes (5) pictures
    
        sleep(15) # waits (15) seconds for video

        stopVideo() # stops video after (1) minutes

        sleep(15) # waits (15) seconds for video

        GPIO.output(11, 0)  #Turn OFF LED, opens relay to turn off light
    
        sendEmail() # sends email of images and video
        
        sleep(120) # waits 2 min before next trigger

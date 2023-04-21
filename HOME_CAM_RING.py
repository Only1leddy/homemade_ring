import RPi.GPIO as GPIO
from gpiozero import LightSensor
import time
import subprocess
import numpy as np
from picamera2 import Picamera2, Preview
from picamera2.encoders import H264Encoder
from picamera2.outputs import FileOutput
import smtplib
from os.path import basename
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from datetime import datetime
# Set the video size and frame rate
main_size = (1280, 720)
lores_size = (320, 240)
framerate = 30
# Initialize the camera
picam2 = Picamera2()
video_config = picam2.create_video_configuration(
    main={"size": main_size, "format": "RGB888"},
    lores={"size": lores_size, "format": "YUV420"})
picam2.configure(video_config)
encoder = H264Encoder(1000000, framerate)
picam2.encoder = encoder
##preview option
#picam2.start_preview(Preview.QT)
picam2.start()
picam2.set_controls({"ExposureTime": 90000, "AwbEnable": True, "Brightness": 0.1, "Contrast": 1.0})
# Initialize variables
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(20, GPIO.OUT)
ldr = LightSensor(12)
w, h = lores_size
prev = None
encoding = False
ltime = 0
sent_items = 0
maxium = 21
wt = 5
dif = 14
ex = 90000
#main loop
while True:
    if ldr.value == 0.0:
        ex = 90000
    else:
        ex = 3000
    picam2.set_controls({"ExposureTime": ex,
                     "AwbEnable": True, "Brightness": 0.0,
                     "Contrast": 1.0,})
    #stop if max reached
    if sent_items == maxium:
        GPIO.cleanup()
        break
    cur = picam2.capture_buffer("lores")
    cur = cur[:w*h].reshape(h, w)
    #check thesesomething to comper
    if prev is not None:
        # Measure pixel differences between current and previous frame
        mse = np.square(np.subtract(cur, prev)).mean()
        if mse > dif:
            if not encoding:
                filename = "Room/{}.h264".format(int(time.time()))
                encoder.output = FileOutput(filename)
                picam2.start_encoder()
                encoding = True
                print("New Motion", mse)
                GPIO.output(20, GPIO.HIGH)
            ltime = time.time()
        else:
            if encoding and time.time() - ltime > wt:
                picam2.stop_encoder()
                encoding = False
                print(mse)
                print('recording stopped')
                GPIO.output(20, GPIO.LOW)
                # Convert the recorded video to MP4 format using ffmpeg
                command = ["ffmpeg", "-i", filename, "-c:v", "libx264", "-preset", "fast", "-pix_fmt", "yuv420p",
                           "-crf", "23", "-c:a", "copy", "{}.mp4".format(filename[:-5])]
                subprocess.call(command)
                print('convert is complated now')
                timestamp = datetime.now().isoformat()
                print('sending email')
                #send email stuff
                from_addr = "YOUR_EMAIL_SENDING"
                to_addr = "TOO_ADDRES_EMAIL"
                subject = f'{timestamp}'
                content = 'Hey man check the film'
                
                msg = MIMEMultipart()

                msg['From'] = from_addr
                msg['To'] = to_addr
                msg['Subject'] = subject
                body = MIMEText(content, 'plain')
                msg.attach(body)

                filename = filename[:-5] + '.mp4'
                
                with open(filename, 'rb') as f:
                    attachment = MIMEApplication(f.read(),Name=basename(filename))
                    attachment['Content-Dispostion'] = 'attachment; filename="{}"'.format(basename(filename))
                
                msg.attach(attachment)
                
                server = smtplib.SMTP_SSL('smtp.gmail.com',465)
                server.login("YOUR_EMAIL_ADS", "YOUR_EMAIL_PW")
                server.send_message(msg, from_addr=from_addr, to_addrs=[to_addr])
                
                server.quit()
                print('email sent!')
                sent_items += 1
                print(f'sent items {sent_items} emails')
                print(f'this set it off {mse}')
                print('<<<<<<< bk to monitering all good >>>>')

    prev = cur

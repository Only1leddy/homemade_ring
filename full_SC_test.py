import time
from picamera2 import Picamera2, Preview
import numpy as np
#from libcamera import controls
#from picamera2.encoders import H264Encoder
from gpiozero import LightSensor
# Set the video size and frame rate
main_size = (1280, 720)
lores_size = (320, 240)
framerate = 30
ldr = LightSensor(12)
import RPi.GPIO as GPIO
# Initialize the camera
picam2 = Picamera2()
#GPIO.setmode(GPIO.BCM)
#GPIO.setwarnings(False)
GPIO.setup(20, GPIO.OUT)
video_config = picam2.create_video_configuration(
    main={"size": main_size, "format": "RGB888"},
    lores={"size": lores_size, "format": "YUV420"})

config = picam2.create_preview_configuration(lores={"size": lores_size, "format": "YUV420"})
picam2.configure(config)

###picam2.configure(video_config)

#encoder = H264Encoder(1000000, framerate)
picam2.set_controls({"ExposureTime": 90000,
                     "AwbEnable": True, "Brightness": 0.0,
                     "Contrast": 1.0,})
                    # "AfMode": controls.AfModeEnum.Continuous})
#picam2.encoder = encoder
picam2.start_preview(Preview.QT)
picam2.start()


# Initialize variables
w, h = lores_size
prev = None
encoding = False
ltime = 0
sent_items = 0
maxium = 5
wt = 1
dif = 20
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
                encoding = True
                print(f"New Motion DETECTED VALUE:{mse}")
                GPIO.output(20, GPIO.HIGH)
            ltime = time.time()
        else:
            if encoding and time.time() - ltime > wt:
                encoding = False
                print(f'recording stoped RESET VALUE:{mse}')
                GPIO.output(20, GPIO.LOW)
                
    prev = cur

#time.sleep(10)
#picam2.capture_file('/home/leddy/%s.jpg' % timestamp)
#picam2.stop_preview()
#picam2.stop()


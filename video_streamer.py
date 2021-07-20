import cv2
import base64
from picamera import PiCamera
from picamera.array import PiRGBArray
import time, socket, logging, configparser, argparse, sys

# pip3 install opencv-python 
# sudo apt-get install libcblas-dev
# sudo apt-get install libhdf5-dev
# sudo apt-get install libhdf5-serial-dev
# sudo apt-get install libatlas-base-dev
# sudo apt-get install libjasper-dev 
# sudo apt-get install libqtgui4 
# sudo apt-get install libqt4-test

#get the directory of app from cmd line arguments, if any given 
parser = argparse.ArgumentParser()
parser.add_argument('--d', nargs=1, default=None)
args = parser.parse_args()

APP_DIR = args.d[0] if args.d != None else "./"
CONFIGURATIONS = APP_DIR + 'configuration.ini'

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(APP_DIR + 'logs/video-streamer | ' + str(time.asctime()) + '.log'),
        logging.StreamHandler()
    ]
)                    

config = configparser.ConfigParser()

if len(config.read(CONFIGURATIONS)) == 0:
    logging.error("Could Not Read Configurations File: " + CONFIGURATIONS)
    sys.exit()     

# Get the relevant configurations from configuration.ini file
DRONE_ID = config['drone']['id']
HOST_IP = config['cloud-app']['ip']
VIDEO_PORT = int( config['cloud-app']['video-port'])

GRAYSCALE = config['video']['grayscale'].lower() == 'true'
FRAMES_PER_SECOND = int( config['video']['fps'])
JPEG_QUALITY = int( config['video']['quality'])
WIDTH = int( config['video']['width'])
HEIGHT = int( config['video']['height'])

logging.info('FPS: %s  Quality: %s  Width %s Height %s  Grayscale: %s', 
             str(FRAMES_PER_SECOND), str(JPEG_QUALITY), str(WIDTH), str(HEIGHT), GRAYSCALE)
logging.info('Drone ID: %s  Video Recipient: %s:%s', str(DRONE_ID), str(HOST_IP), str(VIDEO_PORT))

camera = None
video_socket = None

# Method to convert and combine drone id and image message body to bytes to be sent via socket
def create_datagram_message(drone_id, msg_body):
        return drone_id.encode() + base64.b64encode(msg_body)   

while(True):
    try:
        camera = PiCamera()
        camera.resolution = (WIDTH, HEIGHT)
        camera.framerate = FRAMES_PER_SECOND

        # Capture the raw image data from the pi camera hardware
        rawCapture = PiRGBArray(camera, size=(WIDTH, HEIGHT))
        time.sleep(0.1)

        logging.info("Camera module initiated")
        
#         Initiate udp socket connection to server for multimedia communication
        video_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        video_socket.connect((HOST_IP, VIDEO_PORT))

        logging.info("Socket Opened, Video Streaming started")


        for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
            image_data = frame.array
            
            image_data = cv2.rotate(image_data, cv2.ROTATE_180)
            
#             Set graysacle option to true in config, if internet connection is slow
            if GRAYSCALE:
                image_data = cv2.cvtColor(image_data, cv2.COLOR_BGR2GRAY)
            
#             Convert raw image data to jpg format using open cv api
            code, jpg_buffer = cv2.imencode(".jpg", image_data, [int(cv2.IMWRITE_JPEG_QUALITY), JPEG_QUALITY])

            datagramMsgBytes = create_datagram_message(DRONE_ID, jpg_buffer)
            print
            (datagramMsgBytes)
            video_socket.sendall(datagramMsgBytes)
            
            rawCapture.truncate(0)

# release all resources in case of error and continue the process
    except Exception as e:
        logging.error("Video Stream Ended: "+str(e))
        
        if camera != None:
            camera.close()
        if video_socket != None:
            video_socket.close()
        
        time.sleep(2)

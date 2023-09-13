from bluepy.btle import Scanner, DefaultDelegate
import time, datetime
import questionary
import threading
import pprint
import queue
import sys
import tempfile
from picamera import PiCamera
import psycopg2
import os

os.system('clear')
if len(sys.argv) != 6:
    print("HOST PORT DBNAME USER PASSWORD")
    sys.exit(1)

global end_program 
end_program = False

videoString = "Start Taking Photos"
photos = False
photoName = ""
camera = PiCamera()

qPhoto = queue.Queue()
def takePhotos():
    fotodir = tempfile.TemporaryDirectory()
    print("Temp foto directory: " + fotodir.name)
    while not end_program:
        if photos:
            if secondCounter <= 0:
                filename = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d_%H:%M:%S')
                photoPath = fotodir.name +'/'+filename+'.jpg'
                camera.capture(photoPath)
                qPhoto.put(photoPath)
                secondCounter = 60
            secondCounter-=1
        time.sleep(1)
        if not photos:
            secondCounter = 1
    fotodir.cleanup()

photoThread = threading.Thread(target=takePhotos)
photoThread.start()

conn = psycopg2.connect(host=sys.argv[1], port=sys.argv[2], dbname=sys.argv[3], user=sys.argv[4], password=sys.argv[5])
conn.set_session(autocommit=True)
cur1 = conn.cursor()
cur2 = conn.cursor()

def processSQLPhoto(cur):
    while not end_program:
        try:
            photoPath = qPhoto.get(timeout=1)
            with open(photoPath, mode='rb') as photoFile: 
                wholeFile = photoFile.read()
                cur.execute("INSERT INTO photos (time, name, filename, photo) VALUES (%s, %s, %s, %s)",
                    (datetime.datetime.now(), photoName, photoPath, wholeFile))
        except:
            pass
    cur.close()

sqlPhotoThread = threading.Thread(target=processSQLPhoto, args=(cur1,))
sqlPhotoThread.start()

q = queue.Queue()
def processSQL(cur):
    while not end_program:
        try:
            dataline = q.get(timeout=1) # name address time gravity temp
            cur.execute("INSERT INTO hydrometer (time, device, name, temperature, gravity) VALUES (%s, %s, %s, %s, %s)",
                    (dataline[2], dataline[1], dataline[0], dataline[4], dataline[3]))
        except:
            pass
    cur.close()

sqlThread = threading.Thread(target=processSQL, args=(cur2,))
sqlThread.start()


dump = False
startScan = threading.Event()
scan = threading.Event()
devicesAvailable = {} # Concurrent read write? // should lock, don't lock
devicesLogging = {} # Concurrent read write? // should lock, don't lock

# Scan
class ScanDelegate(DefaultDelegate):
    def __init__(self):
        DefaultDelegate.__init__(self)
    def handleDiscovery(self, dev, isNewDev, isNewData):
        if scan.is_set() and isNewDev and not dev.connectable:
            print(dev.addr, end=", ")
            devicesAvailable[dev.addr] = True
        elif dev.addr in devicesLogging:
            for (adtype, desc, val) in dev.getScanData():
                if desc == "Manufacturer":
                    i = 0
                    vals = [None] * 25 # why 25
                    for i in range(0, 24, 1):
                            pair = val[i*2] + val[(i*2)+1]
                            dec = int(pair, 16)
                            vals[i] = dec # Now we have an array of integers
                            i += 1
                    specific_gravity = (vals[22]<<8)+vals[23]
                    cpu_temp = vals[21]
                    q.put((devicesLogging[dev.addr], dev.addr, datetime.datetime.now(), specific_gravity, cpu_temp))
                    if dump:
                        print(datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
                        print(vals)
                        print("Specific Gravity: " + str(specific_gravity))
                        print("CPU Temp: " + str(cpu_temp))
                        print("%s = %s" % (desc, val))


def startScanner():
    scanner = Scanner().withDelegate(ScanDelegate())
    scanner.start()
    while not end_program:
        scanner.process(1)
        if startScan.is_set():
            scanner.clear()
            devicesAvailable.clear()
            scan.set()
            while not end_program:
                if not startScan.is_set():
                    scan.clear()
                    print("")
                    break
                scanner.process(1)
btScannerThread = threading.Thread(target=startScanner)
btScannerThread.start()
while True:
    result = questionary.select(
        "What command?",
        choices=["Scan", "List Logging", "Start Log", "Stop Log", "Dump Raw", videoString, "Record Event"],
    ).ask()

    if result == "List Logging":
        pprint.pprint(devicesLogging)
    elif result == "Record Event":
        #Literally just do it
        pass
    elif result == videoString:
        if photos:
            photos = False
            videoString = "Start Taking Photos"
        else:
            name = questionary.text("What will the name be?").ask()
            if name is not None:
                photoName = name
                photos = True
                videoString = "Stop Taking Photos"
    elif result == "Stop Log":
        deviceToStop = questionary.select(
            "Which device should we stop logging?",
            choices = [dev for dev in devicesLogging.keys()] + ["<-- Back"],
        ).ask()
        if deviceToStop == "<-- Back" or deviceToStop is None:
            pass
        else:
            del(devicesLogging[deviceToStop])
    elif result == "Start Log":
        deviceToLog = questionary.select(
            "Which device should we start logging?",
            choices=[dev for dev in devicesAvailable.keys() if dev not in devicesLogging.keys()] + ["Back"],
        ).ask()
        if deviceToLog == "Back" or deviceToLog is None:
            pass
        else:
            name = questionary.text("What will the nickname be?").ask()
            if name is not None:
                devicesLogging[deviceToLog] = name # Probably all need locks or something
    elif result == "Scan":
        print("You chose scan! Ctl+C To Stop")
        startScan.set() 
        while True:
            try:
                time.sleep(.25)
            except KeyboardInterrupt:
                startScan.clear()
                break
    elif result == "Dump Raw":
        dump = True
        while True:
            try:
                time.sleep(.25)
            except KeyboardInterrupt:
                dump = False
                break
    elif result is None:
        break
end_program = True
conn.close()

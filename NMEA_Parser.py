import board, busio, displayio, gc, time, math
from adafruit_display_text import label
from adafruit_bitmap_font import bitmap_font

Label = label.Label
#HelveticaBold16 = bitmap_font.load_font("/fonts/Helvetica-Bold-16.bdf")
GoMedium16 = bitmap_font.load_font("/fonts/GoMedium-16.bdf")
Alice1MX12 = bitmap_font.load_font("/fonts/Alice1MX-12.bdf")

uart = busio.UART(board.SDA, board.SCL, baudrate = 9600, timeout = 0.2)

hasFix = False
SIV = 0
latitude = -65535.0
longitude = -65535.0
lastLat = -65535.1
lastLong = -65535.1
firstLat = -65535.2
firstLong = -65535.2
Speed = 0.0
hasUTC_time = False
hasUTC_date = False
UTC_time = ""
UTC_date = ""
lastDate = '-'
lastTime = '-'
lastMessage = ""
lastCon = ""
TTMG = ""
MTMG = ""
systemMessages = []
verbs = {}
constellations = {}
constellations['GA'] = 'Galileo'
constellations['GP'] = 'GPS'
constellations['GL'] = 'GLONASS'
constellations['GN'] = 'Comb.'
constellations['BD'] = 'Beidou'
constellations['GB'] = 'Beidou'
constellations['GQ'] = 'QZSS'

display = board.DISPLAY
mainSplash = displayio.Group()
color_bitmap = displayio.Bitmap(160, 128, 1)
color_palette = displayio.Palette(1)
color_palette[0] = 0xFFFFFF
bg_sprite0 = displayio.TileGrid(color_bitmap, pixel_shader=color_palette, x=0, y=0)
mainSplash.append(bg_sprite0)
lbLatitude = Label(GoMedium16, text="Latitude:", color=0x000000)
lbLatitude.x = 5
lbLatitude.y = 10
mainSplash.append(lbLatitude)
lbLongitude = Label(GoMedium16, text="Longitude:", color=0x000000)
lbLongitude.x = 5
lbLongitude.y = 30
mainSplash.append(lbLongitude)
lbUTC_Time = Label(GoMedium16, text="Time: "+UTC_time, color=0x000000)
lbUTC_Time.x = 5
lbUTC_Time.y = 50
mainSplash.append(lbUTC_Time)
lbConstellation = Label(GoMedium16, text="", color=0x000000)
lbConstellation.x = 5
lbConstellation.y = 70
mainSplash.append(lbConstellation)
lbSIV = Label(GoMedium16, text="SIV: 00", color=0x000000)
lbSIV.x = 5
lbSIV.y = 90
mainSplash.append(lbSIV)
lbDistance = Label(GoMedium16, text="Distance", color=0x000000)
lbDistance.x = 5
lbDistance.y = 110
mainSplash.append(lbDistance)

secondSplash = displayio.Group()
color_bitmap = displayio.Bitmap(160, 128, 1)
bg_sprite1 = displayio.TileGrid(color_bitmap, pixel_shader=color_palette, x=0, y=0)
secondSplash.append(bg_sprite1)

lbSpeed = Label(GoMedium16, text="Speed", color=0x000000)
lbSpeed.x = 5
lbSpeed.y = 10
secondSplash.append(lbSpeed)
lbTTMG = Label(GoMedium16, text="TTMG", color=0x000000)
lbTTMG.x = 5
lbTTMG.y = 30
secondSplash.append(lbTTMG)
lbMTMG = Label(GoMedium16, text="MTMG", color=0x000000)
lbMTMG.x = 5
lbMTMG.y = 50
secondSplash.append(lbMTMG)
lbSystemMessage0 = Label(GoMedium16, text="TXT", color=0x000000)
lbSystemMessage0.x = 5
lbSystemMessage0.y = 70
secondSplash.append(lbSystemMessage0)
lbSystemMessage1 = Label(GoMedium16, text="TXT", color=0x000000)
lbSystemMessage1.x = 5
lbSystemMessage1.y = 90
secondSplash.append(lbSystemMessage1)
lbSystemMessage2 = Label(GoMedium16, text="DOP", color=0x000000)
lbSystemMessage2.x = 5
lbSystemMessage2.y = 110
secondSplash.append(lbSystemMessage2)

splashes = [mainSplash, secondSplash]
splashes[0].hidden = False
splashes[1].hidden = True
splashIndex = 0
display.show(splashes[splashIndex])
lastSwitch = time.monotonic()
switchInterval = 10

def toRad(x):
  return x * 3.141592653 / 180

def haversine(lat1, lon1, lat2, lon2):
  R = 6371
  x1 = lat2-lat1
  dLat = toRad(x1)
  x2 = lon2-lon1
  dLon = toRad(x2)
  a = math.sin(dLat/2) * math.sin(dLat/2) + math.cos(toRad(lat1)) * math.cos(toRad(lat2)) * math.sin(dLon/2) * math.sin(dLon/2)
  c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
  d = R * c
  return round((d + 2.220446049250313e-16) * 100) / 100

def refresh1():
    global TTMG, MTMG, Speed
    global lbTTMG, lbMTMG, lbSpeed
    lbTTMG.text = "TTMG: {}".format(TTMG)
    lbMTMG.text = "MTMG: {}".format(MTMG)
    lbSpeed.text = "Speed: {} km/h".format(Speed)

def refresh0():
    global lbLatitude, lbLongitude, lbDistance, lbConstellation
    global SIV, lastCon, lastLat, latitude, lastLong, longitude, firstLat, firstLong
    if (lastLat != latitude or lastLong != longitude) and latitude > -65000.0:
        lbLatitude.text = "{:.8f}".format(latitude)
        lbLongitude.text = "{:.8f}".format(longitude)
    if firstLat != -65535.2:
        distance = haversine(firstLat, firstLong, latitude, longitude)
        lbDistance.text = "Distance: {} m".format(distance)
    if hasUTC_time and lastTime != UTC_time:
        lbUTC_Time.text = UTC_time + " " + UTC_date
    lbSIV.text = "SIV: " + str(SIV)
    
    # Display the last 3 constellations at most
    s = lbConstellation.text
    if s == "":
        # First time, easy...
        lbConstellation.text = lastCon
        return
    t = s.split(",")
    if t.count(lastCon) == 0:
        # Skip if the constellation is already in the list
        t.append(lastCon)
        # remove constellations above 3
        if len(t)>3:
            t.reverse()
            while len(t)>3:
                t.pop()
            t.reverse()
        lbConstellation.text = ",".join(t)
    
def parseDegrees(term):
  try:
    value = float(term) / 100.0
  except:
    return 0
  left = int(value)
  value = (value - left) * 1.66666666666666
  value += left
  return value

def setTime(token):
    global UTC_time, hasUTC_time, lastTime
    lastTime = UTC_time
    UTC_time = token[0:2] + ":" + token[2:4] + ":" + token[4:6]
    hasUTC_time = True
    #print("Time is {}".format(UTC_time))
    gc.collect()

def setDate(token0, token1, token2):
    global UTC_date, hasUTC_date, lastDate
    lastDate = UTC_date
    UTC_date = token2 + "/" + token1 + "/" + token0
    hasUTC_date = True
    print("Date is {}".format(UTC_date))
    gc.collect()

def setConstellation(prefix):
    global constellations, lastCon
    constellation = constellations.get(prefix)
    if constellation != None:
        lastCon = constellation

def setCoords(long, longNS, lat, latEW):
    global latitude, longitude, lastLat, lastLong, firstLat, firstLong
    long = parseDegrees(long)
    if longNS == "S":
        long *= -1
    lat = parseDegrees(lat)
    if latEW == "w":
        lat *= -1
    hasFix = True
    lastLat = latitude
    lastLong = longitude
    latitude = lat
    longitude = long
    print("Coords: {:.8f}, {:.8f}".format(longitude, latitude))
    if firstLat == -65535.2:
        # set a starting point
        firstLat = latitude
        firstLong = longitude
    else:
        distance = haversine(firstLat, firstLong, latitude, longitude)
        print("Distance: {} m".format(distance))

def parseRMC(result):
    #print('  '.join(result))
    if result[1] != "":
        #print("RMC setting time to {}".format(result[1]))
        setTime(result[1])
    if result[2] == "A":
        #print("RMC setting coords: {} {}, {} {}".format(result[3], result[4], result[5], result[6]))
        setCoords(result[3], result[4], result[5], result[6])
    prefix = result[0][0:2]
    setConstellation(prefix)

def parseGLL(result):
    if result[1] != "":
        #print("GLL setting coords: {} {}, {} {}".format(result[1], result[2], result[3], result[4]))
        setCoords(result[1], result[2], result[3], result[4])
    if len(result) > 5:
        token = result[5]
        if token != "":
            print("Fix taken at "+token[0:2] + ":" + token[2:4] + ":" + token[4:6])
    prefix = result[0][0:2]
    setConstellation(prefix)

def parseZDA(result):
    if result[1] != "":
        #print("ZDA setting time to {}".format(result[1]))
        setTime(result[1])
    if result[2] != "":
        #print("ZDA setting date to {} {} {}".format(result[2], result[3], result[4]))
        setDate(result[2], result[3], result[4])

def parseVTG(result):
    global MTMG, TTMG, Speed
    #print('  '.join(result))
    prefix = result[0][0:2]
    setConstellation(prefix)
    if result[1] != "":
        TTMG = result[1]
        print("VTG True Track Made Good: {}".format(TTMG))
    if result[3] != "":
        MTMG = result[3]
        print("VTG Magnetic Track Made Good: {}".format(MTMG))
    if result[7] != "":
        Speed = float(result[7])
        print("Speed: {} km/h".format(Speed))

def parseGGA(result):
    prefix = result[0][0:2]
    setConstellation(prefix)
    if result[1] != "":
        #print("GGA setting time to {}".format(result[1]))
        setTime(result[1])

def parseGSV(result):
    global SIV
    prefix = result[0][0:2]
    setConstellation(prefix)
    SIV = int(result[3])

def parseGSA(result):
    if result[2] == "1":
        return
    print("DOP Mode: {}. Fix: {}D mode.".format(result[1], result[2]))
    s = "PDOP: {}, HDOP: {}, VDOP: {}".format(result[15], result[16], result[17])
    print(s)
    lbSystemMessage2.text = "DOP: {}, {}, {}".format(result[15], result[16], result[17])

def parseTXT(result):
    global systemMessages
    if result[1] == "":
        return
    systemMessages.append({
        "total" : result[1],
        "number" : result[2],
        "severity" : result[3],
        "msg" : result[4]
    })
    gc.collect()

funs = {}
funs['GGA'] = parseGGA
funs['ZDA'] = parseZDA
funs['TXT'] = parseTXT
funs['RMC'] = parseRMC
funs['GLL'] = parseGLL
funs['VTG'] = parseVTG
funs['GSV'] = parseGSV
funs['GSA'] = parseGSA

if uart.in_waiting > 0:
    s=uart.read()

while True:
    c = uart.read(1)
    while c != b'$':
        c = uart.read(1)
    s = c + uart.readline()
    if s != None:
        if s.find(b'*') > -1:
            s = s.split(b'*')
            line = s[0]
            checksum = s[1]
            try:
                checksum = int(b'0x'+checksum)
                chsum = 0
                line = line[1:]
                for i in line:
                    chsum = chsum ^ i
                if chsum != checksum:
                    print("Incorrect Checksum! {} / {}".format(chsum, checksum))
                    pass
            except:
                print("Stated checksum `{}` is not valid!".format(checksum))
            gc.collect()
            tokens=line.decode().split(',')
            verb = tokens[0][2:]
            v = verbs.get(verb)
            if v == None:
                v = {tokens[0] : 1}
            else:
                cn = v.get(tokens[0])
                if cn == None:
                    cn = 1
                v[tokens[0]] = cn
            verbs[verb] = v
            #print(verbs)
            fn = funs.get(verb)
            if fn != None:
                fn(tokens)
            else:
                print(line)
    refresh0()
    refresh1()
    if len(systemMessages) > 0:
        for m in systemMessages:
            if m['msg'] != lastMessage:
                s = "Message {} / {}, Severity: {}, {}".format(m['total'], m['number'], m['severity'], m['msg'])
                print(s)
                s = s.split(', ')
                lbSystemMessage0.text = s[0] + " [{}]".format(s[1])
                lbSystemMessage1.text = s[2]
                lastMessage = m['msg']
            systemMessages = []
    gc.collect()
    if time.monotonic() - lastSwitch >= switchInterval:
        #print("Switching screens")
        for s in splashes:
            s.hidden = True
        splashIndex += 1
        if splashIndex == len(splashes):
            splashIndex = 0
        splashes[splashIndex].hidden = False
        display.show(splashes[splashIndex])
        lastSwitch = time.monotonic()

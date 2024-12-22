WIDTH, HEIGHT = 800, 600
HSTEP, VSTEP = 13, 18
emojiglobal = set()
SCROLL_STEP = 100

def set_parameters(**params):
	global WIDTH, HEIGHT, HSTEP, VSTEP, SCROLL_STEP
	if "WIDTH" in params: WIDTH = params["WIDTH"]
	if "HEIGHT" in params: HEIGHT = params["HEIGHT"]
	if "HSTEP" in params: HSTEP = params["HSTEP"]
	if "VSTEP" in params: VSTEP = params["VSTEP"]
	if "SCROLL_STEP" in params: SCROLL_STEP = params["SCROLL_STEP"]
 
def getWidth():
    return WIDTH

def setWidth(width):
     global WIDTH
     WIDTH = width

def height():
    return HEIGHT

def setHeight(height):
     global HEIGHT
     HEIGHT = height

def hstep():
    return HSTEP

def vstep():
    return VSTEP

def scroll_step():
    return SCROLL_STEP
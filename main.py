import cv2 
from PIL import Image,ImageChops
import numpy
import math
import os
import sys
import imageio.v2 as imageio

def removeGreenScreen(infile,outfile):
    #open files
    global keyColor, tolerance
    inDataFG = Image.open(infile).convert('YCbCr')
    BG = Image.new('RGBA', inDataFG.size, (0, 0, 0, 0))
    #make sure values are set
    if keyColor == None:keyColor = inDataFG.getpixel((1,1))
    if tolerance == None: tolerance = [50,130]
    [Y_key, Cb_key, Cr_key] = keyColor
    [tola, tolb]= tolerance
    
    (x,y) = inDataFG.size #get dimensions
    foreground = numpy.array(inDataFG.getdata()) #make array from image
    maskgen = numpy.vectorize(colorClose) #vectorize masking function

    
    alphaMask = maskgen(foreground[:,1],foreground[:,2] ,Cb_key, Cr_key, tola, tolb) #generate mask
    alphaMask.shape = (y,x) #make mask dimensions of original image
    imMask = Image.fromarray(numpy.uint8(alphaMask))#convert array to image
    invertMask = Image.fromarray(numpy.uint8(255-255*(alphaMask/255))) #create inverted mask with extremes
    
    #create images for color mask
    colorMask = Image.new('RGB',(x,y),tuple([0,0,0]))
    allgreen = Image.new('YCbCr',(x,y),tuple(keyColor))

    colorMask.paste(allgreen,invertMask) #make color mask green in green values on image
    inDataFG = inDataFG.convert('RGB') #convert input image to RGB for ease of working with
    cleaned = ImageChops.subtract(inDataFG,colorMask) #subtract greens from input
    BG.paste(cleaned,(0,0),imMask)#paste masked foreground over background
    BG.save(outfile, "PNG") #save cleaned image
    
# Print iterations progress
def print_progress(iteration, total, prefix='', suffix='', decimals=1, bar_length=100):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        bar_length  - Optional  : character length of bar (Int)
    """
    str_format = "{0:." + str(decimals) + "f}"
    percents = str_format.format(100 * (iteration / float(total)))
    filled_length = int(round(bar_length * iteration / float(total)))
    bar = '█' * filled_length + '-' * (bar_length - filled_length)

    sys.stdout.write('\r%s |%s| %s%s %s' % (prefix, bar, percents, '%', suffix)),

    if iteration == total:
        sys.stdout.write('\n')
    sys.stdout.flush()

def colorClose(Cb_p,Cr_p, Cb_key, Cr_key, tola, tolb):  
    temp = math.sqrt((Cb_key-Cb_p)**2+(Cr_key-Cr_p)**2)
    if temp < tola:
        z= 0.0
    elif temp < tolb:
        z= ((temp-tola)/(tolb-tola))
    else:
        z= 1.0
    return 255.0*z

def writeLog(data,filename):
    #print(var)
    with open(filename, 'w') as out:
        out.write(str(data) + '\n')

# extract frames 
def frameCapture(path,type): 
    # Path to video file 
    vidObj = cv2.VideoCapture(path) #cv2 v3 or above
    # Used as counter variable 
    count = 0
    # checks whether frames were extracted 
    success = 1
    global length, fps
    if vidObj.isOpened():
        length = int(vidObj.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = vidObj.get(cv2.CAP_PROP_FPS)
        width = vidObj.get(cv2.CAP_PROP_FRAME_WIDTH)   
        height = vidObj.get(cv2.CAP_PROP_FRAME_HEIGHT) 
        writeLog("Frame Width : "+str(width)+"\nFrame Height : "+str(height)+"\nFrame Rate : "+str(fps),"tmp\\footageInfo.txt")
        clear_console()
        while count < length: 
            # vidObj object calls read 
            # function extract frames 
            success, image = vidObj.read() 
            # Saves the frames with frame-count 
            cv2.imwrite("tmp\\"+ str(type) +"\\frame"+ str(count).zfill(6) +".png", image)
            print_progress(count, (length-1), prefix='Creating Image Sequence', suffix="[ Frame : "+ str(count).zfill(6) +" ]", decimals=1, bar_length=50)
            count += 1

def genOutput(footage):
    global length, fps
    count = 0
    clear_console()
    images = []
    for file in [file for file in os.listdir("tmp\\footage\\") if file.endswith('.png')]:
        removeGreenScreen("tmp\\footage\\"+str(file),"tmp\\"+str(file))
        print_progress(count, (length-1), prefix='Generating Frames', suffix="[ File : "+str(file)+" ]", decimals=1, bar_length=50)
        count += 1
        images.append(imageio.imread("tmp\\"+str(file)))
    imageio.mimsave(f"out\\{footage}.webp", images, fps=fps)

def grabInput():
    clear_console()
    print ("~ A simple GreenScreen Removing tool")
    print ("~ Output wil be a .webp file")
    tolerance = input("Enter Tolerance (Ex. 50,130) \n: ")
    if tolerance == "":
        tolerance = [50,130]
    else:
        tolerance = tolerance.split(",")
        tolerance = [int(tolerance[0]),int(tolerance[1])]

    footage = input("Enter Filename with extention (Ex.Footage.mp4) \n: ")
    if footage == "":
        footage = "footage.mp4"
    return footage

def clear_files():
    if not os.path.exists('tmp'):
        os.makedirs('tmp')
    if not os.path.exists('tmp\\footage'):
        os.makedirs('tmp\\footage')
    if not os.path.exists('out'):
        os.makedirs('out')

    for file in [file for file in os.listdir("tmp\\footage\\") if file.endswith('.png') or file.endswith('.png') or file.endswith('.txt')]:
        os.remove("tmp\\footage\\"+str(file))
    for file in [file for file in os.listdir("tmp\\") if file.endswith('.png') or file.endswith('.png') or file.endswith('.txt')]:
        os.remove("tmp\\"+str(file))

def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')

def start(footage):
    global length
    files = [f for f in os.listdir('.') if os.path.isfile(f)]
    if footage in files:
        frameCapture(footage,"footage") 
        genOutput(footage[:footage.find('.')])
        clear_files()
        clear_console()
        print("\nFile Generated successfully! Check the 'out' directory.")
        print("\nPress Enter to Continue.")
        input("")
    else:
        clear_console()
        print("File not found!! Press Enter to Try Again.")
        print("Remember to copy the file into this folder.")
        input("")

if __name__ == '__main__': 
    clear_files()
    fps = 0
    done = False
    length = 0
    keyColor = None
    tolerance = None
    while not done:
        footage = grabInput()
        start(footage)
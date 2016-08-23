#Import Modules
import pygame, random, os
from pygame.locals import QUIT, KEYDOWN, K_UP, K_DOWN, K_LEFT, K_RIGHT, K_RETURN, K_ESCAPE, K_f, K_q, RLEACCEL
from tkinter import *
from tkinter.filedialog import askopenfilename

class ImageSegment():
    def __init__(self,x,y,fullImage,cropRect,isDummy = False):
        self.correctX = x
        self.correctY = y
        self.x = x
        self.y = y
        self.isDummy = isDummy
        self.image = pygame.Surface((cropRect.width,cropRect.height))
        self.image.blit(fullImage,(0,0), (cropRect.x,cropRect.y,cropRect.width,cropRect.height))

class SlidingPuzzle():
    def __init__(self, screenWidthIn, screenHeightIn):
        #Initialize Snake variables (positioning variables are measured in pixels, further initialization done in first resetPuzzle() call)
        self.screenWidth = screenWidthIn #width of the entire screen in pixels
        self.screenHeight = screenHeightIn #height of the entire screen in pixels
        self.snakeFieldWidth = screenWidthIn - 55 #total size in pixels of the field width (55 pixel buffer from window border)
        self.snakeFieldHeight = screenHeightIn - 55 #total size in pixels of the field height (10 pixel buffer from window border, 45 pixels for score pane)
        #calculate offset values to ensure centering regardless of screen size change
        self.snakeScorePaneHeight = 45 #total size in pixels of the score pane height (the width will be equal to the screen width) 
        self.xOffset = int((self.screenWidth - self.snakeFieldWidth - 2) / 2) #subtract 2 as 2 is the border size
        self.yOffset = int((self.screenHeight - self.snakeFieldHeight - self.snakeScorePaneHeight - 2) / 2) #subtract 2 as 2 is the border size
        self.slideTimeDuration = .3 #modified time rate used in conjunction with snakePreviousTimeInt to determine when ticks should occur
        self.toggledLeftArrowThisPress = False #variable to keep track of when the left arrow key is pressed, to simulate a 'key press' event that triggers on a single frame only
        self.toggledRightArrowThisPress = False
        self.toggledQThisPress = False
        self.toggledFThisPress = False
        self.clickedMouseThisPress = False
        self.font = pygame.font.Font(None, 46) #large font used for text rendering
        self.gridSize = 4 #width and height of grid (total size will be gridSize^2)
        self.instructions = ["Press the arrow keys to adjust grid size","Press F to load a custom image file","Press Q to quit the current puzzle"]
        self.resetPuzzle() #prepare the game for its first run at the end of class instantiation
    
    def shufflePieces(self,pieces):
        shuffledList = [item for sublist in pieces for item in sublist]
        random.shuffle(shuffledList)
        return [shuffledList[i:i+self.gridSize] for i in range(0, len(shuffledList), self.gridSize)]
    
    def loadPuzzleImage(self,name="pygameLogo.png"):
        self.imageName = name
        self.image = self.loadImage(self.imageName)
        self.smallImage = pygame.transform.smoothscale(self.image,(int(self.snakeFieldWidth/4),int(self.snakeFieldHeight/4)))
        
    def loadImage(self, imageName, colorkey=None):
        fullname = os.path.join(imageName)
        try:
            image = pygame.image.load(fullname)
        except:
            print('Cannot load image:', fullname)
            raise SystemExit
        image = image.convert()
        if colorkey is not None:
            if colorkey is -1:
                colorkey = image.get_at((0,0))
            image.set_colorkey(colorkey, RLEACCEL)
        image = pygame.transform.smoothscale(image,(self.snakeFieldWidth, self.snakeFieldHeight))
        return image
    
    def swapPieces(self,pieceA,pieceB):
        self.randomizedPuzzlePieces[pieceA.x][pieceA.y] = pieceB
        self.randomizedPuzzlePieces[pieceB.x][pieceB.y] = pieceA
        pieceAX = pieceA.x
        pieceAY = pieceA.y
        pieceA.x = pieceB.x
        pieceA.y = pieceB.y
        pieceB.x = pieceAX
        pieceB.y = pieceAY
    
    def checkBoardSolved(self):
        for i in range(self.gridSize):
            for r in range(self.gridSize):
                if (self.randomizedPuzzlePieces[i][r].x != self.randomizedPuzzlePieces[i][r].correctX or self.randomizedPuzzlePieces[i][r].y != self.randomizedPuzzlePieces[i][r].correctY):
                    return
        self.snakeState = 2
        self.won = True 
        
    def resetPuzzle(self,newState = 0):
        self.snakeState = newState #simple state machine used for game state (0 = awaiting first start, 1 = active, 2 = awaiting restart)
        self.deltaTime = 0 #time passed (in seconds, not milliseconds) this frame/tick (reset here so that delta time from starting frame is not factored into first running frame)
        self.solveTime = 0 #time taken to solve the puzzle
        self.puzzlePieces = [] #2d list of puzzle pieces, where (i,r) correspond to (correctX,correctY)
        self.gridSquareWidth = self.snakeFieldWidth / self.gridSize
        self.gridSquareHeight = self.snakeFieldHeight / self.gridSize
        self.curEmptyX = self.gridSize-1
        self.curEmptyY = 0
        self.won = False
        if (newState != 0): #don't prepare the game if this is our first run, as we will restart again when the player presses enter
            for i in range(self.gridSize): #create the image pieces
                self.puzzlePieces.append([])
                for r in range(self.gridSize):
                    #if (not (i == self.gridSize-1 and r == 0)): #leave the top-right piece blank
                    self.puzzlePieces[i].append(ImageSegment(i,r,self.image,pygame.Rect(self.gridSquareWidth*i,self.gridSquareHeight*r,self.gridSquareWidth,self.gridSquareHeight)))
            self.randomizedPuzzlePieces = self.shufflePieces(self.puzzlePieces) #2d list of puzzle pieces, where (i,r) correspond to (x,y)
            for i in range(self.gridSize): #shuffle the image pieces
                for r in range(self.gridSize):
                    self.randomizedPuzzlePieces[i][r].x = i
                    self.randomizedPuzzlePieces[i][r].y = r
            self.puzzlePieces[self.gridSize-1][0].isDummy = True #dummy the top-right corner piece, and swap it into the top-right corner if it isn't already there
            self.dummyPiece = self.puzzlePieces[self.gridSize-1][0]
            if (self.puzzlePieces[self.gridSize-1][0].x != self.gridSize-1 or self.puzzlePieces[self.gridSize-1][0].y != 0):
                self.swapPieces(self.puzzlePieces[self.gridSize-1][0],self.randomizedPuzzlePieces[self.gridSize-1][0])
            self.checkBoardSolved()
    
    def tryShiftPiece(self,x,y):
        #print("x: " + str(x) + ", dummyX: " + str(self.dummyPiece.x) + ", y: " + str(y) + ", dummyY: "  + str(self.dummyPiece.y))
        if (not (self.dummyPiece.x == x or self.dummyPiece.y == y)):
            return
        isXChange = self.dummyPiece.y == y
        changeAmount = (((self.dummyPiece.x > x)*2) - 1) if isXChange else (((self.dummyPiece.y > y)*2) - 1)
        curPos = x if isXChange else y
        destPos = self.dummyPiece.x if isXChange else self.dummyPiece.y
        while (curPos != destPos):
            curPos += changeAmount
            #print(str(curPos) + ", " + str(self.dummyPiece.x) + ", " + str(self.dummyPiece.y))
            if (isXChange):
                self.swapPieces(self.randomizedPuzzlePieces[x][y], self.randomizedPuzzlePieces[curPos][y])
            else:
                self.swapPieces(self.randomizedPuzzlePieces[x][y], self.randomizedPuzzlePieces[x][curPos])
        self.checkBoardSolved()
                        
    def checkMouseClickPuzzle(self):
        for i in range(self.gridSize):
            for r in range(self.gridSize):
                if (pygame.Rect(self.xOffset+self.randomizedPuzzlePieces[i][r].x*self.gridSquareWidth,self.snakeScorePaneHeight+self.yOffset+self.randomizedPuzzlePieces[i][r].y*self.gridSquareHeight,self.gridSquareWidth,self.gridSquareHeight)).collidepoint(pygame.mouse.get_pos()):
                    self.tryShiftPiece(i,r)
                        
    def checkPuzzleInput(self): #Handle Input Events   
        if (self.snakeState == 1):   
            self.solveTime += self.deltaTime           
        elif ((self.snakeState == 0 or self.snakeState == 2) and pygame.key.get_pressed()[K_RETURN]):
            self.resetPuzzle(1)     
        if (pygame.key.get_pressed()[K_LEFT] or pygame.key.get_pressed()[K_DOWN]):
            if ((not self.toggledLeftArrowThisPress) and self.snakeState != 1): #attempt to pause or unpause, but only if the game is active
                self.gridSize = max(self.gridSize-1,2)
                self.toggledLeftArrowThisPress = True
        else:
            self.toggledLeftArrowThisPress = False
        
        if (pygame.key.get_pressed()[K_RIGHT] or pygame.key.get_pressed()[K_UP]):
            if ((not self.toggledRightArrowThisPress) and self.snakeState != 1): #attempt to pause or unpause, but only if the game is active
                self.gridSize = min(self.gridSize+1,12)
                self.toggledRightArrowThisPress = True
        else:
            self.toggledRightArrowThisPress = False
            
        if (pygame.key.get_pressed()[K_f]):
            if ((not self.toggledFThisPress) and self.snakeState != 1): #attempt to pause or unpause, but only if the game is active
                root = Tk()
                root.withdraw()
                fileName = askopenfilename(title = "Select An Image") 
                if (len(fileName) > 0):
                    self.loadPuzzleImage(fileName)
                root.destroy()
                self.toggledFThisPress = True
        else:
            self.toggledFThisPress = False
            
        if (pygame.key.get_pressed()[K_q]):
            if ((not self.toggledQThisPress) and self.snakeState == 1): #attempt to pause or unpause, but only if the game is active
                self.snakeState = 2
                self.toggledQThisPress = True
        else:
            self.toggledQThisPress = False
            
        if (pygame.mouse.get_pressed()[0]):
            if ((not self.clickedMouseThisPress) and self.snakeState == 1): #attempt to pause or unpause, but only if the game is active
                self.checkMouseClickPuzzle()
                self.clickedMouseThisPress = True
        else:
            self.clickedMouseThisPress = False
           
           
        return len([event for event in pygame.event.get() if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE)]) == 0 #handle window close or escape key events
                
    def drawCenteredSurface(self,surface, rect, screen): #set surface.rect center to rect center prior to rendering
        drawRect = surface.get_rect()
        drawRect.center = rect.center
        screen.blit(surface,drawRect)
    
    def drawPuzzle(self,screen):                
        #draw on-screen message and image preview if game is not running
        if (self.snakeState != 1):
            instructionRect = pygame.Rect(0+self.xOffset, self.snakeScorePaneHeight+self.yOffset, self.snakeFieldWidth, self.snakeFieldHeight + 120*((len(self.instructions))/2))
            screen.blit(self.smallImage,instructionRect)
            for line in self.instructions:
                # + ("Press Enter to Play" if self.snakeState == 0 else "Press Enter to Restart")
                self.drawCenteredSurface(self.font.render(line, 1, (0,0,0)), instructionRect,screen)  
                instructionRect.bottom -= 60
            self.drawCenteredSurface(self.font.render("Press Enter to Play" if self.snakeState == 0 else "Press Enter to Restart", 1, (0,0,0)), instructionRect,screen)  
            
        #draw top pane contents
        self.drawCenteredSurface(self.font.render("Grid Size: " + str(self.gridSize) + "     Time: %.2f" % self.solveTime + "s", 1, (0,0,0)), 
                         pygame.Rect(0, 0, self.screenWidth,self.snakeScorePaneHeight),screen)   
        
        #draw image puzzle
        if (self.snakeState == 1):
            for i in range(len(self.puzzlePieces)):
                for r in range(len(self.puzzlePieces[i])):
                    if (not (self.puzzlePieces[i][r].isDummy)):
                        screen.blit(self.puzzlePieces[i][r].image,(self.xOffset+self.puzzlePieces[i][r].x*self.gridSquareWidth,self.snakeScorePaneHeight+self.yOffset+self.puzzlePieces[i][r].y*self.gridSquareHeight))

        #draw win text
        if (self.won):
            self.drawCenteredSurface(self.font.render("Congratulations, You Solved the Board!", 1, (0,0,200)), pygame.Rect(0+self.xOffset, self.snakeScorePaneHeight+self.yOffset, self.snakeFieldWidth, self.snakeFieldHeight + 240*((len(self.instructions))/2)), screen)

def main(): #this function is called when the program starts. it initializes everything it needs, then runs in a loop until the function returns.
    pygame.init() #initialize the pygame engine
    gameManager = SlidingPuzzle(640,640); #create class to maintain puzzle game variables
    screen = pygame.display.set_mode([gameManager.screenWidth, gameManager.screenHeight]) #set screen width and height
    gameManager.loadPuzzleImage()
    pygame.display.set_caption("Sliding Puzzle") #set window caption
    clock = pygame.time.Clock()
    while gameManager.checkPuzzleInput(): #Main Loop; runs until game is exited
        gameManager.deltaTime = clock.tick(60) / 1000 #update the game at a steady 60 fps if possible (divide by 1000 to convert from milliseconds to seconds)
        screen.fill((160,200,160)) #render the solid color (cool green) background to prepare the screen for a fresh game render     
        gameManager.drawPuzzle(screen)
        pygame.display.flip() #push final screen render to the display
    
if __name__ == "__main__": #this calls the 'main' function when this script is executed directly
    main()
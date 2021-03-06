#Import Modules
import pygame, random, os
from pygame.locals import QUIT, KEYDOWN, K_UP, K_DOWN, K_LEFT, K_RIGHT, K_RETURN, K_ESCAPE, K_f, K_q, RLEACCEL
from tkinter import *
from tkinter.filedialog import askopenfilename

class ImageSegment(): #simple container class to simplify breaking up the puzzle image 
	def __init__(self,x,y,fullImage,cropRect,isDummy = False):
		self.correctX = x
		self.correctY = y
		self.x = x
		self.y = y
		self.isDummy = isDummy
		self.image = pygame.Surface((cropRect.width,cropRect.height))
		self.image.blit(fullImage,(0,0), (cropRect.x,cropRect.y,cropRect.width,cropRect.height))
		self.animated = False

class SlidingPuzzle(): #main game class; houses most game related variables and methods
	def __init__(self, screenWidthIn, screenHeightIn):
		#Initialize puzzle variables (positioning variables are measured in pixels, further initialization done in first resetPuzzle() call)
		self.screenWidth = screenWidthIn #width of the entire screen in pixels
		self.screenHeight = screenHeightIn #height of the entire screen in pixels
		self.puzzleFieldWidth = screenWidthIn - 55 #total size in pixels of the field width (55 pixel buffer from window border)
		self.puzzleFieldHeight = screenHeightIn - 55 #total size in pixels of the field height (10 pixel buffer from window border, 45 pixels for score pane)
		#calculate offset values to ensure centering regardless of screen size change
		self.puzzleScorePaneHeight = 45 #total size in pixels of the score pane height (the width will be equal to the screen width) 
		self.xOffset = int((self.screenWidth - self.puzzleFieldWidth - 2) / 2) #subtract 2 as 2 is the border size
		self.yOffset = int((self.screenHeight - self.puzzleFieldHeight - self.puzzleScorePaneHeight - 2) / 2) #subtract 2 as 2 is the border size
		self.toggledLeftArrowThisPress = False #variable to keep track of when the left arrow key is pressed, to simulate a 'key press' event that triggers on a single frame only
		self.toggledRightArrowThisPress = False
		self.toggledQThisPress = False
		self.toggledFThisPress = False
		self.clickedMouseThisPress = False
		self.toggledEnterThisPress = False
		self.font = pygame.font.Font(None, 46) #large font used for text rendering
		self.gridSize = 4 #width and height of grid (total size will be gridSize^2)
		self.animationElapsedTime = 0 #measured in seconds
		self.animationTotalTime = .4 #measured in seconds
		self.instructions = ["Press the arrow keys to adjust grid size","Press F to load a custom image file","Press Q to quit the current puzzle"]
		self.resetPuzzle() #prepare the game for its first run at the end of class instantiation
	
	def shufflePieces(self,pieces): #shuffle the piece 2dlist by unpacking, randomizing, and repacking the list
		shuffledList = [item for sublist in pieces for item in sublist]
		random.shuffle(shuffledList)
		return [shuffledList[i:i+self.gridSize] for i in range(0, len(shuffledList), self.gridSize)]
	
	def loadPuzzleImage(self,name="pygameLogo.png"):
		self.imageName = name
		self.image = self.loadImage(self.imageName)
		self.smallImage = pygame.transform.smoothscale(self.image,(int(self.puzzleFieldWidth/4),int(self.puzzleFieldHeight/4)))
		
	def loadImage(self, imageName, convertAlpha=False, colorkey=None): #load an image, optionally setting a colorkey - adapted from the pygame chimp example
		fullname = os.path.join(imageName)
		try:
			image = pygame.image.load(fullname)
		except:
			print('Cannot load image:', fullname)
			raise SystemExit
		image = image.convert() if not convertAlpha else image.convert_alpha() #convert_alpha should be used for images with per-pixel alpha transparency 
		if colorkey is not None:
			if colorkey is -1:
				colorkey = image.get_at((0,0))
			image.set_colorkey(colorkey, RLEACCEL)
		image = pygame.transform.smoothscale(image,(self.puzzleFieldWidth, self.puzzleFieldHeight))
		return image
	
	def swapPieces(self,pieceA,pieceB,shouldAnimate = True): #swap two pieces, optionally preparing them to be animated (swapPieces calls can safely be chained together)
		if (shouldAnimate): #prepare position variables if the pieces are to be animated
			self.animationElapsedTime = 0
			if (not pieceA.animated):
				pieceA.animated = True
				pieceA.animationStartX = pieceA.x
				pieceA.animationStartY = pieceA.y
				self.animatedPieces.append(pieceA)
			if (not pieceB.animated):
				pieceB.animated = True
				pieceB.animationStartX = pieceB.x
				pieceB.animationStartY = pieceB.y
				self.animatedPieces.append(pieceB)
		#perform a standard swap on two ImageSegment fields
		self.randomizedPuzzlePieces[pieceA.x][pieceA.y] = pieceB
		self.randomizedPuzzlePieces[pieceB.x][pieceB.y] = pieceA
		pieceAX = pieceA.x
		pieceAY = pieceA.y
		pieceA.x = pieceB.x
		pieceA.y = pieceB.y
		pieceB.x = pieceAX
		pieceB.y = pieceAY
	
	def checkBoardSolved(self): #check if the board is solved, by comparing each piece's position to its correct position
		for i in range(self.gridSize):
			for r in range(self.gridSize):
				if (self.randomizedPuzzlePieces[i][r].x != self.randomizedPuzzlePieces[i][r].correctX or self.randomizedPuzzlePieces[i][r].y != self.randomizedPuzzlePieces[i][r].correctY):
					return
		self.won = True 
		
	def resetPuzzle(self,newState = 0): #reset the game to prepare a new puzzle
		self.puzzleState = newState #simple state machine used for game state (0 = awaiting first start, 1 = active, 2 = awaiting restart)
		self.deltaTime = 0 #time passed (in seconds, not milliseconds) this frame/tick (reset here so that delta time from starting frame is not factored into first running frame)
		self.solveTime = 0 #time taken to solve the puzzle
		self.puzzlePieces = [] #2d list of puzzle pieces, where (i,r) correspond to (correctX,correctY)
		self.randomizedPuzzlePieces = [] #2d list of puzzle pieces, where (i,r) correspond to (x,y)
		self.animatedPieces = [] #pieces which are mid-animation
		self.gridSquareWidth = self.puzzleFieldWidth / self.gridSize
		self.gridSquareHeight = self.puzzleFieldHeight / self.gridSize
		self.curEmptyX = self.gridSize-1
		self.curEmptyY = 0
		self.won = False
		if (newState != 0): #don't prepare the game if this is our first run, as we will restart again when the player presses enter
			for i in range(self.gridSize): #create the image pieces
				self.puzzlePieces.append([])
				for r in range(self.gridSize):
					#if (not (i == self.gridSize-1 and r == 0)): #leave the top-right piece blank
					self.puzzlePieces[i].append(ImageSegment(i,r,self.image,pygame.Rect(self.gridSquareWidth*i,self.gridSquareHeight*r,self.gridSquareWidth,self.gridSquareHeight)))
			self.randomizedPuzzlePieces = self.shufflePieces(self.puzzlePieces)
			for i in range(self.gridSize): #shuffle the image pieces
				for r in range(self.gridSize):
					self.randomizedPuzzlePieces[i][r].x = i
					self.randomizedPuzzlePieces[i][r].y = r
			self.puzzlePieces[self.gridSize-1][self.gridSize-1].isDummy = True #dummy the bottom-right corner piece, and swap it into the bottom-right corner if it isn't already there
			self.dummyPiece = self.puzzlePieces[self.gridSize-1][self.gridSize-1]
			if (self.puzzlePieces[self.gridSize-1][self.gridSize-1].x != self.gridSize-1 or self.puzzlePieces[self.gridSize-1][self.gridSize-1].y != self.gridSize-1):
				self.swapPieces(self.puzzlePieces[self.gridSize-1][self.gridSize-1],self.randomizedPuzzlePieces[self.gridSize-1][self.gridSize-1],False)
			self.makeBoardSolvable() #ensure that the board can be solved
			self.checkBoardSolved() #check if the board happened to be generated already solved
	
	def inversionCount(self): #count the number of inversions on the board (used by checkBoardSolvable)
		inversionNum = 0;
		for i in range(self.gridSize*self.gridSize - 1):
			for j in range(i+1,self.gridSize*self.gridSize):
				#count all values where i's correct value is greater than j's, but i's randomized value is less than j's
				if not self.comparePieces(self.randomizedPuzzlePieces[i%self.gridSize][i//self.gridSize], self.randomizedPuzzlePieces[j%self.gridSize][j//self.gridSize]):
					inversionNum += 1
		return inversionNum
	
	def comparePieces(self,pieceA,pieceB):
		return pieceA.isDummy or pieceB.isDummy or (pieceA.correctY < pieceB.correctY or (pieceA.correctY == pieceB.correctY and pieceA.correctX < pieceB.correctX))
	
	def makeBoardSolvable(self): #check if the board is solvable, flipping the first two pieces if not, in order to guarantee that it is solvable
		if (not self.checkBoardSolvable()):
			self.swapPieces(self.randomizedPuzzlePieces[0][0], self.randomizedPuzzlePieces[1][0],False)
	
	def checkBoardSolvable(self): #check if the board is solvable by counting number of inversions
		invCount = self.inversionCount()
		#if gridSize is odd, board is solvable if inversion count is even
		if (self.gridSize % 2 == 1):
			return (invCount % 2 == 0)
		else: #grid is even, board is solvable if dummy is an even row counting from bottom to top and inversion count is odd, or if the reverse is true
			if ((self.gridSize - self.dummyPiece.y) % 2 == 0):
				return (invCount % 2 == 1)
			else:
				return (invCount % 2 == 0)
	
	def tryShiftPiece(self,x,y): #shift all pieces from x,y to dummy.x,dummy.y, assuming the current piece is not the dummy
		if ((self.dummyPiece.x == x and self.dummyPiece.y == y) or (not (self.dummyPiece.x == x or self.dummyPiece.y == y))):
			return
		isXChange = self.dummyPiece.y == y
		changeAmount = (((self.dummyPiece.x > x)*2) - 1) if isXChange else (((self.dummyPiece.y > y)*2) - 1)
		curPos = x if isXChange else y
		destPos = self.dummyPiece.x if isXChange else self.dummyPiece.y
		while (curPos != destPos):
			curPos += changeAmount
			if (isXChange):
				self.swapPieces(self.randomizedPuzzlePieces[x][y], self.randomizedPuzzlePieces[curPos][y])
			else:
				self.swapPieces(self.randomizedPuzzlePieces[x][y], self.randomizedPuzzlePieces[x][curPos])
		self.checkBoardSolved()
						
	def checkMouseClickPuzzle(self): #determine if the mouse position overlaps any ImageSegments
		for i in range(self.gridSize): #this could be optimized by matching the mouse coordinates to the randomized list indices, rather than looping for O(n) complexity
			for r in range(self.gridSize):
				if (pygame.Rect(self.xOffset+self.randomizedPuzzlePieces[i][r].x*self.gridSquareWidth,self.puzzleScorePaneHeight+self.yOffset+self.randomizedPuzzlePieces[i][r].y*self.gridSquareHeight,self.gridSquareWidth,self.gridSquareHeight)).collidepoint(pygame.mouse.get_pos()):
					self.tryShiftPiece(i,r)
					
	def checkKeyToggle(self,stateVarName,requirePuzzleState, keys): #check if any of the specified keys or mouse buttons ('mbx' where 0 <= x <= 2) are pressed
		if (True in ((pygame.mouse.get_pressed()[int(key[2])] if (isinstance(key,str) and key[:2] == "mb") else pygame.key.get_pressed()[key]) for key in keys)):
			if ((not getattr(self,stateVarName)) and ((not requirePuzzleState) or self.puzzleState != 1)):
				setattr(self,stateVarName,True)
				return True
		else:
			setattr(self,stateVarName,False)
		return False
						
	def checkPuzzleInput(self): #Handle Input Events   
		if (self.puzzleState == 1):   
			self.solveTime += self.deltaTime
		if self.checkKeyToggle("toggledEnterThisPress",True,[K_RETURN]):
			self.resetPuzzle(1)   
		if self.checkKeyToggle("toggledLeftArrowThisPress",True,[K_LEFT,K_DOWN]):
		 	self.gridSize = max(self.gridSize-1,2)
		elif self.checkKeyToggle("toggledRightArrowThisPress",True,[K_RIGHT,K_UP]):
			self.gridSize = min(self.gridSize+1,12)
		elif self.checkKeyToggle("toggledFThisPress",True,[K_f]):
			root = Tk()
			root.withdraw()
			fileName = askopenfilename(title = "Select An Image") 
			if (len(fileName) > 0):
				self.loadPuzzleImage(fileName)
			root.destroy()	
		elif self.checkKeyToggle("toggledQThisPress",False,[K_q]) and self.puzzleState == 1:
			self.puzzleState = 2
			self.animatedPieces = []
			self.toggledQThisPress = True
		elif len(self.animatedPieces) == 0 and self.checkKeyToggle("clickedMouseThisPress",False,["mb0"]) and self.puzzleState == 1: #ignore mouse inputs when mid-animation 
			self.checkMouseClickPuzzle()
		   
		return len([event for event in pygame.event.get() if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE)]) == 0 #handle window close or escape key events
				
	def checkUpdateAnimations(self): #update animation timing, and move any currently animated pieces accordingly
		self.animationElapsedTime = min(self.animationElapsedTime + self.deltaTime, self.animationTotalTime) #don't exceed animationTotalTime
		for piece in self.animatedPieces:
			if (piece.animated):
				piece.animated = False
				piece.animationEndX = piece.x
				piece.animationEndY = piece.y	
			if (self.animationElapsedTime == self.animationTotalTime): #assign these values explicitly when animation ends to ensure that decimals are removed
				piece.x = piece.animationEndX
				piece.y = piece.animationEndY
			else:
				piece.x = piece.animationStartX + (piece.animationEndX - piece.animationStartX) * (self.animationElapsedTime / self.animationTotalTime)
				piece.y = piece.animationStartY + (piece.animationEndY - piece.animationStartY) * (self.animationElapsedTime / self.animationTotalTime)
		if (self.animationElapsedTime == self.animationTotalTime):
			self.animatedPieces = []		
			if (self.won): #win is delayed until animation is done; now we can change states
				self.puzzleState = 2	
			
	def drawCenteredSurface(self,surface, rect, screen): #set surface.rect center to rect center prior to rendering
		drawRect = surface.get_rect()
		drawRect.center = rect.center
		screen.blit(surface,drawRect)
	
	def drawPuzzle(self,screen): #draw on-screen message and image preview if game is not running
		if (self.puzzleState != 1):
			instructionRect = pygame.Rect(0+self.xOffset, self.puzzleScorePaneHeight+self.yOffset, self.puzzleFieldWidth, self.puzzleFieldHeight + 120*((len(self.instructions))/2))
			screen.blit(self.smallImage,instructionRect)
			for line in self.instructions:
				# + ("Press Enter to Play" if self.puzzleState == 0 else "Press Enter to Restart")
				self.drawCenteredSurface(self.font.render(line, 1, (0,0,0)), instructionRect,screen)  
				instructionRect.bottom -= 60
			self.drawCenteredSurface(self.font.render("Press Enter to Play" if self.puzzleState == 0 else "Press Enter to Restart", 1, (0,0,0)), instructionRect,screen)  
			
		#draw top pane contents
		self.drawCenteredSurface(self.font.render("Grid Size: " + str(self.gridSize) + "     Time: %.2f" % self.solveTime + "s", 1, (0,0,0)), 
						 pygame.Rect(0, 0, self.screenWidth,self.puzzleScorePaneHeight),screen)   
		
		#draw image puzzle
		if (self.puzzleState == 1):
			for i in range(len(self.puzzlePieces)):
				for r in range(len(self.puzzlePieces[i])):
					if (not (self.puzzlePieces[i][r].isDummy)): #don't draw the missing piece
						screen.blit(self.puzzlePieces[i][r].image,(self.xOffset+self.puzzlePieces[i][r].x*self.gridSquareWidth,self.puzzleScorePaneHeight+self.yOffset+self.puzzlePieces[i][r].y*self.gridSquareHeight))

		#draw win text
		if (self.won and self.puzzleState == 2):
			self.drawCenteredSurface(self.font.render("Congratulations, You Solved the Board!", 1, (0,0,200)), pygame.Rect(0+self.xOffset, self.puzzleScorePaneHeight+self.yOffset, self.puzzleFieldWidth, self.puzzleFieldHeight + 240*((len(self.instructions))/2)), screen)

def main(): #this function is called when the program starts. it initializes everything it needs, then runs in a loop until the function returns.
	pygame.init() #initialize the pygame engine
	gameManager = SlidingPuzzle(640,640); #create class to maintain puzzle game variables
	screen = pygame.display.set_mode([gameManager.screenWidth, gameManager.screenHeight]) #set screen width and height
	gameManager.loadPuzzleImage()
	pygame.display.set_caption("Sliding Puzzle") #set window caption
	clock = pygame.time.Clock()
	while gameManager.checkPuzzleInput(): #Main Loop; runs until game is exited
		gameManager.deltaTime = clock.tick(60) / 1000 #update the game at a steady 60 fps if possible (divide by 1000 to convert from milliseconds to seconds)
		gameManager.checkUpdateAnimations()
		screen.fill((160,200,160)) #render the solid color (cool green) background to prepare the screen for a fresh game render	 
		gameManager.drawPuzzle(screen)
		pygame.display.flip() #push final screen render to the display
	
if __name__ == "__main__": #this calls the 'main' function when this script is executed directly
	main()
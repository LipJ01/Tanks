# Pygame template - skeleton for a new pygame project
import pygame
import os
import cmath
#from Connector import *

import random

WIDTH = 800
HEIGHT = 600
FPS = 40

MAXSPEED = 8
REVERSESPEED = 2
MAXBOUNCE = 2
BULLETSPEED = 11
MAXBULLETDIST = 300
TURNRATE = 3

# define colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
SAND = (194, 178, 128)


class Bullet(pygame.sprite.Sprite):
    def __init__(self, PNumber, Direction, startingx, startingy):
        pygame.sprite.Sprite.__init__(self)
        self.playerNo = PNumber
        self.direction = Direction
        self.bounces = 0
        self.distance = 0
        self.maxBounce = MAXBOUNCE
        self.image = pygame.image.load("Bullet.png")
        self.image.convert_alpha()
        self.image = pygame.transform.scale(self.image, (20, 20))
        self.rect = self.image.get_rect()
        if self.direction == 1:
            startingx += 30
            startingy += -1
            self.rect.center = (startingx, startingy)
        elif self.direction == 2:
            startingx += 101
            startingy += 30
            self.rect.center = (startingx, startingy)
        elif self.direction == 3:
            startingx += 30
            startingy += 101
            self.rect.center = (startingx, startingy)
        elif self.direction == 4:
            startingx += -1
            startingy += 30
            self.rect.center = (startingx, startingy)
        else:
            print("Bullet doesn't have a direction?")
        self.rect.center = (startingx, startingy)

    def update(self):
        if self.direction == 1:
            self.rect.y -= BULLETSPEED
        elif self.direction == 2:
            self.rect.x += BULLETSPEED
        elif self.direction == 3:
            self.rect.y += BULLETSPEED
        elif self.direction == 4:
            self.rect.x -= BULLETSPEED
        else:
            print("Bullet doesn't have a direction?")
        self.distance += BULLETSPEED
        if self.distance > MAXBULLETDIST:
            all_sprites.remove(self)
            all_bullets.remove(self)

class Tank(pygame.sprite.Sprite):
    def __init__(self, PNumber, posx, posy):
        pygame.sprite.Sprite.__init__(self)
        self.playerNo = PNumber
        print(os.getcwd())
        self.image = pygame.image.load("Tank_Up.png")
        self.image.convert_alpha()
        self.image = pygame.transform.scale(self.image, (60, 100))
        self.keyboardpressed =False
        self.rect = self.image.get_rect()
        self.X = posx
        self.Y = posy
        self.dX = 0
        self.dY = 0
        self.direction = 1  # 1 north, 2 east, 3 south, 4 west
        self.pointing = 1  # same
        self.Blocked = [False, False, False, False]  # NESW for obstruction in front.



    def move(self):
        #self.turns[self.head.pos[:]] = [self.dirnx, self.dirny]
        #sprites collide bit and then changes X and Y
        if self.X + self.dX > 0 and self.rect.bottom + self.dY < HEIGHT and self.rect.right + self.dX < WIDTH and self.Y + self.dY > 0:
            self.X += self.dX
            self.Y += self.dY
        else:
            print("collided with wall")

        if not self.direction == self.pointing:
            originalPos = self.rect.center
            if self.direction == 1:
                self.image = pygame.image.load("Tank_up.png")
                self.image = pygame.transform.scale(self.image, (60, 100))
            elif self.direction == 2:
                self.image = pygame.image.load("Tank_Right.png")
                self.image = pygame.transform.scale(self.image, (100, 60))
            elif self.direction == 3:
                self.image = pygame.image.load("Tank_Down.png")
                self.image = pygame.transform.scale(self.image, (60, 100))
            elif self.direction == 4:
                self.image = pygame.image.load("Tank_Left.png")
                self.image = pygame.transform.scale(self.image, (100, 60))
            self.rect.center = originalPos
            self.X = self.rect.centerx
            self.Y = self.rect.centery
            self.pointing = self.direction
        self.rect.centerx = self.X
        self.rect.centery = self.Y


        if not self.keyboardpressed:
            if self.dX < 0:
                self.dX += 1
            elif self.dX > 0:
                self.dX -= 1
            if self.dY < 0:
                self.dY += 1
            elif self.dY > 0:
                self.dY -= 1
        self.keyboardpressed = False

    def update(self):
        # print(str(self.dX) + ", " + str(self.dY))
        self.move()

    def shoot(self):
        newshot = Bullet(1, self.pointing, self.rect.x + self.dX, self.rect.y + self.dY)
        all_bullets.add(newshot)
        all_sprites.add(newshot)

class TankPolar(pygame.sprite.Sprite):
    def __init__(self, PNumber, posx, posy):
        pygame.sprite.Sprite.__init__(self)
        self.playerNo = PNumber
        print(os.getcwd())
        self.originalimage = pygame.image.load("Tank2.png")
        self.originalimage.convert_alpha()
        self.originalimage = pygame.transform.scale(self.originalimage, (100, 100))
        self.image = self.originalimage
        self.keyboardpressed =False
        self.rect = self.image.get_rect()
        self.X = posx
        self.Y = posy
        self.speed = 0
        self.direction = 0  # degrees from horizontal -+180 (+180 is Left)
        self.pointing = 0  # same
        self.Blocked = [False, False]  # forward and backwards
        self.forwardback = 1
        self.leftright = 0
        self.fired = False



    def move(self):
        #self.turns[self.head.pos[:]] = [self.dirnx, self.dirny]
        #sprites collide bit and then changes X and Y
        if not self.leftright == 0:
            self.direction -= TURNRATE * self.leftright
            self.leftright = 0
        if self.X > 0 and self.rect.bottom < HEIGHT and self.rect.right < WIDTH and self.Y > 0:
            pass
        else:
            print("collided with wall")
        if not self.pointing == self.direction:
            self.image = pygame.transform.rotate(self.originalimage, -self.direction)
            #self.image = pygame.transform.scale(100,100)
            self.rect = self.image.get_rect()
            self.pointing = self.direction
        z = cmath.rect(self.speed, self.direction*2*cmath.pi/360)
        self.X += z.real * self.forwardback
        self.Y += z.imag * self.forwardback
        #print(self.speed)
        #print(self.direction)
        #print(z.real, z.imag)
        self.rect.x = self.X
        self.rect.y = self.Y

        if not self.keyboardpressed:
            if self.speed > 0:
                self.speed -= 1
        self.keyboardpressed = False

    def update(self):
        if self.fired:
            self.shoot()
            self.fired = False
        self.move()
    def shoot(self):
        newshot = Bullet(self.playerNo, self.direction, self.rect.x, self.rect.y)
        all_bullets.add(newshot)
        all_sprites.add(newshot)


def UploadData():
    pass


def KeyboardEvents():
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
        keys = pygame.key.get_pressed()
        ldx = 0
        ldy = 0
        tank1 = Player1
        tank2 = Player2
        for key in keys:
            # Tank 1 cartesian tank
            if not tank1.keyboardpressed:
                if keys[pygame.K_SPACE]:
                    tank1.shoot()
                elif keys[pygame.K_LEFT]:
                    if tank1.dX > -MAXSPEED and not ldx == -1:
                        ldx += -1
                        ldy = 0
                        tank1.keyboardpressed = True
                        tank1.direction = 4
                    # self.turns[self.head.pos[:]] = [self.dirnx, self.dirny]

                elif keys[pygame.K_RIGHT]:
                    if tank1.dX < MAXSPEED and not ldx == 1:
                        ldx += 1
                        ldy = 0
                        tank1.keyboardpressed = True
                        tank1.direction = 2
                    # self.turns[self.head.pos[:]] = [self.dirnx, self.dirny]

                elif keys[pygame.K_UP]:
                    if tank1.dY > -MAXSPEED and not ldy == -1:
                        ldx = 0
                        ldy += -1
                        tank1.keyboardpressed = True
                        tank1.direction = 1
                    # self.turns[self.head.pos[:]] = [self.dirnx, self.dirny]

                elif keys[pygame.K_DOWN]:
                    if tank1.dY < MAXSPEED and not ldy == 1:
                        ldx = 0
                        ldy += 1
                        tank1.keyboardpressed = True
                        tank1.direction = 3

            # Tank 2 (polar tank)
            if keys[pygame.K_q]:
                tank2.fired = True
            if keys[pygame.K_w]:
                if tank2.speed < MAXSPEED:
                    tank2.speed += 1
                    tank2.keyboardpressed = True
                if tank2.forwardback == -1:
                    tank2.speed -= 1
                    if tank2.speed == 0:
                        tank2.forwardback = 1
                # self.turns[self.head.pos[:]] = [self.dirnx, self.dirny]
            if keys[pygame.K_a]:
                tank2.leftright = 1
                tank2.keyboardpressed = True
                # self.turns[self.head.pos[:]] = [sel
                # f.dirnx, self.dirny]
            if keys[pygame.K_d]:
                tank2.leftright = -1
                tank2.keyboardpressed = True
                # self.turns[self.head.pos[:]] = [self.dirnx, self.dirny]
            if keys[pygame.K_s]:
                if tank2.speed > 0:
                    tank2.speed -= 1
                else:
                    tank2.forwardback = -1
                    tank2.speed = REVERSESPEED
                    tank2.keyboardpressed = True
        tank1.dX += ldx
        tank1.dY += ldy


# initialize pygame and create window
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Tanks")
pygame.mixer.init()
pygame.key.set_repeat(25)
clock = pygame.time.Clock()



#Sprite groups
all_sprites = pygame.sprite.Group()
all_tanks = pygame.sprite.Group()
all_bullets = pygame.sprite.Group()

#code to start the game.
Player1 = Tank(1, 50, 50)
Player2 = TankPolar(2, 250, 50)
all_sprites.add(Player1)
all_sprites.add(Player2)
all_tanks.add(Player1)
all_tanks.add(Player2)


# The callback for when the client receives a CONNACK response from the server.








# Game loop
running = True
while running:
    # keep loop running at the right speed
    clock.tick(FPS)
    # Process input (events)
    KeyboardEvents()
    # Update
    all_sprites.update()
    #upload


    # Draw / render
    screen.fill(SAND)
    all_sprites.draw(screen)
    # *after* drawing everything, flip the display
    pygame.display.flip()

pygame.quit()


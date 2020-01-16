# Tilemap Demo
# KidsCanCode 2017
import pygame as pg
import sys
import os
from random import choice, random
from settings import *
from sprites import *
from Servertilemap import *
import Connector
import ntplib
from datetime import datetime, timezone



c = ntplib.NTPClient()
# Provide the respective ntp server ip in below function
response = c.request('uk.pool.ntp.org', version=3)

# UTC timezone used here, for working with different timezones you can use [pytz library][1]
print(datetime.fromtimestamp(response.tx_time, timezone.utc))

# HUD functions
def draw_player_health(surf, x, y, pct):
    if pct < 0:
        pct = 0
    BAR_LENGTH = 100
    BAR_HEIGHT = 20
    fill = pct * BAR_LENGTH
    outline_rect = pg.Rect(x, y, BAR_LENGTH, BAR_HEIGHT)
    fill_rect = pg.Rect(x, y, fill, BAR_HEIGHT)
    if pct > 0.6:
        col = GREEN
    elif pct > 0.3:
        col = YELLOW
    else:
        col = RED
    pg.draw.rect(surf, col, fill_rect)
    pg.draw.rect(surf, WHITE, outline_rect, 2)


class Game:
    def __init__(self):
        os.environ['SDL_VIDEO_CENTERED'] = '1'
        pg.mixer.pre_init(44100, -16, 4, 2048)
        pg.init()
        info = pg.display.Info()  # You have to call this before pygame.display.set_mode()
        self.screen_width = info.current_w
        self.screen_height = info.current_h
        self.screen = pg.display.set_mode((WIDTH, HEIGHT), pg.RESIZABLE)
        pg.display.set_caption(TITLE)
        self.clock = pg.time.Clock()
        self.load_data()
        self.isserver = True
        self.connection = Connector.Connection(self)
        self.lastOnline = pg.time.get_ticks() + 1000
        self.subscribed = False
        #self.connection.con_subscribe("all/tanks/server/playerpos")
        #self.connection.con_subscribe("all/tanks/server/bulletfired")
        #self.connection.con_subscribe("all/tanks/server/tanksconnected")

    def draw_text(self, text, font_name, size, color, x, y, align="topleft"):
        font = pg.font.Font(font_name, size)
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect(**{align: (x, y)})
        self.screen.blit(text_surface, text_rect)

    def load_data(self):
        game_folder = os.path.dirname(__file__)
        img_folder = os.path.join(game_folder, 'img')
        snd_folder = os.path.join(game_folder, 'snd')
        music_folder = os.path.join(game_folder, 'music')


        self.map_folder = os.path.join(game_folder, 'maps')
        self.title_font = os.path.join(img_folder, 'ZOMBIE.TTF')
        self.hud_font = os.path.join(img_folder, 'Impacted2.0.ttf')
        self.dim_screen = pg.Surface(self.screen.get_size()).convert_alpha()
        self.dim_screen.fill((0, 0, 0, 180))

        self.player_img = pg.image.load(os.path.join(img_folder, PLAYER_IMG)).convert_alpha()
        self.nothing_img = pg.image.load(os.path.join(img_folder, NOTHING_IMG)).convert_alpha()

        self.bullet_images = {}
        self.bullet_images['lg'] = pg.image.load(os.path.join(img_folder, BULLET_IMG)).convert_alpha()
        self.bullet_images['sm'] = pg.transform.scale(self.bullet_images['lg'], (10, 10))
        self.mob_img = pg.image.load(os.path.join(img_folder, MOB_IMG)).convert_alpha()
        self.splat = pg.image.load(os.path.join(img_folder, SPLAT)).convert_alpha()
        self.splat = pg.transform.scale(self.splat, (64, 64))
        self.gun_flashes = []
        for img in MUZZLE_FLASHES:
            self.gun_flashes.append(pg.image.load(os.path.join(img_folder, img)).convert_alpha())
        self.item_images = {}
        for item in ITEM_IMAGES:
            self.item_images[item] = pg.image.load(os.path.join(img_folder, ITEM_IMAGES[item])).convert_alpha()
        # lighting effect
        self.fog = pg.Surface((WIDTH, HEIGHT))
        self.fog.fill(NIGHT_COLOR)
        self.light_mask = pg.image.load(os.path.join(img_folder, LIGHT_MASK)).convert_alpha()
        self.light_mask = pg.transform.scale(self.light_mask, LIGHT_RADIUS)
        self.light_rect = self.light_mask.get_rect()
        # Sound loading
        pg.mixer.music.load(os.path.join(music_folder, BG_MUSIC))
        self.effects_sounds = {}
        for type in EFFECTS_SOUNDS:
            self.effects_sounds[type] = pg.mixer.Sound(os.path.join(snd_folder, EFFECTS_SOUNDS[type]))
        self.weapon_sounds = {}
        for weapon in WEAPON_SOUNDS:
            self.weapon_sounds[weapon] = []
            for snd in WEAPON_SOUNDS[weapon]:
                s = pg.mixer.Sound(os.path.join(snd_folder, snd))
                s.set_volume(0.3)
                self.weapon_sounds[weapon].append(s)
        self.zombie_moan_sounds = []
        for snd in ZOMBIE_MOAN_SOUNDS:
            s = pg.mixer.Sound(os.path.join(snd_folder, snd))
            s.set_volume(0.2)
            self.zombie_moan_sounds.append(s)
        self.player_hit_sounds = []
        for snd in PLAYER_HIT_SOUNDS:
            self.player_hit_sounds.append(pg.mixer.Sound(os.path.join(snd_folder, snd)))
        self.zombie_hit_sounds = []
        for snd in ZOMBIE_HIT_SOUNDS:
            self.zombie_hit_sounds.append(pg.mixer.Sound(os.path.join(snd_folder, snd)))

    def new(self):
        # initialize all variables and do all the setup for a new game
        self.all_sprites = pg.sprite.LayeredUpdates()
        self.walls = pg.sprite.Group()
        self.mobs = pg.sprite.Group()
        self.bullets = pg.sprite.Group()
        self.items = pg.sprite.Group()
        self.other_players = pg.sprite.Group()
        self.map = TiledMap(os.path.join(self.map_folder, 'level1.tmx'))
        self.map_img = self.map.make_map()
        self.map.rect = self.map_img.get_rect()

        self.fakeplayer = FakePlayer(self, TILESIZE, TILESIZE)
        self.player = CameraPlayer(self, TILESIZE, TILESIZE)
        for tile_object in self.map.tmxdata.objects:
            obj_center = vec((tile_object.x + tile_object.width / 2), (tile_object.y + tile_object.height / 2))
            if tile_object.name == 'player':
                pass
            #                self.player = Player(self, obj_center.x, obj_center.y)
            if tile_object.name == 'zombie':
                pass
                Mob(self, obj_center.x, obj_center.y)
            if tile_object.name == 'wall':
                Obstacle(self, tile_object.x, tile_object.y,
                         tile_object.width, tile_object.height)
            if tile_object.name in ['health', 'shotgun']:
                pass
                Item(self, obj_center, tile_object.name)
        self.camera = Camera2(self.map.width, self.map.height, WIDTH, HEIGHT)
        self.draw_debug = False
        self.paused = False
        self.night = False
        self.effects_sounds['level_start'].play()


    def run(self):
        # game loop - set self.playing = False to end the game
        self.playing = True
        pg.mixer.music.play(loops=-1)
        while self.playing:
            self.dt = self.clock.tick(FPS) / 1000.0  # fix for Python 2.x
            self.events()
            if not self.paused:
                self.update()
            self.draw()

    def quit(self):
        pg.quit()
        sys.exit()

    def update(self):
        # update portion of the game loop
        self.all_sprites.update()
        self.camera.update(self.player)
        now = pg.time.get_ticks()
        if now - self.lastOnline > 50:
            self.onlineUpdate()
            self.lastOnline = now
        # game over?
        if len(self.mobs) == 0:
            pass
            #self.playing = False
        # player hits items

        # need to change this bit so that it checks the position of each player it has (from a list of players generated by incoming player connections) then does hits for each one. Then does the thing on the screen but also sends back to each client that the event just happened sort of thing.

#        hits = pg.sprite.spritecollide(self.player, self.items, False)
#        for hit in hits:
#            if hit.type == 'health' and self.player.health < PLAYER_HEALTH:
#                hit.kill()
#                self.effects_sounds['health_up'].play()
#                self.player.add_health(HEALTH_PACK_AMOUNT)
#            if hit.type == 'shotgun':
#                hit.kill()
#                self.effects_sounds['gun_pickup'].play()
#                self.player.weapon = 'shotgun'

        # Question: do I want player hits to happen server side or client side? Answer: whichever is easiest, so still don't know.
        # mobs hit player

#        hits = pg.sprite.spritecollide(self.player, self.mobs, False, collide_hit_rect)
#        for hit in hits:
#            if random() < 0.7:
#                choice(self.player_hit_sounds).play()
#            self.player.health -= MOB_DAMAGE
#            hit.vel = vec(0, 0)
#            if self.player.health <= 0:
#                self.playing = False
#        if hits:
#            self.player.hit()
#            self.player.pos += vec(MOB_KNOCKBACK, 0).rotate(-hits[0].rot)

        # again back to the server/client argument. I'm currently leaning towards everything happening on the server
        # bullets hit mobs
        hits = pg.sprite.groupcollide(self.mobs, self.bullets, False, True)
        for mob in hits:
            # hit.health -= WEAPONS[self.player.weapon]['damage'] * len(hits[hit])
            for bullet in hits[mob]:
                mob.health -= bullet.damage
            mob.vel = vec(0, 0)

    def draw_grid(self):
        for x in range(0, WIDTH, TILESIZE):
            pg.draw.line(self.screen, LIGHTGREY, (x, 0), (x, HEIGHT))
        for y in range(0, HEIGHT, TILESIZE):
            pg.draw.line(self.screen, LIGHTGREY, (0, y), (WIDTH, y))

    def render_fog(self):
        # draw the light mask (gradient) onto fog image
        self.fog.fill(NIGHT_COLOR)
        self.light_rect.center = self.camera.apply(self.player).center
        self.fog.blit(self.light_mask, self.light_rect)
        self.screen.blit(self.fog, (0, 0), special_flags=pg.BLEND_MULT)

    def draw(self):
        pg.display.set_caption("{:.2f}".format(self.clock.get_fps()))
        # self.screen.fill(BGCOLOR)
        self.screen.blit(self.map_img, self.camera.apply(self.map))
        # self.draw_grid()
        for sprite in self.all_sprites:
            if isinstance(sprite, Mob):
                sprite.draw_health()
            self.screen.blit(sprite.image, self.camera.apply(sprite))
            if self.draw_debug:
                pg.draw.rect(self.screen, CYAN, self.camera.apply_rect(sprite.hit_rect), 1)
        if self.draw_debug:
            for wall in self.walls:
                pg.draw.rect(self.screen, CYAN, self.camera.apply_rect(wall.rect), 1)

        # pg.draw.rect(self.screen, WHITE, self.player.hit_rect, 2)
        if self.night:
            self.render_fog()
        # HUD functions
#        draw_player_health(self.screen, 10, 10, self.player.health / PLAYER_HEALTH)
        self.draw_text('Bots Alive: {}'.format(len(self.mobs)), self.hud_font, 30, WHITE,
                       WIDTH - 10, 10, align="topright")
        if self.paused:
            self.screen.blit(self.dim_screen, (0, 0))
            self.draw_text("Paused", self.title_font, 105, RED, WIDTH / 2, HEIGHT / 2, align="center")
        pg.display.flip()

    def events(self):
        # catch all events here
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.quit()
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    self.quit()
                if event.key == pg.K_h:
                    self.draw_debug = not self.draw_debug
                if event.key == pg.K_p:
                    self.paused = not self.paused
                if event.key == pg.K_n:
                    self.night = not self.night
                if event.key == pg.K_8:
                    print("Fullscreen")
                    pg.display.toggle_fullscreen()
            if event.type == pg.VIDEORESIZE:
                print("VIDEORESIZE EVENT")
                self.camera.sw = event.w
                self.camera.sh = event.h
                print("sucess")

    def show_start_screen(self):
        pass

    def show_go_screen(self):
        self.screen.fill(BLACK)
        self.draw_text("GAME OVER", self.title_font, 100, RED,
                       WIDTH / 2, HEIGHT / 2, align="center")
        self.draw_text("Press a key to start", self.title_font, 75, WHITE,
                       WIDTH / 2, HEIGHT * 3 / 4, align="center")
        pg.display.flip()
        self.wait_for_key()

    def wait_for_key(self):
        pg.event.wait()
        waiting = True
        while waiting:
            self.clock.tick(FPS)
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    waiting = False
                    self.quit()
                if event.type == pg.KEYUP:
                    waiting = False

    def onlineUpdate(self):
        if self.connection.connected:
            if not self.subscribed:
                self.connection.con_subscribe("all/tanks/server/#")
                self.connection.con_subscribe("all/tanks/disconnect")
                print("subscribed to server messages")
                self.subscribed = True
            listofplayers = []
            listofmobs = []
            listofitems = []
            for player in self.other_players:
                row = []
                #print(player.tankID)
                row.append(player.rect.centerx)
                row.append(player.rect.centery)
                row.append(player.rot)
                row.append(player.tankID)
                listofplayers.append(row)
            for mob in self.mobs:
                row = []
                row.append(mob.rect.centerx)
                row.append(mob.rect.centery)
                row.append(mob.rot)
                listofmobs.append(row)
            for item in self.items:
                row = []
                row.append(item.rect.centerx)
                row.append(item.rect.centery)
                listofitems.append(row)
            self.connection.send_alldata(listofplayers,listofmobs,listofitems)

    def newTankConnected(self, tankID):
        print("new tank: " + tankID)
        spawnpos = vec(3*TILESIZE, 3*TILESIZE)
        tankalreadyexist = False
        for tank in self.other_players:
            if tank.tankID == tankID:
                tankalreadyexist = True
        if not tankalreadyexist:
            self.connection.send_PlayerPos("all/tanks/client/movetank", spawnpos, 270, vec(0, 0), tankID)
            ServerPlayer(self, spawnpos.x, spawnpos.y, 270, tankID)

    def otherplayerupdate(self, tankID, tankpos, tankrot, tankvel):
        for tank in self.other_players:
            if tank.tankID == tankID:
                #print("updating " + tankID)
                tank.pos = tankpos
                tank.rot = tankrot
                tank.vel = tankvel

    def OnlinePlayerDisconnect(self, tankID):
        for tank in self.other_players:
            if tank.tankID == tankID:
                print("removing " + tankID)
                self.other_players.remove(tank)
                self.all_sprites.remove(tank)
                tank.kill()
                self.map_img.blit(self.splat, tank.pos - vec(32, 32))
                for i in range(0, 10): # a pause of 10 frames seemed to fix it, don't know why.
                    self.clock.tick(FPS)







# create the game object

g = Game()
g.show_start_screen()
while True:
    g.new()
    g.run()
    g.show_go_screen()

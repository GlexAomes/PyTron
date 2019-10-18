import pygame
import os
import sys
import psutil
# Author: Alex Gomes
# Date: Oct 17/2019
# Notes: Just a quick game, no real graphics, just polygons, supports up to 4 players, min 2 players 

# The dimensions for the window will be (W+RADIUS, H+RADIUS)
W = 500
H = 500
RADIUS = 4

# Player objects
# Instantiation takes x, y, coords of where to spawn the player
# It also takes c, the colour of the player
# Also takes in a keymap, which is a dictionary that maps UP, DOWN, LEFT, RIGHT to pygame keys
# Also takes in a name, for the player
# Keeps track of a constant velocity in which the player will move at
# The size of the player is proportional to the velocity, so we don't have gaps in the grid
# Keeps track of whether or not it is alive
# Also keeps track of the name of the player
class Player:
    def __init__(self, x, y, c, keymap, name):
        self.x = x
        self.y = y
        self.c = c
        self.keys = keymap
        self.r = RADIUS
        self.v = self.r
        self.alive = True
        self.traversed = [(self.x, self.y)]
        self.name = name
        self.reset_move()
        
        # determine which way we will start, depending on how far we are from the top, start moving towards the directon
        if y > W//2:
            self.up = True
        else:
            self.down = True

    # gritty function to reset all movement vars
    def reset_move(self):
        self.up = False
        self.down = False
        self.left = False
        self.right = False

    # basic checks for collision with following logic:
    #   check if player's current position is inside coords of our player's traversed path
    #   check if player's current position is inside coords of the grid's traversed paths, the paths from all players
    #   check if player is outside the bounds of the window
    # if any of these fail, then the player is dead
    def check_collision(self, grid_traversed):
        if (self.x, self.y) in self.traversed \
            or (self.x, self.y) in grid_traversed \
            or self.x > W or self.x < 0 \
            or self.y > H or self.y < 0:
            self.alive = False

    # takes in the key list of the states of all keys, and the grid state of all the traversed paths
    # checking if the inputted key corresponds to the player's designated key as per mapping logic
    # before moving, we check if we were not moving in the opposite direction of the input key, because we cannot do a flip, we'd be inside our path
    # reset all the other direciton, then set the direction 
    # depending on the bool that's true, move our player's x or y in the correct direction by the constant velocity
    # perform a collision check for this player
    # add this iteration of movement to our player's traversed path and to the grid's traversed path
    # return the updated grid for future collision checks
    def move(self, key_buffer, grid_traversed):
        if len(self.keys):
            if key_buffer[self.keys["UP"]]:
                if not self.down:
                    self.reset_move()
                    self.up = True

            elif key_buffer[self.keys["DOWN"]]:
                if not self.up:
                    self.reset_move()
                    self.down = True

            elif key_buffer[self.keys["LEFT"]]:
                if not self.right:
                    self.reset_move()
                    self.left = True

            elif key_buffer[self.keys["RIGHT"]]:
                if not self.left:
                    self.reset_move()
                    self.right = True

        if self.up:
            self.y -= self.v
        elif self.down:
            self.y += self.v
        elif self.left: 
            self.x -= self.v
        elif self.right: 
            self.x += self.v

        self.check_collision(grid_traversed)
        self.traversed.append((self.x, self.y))
        grid_traversed.append((self.x, self.y))

        return grid_traversed
        
    # the draw logic for the player, takes in the window context to draw into
    # draws the trail based on the players traversed path
    # draws the head of the player as well on top
    def draw(self, gfx):
        for point in self.traversed:
            pygame.draw.rect(gfx, self.c, (point[0], point[1], self.r, self.r))
        pygame.draw.rect(gfx, (255, 255, 255), (self.x, self.y, self.r, self.r))

    # basic logic of player death makes it so the trail of the player is recoloured as the same colour as the bg
    # this would be a problem if trails overlapped, but they don't, so no worries
    # we will also remove the union of the this player's path and the grid from the grid
    def death(self, gfx, bg, grid_traversed):
        for point in self.traversed:
            pygame.draw.rect(gfx, bg, (point[0], point[1], self.r, self.r))
            if point in grid_traversed:
                grid_traversed.remove(point)
        return grid_traversed

class Computer(Player):
    difficulties = {
        'Easy': 2*RADIUS,
        'Medium': RADIUS,
        'Hard': RADIUS // 2
    }

    DEBUG = False

    # Computer object, similar logic to Player but movement is automated
    # The difficulty is inversely proportional to a scalar multiple of the radius of the grid cells, this determines the AI's reaction time
    def __init__(self, x, y, c, name, difficulty):
        self.diff_factor = self.difficulties[difficulty]
        super().__init__(x, y, c, {}, name)

    # The logic of how it needs to move left or right when moving up or down
    def vertical_avoid(self, potential):
        self.reset_move()
        if potential[0] > W // 2:
            self.left = True
            if self.DEBUG: print(f"moved left to avoid {potential}")
        else:
            self.right = True
            if self.DEBUG: print(f"moved right to avoid {potential}")

    # The logic of how it needs to move up or down when moving left or right
    def horizontal_avoid(self, potential):
        self.reset_move()
        if potential[1] > H // 2:
            self.up = True
            if self.DEBUG: print(f"moved up to avoid {potential}")
        else:
            self.down = True
            if self.DEBUG: print(f"moved down to avoid {potential}")

    # accepting key_buffer just so it can be called like parent class
    # practically similar to parent except for the input handle will be automated based on logical checks if it thinks it will collide into
    #   something while moving along the path and the reaction time of avoiding is scaled based on the distance it will predict, the lower
    #   the more accurate, this is also scaled based on the difficulty factor
    def move(self, key_buffer, grid_traversed):
        # collision avoidance logic here
        if self.up:
            potential = (self.x, self.y - self.r*self.diff_factor)
            if self.DEBUG: print(f"UP | PT={potential}")
            if potential in grid_traversed or potential[1] <= self.r*self.diff_factor:
                self.vertical_avoid(potential)
        
        if self.down:
            potential = (self.x, self.y + self.r*self.diff_factor)
            if self.DEBUG: print(f"DOWN | PT={potential}")
            if potential in grid_traversed or potential[1] >= H - self.r*self.diff_factor:
                self.vertical_avoid(potential)

        if self.left:
            potential = (self.x - self.r*self.diff_factor, self.y)
            if self.DEBUG: print(f"LEFT | PT={potential}")
            if potential in grid_traversed or potential[0] <= self.r*self.diff_factor:
                self.horizontal_avoid(potential)

        if self.right:
            potential = (self.x + self.r*self.diff_factor, self.y)
            if self.DEBUG: print(f"RIGHT | PT={potential}")
            if potential in grid_traversed or potential[0] >= W - self.r*self.diff_factor:
                self.horizontal_avoid(potential)

        # move based on set direction
        if self.up:
            self.y -= self.v
        elif self.down:
            self.y += self.v
        elif self.left: 
            self.x -= self.v
        elif self.right: 
            self.x += self.v

        self.check_collision(grid_traversed)
        self.traversed.append((self.x, self.y))
        grid_traversed.append((self.x, self.y))

        return grid_traversed

# the game object, responsible for the environment and resource management
# instantiation takes in the width and height of the window
# keeps track of all the resources that are dependant on the environment, in this case just the players, could just keep track of players, this will
#   be useful if we ever decide to have more game objects
# keeps track of the spawned players, eventually used to see which player is left alive
# keeps track of how much of the grid has been traversed
# sets up the clock and other necessary graphics objects
class Game:
    def __init__(self, w, h):
        self.w = w
        self.h = h
        self.resources = []
        self.bg = (0, 0, 0)
        self.spawned_players = []
        self.traversed = []

        pygame.init()
        self.window = pygame.display.set_mode((w, h))
        pygame.display.set_caption("PyTron")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font('freesansbold.ttf', 32) 
        self.sandbox = False
        self.finished = False

        self.default_keys = [{
            "UP": pygame.K_w,
            "LEFT": pygame.K_a,
            "RIGHT": pygame.K_d,
            "DOWN": pygame.K_s
        }, {
            "UP": pygame.K_y,
            "LEFT": pygame.K_g,
            "RIGHT": pygame.K_j,
            "DOWN": pygame.K_h
        }, {
            "UP": pygame.K_p,
            "LEFT": pygame.K_l,
            "RIGHT": pygame.K_QUOTE,
            "DOWN": pygame.K_SEMICOLON
        }, {
            "UP": pygame.K_UP,
            "LEFT": pygame.K_LEFT,
            "RIGHT": pygame.K_RIGHT,
            "DOWN": pygame.K_DOWN
        }]

        self.default_colors = {
            "red": (255, 64, 64),
            "green": (64, 255, 64),
            "blue": (64, 64, 255),
            "yellow": (255, 255, 128)
        }

    # append game object to resources list, a bit redundent but good practice
    def add(self, obj):
        type = obj.__class__.__name__

        if type == 'Player' or type == 'Computer':
            if len(self.spawned_players) < 4:
                if not obj.name:
                    obj.name = f'Player {len(self.spawned_players) + 1}'
                if type == 'Computer':
                    obj.name += ' (CPU)'
                self.traversed.append((obj.x, obj.y))
                self.spawned_players.append(obj.name)

        self.resources.append(obj)

    # handling game environment key mapping
    # currently only handle spacebar to restart the entire process
    # we will make sure we clean up orphan processes
    def handle_game_input(self, keys):
        if keys[pygame.K_SPACE]:
            try:
                p = psutil.Process(os.getpid())
                for handler in p.get_open_files() + p.connections():
                    os.close(handler.fd)
            except Exception as e:
                pass # swallow, because if the process is exits normally, it will throw an error for p

            python = sys.executable
            os.execl(python, python, f'{sys.argv[0]}')

    # create a player if we have room for one, track this player into the players list and add the player's spawn location to the grid traversed
    # we will assign a default name if name is left empty as "Player n"
    # we will also have a default keymap, set to empty, as in no controls, but this may throw an uncaught exception on runtime 
    # we will also allow AI players to spawn from here
    def spawn_player(self, x, y, c, name="", keymap={}, ai=False, difficulty='Easy'):
        """ if len(self.spawned_players) < 4:
            if not name:
                name = f'Player {len(self.spawned_players) + 1}'
            if ai:
                name += ' (CPU)' """
        if ai:
            return Computer(x, y, c, name, difficulty)
        if len(keymap):
            return Player(x, y, c, keymap, name)

    # redraw the background, which will clear everything
    # also draw the borders of the window
    def reset(self):
        self.window.fill((self.bg))
        pygame.draw.rect(self.window, (255, 255, 255), (0, 0, W+RADIUS, H+RADIUS), RADIUS)

    # update the window after all calculations
    # responsible for calling the update and draw for all resources in the game environment
    # starts by resetting the window for a new iteration
    # loops through all the resources, if the resource is a player, and we have more than 1 player alive, draw them, else
    #   call the death function to take them off the board and remove them from the list of players we are tracking
    #  while we have players, draw them, else clear screen, and write the winner's name
    def update(self):
        self.reset()
        for resource in self.resources:
            type = resource.__class__.__name__
            if (type == "Player" or type == "Computer") and (len(self.spawned_players) > 1 or self.sandbox):
                if resource.alive:
                    resource.draw(self.window)
                else:
                    if resource.name in self.spawned_players:
                        self.traversed = resource.death(self.window, self.bg, self.traversed)
                        self.spawned_players.remove(resource.name)
                        print(f"{resource.name} has died!")

        if self.sandbox:
            pygame.display.update()
            return

        if len(self.spawned_players) > 1:
            pygame.display.update()
        else:
            text = self.font.render(f'{self.spawned_players[0]} wins!', True, (0, 0, 0), (255, 255, 255))
            if not self.finished:
                print(f"{resource.name} won the game!")
                self.finished = True
            textRect = text.get_rect()
            textRect.center = (W // 2, H // 2 - 50)
            self.window.blit(text, textRect)
            text = self.font.render(f'Press Space to restart!', True, (0, 0, 0), (255, 255, 255)) 
            textRect = text.get_rect()
            textRect.center = ((W) // 2, H // 2 + 50)
            self.window.blit(text, textRect)
            pygame.display.update()

    # main loop for the game environment
    # has an internal running bool, which is always True unless we hit the quit button
    # we loop through all the game resources, if it's a player and they are alive, delegate movement for them by passing the keys state and grid traversed
    # return the state of whether or not the quit button was hit
    def run(self):
        running = True
        self.clock.tick(60)

        for evt in pygame.event.get():
            if evt.type == pygame.QUIT:
                running = False

        keys = pygame.key.get_pressed()

        self.handle_game_input(keys)

        for resource in self.resources:
            type = resource.__class__.__name__
            if (type == "Player" or type == "Computer") and (len(self.spawned_players) > 1 or self.sandbox):
                if resource.alive:
                    resource.move(keys, self.traversed)

        return running

# MAIN LOGIC AND SETUP

# Creating the game object
game = Game(W+RADIUS, H+RADIUS)

# Player keymap with arrow keys

"""custom_keys = {
    "UP": pygame.K_i,
    "LEFT": pygame.K_j,
    "RIGHT": pygame.K_l,
    "DOWN": pygame.K_k
}"""

custom_keys = {}

custom_color = (255, 64, 255)

# spawn the players 
red_player = game.spawn_player(400, 400, c=game.default_colors['red'], keymap=game.default_keys[0])
#blue_player = game.spawn_player(100, 100, c=game.default_colors['blue'], keymap=game.default_keys[3])
#magenta = game.spawn_player(200, 200, c=custom_color, name="Mag", keymap=custom_keys)

# add the players as resources to the game environment
game.add(red_player)
#game.add(blue_player)
#game.add(magenta)

# AI
cpu = game.spawn_player(100, 100, c=(171, 235, 52), ai=True, difficulty='Hard')
#cpu2 = game.spawn_player(400, 400, c=(52, 235, 171), ai=True, difficulty='Hard')
game.add(cpu)
#game.add(cpu2)

game.sandbox = False

if len(game.spawned_players) < 2 and not game.sandbox:
    print(f"Need at least 2 players, or use sandbox mode!")
    exit(0)

# run the main loop logic of the game
while game.run():
    game.update()

# TODO: The AI is very tacky, if you start the game with 2 CPU players, they will be symmetric. In other words, there is no entropy to the AI.
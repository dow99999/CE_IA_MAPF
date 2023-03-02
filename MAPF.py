from pysat import card
from pysat.formula import IDPool
from constants import *

if SAVE_MAZE_SOLUTION_TO_PNG:
  import png

from MAMaze import MAMaze
import time
class FLAGS():
  USE_TILE_VARIABLES =                    0b0000000000000000
  
  ARC_BLOCK_IMMEDIATE_LOOPS =             0b0000000000000000
  ARC_ONLY_ONE_INPUT =                    0b0000000000000000
  ARC_ONE_OUTPUT_MEANS_ONE_INPUT =        0b0000000000000000

class MAPF(MAMaze):
  """
  Clase para representar un laberinto y generar las clausulas necesarias para resolverlo.
  en esta resolucion se utiliza el siguiente concepto:
  Se busca generar un camino entre el punto de salida (el agente) y uno de los objetivos
  Por tanto, cada casilla que no sea un agente o objetivo y este dentro del camino tendra dos casillas adyacentes
  """


  def __init__(self,matrix: list = None, flags=0):
    super().__init__(matrix)
    
    self.__position_to_tile = {}
    self.__tile_to_position = []
    
    self.__pyramids = {}
    self.__exploration_space = {} # All space covered by the pyramids for each time step
    self.__exploration_literal_to_tile = {}
    self.__tile_to_exploration_literals = {}

    self.__pyramid_arc_to_tiles = {}
    self.__tiles_to_pyramid_arc = {}

    self.flags = flags

    self.__maximum_literal = 1
    self.__maximum_tile_literal = 1
    self.__maximum_exploration_space_literal = 1
    self.__maximum_pyramid_arc_literal = 1


  def __get_card_eq1(literals):
    clauses = []

    # >= 1
    clauses.append([literal for literal in literals])
    # <= 1
    aux_clauses = MAMaze.combinations_generator(literals, 2)
    for clause in aux_clauses:
      for i in range(len(clause)):
        clause[i] = -clause[i]
        
    clauses.extend(aux_clauses)

    return clauses
  
  def __get_card_max1(literals):
    clauses = []

    # <= 1
    aux_clauses = MAMaze.combinations_generator(literals, 2)
    for clause in aux_clauses:
      for i in range(len(clause)):
        clause[i] = -clause[i]
        
    clauses.extend(aux_clauses)

    return clauses

  def __get_card_min1(literals):
    clauses = []

    # >= 1
    clauses.append([literal for literal in literals])

    return clauses

  #######################################################################
  ## Maze Representations
  #######################################################################

  def get_maze_literals_representation(self, pretty: bool = False):
    """
    Devuelve un string con la representacion del laberinto en literales
    """
    out = ""

    for row in range(self._height):
      for col in range(self._width):
        try:
          out += str(self.get_literal_from_position(row, col)) + " "
        except:
          out += self._representation[row][col] + " "
      out += "\n"

    out = out[:-1]

    return out if not pretty else self._box_maze(out)

  def get_maze_literals_on_path(self, pretty: bool = False):
    """
    Devuelve un string con la representacion del laberinto y los literales del camino
    """
    out = "W"

    return out if not pretty else self._box_maze(out)

  def get_maze_representation_with_path(self, model: list, pretty: bool = False):
    """
    Devuelve un string con la misma representacion de laberinto que get_maze_representation pero con
    el camino definido por model marcado por puntos
    """
    out = ""
    model_i = 1

    for row in self._representation:
      for element in row:
        out += (MAMaze.WAY if model[model_i - 1] > 0 else element) + " "
        model_i += 1
      out += "\n"

    out = out[:-1]

    return out if not pretty else self._box_maze(out)

  def save_solved_maze_to_image(self, model: list):
    pixel_matrix = []
    model = [self.get_position_from_literal(m) for m in model if m > 0 and m <= self.__maximum_tile_literal]

    for row_i in range(len(self._representation)):
      pixel_matrix.append([])
      for col_i in range(len(self._representation[row_i])):
        colors = self.COLORS[self._representation[row_i][col_i]] if not (row_i, col_i) in model else MAMaze.color_merger(self.COLORS[self.WAY], self.COLORS[self._representation[row_i][col_i]])

        pixel_matrix[len(pixel_matrix) - 1].append(colors[0])
        pixel_matrix[len(pixel_matrix) - 1].append(colors[1])
        pixel_matrix[len(pixel_matrix) - 1].append(colors[2])
        

    png.from_array(pixel_matrix, "RGB").save(OUTPUT_DIR + "solved_maze.png")

  def save_solved_maze_with_dirs_to_image(self, model: list):
    pixel_matrix = []
    model_i = 1
    model = [m for m in model if m > 0]
    user_pos = None
    flag_pos = None

    for row in range(self._height):
      for col in range(self._width):
        if self.get_maze_position_type(row, col) == self.GOAL:
          flag_pos = (row, col)

    arcs = [self.get_positions_from_arc(m) for m in model if ( self.__maximum_tile_literal < m <= self.__maximum_arc_literal )]

    def get_arrow_pixel_positions(pos1, pos2, middle):
      dir = None
      if pos1[0] > pos2[0]:
        dir = "N"
      elif pos1[0] < pos2[0]:
        dir = "S"
      elif pos1[1] > pos2[1]:
        dir = "W"
      elif pos1[1] < pos2[1]:
        dir = "E"

      return [(middle[0] + pos[0], middle[1] + pos[1]) for pos in self.ARROWS[dir]]


    if not self.USING_TILES:
      mdl = set()
      for key in self.__positions_to_arc:
        if self.__positions_to_arc[key] in model:
          mdl.add(key[0])
          mdl.add(key[1])

      model = list(mdl)
    else:
      mdl = []
      for m in model:
        if (m - 1) < len(self.__tile_to_position):
          mdl.append(self.get_position_from_literal(m))
      model = mdl

    model = set(model)

    mult = TILE_PIXELS

    total_it = self._width * self._height * mult * mult
    current_it = 1

    for row_i in range(len(self._representation) * mult):
      pixel_matrix.append([])
      for col_i in range(len(self._representation[row_i // mult]) * mult):
        current_it += 1
        if current_it % 100 == 0:
          print("Generating Image " + str(round((current_it / total_it) * 100, 2)) + "%  ", end="\r")
        if SHOW_GRID and (row_i == (row_i // mult) * mult or col_i == (col_i // mult) * mult):
          colors = [33, 33, 33]
        else:
          colors = self.COLORS[self._representation[row_i // mult][col_i // mult]] if not (row_i // mult, col_i // mult) in model else MAMaze.color_merger(self.COLORS[self.WAY], self.COLORS[self._representation[row_i // mult][col_i // mult]])
        # colors = self.COLORS[self._representation[row_i // mult][col_i // mult]]

        pixel_matrix[len(pixel_matrix) - 1].append(colors[0])
        pixel_matrix[len(pixel_matrix) - 1].append(colors[1])
        pixel_matrix[len(pixel_matrix) - 1].append(colors[2])

        model_i += 1
    
    print("Generating Image 100.0%")

    for arc in arcs:
      pos1 = arc[0]
      pos2 = arc[1]

      out_pm_row = (pos1[0] * mult) + (mult // 2)
      out_pm_col = (pos1[1] * mult + (mult // 2))
      in_pm_row = (pos2[0] * mult) + (mult // 2)
      in_pm_col = (pos2[1] * mult + (mult // 2))

      half_row = (out_pm_row + in_pm_row) // 2
      half_col = (out_pm_col + in_pm_col) // 2

      arrow_pos = get_arrow_pixel_positions(pos1, pos2, (half_row, half_col))

      dist1 = (abs(pos1[0] - flag_pos[0]) + abs(pos1[1] - flag_pos[1]))
      dist2 = (abs(pos2[0] - flag_pos[0]) + abs(pos2[1] - flag_pos[1]))
      arrow_color = self.ARROW_COLORS["GOOD"] if dist1 >= dist2 else self.ARROW_COLORS["BAD"]
      for pos in arrow_pos:

        pixel_matrix[pos[0]][(pos[1] * 3) + 0] = arrow_color[0]
        pixel_matrix[pos[0]][(pos[1] * 3) + 1] = arrow_color[1]
        pixel_matrix[pos[0]][(pos[1] * 3) + 2] = arrow_color[2]

    png.from_array(pixel_matrix, "RGB").save(OUTPUT_DIR + "dir_solved_maze.png")


  def visualize_exploration_space(self, model=[]):
    out = ""
    
    def add_point(x, y, z, r, g, b):
      return f"{x} {y} {z} {r} {g} {b}\n"

    for y in range(len(self._representation)):
      for x in range(len(self._representation[y])):
        color = [color/255 for color in MAMaze.COLORS[self._representation[y][x]]]
        out += add_point(x, y, 0, color[0], color[1], color[2])

    # for time in self.__exploration_space:
    #   for tile in self.__exploration_space[time]:
    #     tile_pos = self.get_position_from_literal(tile)

    #     out += add_point(tile_pos[1], tile_pos[0], time + 1, 0.2, 0.2, 0.5)

    # TODO: Auto-generate colors for all agents + merge colors from intersected pyramids
    colors = [
      (0.2, 0.2, 0.5),
      (0.2, 0.5, 0.2),
      (0.5, 0.2, 0.2)
      ]
    i = 0
    for agent in self.__pyramids:
      color = colors[i%len(colors)]
      for time in self.__pyramids[agent]:
        for tile in self.__pyramids[agent][time]:
          tile_pos = self.get_position_from_literal(tile)

          out += add_point(tile_pos[1], tile_pos[0], -time - 1, color[0], color[1], color[2])
      i += 1


    with open(OUTPUT_DIR + "pc.xyzrgb", "w") as f:
      f.write(out)

  #######################################################################
  ## Transformations
  #######################################################################

  def get_literal_from_position(self, row: int, col: int):
    """
    Devuelve un literal dadas las coordenadas de una casilla
    """
    return self.__position_to_tile[(row, col)]

  def get_position_from_literal(self, literal: int):
    """
    Devuelve las coordenadas de una casilla dado un literal
    """
    return self.__tile_to_position[literal - 1]

  def get_arc_from_positions(self, row1: int, col1: int, row2: int, col2: int):
    """
    Devuelve un arco dadas las coordenadas de sus casillas
    """
    return self.__positions_to_arc[((row1, col1), (row2, col2))]

  def get_positions_from_arc(self, literal: int):
    """
    Devuelve las coordenadas de un arco dado un literal
    """
    # a = 42
    # print(self.__position_to_tile)
    # print(self.__arc_to_positions[a])
    # print(a - 1 - (self.__positions_to_arc[self.__arc_to_positions[0]] - 1 if self.USING_TILES else 0))
    # print(self.__arc_to_positions[a - 1 - (self.__positions_to_arc[self.__arc_to_positions[0]] - 1 if self.USING_TILES else 0)])
    return self.__arc_to_positions[literal - 1 - (self.__positions_to_arc[self.__arc_to_positions[0]] - 1 if self.USING_TILES else 0)]






  #######################################################################
  ## Clause generators
  #######################################################################

  def _load_all_literals(self):
    self.__tile_to_position = []
    self.__position_to_tile = {}
    self.__pyramids = {}  # Portion of the covered space by an agent
    self.__exploration_space = {} # All space covered by the pyramids for each time step
    
    self.__exploration_literal_to_tile = {}
    self.__tile_to_exploration_literals = {}

    self.__pyramid_arc_to_tiles = {}
    self.__tiles_to_pyramid_arc = {}

    next_literal = 1
    
    # Generate Tile Literal <-> Position Translators
    for row in range(self._height):
      for col in range(self._width):
        if self._representation[row][col] == self.WALL: continue
        
        pos = (row, col)
        self.__position_to_tile[pos] = next_literal
        self.__tile_to_position.append(pos)
        next_literal += 1

    self.__maximum_tile_literal = next_literal - 1

    # Generate Pyramids + exploration space

    # makespan = len(self.__tile_to_position) # TBD
    makespan = 100 # TBD
    
    for agent_pos in self._agents_position:
      agent = self.get_literal_from_position(*agent_pos)
      
      self.__pyramids[agent] = {}

      for tile_pos in self.__position_to_tile:
        tile = self.get_literal_from_position(*tile_pos)
        
        if tile not in self.__tile_to_exploration_literals:
          self.__tile_to_exploration_literals[tile] = {}
        
        user_dist = (abs(tile_pos[0] - agent_pos[0]) + abs(tile_pos[1] - agent_pos[1]))

        for target_dist in [(agent, user_dist)]:
          for step_time in range(target_dist[1], makespan + 1):

            if step_time not in self.__exploration_space:
              self.__exploration_space[step_time] = {}
            if step_time not in self.__pyramids[agent]:
              self.__pyramids[agent][step_time] = {}

            if tile in self.__exploration_space[step_time]:
              copy_literal = self.__exploration_space[step_time][tile]
            else:
              copy_literal = next_literal

            self.__pyramids[agent][step_time][tile] = copy_literal
            self.__exploration_space[step_time][tile] = copy_literal

            self.__exploration_literal_to_tile[copy_literal] = tile
            self.__tile_to_exploration_literals[tile][step_time] = copy_literal
            
            if copy_literal == next_literal: 
              next_literal += 1


    self.__maximum_exploration_space_literal = next_literal - 1

    # Generate arcs for each pyramid
    for agent in self.__pyramids:
      for step_time in self.__pyramids[agent]:
        for tile in self.__pyramids[agent][step_time]:
          copy_tile = self.__tile_to_exploration_literals[tile][step_time]
          neighs = [ self.get_literal_from_position(*neigh_pos) for neigh_pos in self.get_base_neighbour_positions(*self.get_position_from_literal(tile)) ]
          
          for neigh in neighs:
            if step_time < makespan:
              self.__tiles_to_pyramid_arc[(copy_tile, self.__tile_to_exploration_literals[neigh][step_time + 1])] = next_literal
              self.__pyramid_arc_to_tiles[next_literal] = (copy_tile, self.__tile_to_exploration_literals[neigh][step_time + 1])
              next_literal += 1
    
    self.__maximum_pyramid_arc_literal = next_literal - 1

    self.__maximum_literal = next_literal - 1
    self.__idpool = IDPool(occupied=[[1, self.__maximum_literal]])











  def get_base_neighbour_positions(self, row, col):
    neighbours = []

    N = (row - 1, col)
    S = (row + 1, col)
    E = (row, col + 1)
    W = (row, col - 1)

    if row > 0 and self._representation[N[0]][N[1]] != MAMaze.WALL:
      neighbours.append(N)

    if row < self._height - 1 and self._representation[S[0]][S[1]] != MAMaze.WALL:
      neighbours.append(S)

    if col > 0 and self._representation[W[0]][W[1]] != MAMaze.WALL:
      neighbours.append(W)

    if col < self._width - 1 and self._representation[E[0]][E[1]] != MAMaze.WALL:
      neighbours.append(E)

    return neighbours

  def get_all_clauses(self):
    print("Generating Hard Restrictions   0.00%", end="\r")
    self._load_all_literals()
    print("Generating Hard Restrictions  50.00%", end="\r")
    clauses = []

    clauses.extend(self.get_agent_clauses())
    print("Generating Hard Restrictions  60.00%", end="\r")
    clauses.extend(self.get_goal_clauses())
    print("Generating Hard Restrictions  70.00%", end="\r")
    print("Generating Hard Restrictions 100.00%")
    return clauses

  def get_agent_clauses(self):
    clauses = []

    for agent_pos in self._agents_position:
      agent = self.get_literal_from_position(*agent_pos)
      clauses.append([agent])

    return clauses

  def get_goal_clauses(self):
    clauses = []

    for goal_pos in self._goals_position:
      goal = self.get_literal_from_position(*goal_pos)
      clauses.append([goal])
    
    return clauses

  def add_soft_clauses(self, wcnf):
    print("Generating Soft Restrictions   0.00%", end="\r")
    
    print("Generating Soft Restrictions 100.00%")

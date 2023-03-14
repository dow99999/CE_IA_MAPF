import distinctipy as dc
from pysat import card
from pysat.formula import IDPool
from constants import *

if SAVE_MAZE_SOLUTION_TO_PNG:
  import png

from MAMaze import MAMaze
import time
class FLAGS():
  OPTIMIZE_PYRAMIDS =                     0b0000000000000001
  NEW_PYRAMID_GENERATION =                0b0000000000000010
  OPTIMIZE_MAKESTEP =                     0b0000000000000100



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

    self.__final_states = {}

    self.flags = flags

    self.__maximum_literal = 1
    self.__maximum_tile_literal = 1
    self.__maximum_exploration_space_literal = 1
    self.__maximum_pyramid_arc_literal = 1
    self.__maximum_final_state_literal = 1

    self.__makespan = None


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


  def visualize_exploration_space(self, model=[]):
    out = ""

    model = [ m for m in model if m > 0 ]

    WAY_COLOR = [color/255 for color in MAMaze.COLORS[MAMaze.WAY]]

    def add_point(x, y, z, r, g, b):
      return f"{x} {y} {z} {r} {g} {b}\n"

    def merge_colors(colors):
      r = 0
      g = 0
      b = 0

      for color in colors:
        r += color[0]
        g += color[1]
        b += color[2]

      return (r/len(colors), g/len(colors), b/len(colors))


    for y in range(len(self._representation)):
      for x in range(len(self._representation[y])):
        color = [color/255 for color in MAMaze.COLORS[self._representation[y][x]]]
        if (y, x) in self.__position_to_tile:
          tile = self.__position_to_tile[(y, x)]
          if tile in model:
            color = merge_colors([WAY_COLOR, color])
        out += add_point(x, y, 0, color[0], color[1], color[2])


    if not SHOW_DISTINC_PYRAMIDS:
      for time in self.__exploration_space:
        for tile in self.__exploration_space[time]:
          tile_pos = self.get_position_from_literal(tile)

          exploration_literals = self.__exploration_space[time][tile]
          
          if len([agent for agent in exploration_literals if self.__exploration_space[time][tile][agent] in model]) > 0:
            out += add_point(tile_pos[1], tile_pos[0], -time - 1, 1, 0, 0)
          elif not SHOW_ONLY_SOLUTION:
            out += add_point(tile_pos[1], tile_pos[0], -time - 1, 0.2, 0.2, 0.5)
    else:
      colors = dc.get_colors(len(self._agents_position))
      i = 0
      voxels = set()
      voxel_colors = {}

      for agent in self.__pyramids:
        color = colors[i]
        for time in self.__pyramids[agent]:
          for tile in self.__pyramids[agent][time]:
            tile_pos = self.get_position_from_literal(tile)
            voxel = (tile_pos[1], tile_pos[0], -time - 1)
            voxels.add(voxel)
            if voxel not in voxel_colors:
              voxel_colors[voxel] = []

            voxel_colors[voxel].append(color)

        i += 1

      for voxel in voxels:
        exploration_literals = self.__exploration_space[-voxel[2] - 1][self.get_literal_from_position(voxel[1], voxel[0])]
        if len([agent for agent in exploration_literals if self.__exploration_space[-voxel[2] - 1][self.get_literal_from_position(voxel[1], voxel[0])][agent] in model]) > 0:
          out += add_point(*voxel, 1,0,0)
        elif not SHOW_ONLY_SOLUTION:
          out += add_point(*voxel, *merge_colors(voxel_colors[voxel]))

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

  def __propagate_pyramid_from_position(self, row, col, pyramid={}, time_step=0, reverse=False):
    if not reverse and time_step > self.__makespan: return
    if reverse and time_step < 0: return

    next_time_step = time_step + (1 if not reverse else -1)

    if time_step not in pyramid:
      pyramid[time_step] = {}
    if (next_time_step) not in pyramid:
      pyramid[next_time_step] = {}
    
    # Current
    pyramid[time_step][self.get_literal_from_position(row, col)] = True
    
    neigh_pos = self.get_base_neighbour_positions(row, col)

    # Wait
    if self.get_literal_from_position(row, col) not in pyramid[next_time_step]:
      self.__propagate_pyramid_from_position(row, col, pyramid, next_time_step, reverse)
    
    # Neighs
    for pos in neigh_pos:
      if self.get_literal_from_position(pos[0], pos[1]) not in pyramid[next_time_step]:
        self.__propagate_pyramid_from_position(pos[0], pos[1], pyramid, next_time_step, reverse)


    

    


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

    #######################################################
    # Generate Tile Literal <-> Position Translators
    for row in range(self._height):
      for col in range(self._width):
        if self._representation[row][col] == self.WALL: continue
        
        pos = (row, col)
        self.__position_to_tile[pos] = next_literal
        self.__tile_to_position.append(pos)
        next_literal += 1

    self.__maximum_tile_literal = next_literal - 1
    #
    #######################################################
    
    
    
    #######################################################
    # Generate Pyramids + exploration space
    
    for agent_pos in self._agents_position:
      agent = self.get_literal_from_position(*agent_pos)
      goal_pos = [connection for connection in self._agent_goal_connections if (connection[0] == agent_pos)][0][1]
      goal = self.get_literal_from_position(*goal_pos)
      
      self.__pyramids[agent] = {}

      if self.__makespan is None:
        self.__makespan = len(self.__tile_to_position) // 2 # TBD

      ##########################################################################################################
      # Forma nueva
      if self.flags & FLAGS.NEW_PYRAMID_GENERATION:
        agent_pyramid = {}
        goal_pyramid = {}

        # Calculate pyramids from agent and goal
        self.__propagate_pyramid_from_position(*agent_pos, agent_pyramid)
        self.__propagate_pyramid_from_position(*goal_pos, goal_pyramid, self.__makespan, reverse=True)

        for step_time in agent_pyramid:
          if step_time not in self.__exploration_space:
            self.__exploration_space[step_time] = {}
          if step_time not in self.__pyramids[agent]:
            self.__pyramids[agent][step_time] = {}

          for tile in agent_pyramid[step_time]:
            if not(self.flags & FLAGS.OPTIMIZE_PYRAMIDS) or (step_time in goal_pyramid and tile in goal_pyramid[step_time]): # Intersect pyramids
              if tile not in self.__exploration_space[step_time]:
                self.__exploration_space[step_time][tile] = {}
              if tile not in self.__tile_to_exploration_literals:
                self.__tile_to_exploration_literals[tile] = {}
              if step_time not in self.__tile_to_exploration_literals[tile]:
                self.__tile_to_exploration_literals[tile][step_time] = []
            
              self.__pyramids[agent][step_time][tile] = next_literal
              self.__exploration_space[step_time][tile][agent] = next_literal

              self.__exploration_literal_to_tile[next_literal] = tile
              self.__tile_to_exploration_literals[tile][step_time].append(next_literal)
              next_literal += 1
      ##########################################################################################################



      ##########################################################################################################
      # Forma antigua
      if not(self.flags & FLAGS.NEW_PYRAMID_GENERATION):
        for tile_pos in self.__position_to_tile:
          tile = self.get_literal_from_position(*tile_pos)
          
          if tile not in self.__tile_to_exploration_literals:
            self.__tile_to_exploration_literals[tile] = {}
          
          user_dist = (abs(tile_pos[0] - agent_pos[0]) + abs(tile_pos[1] - agent_pos[1]))
          goal_dist = (abs(tile_pos[0] - goal_pos[0]) + abs(tile_pos[1] - goal_pos[1]))

          for target_dist in [(agent, user_dist)]:
            for step_time in range(target_dist[1], ((self.__makespan - goal_dist) if self.flags & FLAGS.OPTIMIZE_PYRAMIDS else (self.__makespan)) + 1):
              if step_time not in self.__exploration_space:
                self.__exploration_space[step_time] = {}
              if step_time not in self.__pyramids[agent]:
                self.__pyramids[agent][step_time] = {}

              # if tile in self.__exploration_space[step_time]:
              #   copy_literal = self.__exploration_space[step_time][tile]
              # else:
              copy_literal = next_literal

              if tile not in self.__exploration_space[step_time]:
                self.__exploration_space[step_time][tile] = {}
              if step_time not in self.__tile_to_exploration_literals[tile]:
                self.__tile_to_exploration_literals[tile][step_time] = []

              self.__pyramids[agent][step_time][tile] = copy_literal
              self.__exploration_space[step_time][tile][agent] = copy_literal

              self.__exploration_literal_to_tile[copy_literal] = tile
              self.__tile_to_exploration_literals[tile][step_time].append(copy_literal)
              
              if copy_literal == next_literal:
                next_literal += 1
      ##########################################################################################################

    if self.flags & FLAGS.OPTIMIZE_MAKESTEP:
      max_times = []
      for agent in self.__pyramids:
        agent_pos = self.get_position_from_literal(agent)
        goal_pos = [connection for connection in self._agent_goal_connections if (connection[0] == agent_pos)][0][1]
        goal = self.get_literal_from_position(*goal_pos)
        max_times.append(-1)

        for step_time in range(self.__makespan, 0, -1):
          if goal not in self.__pyramids[agent][step_time]: break
          if max_times[len(max_times) - 1] == -1 or max_times[len(max_times) - 1] > step_time:
            max_times[len(max_times) - 1] = step_time
      

      if self.__makespan == len(self.__tile_to_position) // 2:
        self.__makespan = max(max_times)
        self._load_all_literals()

    self.__maximum_exploration_space_literal = next_literal - 1
    #
    #######################################################



    #######################################################
    # Generate arcs for each pyramid
    for agent in self.__pyramids:
      for step_time in self.__pyramids[agent]:
        for tile in self.__pyramids[agent][step_time]:
          neighs = [tile] + [ self.get_literal_from_position(*neigh_pos) for neigh_pos in self.get_base_neighbour_positions(*self.get_position_from_literal(tile)) ]
          
          for neigh in neighs:
            if step_time < self.__makespan:
              if not(self.flags & FLAGS.OPTIMIZE_PYRAMIDS) or neigh in self.__tile_to_exploration_literals and step_time + 1 in self.__tile_to_exploration_literals[neigh]:
                for neigh_exploration_literal in self.__tile_to_exploration_literals[neigh][step_time + 1]:
                  for copy_tile in self.__tile_to_exploration_literals[tile][step_time]:
                    if copy_tile not in self.__tiles_to_pyramid_arc:
                      self.__tiles_to_pyramid_arc[copy_tile] = {}

                    self.__tiles_to_pyramid_arc[copy_tile][neigh_exploration_literal] = next_literal
                    self.__pyramid_arc_to_tiles[next_literal] = (copy_tile, neigh_exploration_literal)
                  next_literal += 1
    
    self.__maximum_pyramid_arc_literal = next_literal - 1
    #
    #######################################################




    #######################################################
    # Generate final states
    for agent_pos in self._agents_position:
      agent = self.get_literal_from_position(*agent_pos)
      goal_pos = [connection for connection in self._agent_goal_connections if (connection[0] == agent_pos)][0][1]
      goal = self.get_literal_from_position(*goal_pos)

      self.__final_states[agent] = {}
      
      for time_step in self.__pyramids[agent]:
        if goal in self.__pyramids[agent][time_step]:
          self.__final_states[agent][time_step] = next_literal
          next_literal += 1

    self.__maximum_final_state_literal = next_literal - 1
    #
    #######################################################

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
    clauses.extend(self.get_tile_clauses())
    print("Generating Hard Restrictions 100.00%")

    return clauses

  def get_agent_clauses(self):
    clauses = []

    for agent_pos in self._agents_position:
      agent = self.get_literal_from_position(*agent_pos)
      clauses.append([agent])
      # H5
      clauses.append([self.__final_states[agent][self.__makespan]])
      # H7
      clauses.append([self.__exploration_space[0][agent][agent]])

    return clauses

  def get_goal_clauses(self):
    clauses = []

    for goal_pos in self._goals_position:
      goal = self.get_literal_from_position(*goal_pos)
      clauses.append([goal])
      for agent in self.__pyramids:
        if agent in self.__exploration_space[self.__makespan][goal]:
          # H8
          clauses.append([self.__exploration_space[self.__makespan][goal][agent]])

    return clauses


  def get_tile_clauses(self):
    clauses = []

    for from_tile in self.__tiles_to_pyramid_arc:
      arcs = []
      pairs = []
      for to_tile in self.__tiles_to_pyramid_arc[from_tile]:
        arcs.append(self.__tiles_to_pyramid_arc[from_tile][to_tile])
        pairs.extend([from_tile, self.__tiles_to_pyramid_arc[from_tile][to_tile]])
        # H1
        clauses.append([-from_tile, -to_tile, self.__tiles_to_pyramid_arc[from_tile][to_tile]])
        # H2
        clauses.append([-from_tile, -self.__tiles_to_pyramid_arc[from_tile][to_tile], to_tile])

        if to_tile in self.__tiles_to_pyramid_arc and from_tile in self.__tiles_to_pyramid_arc[to_tile]:
          # H9
          clauses.append([-self.__tiles_to_pyramid_arc[from_tile][to_tile], -self.__tiles_to_pyramid_arc[to_tile][from_tile]])
        
        # H10
        if to_tile in self.__tiles_to_pyramid_arc and to_tile in self.__tiles_to_pyramid_arc[to_tile]:
          clauses.append([-self.__tiles_to_pyramid_arc[from_tile][to_tile], self.__tiles_to_pyramid_arc[to_tile][to_tile]])
      
      # C1
      clauses.extend([clause for clause in card.CardEnc.equals(
          lits=arcs,
          bound=1,
          vpool=self.__idpool,
          encoding=card.EncType.pairwise
        ).clauses
      ])

    for agent in self.__pyramids:
      for time_step in self.__pyramids[agent]:
        for tile in self.__pyramids[agent][time_step]:
          # proyeccion
          clauses.append([-self.__pyramids[agent][time_step][tile], tile])

        if time_step + 1 in self.__pyramids[agent]:
          aux = []
          for tile in self.__pyramids[agent][time_step]:
            aux.append(self.__pyramids[agent][time_step][tile])
          for tile in self.__pyramids[agent][time_step + 1]:
            # H3
            clauses.append([-tile] + aux)


    for tile_pos in self.__position_to_tile:
      tile = self.get_literal_from_position(*tile_pos)
      aux = []
      for time_step in self.__exploration_space:
        if tile in self.__exploration_space[time_step]:
          for agent in self.__exploration_space[time_step][tile]:
            aux.append(self.__exploration_space[time_step][tile][agent])
      # proyeccion
      clauses.append([-tile] + aux)


    
    for agent in self.__final_states:
      agent_pos = self.get_position_from_literal(agent)
      goal_pos = [connection for connection in self._agent_goal_connections if (connection[0] == agent_pos)][0][1]
      goal = self.get_literal_from_position(*goal_pos)
      for time_step in self.__final_states[agent]:
        if time_step + 1 in self.__final_states[agent]:
          # H6 ->
          clauses.append([-self.__pyramids[agent][time_step][goal], -self.__final_states[agent][time_step + 1], self.__final_states[agent][time_step]])
          # H6 <-
          clauses.append([-self.__final_states[agent][time_step], self.__final_states[agent][time_step + 1]])
          clauses.append([-self.__final_states[agent][time_step], self.__pyramids[agent][time_step][goal]])

    for time_step in self.__exploration_space:
      for tile in self.__exploration_space[time_step]:
        tiles = []
        for agent in self.__exploration_space[time_step][tile]:
          tiles.append(self.__exploration_space[time_step][tile][agent])
        # C2
        if len(tiles) > 1:
          clauses.extend([clause for clause in card.CardEnc.atmost(
            lits=tiles,
            bound=1,
            vpool=self.__idpool,
            encoding=card.EncType.pairwise
            ).clauses
          ])


    for agent in self.__pyramids:
      for time_step in self.__pyramids[agent]:
        p_slice = []
        for tile in self.__pyramids[agent][time_step]:
          p_slice.append(self.__pyramids[agent][time_step][tile])
        # C3
        if len(p_slice) > 0:
          clauses.extend([clause for clause in card.CardEnc.equals(
            lits=p_slice,
            bound=1,
            vpool=self.__idpool,
            encoding=card.EncType.pairwise
            ).clauses
          ])        



    return clauses


  def add_soft_clauses(self, wcnf):
    print("Generating Soft Restrictions   0.00%", end="\r")
    
    for agent in self.__final_states:
      for time_step in self.__final_states[agent]:
        # S1
        wcnf.append([self.__final_states[agent][time_step]], weight=1)
      

    print("Generating Soft Restrictions 100.00%")

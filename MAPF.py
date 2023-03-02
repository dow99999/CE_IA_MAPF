from pysat import card
from pysat.formula import IDPool
from constants import *

if SAVE_MAZE_SOLUTION_TO_PNG:
  import png

from MAMaze import MAMaze
import time
class FLAGS():
  USE_TILE_VARIABLES =                    0b0000000000000001
  
  ARC_BLOCK_IMMEDIATE_LOOPS =             0b0000000000000010
  ARC_ONLY_ONE_INPUT =                    0b0000000000000100
  ARC_ONE_OUTPUT_MEANS_ONE_INPUT =        0b0000000000001000

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

    self.flags = flags

    self.__maximum_literal = 1
    self.__maximum_tile_literal = 1
    self.__maximum_pyramid_literal = 1
    

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
    model_i = 1
    model = [m for m in model if m > 0]

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

    for row_i in range(len(self._representation)):
      pixel_matrix.append([])
      for col_i in range(len(self._representation[row_i])):
        colors = self.COLORS[self._representation[row_i][col_i]] if not (row_i, col_i) in model else MAMaze.color_merger(self.COLORS[self.WAY], self.COLORS[self._representation[row_i][col_i]])

        pixel_matrix[len(pixel_matrix) - 1].append(colors[0])
        pixel_matrix[len(pixel_matrix) - 1].append(colors[1])
        pixel_matrix[len(pixel_matrix) - 1].append(colors[2])

        model_i += 1
        

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

    next_literal = 1
    
    # Generate Tile Literal <-> Position Translators
    for row in range(self._height):
      for col in range(self._width):
        if self._representation[row][col] == self.WALL: continue
        
        pos = (row, col)
        self.__position_to_tile[pos] = next_literal
        self.__tile_to_position.append(pos)
        next_literal += 1

    self.__maximum_literal

    if self.flags & FLAGS.USE_AMO_MANHATTAN:
      for row in range(self._height):
        for col in range(self._width):
          if self.get_maze_position_type(row, col) == self.GOAL:
            flag_pos = (row, col)
          if self.get_maze_position_type(row, col) == self.AGENT:
            user_pos = (row, col)

      user = self.get_literal_from_position(*user_pos)
      flag = self.get_literal_from_position(*flag_pos)
      
      max_dist = 0

      if self.flags & FLAGS.MANHATTAN_RECTANGLE_DISTANCE:
        max_dist = (abs(user_pos[0] - flag_pos[0]) + abs(user_pos[1] - flag_pos[1]))

      if self.flags & FLAGS.MANHATTAN_FURTHEST_TILE_DISTANCE:
        for tile_pos in self.__position_to_tile:
          flag_dist = (abs(tile_pos[0] - flag_pos[0]) + abs(tile_pos[1] - flag_pos[1]))
          user_dist = (abs(tile_pos[0] - user_pos[0]) + abs(tile_pos[1] - user_pos[1]))
          big_dist = max(flag_dist, user_dist)
          if max_dist < big_dist:
            max_dist = big_dist

      if self.flags & FLAGS.MANHATTAN_FULL_PATH_DISTANCE:
        max_dist = self._width * self._height
        
      self.__pyramids[user] = {}
      self.__pyramids[flag] = {}

      for tile_pos in self.__position_to_tile:
        tile = self.get_literal_from_position(*tile_pos)
        flag_dist = (abs(tile_pos[0] - flag_pos[0]) + abs(tile_pos[1] - flag_pos[1]))
        user_dist = (abs(tile_pos[0] - user_pos[0]) + abs(tile_pos[1] - user_pos[1]))
        
        if tile not in self.__tile_to_pyramid_literals:
          self.__tile_to_pyramid_literals[tile] = []

        for target_dist in [(user, user_dist)]: # (flag, flag_dist) Eliminamos la doble piramide
          for dist in range(target_dist[1], max_dist + 1):
            if dist not in self.__pyramids[target_dist[0]]:
              self.__pyramids[target_dist[0]][dist] = []
            
            if not(self.flags & FLAGS.AMO_OPTIMIZE_PYRAMID) or (dist + flag_dist) <= max_dist:
              self.__pyramids[target_dist[0]][dist].append(next_literal)

              self.__tile_to_pyramid_literals[tile].append(next_literal)
              self.__pyramid_literals_to_tile[next_literal] = tile
              
              # if self.flags & FLAGS.AMO_OPTIMIZE_PYRAMID and (dist + flag_dist) > max_dist:
              #   self.__pyramid_false_literals.append([-next_literal])
              
              next_literal += 1


        
      self.__maximum_pyramid_literal = next_literal - 1

    self.__maximum_literal = next_literal - 1
    self.__idpool = IDPool(occupied=[[1, self.__maximum_literal]])











  def get_neighbour_positions(self, row, col):
    neighbours = []

    if row > 0 and (((row, col), (row - 1, col)) in self.__positions_to_arc or ((row - 1, col), (row, col)) in self.__positions_to_arc):
      neighbours.append((row - 1, col))

    if row < self._height - 1 and (((row, col), (row + 1, col)) in self.__positions_to_arc or ((row + 1, col), (row, col)) in self.__positions_to_arc):
      neighbours.append((row + 1, col))

    if col > 0 and (((row, col), (row, col - 1)) in self.__positions_to_arc or ((row, col - 1), (row, col)) in self.__positions_to_arc):
      neighbours.append((row, col - 1))

    if col < self._width - 1 and (((row, col), (row, col + 1)) in self.__positions_to_arc or ((row, col + 1), (row, col)) in self.__positions_to_arc):
      neighbours.append((row, col + 1))

    return neighbours

  def get_base_neighbour_positions(self, row, col):
    neighbours = []

    if row > 0:
      neighbours.append((row - 1, col))

    if row < self._height - 1:
      neighbours.append((row + 1, col))

    if col > 0:
      neighbours.append((row, col - 1))

    if col < self._width - 1:
      neighbours.append((row, col + 1))

    return neighbours

  def get_all_clauses(self):
    print("Generating Hard Restrictions   0.00%", end="\r")
    self._load_all_literals()
    print("Generating Hard Restrictions  50.00%", end="\r")
    clauses = []

    clauses.extend(self.get_user_clauses())
    print("Generating Hard Restrictions  60.00%", end="\r")
    clauses.extend(self.get_flag_clauses())
    print("Generating Hard Restrictions  70.00%", end="\r")
    if self.USING_TILES:
      clauses.extend(self.get_arc_clauses_tiles())
      print("Generating Hard Restrictions  80.00%", end="\r")
      if self.flags & FLAGS.USE_AMO_MANHATTAN:
        clauses.extend(self.get_distance_ring_clauses())
        print("Generating Hard Restrictions  90.00%", end="\r")
      if self.flags & FLAGS.USE_ALO_MANHATTAN:
        clauses.extend(self.get_basic_distance_ring_clauses())
        print("Generating Hard Restrictions  90.00%", end="\r")

    else:
      clauses.extend(self.get_arc_clauses_no_tiles())
      print("Generating Hard Restrictions  80.00%", end="\r")


    print("Generating Hard Restrictions 100.00%")
    return clauses

  def get_user_clauses(self):
    users = []
    clauses = []
    

    for row in range(self._height):
      for col in range(self._width):
        if self.get_maze_position_type(row, col) == self.AGENT:
          users.append((row, col))

    for user in users:
      arcs = []
      neighbors = self.get_neighbour_positions(*user)

      if self.USING_TILES:
        clauses.append([self.get_literal_from_position(*user)])

      for neigh in neighbors:
        arcs.append(self.get_arc_from_positions(*user, *neigh))

      clauses.extend(MAPF.__get_card_eq1(arcs))

    return clauses

  def get_flag_clauses(self):
    flags = []
    clauses = []

    for row in range(self._height):
      for col in range(self._width):
        if self.get_maze_position_type(row, col) == self.GOAL:
          flags.append((row, col))

    for flag in flags:
      arcs = []
      neighbors = self.get_base_neighbour_positions(*flag)

      if self.USING_TILES:
        clauses.append([self.get_literal_from_position(*flag)])

      for neigh in neighbors:
        ineighbors = self.get_neighbour_positions(*neigh)
        for ineigh in ineighbors:
          if self.get_maze_position_type(*ineigh) == self.GOAL:
            arcs.append(self.get_arc_from_positions(*neigh, *ineigh))
      
      clauses.extend(MAPF.__get_card_eq1(arcs))


    return clauses

  def get_arc_clauses_no_tiles(self):
    clauses = []

    for tile_pos in self.__position_to_tile:
      tile_type = self.get_maze_position_type(*tile_pos)
      neighbours = self.get_neighbour_positions(*tile_pos)

      if tile_type == self.PATH:
        in_arcs = [ self.get_arc_from_positions(*neigh, *tile_pos) for neigh in neighbours if self.get_maze_position_type(*neigh) != self.GOAL ]
        out_arcs = [ self.get_arc_from_positions(*tile_pos, *neigh) for neigh in neighbours if self.get_maze_position_type(*neigh) != self.AGENT ]

        if self.flags & FLAGS.ARC_ONLY_ONE_INPUT:
          # Only one input
          clauses.extend(MAPF.__get_card_max1(in_arcs))

        if self.flags & FLAGS.ARC_ONE_OUTPUT_MEANS_ONE_INPUT:
          for out_arc in out_arcs:
            clauses.extend([[-out_arc] + claus for claus in MAPF.__get_card_eq1(in_arcs)])

        # only one output if there is input
        for in_arc in in_arcs:
          clauses.extend([[-in_arc] + claus for claus in MAPF.__get_card_eq1(out_arcs)])

    if self.flags & FLAGS.ARC_BLOCK_IMMEDIATE_LOOPS:
      # prohibimos loops
      loops = []
      for key in self.__positions_to_arc:
        if (key[1], key[0]) in self.__positions_to_arc and self.__positions_to_arc[(key[1], key[0])] not in loops:
          loops.append([self.__positions_to_arc[key], self.__positions_to_arc[(key[1], key[0])]])
      # <= 1
      for c in loops:
        clauses.append([-x for x in c])

    

    return clauses


  def get_arc_clauses_tiles(self):
    clauses = []

    for tile_pos in self.__position_to_tile:
      tile_type = self.get_maze_position_type(*tile_pos)
      neighbours = self.get_neighbour_positions(*tile_pos)

      if tile_type == self.PATH:
        in_arcs = [ self.get_arc_from_positions(*neigh, *tile_pos) for neigh in neighbours if self.get_maze_position_type(*neigh) != self.GOAL ]
        out_arcs = [ self.get_arc_from_positions(*tile_pos, *neigh) for neigh in neighbours if self.get_maze_position_type(*neigh) != self.AGENT ]
        tile_literal = self.get_literal_from_position(*tile_pos)

        # A(neigh, o) -> Ro | neigh = { Vecinos posibles de o }
        # One input means tile in way
        for in_arc in in_arcs:
          clauses.append([-in_arc, tile_literal])
        
        if self.flags & FLAGS.TILE_OUTPUT_MEANS_WAY:
          # A(o, neigh) -> Ro | neigh = { Vecinos posibles de o }
          # One input means tile in way
          for out_arc in out_arcs:
            clauses.append([-out_arc, tile_literal])
        
        # Ro -> cardinality(1, A(o, neigh)) | neigh = { Vecinos posibles de o }
        # only one output if tile is in way
        clauses.extend([[-tile_literal] + claus for claus in MAPF.__get_card_eq1(out_arcs)])
        
        # only one input if tile is in way
        clauses.extend([[-tile_literal] + claus for claus in MAPF.__get_card_eq1(in_arcs)])

        if self.flags & FLAGS.TILE_CARDINALITY_EQ2:
          # Cardinality 2 for every tile neighbor
          if len(neighbours) > 1:
            clauses.extend([[-tile_literal] + clause for clause in card.CardEnc.equals(
                lits=[ self.get_literal_from_position(*neigh) for neigh in neighbours ],
                bound=2,
                vpool=self.__idpool,
                encoding=card.EncType.seqcounter
              ).clauses
            ])

    if self.flags & FLAGS.ARC_BLOCK_IMMEDIATE_LOOPS: # Fix duplicates
      # prohibimos loops
      loops = {}
      for key in self.__positions_to_arc:
        if (key[1], key[0]) in self.__positions_to_arc and self.__positions_to_arc[(key[1], key[0])] not in loops:
          loops[self.__positions_to_arc[key]] = self.__positions_to_arc[(key[1], key[0])]
      # <= 1
      for c in loops:
        clauses.append([-c, -loops[c]])



    return clauses
  
  def get_basic_distance_ring_clauses(self):
    """
    Un anillo de distancias que pase por el rectangulo delimitado por el usuario y el flag
    debera tener una o mas casillas
    """
    clauses = []

    rings = {}
    flag_pos = None
    user_pos = None
    done_literals = []

    for row in range(self._height):
      for col in range(self._width):
        if self.get_maze_position_type(row, col) == self.GOAL:
          flag_pos = (row, col)
        if self.get_maze_position_type(row, col) == self.AGENT:
          user_pos = (row, col)


    max_dist = (abs(user_pos[0] - flag_pos[0]) + abs(user_pos[1] - flag_pos[1]))

    for tile_pos in self.__position_to_tile:
      tile = self.get_literal_from_position(*tile_pos)
      dist = (abs(tile_pos[0] - flag_pos[0]) + abs(tile_pos[1] - flag_pos[1]))
      if dist > max_dist: continue
      
      if dist not in rings:
        rings[dist] = []

      rings[dist].append(tile)


    for ring in rings:
      if set(rings[ring]) in done_literals: continue

      clauses.extend(MAPF.__get_card_min1(rings[ring]))
      done_literals.append(set(rings[ring]))
      
    if self.flags & FLAGS.USE_DOUBLE_ALO_MANHATTAN:
      for tile_pos in self.__position_to_tile:
        tile = self.get_literal_from_position(*tile_pos)
        dist = (abs(tile_pos[0] - user_pos[0]) + abs(tile_pos[1] - user_pos[1]))
        if dist > max_dist: continue
        
        if dist not in rings:
          rings[dist] = []

        rings[dist].append(tile)
      
        for ring in rings:
          if set(rings[ring]) in done_literals: continue

          clauses.extend(MAPF.__get_card_min1(rings[ring]))
          done_literals.append(set(rings[ring]))

    return clauses

  def get_distance_ring_clauses(self):
    clauses = []

    for tile in self.__tile_to_pyramid_literals:
      # 1: de todas las copias de una casilla una o ninguna
      clauses.extend(
        card.CardEnc.atmost(
                lits=self.__tile_to_pyramid_literals[tile],
                bound=1,
                vpool=self.__idpool,
                encoding=card.EncType.bitwise
              ).clauses
      )

      # 2: y.o,i,j -> tile
      clauses.extend([(-cpy, tile) for cpy in self.__tile_to_pyramid_literals[tile]])

      # 2: tile -> V y.o,i,j
      clauses.append((-tile,) + tuple(self.__tile_to_pyramid_literals[tile]))

    if self.flags & FLAGS.AMO_OPTIMIZE_PYRAMID:
      clauses.extend(self.__pyramid_false_literals)

    if not(self.flags & FLAGS.AMO_FIX_DIRECTIONS):
      # 3.1: Un slice de piramide solo debe tener una tile o ninguna
      for gen in self.__pyramids:
        # i = 0
        for p_slice in self.__pyramids[gen]:
          # if i == 5: break
          # i += 1
          clauses.extend(
            card.CardEnc.atmost(
                    lits=self.__pyramids[gen][p_slice],
                    bound=1,
                    vpool=self.__idpool,
                    encoding=card.EncType.bitwise
                  ).clauses
          )
    if self.flags & FLAGS.AMO_FIX_DIRECTIONS:
      # 3.2: Una variable de una casilla solo tendra una de las copias del slice superior en caso de estar activa
      for gen in self.__pyramids:
        # i = 0
        for p_slice_i in range(0, len(self.__pyramids[gen]) - 1):
          target_slice = self.__pyramids[gen][p_slice_i]
          next_slice = self.__pyramids[gen][p_slice_i + 1]
          next_slice_set = set(next_slice)

          for literal_copy in target_slice:
            tile = self.__pyramid_literals_to_tile[literal_copy]
            tile_pos = self.get_position_from_literal(tile)
            tile_neighs = [ self.get_literal_from_position(*neigh_pos) for neigh_pos in self.get_neighbour_positions(*tile_pos) ]
            
            neigh_copy_tiles = []
            for neigh in tile_neighs:
              # Extraemos los neighbors presentes en la siguiente slice
              neigh_copy_tiles.extend(list(next_slice_set & set(self.__tile_to_pyramid_literals[neigh])))

            if len(neigh_copy_tiles) > 0:
              clauses.extend([ [-literal_copy] + cardinality for cardinality in 
                        card.CardEnc.atmost(
                          lits=neigh_copy_tiles,
                          bound=1,
                          vpool=self.__idpool,
                          encoding=card.EncType.pairwise
                        ).clauses ]
                    )          


    return clauses

  def add_soft_clauses(self, wcnf):
    print("Generating Soft Restrictions   0.00%", end="\r")
    flag_pos = None
    for row in range(self._height):
      for col in range(self._width):
        if self.get_maze_position_type(row, col) == self.GOAL:
          flag_pos = (row, col)
    
    for arc in self.__positions_to_arc:
      pos1 = arc[0]
      pos2 = arc[1]

      dist1 = (abs(pos1[0] - flag_pos[0]) + abs(pos1[1] - flag_pos[1]))
      dist2 = (abs(pos2[0] - flag_pos[0]) + abs(pos2[1] - flag_pos[1]))
      if dist1 < dist2:
        weight = 1
        if self.flags & FLAGS.USE_DISTANCE_AS_WEIGHT:
          weight = dist2
        
        wcnf.append([-self.get_arc_from_positions(*pos1, *pos2)], weight=weight)
    
    print("Generating Soft Restrictions 100.00%")

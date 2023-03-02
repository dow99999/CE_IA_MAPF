class MAMaze:
  """
  Clase para representar un laberinto
  """

  # Representaciones de cada tipo de casilla
  PATH = " "
  WALL = "■"
  AGENT = "¤"
  GOAL = "ƒ"
  WAY = "·"

  COLORS = {
    str(PATH): (200, 200, 200),
    str(WALL): (0, 0, 0),
    str(AGENT): (0, 0, 255),
    str(GOAL): (255, 0, 0),
    str(WAY): (255, 153, 0)
  }
  
  def color_merger(col1, col2):
    return ((col1[0] + col2[0]) // 2), ((col1[1] + col2[1]) // 2), ((col1[2] + col2[2]) // 2)
    
  def combinations_generator(elements: list, length: int):
    """
    Devuelve una lista con todas las combinaciones sin repeticiones de length longitud posibles de todos los elementos de elements
    """
    combinations = []

    # Hacemos todas las combinaciones posibles de elementos
    def generate(comb):
      if len(comb) == length:
        if comb not in combinations:
          combinations.append(comb) # Anadimos una combinacion solo si no ha sido anadida ya
        return
      
      for e in elements:
        if e not in comb:
          generate(comb | {e})
    
    generate(set())

    return [ list(x) for x in combinations ]  # Convertimos los sets en listas











  def __init__(self, matrix: list = None):
    self._representation = []
    self._width = 0
    self._height = 0

    self._agents_position = []
    self._goals_position = []

    self._agent_goal_connections = []

    if matrix != None:
      self.load_maze_from_matrix(matrix)

  def load_maze_from_matrix(self, matrix: list):
    """
    Carga una matriz de tipos de casilla en el objeto Maze
    """
    self._representation = matrix.copy()
    self._width = len(self._representation[0])
    self._height = len(self._representation)

  def load_maze_from_file(self, path: str):
    """
    Carga los datos de las casillas del laberinto a traves de un archivo de texto plano
    """
    raw_data = open(path, "r").readlines()
    maze_matrix = []

    types = [ t for t in raw_data[0] ][:-1]
    assert len(types) == 4 and len([c for c in types if len(c) > 1]) == 0, "Bad format on tile type specifications, there has to be 4 types (agent, goal, path, walls) and each one must be only one character"

    agent, goal, path, wall = types

    translator = {
      (agent): self.AGENT,
      (goal): self.GOAL,
      (wall): self.WALL,
      (path): self.PATH
    }

    for line_i in range(1, len(raw_data)):
      if raw_data[line_i] == "\n": continue

      if len(raw_data[1]) == len(raw_data[line_i]):
        maze_matrix.append([])
        for tile_type_i in range(len(raw_data[line_i])):
          if raw_data[line_i][tile_type_i] != "\n":
            tile_type = translator[raw_data[line_i][tile_type_i]]
            if tile_type == self.AGENT:
              self._agents_position.append((line_i - 1, tile_type_i))
            if tile_type == self.GOAL:
              self._goals_position.append((line_i - 1, tile_type_i))
            maze_matrix[line_i - 1].append(tile_type)
      else:
        connection = raw_data[line_i].split("\n")[0].split(" ")
        self._agent_goal_connections.append((self._agents_position[int(connection[0]) - 1], self._goals_position[int(connection[1]) - 1]))
      

    self.load_maze_from_matrix(maze_matrix)
        



  def _box_maze(self, representation: str):
    """
    Funcion interna para representar lineas de un string de misma longitud dentro de un recuadro
    """
    out = ""
    lines = representation.split("\n")

    out += "┌" + ("─" * (len(lines[0]) + 1)) + "┐\n"

    for line in lines:
      out += "│ "
      for c in line:
        out += c
      out += "│\n"

    out += "└" + ("─" * (len(lines[0]) + 1)) + "┘"

    return out

  def get_maze_position_type(self, row, col):
    return self._representation[row][col]

  def get_maze_matrix(self):
    """
    Devuelve la matriz de tipos de casilla del objeto
    """
    return self._representation.copy()

  def get_maze_height(self):
    """
    Devuelve la altura del laberinto
    """
    return self._height
    
  def get_maze_width(self):
    """
    Devuelve el ancho del laberinto
    """
    return self._width
  
  def get_maze_representation(self, pretty: bool = False):
    """
    Devuelve un string con la representacion del laberinto con un simbolo por tipo de casilla
    Ver las constantes estaticas de Maze para saber los tipos de casilla y su representacion
    """
    out = ""

    for row in self._representation:
      for element in row:
        out += element + " "
      out += "\n"

    out = out[:-1]

    return out if not pretty else self._box_maze(out)



  def modify_element(self, row: int, col: int, new_element: str):
    """
    Modifica el tipo de una casilla
    """
    self._representation[row][col] = new_element


  def get_element_literals(self, target: str):
    """
    Devuelve una lista de todos los literales de un tipo
    """
    literals = []
    current_literal = 1

    for row in self._representation:
      for element in row:
        if element == target:
          literals.append(current_literal)
        current_literal += 1

    return literals
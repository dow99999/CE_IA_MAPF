from MAMaze import MAMaze as M

TEST_OVERRIDES = False

SOLVERS = {
  "CaDiCaL": "cd",
  "GlueCard3": "gc3",
  "GlueCard41": "gc4",
  "Glucose3": "g3",
  "Glucose4": "g4",
  "Lingeling": "lgl",
  "Maplechrono": "mcb",
  "Maplecm": "mcm",
  "MapleSAT": "mpl",
  "MergeSAT": "mg3",
  "MiniCard": "mc",
  "MiniSAT22": "m22",
  "MiniSATgh": "mgh"
}

### Solver a utilizar
SOLVER_NAME = SOLVERS["CaDiCaL"]
if TEST_OVERRIDES:
  from constants_test import SOLVER_NAME

# Iteraciones para las que se ejecutara el calculo de la solucion
TEST_ITERATIONS = 1

#####################################################################################################################
# Generacion de archivos de datos
###

# Guarda las clausulas generadas por un experimento en un archivo (clauses.cnf | clauses.wcnf)
SAVE_CLAUSES_TO_FILE = True

# Guarda el modelo que soluciona el experimento en un archivo .json (solution.json)
DUMP_MODEL_TO_FILE = True

# Guarda la representacion del laberinto solucionado en un archivo de imagen(solved_maze.png)
SAVE_MAZE_SOLUTION_TO_PNG = True

# Todos los archivos de salida se guardaran dentro de esta carpeta
OUTPUT_DIR = "./out_files/"
if TEST_OVERRIDES:
  from constants_test import OUTPUT_DIR


#####################################################################################################################
# Opciones de visualizacion de laberintos
###

# Distinc pyramids of each agent with colors
SHOW_DISTINC_PYRAMIDS = True

# Don't show all the exploration space, only the solution
SHOW_ONLY_SOLUTION = True

# Show all the possible arcs between pyramid tiles
SHOW_PYRAMID_ARCS = True

#####################################################################################################################
# Opciones de visualizacion de variables
###

# Muestra el numero total de clausulas generadas
SHOW_CLAUSE_NUMBER = True

# Muestra el tiempo empleado por el solver para resolver el problema
SHOW_SOLVING_TIME = True


def normalize_digits(num, max_num):
  num = str(num)
  max_num = str(max_num)

  return "0" * (len(max_num) - len(num)) + num

#####################################################################################################################
# Configuracion general del programa
###

# Representacion del laberinto en una matriz por tipos
MAZE_MATRIX = [
  [ M.PATH, M.WALL, M.WALL, M.WALL, M.WALL, M.WALL, M.WALL, M.GOAL ],
  [ M.PATH, M.PATH, M.PATH, M.PATH, M.WALL, M.PATH, M.PATH, M.PATH ],
  [ M.PATH, M.WALL, M.WALL, M.PATH, M.WALL, M.PATH, M.WALL, M.PATH ],
  [ M.PATH, M.PATH, M.WALL, M.PATH, M.WALL, M.PATH, M.WALL, M.PATH ],
  [ M.WALL, M.PATH, M.WALL, M.PATH, M.PATH, M.PATH, M.PATH, M.PATH ],
  [ M.WALL, M.PATH, M.WALL, M.WALL, M.WALL, M.WALL, M.WALL, M.WALL ],
  [ M.PATH, M.PATH, M.PATH, M.PATH, M.PATH, M.PATH, M.PATH, M.PATH ],
  [ M.WALL, M.WALL, M.WALL, M.WALL, M.PATH, M.WALL, M.WALL, M.WALL ],
  [ M.AGENT, M.PATH, M.PATH, M.PATH, M.PATH, M.WALL, M.PATH, M.PATH ]
]

#####################################
# Lista de experimentos
SAT_CUSTOM_RESTRICTIONS = "1"
MAXSAT_CUSTOM_RESTRICTIONS = "2"


OPTIONS = [
    SAT_CUSTOM_RESTRICTIONS,
    MAXSAT_CUSTOM_RESTRICTIONS
  ]

SAT_OPTIONS = [
  SAT_CUSTOM_RESTRICTIONS
]

MAXSAT_OPTIONS = [
  MAXSAT_CUSTOM_RESTRICTIONS
]
#####################################

#####################################################################################################################
# Definicion de flags custom
###

from MAPF import FLAGS

# Flags para usar en la opcion custom
CUSTOM_FLAGS =\
  FLAGS.NEW_PYRAMID_GENERATION |\
  FLAGS.OPTIMIZE_PYRAMIDS | FLAGS.OPTIMIZE_MAKESPAN |\
  FLAGS.RESTRICTION_C1 | FLAGS.RESTRICTION_C2 |\
  FLAGS.RESTRICTION_H1 | FLAGS.RESTRICTION_H2 | FLAGS.RESTRICTION_H3 | FLAGS.RESTRICTION_H5 | FLAGS.RESTRICTION_H6 | FLAGS.RESTRICTION_H7 | FLAGS.RESTRICTION_H8 | FLAGS.RESTRICTION_H9 | FLAGS.RESTRICTION_H10 |\
  FLAGS.RECTRICTION_O_C3 | FLAGS.RESTRICTION_O_H11

if TEST_OVERRIDES:
  from constants_test import CUSTOM_FLAGS
import sys
import time

from pysat.solvers import Solver
from pysat.examples.rc2 import RC2
from pysat.formula import CNF, WCNF

from constants import *

from MAPF import MAPF
from MAPF import FLAGS

# sys.stdout.reconfigure(encoding='utf-16')


if len(sys.argv) not in [2, 3] or sys.argv[1] not in OPTIONS:
  print("Needs one argument from this list ", [ int(o) for o in OPTIONS ],": ", sep="")
  print(" 1. SAT Custom Restrictions")
  print()
  print(" 2. MaxSAT Custom Restrictions")
  exit()





maze = MAPF(flags=CUSTOM_FLAGS)

# Definimos si es SAT o MaxSAT
if sys.argv[1] in MAXSAT_OPTIONS:
  USING_MAXSAT = True
else:
  USING_MAXSAT = False

# Cargamos los datos de casilla del laberinto
if len(sys.argv) == 3:
  maze.load_maze_from_file(sys.argv[2])
else:
  maze.load_maze_from_matrix(MAZE_MATRIX)


exit()







# Cargamos las clausulas del laberinto
multipurpose_cnf = WCNF() if USING_MAXSAT else CNF()
multipurpose_cnf.extend(maze.get_all_clauses())

# Cargamos las soft clauses en caso de ser MaxSAT
if USING_MAXSAT:
  maze.add_soft_clauses(multipurpose_cnf)

print("Saving Clauses' File")
# Guardamos en un fichero el .cnf o .wcnf de las clausulas generadas
multipurpose_cnf.to_file(OUTPUT_DIR + "clauses." + ("w" if USING_MAXSAT else "") + "cnf")




f_time = 0
for i in range(TEST_ITERATIONS):
  print(f"Processing iteration {normalize_digits(i + 1, TEST_ITERATIONS)}/{TEST_ITERATIONS}", end="\r")


  # Inicializamos el solver con las restricciones ya generadas
  solver = RC2(multipurpose_cnf, solver=SOLVER_NAME) if USING_MAXSAT else Solver(bootstrap_with=multipurpose_cnf, name=SOLVER_NAME, use_timer=True)

  i_time = time.time_ns()
  
  # Resolvemos el laberinto y obtenemos el modelo, diferenciando entre una resolucion SAT y una MaxSAT:
  if not USING_MAXSAT:
    solver.solve()
    f_time += solver.time() * 1000000000    # Pasamos de segundos a nanosegundos para mantener una misma unidad
    model = solver.get_model()
  else:
    model = solver.compute()  # en caso de MaxSAT resolvemos aqui el laberinto
    f_time += solver.oracle_time() * 1000000000


print()




if SHOW_SOLVING_TIME:
  print("Solving time for " + str(TEST_ITERATIONS) + " iterations:", (f_time / 1000000) / 1000, "s")

if SHOW_CLAUSE_NUMBER:
  if not USING_MAXSAT:
    print("Number of clauses: ", len(multipurpose_cnf.clauses))
  else:
    print("Number of clauses: ", "Soft: " + str(len(multipurpose_cnf.soft)), "Hard: " + str(len(multipurpose_cnf.hard)), "Total: " + str(len(multipurpose_cnf.hard) + len(multipurpose_cnf.soft)))

if model is None:
  print("UNSAT")
  exit()

# Mostramos datos de la solucion
maze.save_solved_maze_to_image(model)
maze.save_solved_maze_with_dirs_to_image(model)
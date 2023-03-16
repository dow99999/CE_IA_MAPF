from constants import OUTPUT_DIR
import math

def parse_matrix_to_dots_cloud(dots):
  out = ""

  for i in dots:
    for j in dots[i]:
      for k in dots[i][j]:
        color = dots[i][j][k]
        if len(color) == 3:
          out += f"{i} {j} {k} {color[0]} {color[1]} {color[2]}\n"

  with open(OUTPUT_DIR + "pc.xyzrgb", "w") as f:
    f.write(out)

dots = {}

# I = 100
# J = 100
# K = 100

# for i in range(1, I + 1):
#   dots[i] = {}
#   for j in range(1, J + 1):
#     dots[i][j] = {}
#     for k in range(1, K + 1):
#       if k % 10 == 1 or i % 10 == 1 or j == 1:
#         dots[i][j][k] = (i / I, j / J, k / K)


X = 100

for x in range(1, X + 1):
  y = math.sin(x) * 2 + x
  z = 0

  dots[x] = {}
  dots[x][y] = {}
  for z in range(10):
    dots[x][y][z] = (x / X, 0.7, z / X)

      

parse_matrix_to_dots_cloud(dots)
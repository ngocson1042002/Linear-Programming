import numpy as np
from fractions import Fraction
from simplex import LinearProgramming
import os

with open('input.txt', 'r') as rf:
        lines = rf.readlines()
    
num_variables, num_constraints = int(lines[0].split()[0]), int(lines[0].split()[1])
objective_type = lines[1]
c = [float(i) for i in lines[2].split()]

# signs la dau: >=, <=
A, signs, b = [], [], []
for i in range(3,len(lines)-1):
    elements = lines[i].split()
    A.append([float(elements[j]) for j in range(num_variables)])

    signs.append(elements[-2])
    b.append(float(elements[-1]))

# Rang buoc dau: 1 la x >= 0, 0 la x <= 0, None la x tuy y
restricted = tuple([None if r.strip().lower() == 'none' else int(r)  for r in lines[len(lines)-1].split()])

c_frac = np.array([Fraction(i) for i in c])
b_frac = np.array([Fraction(i) for i in b])
A_frac = np.array([[Fraction(col) for col in row] for row in A])

problem = LinearProgramming(num_variables, num_constraints)
problem.generate(objective_type, c_frac, A_frac, b_frac, signs, restricted)

try:
    optimal_value, solution = problem.optimize(type_rotate='Dantzig', print_details=True)
except Exception as err:
    # os.system('cls')
    print(err)
    print('\n' + '*'*35 + f'Bland' + '*'*35 + '\n')
    optimal_value, solution = problem.optimize(type_rotate='Bland', print_details=True)

if problem.status == 2: # No solution
    print('No solution')
elif problem.status == 0: # Unboundedness
    print(f'Optimal value: {optimal_value}\nSolution:{solution}')
else: # ??????
    print(f'Optimal value: {optimal_value}')
    res = 'Solution: ('
    for i in range(num_variables-1):
        res += f'{solution[i]}, '
    print(res + f'{solution[num_variables-1]})')
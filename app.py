# app.py

from flask import Flask, request, render_template
import numpy as np
from fractions import Fraction
from simplex import LinearProgramming

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/result', methods=['POST'])
def result():
    print(request.data)
    num_variables = int(request.form['input'])
    num_constraints = int(request.form['input1'])
    objective_type = request.form['input2']


    
    c = [float(i) for i in request.form['input3'].split()]
      
      
    print('yoyoCCCC')
    print(num_constraints)
    print(c)
    # signs la dau: >=, <=
    A, signs, b = [], [], []
    lines = []
    for i in range(1, num_constraints + 1):
       # print('input2_' + str(i))
        try:
            lines.append(request.form['input2_' + str(i - 1)])
        except Exception as e :
            print(e)
            
    print(lines)
    for i in range(num_constraints):
        elements = lines[i].split()
        A.append([float(elements[j]) for j in range(num_variables)])

        signs.append(elements[-2])
        b.append(float(elements[-1]))
    print('yoyoz')
    # Rang buoc dau: 1 la x >= 0, 0 la x <= 0, None la x tuy y
    restricted = tuple([None if r.strip().lower() == 'none' else int(r)  for r in request.form['input4'].split()])

    c_frac = np.array([Fraction(i) for i in c])
    b_frac = np.array([Fraction(i) for i in b])
    A_frac = np.array([[Fraction(col) for col in row] for row in A])

    problem = LinearProgramming(num_variables, num_constraints)
    problem.generate(objective_type, c_frac, A_frac, b_frac, signs, restricted)
    problem.identify_equality_constraints()
    
    output_data = ''
    print('yoyo')
    try:
        optimal_value, solution = problem.optimize(type_rotate='Dantzig', print_details=True)
    except Exception as err:
        # os.system('cls')
        output_data += str(err) + '\n'
        output_data += str('\n' + '*'*35 + f'Bland' + '*'*35 + '\n')
        optimal_value, solution = problem.optimize(type_rotate='Bland', print_details=True)

    if problem.status == 2: # No solution
        output_data += str('Status: No solution\n')
    elif problem.status == 0: # Unboundedness
        output_data += str('Status: The problem is unboundedness')
        output_data += str(f'Optimal value: {optimal_value}')
    else: # ??????
        output_data += str('Status: The solution was found')
        output_data += str(f'Optimal value: {optimal_value}')
        res = 'Solution: ('
        for i in range(num_variables-1):
            res += f'{solution[i]}, '
        output_data += str(res + f'{solution[num_variables-1]})')
    print('Hello')
    return render_template('result.html', output_data = "type(output_data)")
    
#    return "hello"

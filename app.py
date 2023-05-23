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
    num_variables = int(request.form['numVariables'])
    num_constraints = int(request.form['numConstraints'])
    objective_type = request.form['objectiveType']


    
    c = [float(i) for i in request.form['objectiveCoeff'].split()]

    # # signs la dau: >=, <=
    A, signs, b = [], [], []
    lines = []
    for i in range(num_constraints):
        try:
            lines.append(request.form[f'constraint{i}'])
            signs.append(request.form[f'operator{i}'])
            b.append(request.form[f'constraintValue{i}'])
        except Exception as e :
            print(e)
            
    for i in range(num_constraints):
        elements = lines[i].split()
        A.append([float(elements[j]) for j in range(num_variables)])

    # Rang buoc dau: 1 la x >= 0, 0 la x <= 0, None la x tuy y
    restricted = tuple([None if r.strip().lower() == 'none' else int(r)  for r in request.form['restrictions'].split()])

    c_frac = np.array([Fraction(i) for i in c])
    b_frac = np.array([Fraction(i) for i in b])
    A_frac = np.array([[Fraction(col) for col in row] for row in A])

    problem = LinearProgramming(num_variables, num_constraints)
    problem.generate(objective_type, c_frac, A_frac, b_frac, signs, restricted)
    problem.identify_equality_constraints()
    
    output_data = ''
    try:
        optimal_value, solution = problem.optimize(type_rotate='Dantzig', print_details=True)
    except Exception as err:
        # os.system('cls')
        output_data += str(err) + '\n'
        output_data += str('\n' + '*'*33 + f'Bland' + '*'*33 + '\n')
        optimal_value, solution = problem.optimize(type_rotate='Bland', print_details=True)
        
    result = '\n'
    for i in range(len(problem.dict_steps['optimal'])) :
        result += '\n' + '*'*30 + f'Dictionary {i + 1}' + '*'*30 + '\n\n'
        result += f"z = {problem.dict_steps['optimal'][i]}"
        for j in range(len(problem.dict_steps['c'][i])):
            if (problem.dict_steps['c'][i][j] >= 0):
                result += f" + {abs(problem.dict_steps['c'][i][j])}{problem.dict_steps['non_basics'][i][j]}"
            else:
                result += f" - {abs(problem.dict_steps['c'][i][j])}{problem.dict_steps['non_basics'][i][j]}"
                
            
        result += '\n' + '_'*problem.num_variables*12
        
        for j in range(len(problem.dict_steps['A'][i])):
            result += f"\n{problem.dict_steps['basics'][i][j]} = {problem.dict_steps['b'][i][j]}"
            for k in range(len(problem.dict_steps['A'][i][j])):
                if (-problem.dict_steps['A'][i][j][k] >= 0):
                    result += f" + {abs(problem.dict_steps['A'][i][j][k])}{problem.dict_steps['non_basics'][j][k]}"
                else:
                    result += f" - {abs(problem.dict_steps['A'][i][j][k])}{problem.dict_steps['non_basics'][j][k]}"
        result += '\n\n'
    
    output_data += result

    if problem.status == 2: # No solution
        output_data += str('Status: No solution\n')
    elif problem.status == 0: # Unboundedness
        output_data += 'Status: The problem is unboundedness\n'
        output_data += f'Optimal value: {optimal_value}\n'
    else: # ??????
        output_data += 'Status: The solution was found\n'
        output_data += f'Optimal value: {optimal_value}\n'
        res = 'Solution: ('
        for i in range(num_variables-1):
            res += f'{solution[i]}, '
        output_data += str(res + f'{solution[num_variables-1]})\n')
   
    return render_template('result.html', output_data = output_data)

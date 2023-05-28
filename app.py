# app.py

from flask import Flask, request, render_template
import numpy as np
from fractions import Fraction
from simplex import LinearProgramming

def handlePrintSubVar(arr):
    basics = []
    # Lặp qua từng phần tử trong mảng arr
    if(len(arr) != 0):
        for sublist in arr:
            temp = []
            for item in sublist:
                # Tách ký tự đầu tiên và hệ số sau ký tự "_"
                character = item[0]
                coefficient = item[2:]
                
                # Sử dụng phương thức format để tạo chuỗi a<sub>i</sub>
                formatted_string = "{}<sub>{}</sub>".format(character, coefficient)
                
                # Thêm chuỗi đã được định dạng vào mảng tạm thời
                temp.append(formatted_string)
            
            # Thêm mảng tạm vào mảng b
            basics.append(temp)
    return basics

def handlePrintStatus(arr):
    converted_array = []
    for item in arr:
        sub_array = []
        pairs = item.split(', ')
        for pair in pairs:
            character, coefficient = pair.split('_')
            formatted_string = "{}<sub>{}</sub>".format(character, coefficient[0])
            sub_array.append(formatted_string)
        converted_array.append(sub_array)
    return converted_array

def printDictionary(problem, problem_type):
    result = ''
    
    basics = handlePrintSubVar(problem_type['basics'])

    nonBasics = handlePrintSubVar(problem_type['non_basics'])
             
    problemStatus = handlePrintStatus(problem_type['status'])
    
    if(len(problem_type['optimal']) != 0):
        for i in range(len(problem_type['optimal'])) :
            if (i != 0 and i-1 < len(problem_type['status'])):
                result += '<br><b style="color: blue;">' + problemStatus[i-1][0] + ' entering, ' + problemStatus[i-1][1] + ' leaving' + '</b>'
                
            result += '<br>' + '*'*30 + f'<b>Dictionary {i + 1}</b>' + '*'*30 + '<br><br>'
            result += f"z = {problem_type['optimal'][i]}"
            for j in range(len(problem_type['c'][i])):
                if (problem_type['c'][i][j] >= 0):
                    result += f" + {abs(problem_type['c'][i][j])}{nonBasics[i][j]}"
                else:
                    result += f" - {abs(problem_type['c'][i][j])}{nonBasics[i][j]}"
                    
                
            result += '<br>' + '_'*problem.num_variables*8
            
            for j in range(len(problem_type['A'][i])):
                result += f"<br>{basics[i][j]} = {problem_type['b'][i][j]}"
                for k in range(len(problem_type['A'][i][j])):
                    # if nonBasics and j < len(nonBasics) and k < len(nonBasics[j]):
                    if (-problem_type['A'][i][j][k] >= 0):
                        result += f" + {abs(problem_type['A'][i][j][k])}{nonBasics[i][k]}"
                    else:
                        result += f" - {abs(problem_type['A'][i][j][k])}{nonBasics[i][k]}"
            result += '<br>'
    print(problem_type['A'])
    print(problem_type['non_basics'])
    print('Result', result)
    return result        

app = Flask(__name__)

# Cấu hình đường dẫn đến thư mục templates
app.template_folder = 'static/templates'
app.add_url_rule('/photos/<path:filename>', ...)

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
    temp = []
    for i in range(num_variables):
        temp.append(request.form[f'restriction{i}'])
    
    restricted = tuple([None if r.strip().lower() == 'none' else int(r)  for r in temp])

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
        output_data += str(err) + '<br>'
        output_data += str('<br>' + '*'*33 + f'Bland' + '*'*33 + '<br>')
        optimal_value, solution = problem.optimize(type_rotate='Bland', print_details=True)
        
    # Artifical variables: ['a_1']
    
    if(len(problem.dict_steps['Aux']['A']) > 0 and len(problem.dict_steps['Prime']['A']) > 0):
        output_data += str('*'*30 + f'<b>Auxiliary Problem</b>' + '*'*30 + '<br>')
        output_data += printDictionary(problem, problem.dict_steps['Aux'])
        output_data += str('*'*30 + f'<b>Prime Problem</b>' + '*'*30 + '<br>')
        output_data += printDictionary(problem, problem.dict_steps['Prime'])
    elif (len(problem.dict_steps['Prime']['A']) > 0):
        output_data += str('*'*30 + f'<b>Prime Problem</b>' + '*'*30 + '<br>')
        output_data += printDictionary(problem, problem.dict_steps['Prime'])
    else:
        output_data += str('*'*30 + f'<b>Auxiliary Problem</b>' + '*'*30 + '<br>')
        output_data += printDictionary(problem, problem.dict_steps['Aux'])

    if problem.status == 2: # No solution
        output_data += str('<br><b>Status: </b>No solution<br>')
    elif problem.status == 0: # Unboundedness
        output_data += '<br><b>Status: </b>The problem is unboundedness<br>'
        output_data += f'<b>Optimal value: </b>{optimal_value}<br>'
    else: # ??????
        output_data += '<br><b>Status: </b>The solution was found<br>'
        output_data += f'<b>Optimal value: </b>{optimal_value}<br>'
        res = '<b>Solution: </b>('
        for i in range(num_variables-1):
            res += f'{solution[i]}, '
        output_data += str(res + f'{solution[num_variables-1]})<br><br>')
    return render_template('result.html', output_data = output_data)

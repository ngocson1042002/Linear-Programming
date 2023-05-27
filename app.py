# app.py

from flask import Flask, request, render_template
import numpy as np
from fractions import Fraction
from simplex import LinearProgramming

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
    
    
    print("AAAAA",problem.dict_steps['A'])
    print("BBBBBBB",problem.dict_steps['basics'])
    print("NNNNNNN",problem.dict_steps['non_basics'])
    
    # Xử lí output để hiển thị trong html
    basics = []
    # Lặp qua từng phần tử trong mảng a
    if(len(problem.dict_steps['basics']) != 0):
        for sublist in problem.dict_steps['basics']:
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
    
    nonBasics = []

    # Lặp qua từng phần tử trong mảng a
    if(len(problem.dict_steps['non_basics']) != 0):
        for sublist in problem.dict_steps['non_basics']:
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
            nonBasics.append(temp)
    
    print(nonBasics)
            
    result = ''
    if(len(problem.dict_steps['optimal']) != 0):
        for i in range(len(problem.dict_steps['optimal'])) :
            result += '<br>' + '*'*30 + f'Dictionary {i + 1}' + '*'*30 + '<br><br>'
            result += f"z = {problem.dict_steps['optimal'][i]}"
            for j in range(len(problem.dict_steps['c'][i])):
                if (problem.dict_steps['c'][i][j] >= 0):
                    result += f" + {abs(problem.dict_steps['c'][i][j])}{nonBasics[i][j]}"
                else:
                    result += f" - {abs(problem.dict_steps['c'][i][j])}{nonBasics[i][j]}"
                    
                
            result += '<br>' + '_'*problem.num_variables*8
            
            for j in range(len(problem.dict_steps['A'][i])):
                result += f"<br>{basics[i][j]} = {problem.dict_steps['b'][i][j]}"
                for k in range(len(problem.dict_steps['A'][i][j])):
                    if nonBasics and j < len(nonBasics) and k < len(nonBasics[j]):
                        if (-problem.dict_steps['A'][i][j][k] >= 0):
                            result += f" + {abs(problem.dict_steps['A'][i][j][k])}{nonBasics[j][k]}"
                        else:
                            result += f" - {abs(problem.dict_steps['A'][i][j][k])}{nonBasics[j][k]}"
            result += '<br>'
    
    output_data += result


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

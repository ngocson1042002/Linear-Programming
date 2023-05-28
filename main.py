import numpy as np
from fractions import Fraction
from simplex import LinearProgramming
import os

def handlePrintSubVar(arr):
    print(1)
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
    print(nonBasics)
             
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
                    if nonBasics and j < len(nonBasics) and k < len(nonBasics[j]):
                        if (-problem_type['A'][i][j][k] >= 0):
                            result += f" + {abs(problem_type['A'][i][j][k])}{nonBasics[j][k]}"
                        else:
                            result += f" - {abs(problem_type['A'][i][j][k])}{nonBasics[j][k]}"
            result += '<br>'
    return result  

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
problem.identify_equality_constraints()

try:
    optimal_value, solution = problem.optimize(type_rotate='Dantzig', print_details=True)
except Exception as err:
    # os.system('cls')
    print(err)
    print('\n' + '*'*35 + f'Bland' + '*'*35 + '\n')
    optimal_value, solution = problem.optimize(type_rotate='Bland', print_details=True)

if problem.status == 2: # No solution
    print('Status: No solution')
elif problem.status == 0: # Unboundedness
    print('Status: The problem is unboundedness')
    print(f'Optimal value: {optimal_value}')
else: # ??????
    print('Status: The solution was found')
    print(f'Optimal value: {optimal_value}')
    res = 'Solution: ('
    for i in range(num_variables-1):
        res += f'{solution[i]}, '
    print(res + f'{solution[num_variables-1]})')
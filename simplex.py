import numpy as np
from fractions import Fraction
import os

MAX_INT = 999999

def check_same_chars(a, b):
    a = a.split()
    b = b.split()
    
    if len(a) != len(b):
        return False
    for char in a:
        if char not in b:
            return False

    return True

class LinearProgramming:
    def __init__(self, num_variables, num_constraints):
        self.num_variables = num_variables
        self.num_constraints = num_constraints
        self.objective_type = None
        self.c = None
        self.A = None
        self.b = None
        self.signs = None
        self.restricted = None
        self.var_change = dict()
        self._name_variables = [f'x_{i+1}' for i in range(self.num_variables)]
        self.basics = np.array([f'w_{i+1}' for i in range(num_constraints)])
        self.non_basics = np.array(self.name_variables)
        self.status = None
        self.priority_index = dict()
        self.first_dictionary = None  
        self.current_dictionary = None
        self.arti_variables = None
        self.dict_steps = {'Aux': {'A': [], 'b': [], 'c': [], 'optimal': [], 'basics': [], 'non_basics': [], 'status': []}, 
                        'Prime': {'A': [], 'b': [], 'c': [], 'optimal': [], 'basics': [], 'non_basics': [], 'status': []},
                        'var_change': []}
        
    @property
    def name_variables(self):
        return self._name_variables
    
    @name_variables.setter
    def name_variables(self, value):
        self._name_variables = value
        self.non_basics = np.array(value)
        
    def generate(self, objective_type, c, A, b, signs, restricted):
        self.objective_type = objective_type
        self.c = np.array(c)
        self.A = np.array(A)
        self.b = np.array(b)
        self.signs = np.array(signs)
        self.restricted = np.array(restricted)
        
    def update_first_dictionary(self, first_dict):
        self.first_dictionary = first_dict
        return first_dict
        
    def update_cur_dictionary(self, cur_dict):
        self.cur_dictionary = cur_dict
        return cur_dict
    
    def __str__(self):

        res = f'{self.objective_type.title()}\t\t{self.c[0]}{self.name_variables[0]}'
        for i in range(1, self.num_variables):
            if self.c[i] >= 0:
                res += f' + {self.c[i]}{self.name_variables[i]}'
            else:
                res += f' - {abs(self.c[i])}{self.name_variables[i]}'
                
        res += '\nSubject to'
        for i in range(self.num_constraints):
            res += f'\n\t\t({i+1}) {self.A[i,0]}{self.name_variables[0]}'
            for j in range(1, self.num_variables):
                if self.A[i,j] >= 0:
                    res += f' + {self.A[i,j]}{self.name_variables[j]} ' 
                else:
                    res += f' - {abs(self.A[i,j])}{self.name_variables[j]} '
            res += f'{self.signs[i]} {self.b[i]}'
            
        res += '\n\n\t\t'
        for i in range(self.num_variables-1):
            if self.restricted[i] == 0:
                res += f'{self.name_variables[i]} <= 0, '
            elif self.restricted[i] == 1:
                res += f'{self.name_variables[i]} >= 0, '
            else:
                res += f'{self.name_variables[i]} is no bound, '
        
        if self.restricted[self.num_variables-1] == 0:
            res += f'{self.name_variables[-1]} <= 0'
        elif self.restricted[self.num_variables-1] == 1:
            res += f'{self.name_variables[-1]} >= 0'
        else:
            res += f'{self.name_variables[-1]} is no bound'
            
        return res

    def generate_equations(self, basic_solution, tableau):
        equations = ''
        for i in range(self.num_constraints):
            equations += f'{self.basics[i]} = {basic_solution[i]}'
            for j in range(self.num_variables):
                if tableau[i,j] >= 0:
                    equations += f' - {tableau[i,j]}{self.non_basics[j]}'
                else:
                    equations += f' + {abs(tableau[i,j])}{self.non_basics[j]}'
            equations += '\n'
        return equations
    
    def print_dictionary(self, basic_solution, tableau, objective_coef, c):

        z = f'z = {c}'
        for i in range(self.num_variables):
            if objective_coef[i] >= 0:
                z += f' + {objective_coef[i]}{self.non_basics[i]}'
            else:
                z += f' - {abs(objective_coef[i])}{self.non_basics[i]}'
        print(z)
        print('-'*self.num_variables*14)
        
        equations = self.generate_equations(basic_solution, tableau)
        print(equations)
    
    def normalize(self):
        c_new = np.copy(self.c)
        A_new = np.copy(self.A)
        b_new = np.copy(self.b)
        signs_new = np.copy(self.signs)
        num_variables_new = self.num_variables
        num_constraints_new = self.num_constraints

        eq_indices  = np.where(self.signs == '=')[0]
        if len(eq_indices) > 0:
            for i in eq_indices:
                if b_new[i] < 0:
                    b_new[i] *= -1
                    A_new[i] *= -1
            signs_new[signs_new == '='] = '<='
            A_new = np.vstack((A_new, A_new[eq_indices]*(-1)))
            signs_new = np.hstack((signs_new, ['<=']*len(eq_indices)))
            b_new = np.hstack((b_new, b_new[eq_indices]*(-1)))
            num_constraints_new  += len(eq_indices)

        neg_indices = np.where(self.restricted == 0)[0]
        unrestricted_indices = np.where(self.restricted == None)[0]
        num_variables_new += len(unrestricted_indices)
        new_problem = LinearProgramming(num_variables_new, num_constraints_new)

        name_variables_new = []

        for i in range(self.num_variables):
            tmp = np.where(unrestricted_indices == i)[0]
            if len(tmp):
                name_variables_new.append(f'u_{2*tmp[0]+1}')
                name_variables_new.append(f'u_{2*tmp[0]+2}')
                self.var_change[self.name_variables[i]] = [f'u_{2*tmp[0]+1}', f'u_{2*tmp[0]+2}',1]
                continue
            tmp = np.where(neg_indices == i)[0]
            if len(tmp):
                name_variables_new.append(f'u_{2*len(unrestricted_indices)+tmp[0]+1}')
                self.var_change[self.name_variables[i]] = [f'u_{2*len(unrestricted_indices)+tmp[0]+1}',1]
            else:
                name_variables_new.append(self.name_variables[i])
                self.var_change[self.name_variables[i]] = [self.name_variables[i],0]
                
        new_problem.name_variables = name_variables_new

        if len(neg_indices) > 0:
            c_new[neg_indices] *= -1
            A_new[:, neg_indices] *= -1

        if len(unrestricted_indices) > 0:        
            A_new = np.insert(A_new, unrestricted_indices+1, -A_new[:, unrestricted_indices], axis=1)
            c_new = np.insert(c_new, unrestricted_indices+1, -c_new[unrestricted_indices])
            

        if self.objective_type.strip().lower() == 'max':
            c_new *= -1

        neg_ineq_indices = np.where(self.signs == '>=')[0]
        if len(neg_ineq_indices) > 0:
            A_new[neg_ineq_indices,:] *= -1
            b_new[neg_ineq_indices] *= -1
            signs_new[neg_ineq_indices] = '<='

        new_problem.generate('min', c_new, A_new, b_new, signs_new, tuple(np.ones(num_variables_new,dtype=int)))
        
        return new_problem
        
    def update_tableau(self, tableau, basic_solution, objective_coef, optimal_value, type_rotate,print_details):
        entering_variable_index = np.argmin(objective_coef)
        
        if type_rotate == 'Bland':
            for i in range(self.num_variables):
                self.priority_index[f'x_{i+1}'] = i
            for i in range(self.num_variables, self.num_variables + self.num_constraints):
                self.priority_index[f'w_{i-self.num_variables+1}'] = i
            
            for i in range(len(objective_coef)):
                if objective_coef[i] < 0 and i != entering_variable_index:
                    if self.priority_index[self.non_basics[i]] < self.priority_index[self.non_basics[entering_variable_index]]:
                        entering_variable_index = i
                        
        ratio_indices = np.where(tableau[:, entering_variable_index] > 0)[0]
        if ratio_indices.size == 0:
            return

        ratio = basic_solution[ratio_indices]/tableau[:, entering_variable_index][tableau[:, entering_variable_index] > 0]
        leaving_variable_index = ratio_indices[ratio.argmin()]

        status = f'{self.non_basics[entering_variable_index]} entering, {self.basics[leaving_variable_index]} leaving'
        if print_details:
            print(status)

        self.non_basics[entering_variable_index], self.basics[leaving_variable_index] = self.basics[leaving_variable_index], self.non_basics[entering_variable_index]
        remainder = tableau[leaving_variable_index,entering_variable_index]
        k = objective_coef[entering_variable_index]/remainder
        objective_coef -= k*tableau[leaving_variable_index,:]
        objective_coef[entering_variable_index] = -k
        optimal_value += basic_solution[leaving_variable_index]*k

        for i in range(self.num_constraints):
            if i == leaving_variable_index:
                continue
            if tableau[i,entering_variable_index] != 0:
                k = tableau[i,entering_variable_index]/remainder
                tableau[i,:] -= k*tableau[leaving_variable_index,:]
                tableau[i,:][entering_variable_index] = -k
                basic_solution[i] -= k*basic_solution[leaving_variable_index]

        basic_solution[leaving_variable_index] /= remainder
        tableau[leaving_variable_index,:] /= remainder
        tableau[leaving_variable_index,:][entering_variable_index] /= remainder

        return tableau, basic_solution, objective_coef, optimal_value, status
        
    
    def initial_feasible_solution(self, normalize_problem, print_details):
        optimal_value = 0
        infeasibility = False
        if np.any(normalize_problem.b < 0):
            count = 1
            aux_A = np.append(normalize_problem.A.copy(), -np.ones((normalize_problem.num_constraints,1),dtype=self.A.dtype), axis=1)
            aux_non_basics = np.append(normalize_problem.non_basics, 'x_0')
            aux_basics, aux_b = normalize_problem.basics.copy(), normalize_problem.b.copy()
            aux_c = np.zeros(normalize_problem.num_variables+1, dtype=self.A.dtype)
            aux_c[-1] = 1
            
            aux_problem = LinearProgramming(normalize_problem.num_variables+1, normalize_problem.num_constraints)
            aux_problem.name_variables = aux_non_basics
            aux_problem.generate('min', aux_c, aux_A, aux_b, normalize_problem.signs, normalize_problem.restricted)
            
            if print_details:
                print('*'*30 + f'Auxiliary Problem' + '*'*30)
                print('*'*30 + f'Dictionary {count}' + '*'*30)
                aux_problem.print_dictionary(aux_b, aux_A, aux_c, optimal_value)
                count += 1

            self.add_dict_steps('Aux', aux_A, aux_b, aux_c, optimal_value, aux_problem.basics, aux_problem.non_basics)
            
            tableau_temp, b_temp, z_coef_temp = aux_problem.A.copy(), aux_problem.b.copy(), aux_problem.c.copy()
            
            min_index = np.argmin(b_temp)
            status = f'{aux_problem.non_basics[-1]} entering, {aux_problem.basics[min_index]} leaving'
            if print_details:
                print(status)
            self.dict_steps['Aux']['status'].append(status)

            aux_problem.non_basics[-1], aux_problem.basics[min_index] = aux_problem.basics[min_index], aux_problem.non_basics[-1]

            tableau_temp[min_index,:] *= -1
            b_temp[min_index] *= -1
            z_coef_temp -= tableau_temp[min_index,:]
            z_coef_temp[-1] = 1
            optimal_value += b_temp[min_index]
            
            for i in range(self.num_constraints):
                if i == min_index:
                    continue
                tableau_temp[i,:] += tableau_temp[min_index,:]
                tableau_temp[i,:][aux_problem.num_variables-1] = -1
                b_temp[i] += b_temp[min_index]
            tableau_temp[min_index][-1] = -1

            if print_details:
                print('*'*30 + f'Dictionary {count}' + '*'*30)
                aux_problem.print_dictionary(b_temp, tableau_temp, z_coef_temp, optimal_value)
                count += 1
            self.add_dict_steps('Aux', tableau_temp, b_temp, z_coef_temp, optimal_value, aux_problem.basics, aux_problem.non_basics)

            while np.any(z_coef_temp < 0):
                tableau_temp, b_temp, z_coef_temp, optimal_value, status = aux_problem.update_tableau(tableau_temp, b_temp, z_coef_temp, optimal_value, type_rotate='Dantzig', print_details=print_details)    
                if print_details:
                    print('*'*30 + f'Dictionary {count}' + '*'*30)
                    aux_problem.print_dictionary(b_temp, tableau_temp, z_coef_temp, optimal_value)
                    count += 1
                self.add_dict_steps('Aux', tableau_temp, b_temp, z_coef_temp, optimal_value, aux_problem.basics, aux_problem.non_basics)
                self.dict_steps['Aux']['status'].append(status)
            
            if not (np.sum(z_coef_temp) == 1 and z_coef_temp[z_coef_temp == 0].size == z_coef_temp.size - 1 and aux_problem.non_basics[np.where(z_coef_temp == 1)[0]] == 'x_0'):
                infeasibility = True
                return tableau_temp, b_temp, z_coef_temp, optimal_value, infeasibility
                    
            if print_details:
                print('*'*30 + f'Prime Problem' + '*'*30)
                
            t = np.where(aux_problem.non_basics == 'x_0')[0]
            tableau = np.delete(tableau_temp, t, axis=1)
            res = np.zeros(normalize_problem.num_variables, dtype=self.A.dtype)
            new_non_basics = np.delete(aux_problem.non_basics, t)
            
            for i in range(len(normalize_problem.non_basics)):
                d = normalize_problem.c[i]
                tmp = np.where(aux_problem.basics == normalize_problem.non_basics[i])[0]
                if len(tmp) > 0:
                    res -= d*np.squeeze(tableau[tmp,:])
                    optimal_value += d*b_temp[tmp]
                else:
                    k = np.where(new_non_basics == normalize_problem.non_basics[i])[0]
                    res[k] += d
    
            normalize_problem.non_basics = new_non_basics       
            optimal_value = np.squeeze(optimal_value).item()
            z_coef = res
            normalize_problem.basics = aux_problem.basics
            basic_solution = b_temp
            return tableau, basic_solution, z_coef, optimal_value, infeasibility

        tableau, basic_solution, z_coef = normalize_problem.A.copy(), normalize_problem.b.copy(), normalize_problem.c.copy()
        return tableau, basic_solution, z_coef, optimal_value, infeasibility

    def identify_equality_constraints(self):
        n = self.A.shape[0]
        row_indices = []
        for i in range(n):
            is_equal = np.all(self.A == self.A[i,:], axis=1)
            equal_indices = np.where(is_equal)[0]
            row_indices.append(equal_indices)

        indices = set()
        for i, t in enumerate(row_indices):
            if t[0] == i:
                indices.add(i)
            if t.size > 1:
                self.signs[i] = '='
        indices = list(indices)
        self.A = self.A[indices]
        self.b = self.b[indices]
        self.signs = self.signs[indices]
        self.num_constraints = self.A.shape[0]


    def process_equality(self, problem, initial_op):
        if not np.any(self.signs == '='):
            return False

        num_equality_constraints = len(self.signs[self.signs == '='])
        num_basics = len(problem.basics)
        j = 0
        basics_to_replace = []
        identity_matrices = []
        artificial_variables = []
        
        while num_equality_constraints:
            basics_to_replace.append(problem.basics[num_basics - num_equality_constraints])
            identity_matrices.append([-1 if k == num_basics - num_equality_constraints else 0 for k in range(num_basics)])
            problem.b[num_basics - num_equality_constraints] *= -1
            problem.A[num_basics - num_equality_constraints, :] *= -1
            problem.basics[num_basics - num_equality_constraints] = f'a_{j+1}'
            artificial_variables.append(f'a_{j+1}')
            j += 1
            num_equality_constraints -= 1

        problem.arti_variables = np.array(artificial_variables)
        identity_matrices = np.array(identity_matrices, dtype=problem.A.dtype)
        problem.A = np.hstack((problem.A, identity_matrices.T))
        problem.non_basics = np.hstack((problem.non_basics, basics_to_replace))
        problem.c = np.hstack((problem.c, [0] * len(self.signs[self.signs == '='])))
        problem.num_variables += len(self.signs[self.signs == '='])

        num_equality_constraints = len(self.signs[self.signs == '='])

        while num_equality_constraints:
            problem.c += (-MAX_INT) * problem.A[num_basics - num_equality_constraints, :]
            initial_op[0] += MAX_INT * problem.b[num_basics - num_equality_constraints]
            num_equality_constraints -= 1
            
        return True

    def add_dict_steps(self, type_problem, tableau, basic_solution, z_coef, optimal_value, basics, non_basics):
        self.dict_steps[type_problem]['A'].append(np.copy(tableau))
        self.dict_steps[type_problem]['b'].append(np.copy(basic_solution))
        self.dict_steps[type_problem]['c'].append(np.copy(z_coef))
        self.dict_steps[type_problem]['optimal'].append(np.copy(optimal_value))
        self.dict_steps[type_problem]['basics'].append(np.copy(basics))
        self.dict_steps[type_problem]['non_basics'].append(np.copy(non_basics))

  
    def optimize(self,type_rotate='Dantzig', print_details=False):
        normalize_problem = self.normalize()

        r = ''
        for key, value in self.var_change.items():
            if len(value) == 3:
                t  = f'{key} = {value[0]} - {value[1]}'
                r += (t+'\n')
                self.dict_steps['var_change'].append(t)
            elif value[-1] == 1:
                t =  f'{value[0]} = -{key}'
                r += (t+'\n')
                self.dict_steps['var_change'].append(t)

        if print_details:
            print(r)

        flag = False
        init_optimal=[0]

        if self.process_equality(normalize_problem, init_optimal):
            flag = True
            if print_details:
                print(f'Artifical variables: {normalize_problem.arti_variables}\n')

        tableau, basic_solution, z_coef, optimal_value, infeasibility = self.initial_feasible_solution(normalize_problem, print_details)

        if infeasibility == True:
            self.status = 2 # No solution
            optimal_value, solution = np.array([]), np.array([])
            return optimal_value, solution

        if flag:
            optimal_value += init_optimal[0]
            
        count = 1
        count_duplicate = 0
        equations = normalize_problem.generate_equations(basic_solution, tableau)
        normalize_problem.first_dictionary = normalize_problem.update_first_dictionary(equations)

        if print_details:
            print('*'*30 + f'Dictionary {count}' + '*'*30)
            normalize_problem.print_dictionary(basic_solution, tableau, z_coef, optimal_value)
            count += 1
        
        self.add_dict_steps('Prime',tableau, basic_solution, z_coef, optimal_value, normalize_problem.basics, normalize_problem.non_basics)


        while np.any(z_coef < 0):
            try:
                tableau, basic_solution, z_coef, optimal_value, status = normalize_problem.update_tableau(tableau, basic_solution, z_coef, optimal_value, type_rotate, print_details)
            except:              
                # Unboundedness
                self.status = 0

                if self.objective_type.strip().lower() == 'max':
                    optimal_value = float('inf')
                else:
                    optimal_value = float('-inf')
                solution = np.array([])
                return optimal_value, solution
            
            if print_details:
                print('*'*30 + f'Dictionary {count}' + '*'*30)
                normalize_problem.print_dictionary(basic_solution, tableau, z_coef, optimal_value)
                count += 1
            
            self.add_dict_steps('Prime',tableau, basic_solution, z_coef, optimal_value, normalize_problem.basics, normalize_problem.non_basics)
            self.dict_steps['Prime']['status'].append(status)
            equations = normalize_problem.generate_equations(basic_solution, tableau)
            normalize_problem.current_dictionary = normalize_problem.update_cur_dictionary(equations)
            isSameDict = check_same_chars(normalize_problem.first_dictionary, normalize_problem.current_dictionary) == True

            if isSameDict:
                count_duplicate += 1
            if isSameDict and count_duplicate == 1:
                self.dict_steps['Aux'] = {'A': [], 'b': [], 'c': [], 'optimal': [], 'basics': [], 'non_basics': [], 'status': []}
                self.dict_steps['Prime'] = {'A': [], 'b': [], 'c': [], 'optimal': [], 'basics': [], 'non_basics': [], 'status': []}
                raise Exception('<b style="color: red; font-size: 17px;">Warning: </b><b style="font-size: 16px;">The simplex method with Dantzig occurs cycling!</b>')
            
        if self.objective_type.strip().lower() == 'max':
            optimal_value *= -1

        self.status=1    # ??????

        # if np.any(basic_solution < 0):
        #     self.status = 2 # No solution
        # elif np.all(basic_solution > 0):
        #     self.status = 3 # Optimization terminated successfully
        # else:
        #     self.status = 1 # Infinitely many roots
        #     return optimal_value, np.array([],dtype=self.A.dtype)

        if normalize_problem.arti_variables is not None:
            a = np.isin(normalize_problem.arti_variables, normalize_problem.non_basics)
            l = a.size - np.count_nonzero(a==False)

            for i, basic in enumerate(normalize_problem.basics):
                if basic_solution[i] == 0 and np.where(normalize_problem.arti_variables == basic)[0].size:
                    l += 1
            if l != normalize_problem.arti_variables.size:
                self.status = 2
                optimal_value, solution = np.array([]), np.array([])
                return optimal_value, solution
        else:
            l = 0

        x = np.zeros(normalize_problem.num_variables-l,dtype=self.A.dtype)
        for i in range(normalize_problem.num_variables-l):
            tmp = np.where(normalize_problem.basics == normalize_problem.name_variables[i])[0]

            if len(tmp):
                x[i] = basic_solution[tmp[0]]

        solution = np.zeros(self.num_variables,dtype=self.A.dtype)
        p = 0
        for i, name in enumerate(self.name_variables):
            if len(self.var_change[name]) == 3:
                solution[i] = x[p] - x[p+1] 
                p += 2
            elif len(self.var_change[name]) == 2 and self.var_change[name][-1] == 1:
                solution[i] = -x[p]
                p += 1
            else:
                solution[i] = x[p]
                p += 1
                
        return optimal_value, solution

if __name__ == "__main__":

    c = np.array([-10,57,9,24])
    A = np.array([[0.5,-5.5,-2.5,9],[0.5,-1.5,-0.5,1],[1,0,0,0]])
    b = np.array([0,0,1])

    c_frac = np.array([Fraction(i) for i in c])
    b_frac = np.array([Fraction(i) for i in b])
    A_frac = np.array([[Fraction(col) for col in row] for row in A])

    problem = LinearProgramming(4,3)
    problem.generate('min', c_frac, A_frac, b_frac, ['<=', '<=', '<='], (1, 1, 1,1))
    try:
        problem.optimize(type_rotate='Dantzig', print_details=True)
    except Exception as err:
        # os.system('cls')
        print(err)
        print('\n' + '*'*35 + f'Bland' + '*'*35 + '\n')
        optimal_value, solution = problem.optimize(type_rotate='Bland', print_details=True)
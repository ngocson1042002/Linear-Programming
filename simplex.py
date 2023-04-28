import numpy as np
from fractions import Fraction

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
    
    def print_dictionary(self, basic_solution, tableau, objective_coef, c):
        z = f'z = {c}'
        for i in range(self.num_variables):
            if objective_coef[i] >= 0:
                z += f' + {objective_coef[i]}{self.non_basics[i]}'
            else:
                z += f' - {abs(objective_coef[i])}{self.non_basics[i]}'
        print(z)
        print('-'*self.num_variables*14)
        
        equations = ''
        for i in range(self.num_constraints):
            equations += f'{self.basics[i]} = {basic_solution[i]}'
            for j in range(self.num_variables):
                if tableau[i,j] >= 0:
                    equations += f' - {tableau[i,j]}{self.non_basics[j]}'
                else:
                    equations += f' + {abs(tableau[i,j])}{self.non_basics[j]}'
            equations += '\n'
        print(equations)
    
    def normalize(self):
        c_new = np.copy(self.c)
        A_new = np.copy(self.A)
        b_new = np.copy(self.b)
        signs_new = np.copy(self.signs)
        num_variables_new = self.num_variables

        neg_indices = np.where(self.restricted == 0)[0]
        unrestricted_indices = np.where(self.restricted == None)[0]
        num_variables_new += len(unrestricted_indices)
        new_problem = LinearProgramming(num_variables_new, self.num_constraints)
        
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
            self.status = 0
            return
        ratio = basic_solution[ratio_indices]/tableau[:, entering_variable_index][tableau[:, entering_variable_index] > 0]
        leaving_variable_index = ratio_indices[ratio.argmin()]

        if print_details:
            print(f'{self.non_basics[entering_variable_index]} entering, {self.basics[leaving_variable_index]} leaving\n')
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

        return tableau, basic_solution, objective_coef, optimal_value
        
    
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
                if print_details:
                    for key, value in self.var_change.items():
                        if len(value) == 3:
                            print(f'{key} = {value[0]} - {value[1]}')
                        elif value[-1] == 1:
                            print(f'{value[0]} = -{key}')
                print('*'*30 + f'Dictionary {count}' + '*'*30)
                aux_problem.print_dictionary(aux_b, aux_A, aux_c, optimal_value)
                count += 1
            
            tableau_temp, b_temp, z_coef_temp = aux_problem.A.copy(), aux_problem.b.copy(), aux_problem.c.copy()
            
            min_index = np.argmin(b_temp)
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

            while np.any(z_coef_temp < 0):
                tableau_temp, b_temp, z_coef_temp, optimal_value = aux_problem.update_tableau(tableau_temp, b_temp, z_coef_temp, optimal_value, type_rotate='Dantzig', print_details=print_details)    
                if print_details:
                    print('*'*30 + f'Dictionary {count}' + '*'*30)
                    aux_problem.print_dictionary(b_temp, tableau_temp, z_coef_temp, optimal_value)
                    count += 1
            
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
        
        
    def optimize(self,type_rotate='Dantzig', print_details=False):
        normalize_problem = self.normalize()
        tableau, basic_solution, z_coef, optimal_value, infeasibility = self.initial_feasible_solution(normalize_problem, print_details)
        if infeasibility == True:
            self.status = 2 # No solution
            optimal_value, solution = np.array([]), np.array([])
            return optimal_value, solution
        count = 1
        if print_details:
            print('*'*30 + f'Dictionary {count}' + '*'*30)
            normalize_problem.print_dictionary(basic_solution, tableau, z_coef, optimal_value)
            count += 1
        while np.any(z_coef < 0):
            try:
                tableau, basic_solution, z_coef, optimal_value = normalize_problem.update_tableau(tableau, basic_solution, z_coef, optimal_value, type_rotate, print_details)
            except:              
                # Unboundedness
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
            
        if self.objective_type.strip().lower() == 'max':
            optimal_value *= -1
            
        if np.any(basic_solution < 0):
            self.status = 2 # No solution
        elif np.all(basic_solution > 0):
            self.status = 3 # Optimization terminated successfully
        else:
            self.status = 1 # Infinitely many roots
            return optimal_value, np.array([],dtype=self.A.dtype)
            
        x = np.zeros(normalize_problem.num_variables,dtype=self.A.dtype)
        for i in range(normalize_problem.num_variables):
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
    print(problem.optimize(type_rotate='Bland', print_details=True))



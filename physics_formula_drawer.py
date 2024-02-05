#!/usr/bin/env python
# coding: utf-8

# In[1]:


import os
import subprocess

def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# Try importing the packages, install if the import fails
try:
    import sympy
except ImportError:
    install('sympy')

try:
    import matplotlib
except ImportError:
    install('matplotlib')

try:
    import pyeda
except ImportError:
    install('pyeda')

try:
    import numpy
except ImportError:
    install('numpy')


# In[2]:


import re
import matplotlib.pyplot as plt
import sympy as sp
from sympy import symbols, Eq, solve, sympify, latex
from pyeda.inter import *
import numpy as np


# In[81]:


#Funtion for adding missing * in between variables in formula
#Prameters: formula string
#Returns modified formula
def normalize_formula(formula):
    #insert * between leters
    formula = re.sub(r'(?<=[a-zA-Z])(?=[a-zA-Z])', '*', formula)
    #insert * between number and letter
    formula = re.sub(r'(?<=[0-9])(?=[a-zA-Z\u0391-\u03A9\u03B1-\u03C9])', '*', formula)
    #insert * after leter if ( follows
    formula = re.sub(r'(?<=[a-zA-Z\u0391-\u03A9\u03B1-\u03C9])(?=[(])', '*', formula) 
    #insert * after ) if letter follows
    formula = re.sub(r'(?<=[)])(?=[a-zA-Z\u0391-\u03A9\u03B1-\u03C9(])', '*', formula)
    return formula

#Function that extracts variables from formula
#Prameters: formula string
#Returns list of variables used in formula
def get_variables_from_formula(formula):
    #finds all letters inside of formula
    return set(re.findall(r'\b[a-zA-Z\u0391-\u03A9\u03B1-\u03C9]\w*\b', formula))

#Function that rearanges formulas based on every variable
#Prameters: formula string and list of string that cointains variables
#Returns all formula rearangements
def rearrange_formula(formula_str, var_names):
    sym_vars = symbols(' '.join(var_names))
    #create symbol dictionary
    sym_dict = dict(zip(var_names, sym_vars))
    
    left_str, right_str = formula_str.split('=')
    #create symbolic expresion of left and right equation parts
    left_sym = sympify(left_str, locals=sym_dict)
    right_sym = sympify(right_str, locals=sym_dict)
    
    #create equation
    eq = Eq(left_sym, right_sym)
    
    variables = eq.free_symbols
    rearranged_forms = []
    #iterate through variables and expres formula that every variable is on the left of equation
    for var in variables:
        solved = solve(eq, var)
        for sol in solved:
            rearranged_forms.append(f"{var} = {sol}")

    return rearranged_forms

#Function that returns text between keywords
#Prameters: text, begin keyword and end keyword
#Returns string list of every fragment of the text between keywords
def extract_text(text, start, end):
    pattern = re.escape(start) + '(.*?)' + re.escape(end)
    matches = re.findall(pattern, text, re.DOTALL)
    return [match.strip() for match in matches]

#Function that returns first instance of the text between same keywords
#Prameters: text and keyword
#Returns string list
def extract_formula(text, keyword):
    pattern = re.escape(keyword) + '(.*?)' + re.escape(keyword)
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    else:
        return None
    
#Function that converts formula string to latex format
#Prameters: formula
#Returns latex string
def string_to_latex(s):
    #Replace ** with ^ for power
    s = re.sub(r'\*\*', '^', s)
    #Replace * with \cdot for multiplication
    s = s.replace('*', r'\cdot ')
    #Replace square root
    s = re.sub(r'sqrt\((.*?)\)', r'\\sqrt{\1}', s)
    
    #Extract the part before and after the equal sign
    parts = s.split('=')
    before_equal, after_equal = parts[0].strip(), parts[1].strip()
    
    #Fractions that has multiple () inside
    after_equal = re.sub(
        r'([^/=]+)(/)\(((?:[^\(\)]+|\([^\(\)]*\))*)\)',
        lambda m: '\\frac{' + m.group(1) + '}{' + m.group(3) + '}',
        after_equal
    )
    #Fractions for number or letter divided by number or letter
    after_equal = re.sub(
        r'\b(\d+|\w+)(\^[\d\w]+)?\s*/\s*(\d+|\w+)(\^[\d\w]+)?\b',
        lambda m: '\\frac{' + m.group(1) + (m.group(2) or '') + '}{' + m.group(3) + (m.group(4) or '') + '}',
        after_equal
    )
    #Fractions that has sequence inside ()  divided by number or letter
    after_equal = re.sub(
        r'([^/=]+)(/)([^(\s]+)',
        lambda m: '\\frac{' + m.group(1) + '}{' + re.sub(r'\^', r'^{', m.group(3)) + '}',
        after_equal
    )

    # Reassemble the equation
    s = before_equal + '=' + after_equal

    #Convert string to LaTeX math enviroment
    s = f"${s}$"
    
    return s


# In[82]:


#Function taht draws graph of given formula
#Prameters: formula and variable list
def draw_graph(formula_str, variable_dict, variable_value=None, formula_value=None):
    #Create subol dictionary
    symbols_dict = {var: sp.symbols(var) for var in variable_dict.keys()}
    
    
    left, right = formula_str.split('=')
    #create symbolic expresion of left and right equation parts
    left_sym = sp.sympify(left, locals=symbols_dict)
    right_sym = sp.sympify(right, locals=symbols_dict)
    
    #Find dynamic variable in formula
    dynamic_var = next((var for var, value in variable_dict.items() if value is None), None)

    if dynamic_var is None:
        raise ValueError("Privalo būti vienas kintamasis be nesikeičiančios reikšmės")
    
    #fill dynamic values
    x_values = np.linspace(0, 100, 50)

    y_values = []
    
    incorrect_values = []
    #Iterate through dynamic values and finc Y values which all varible values
    for i,x_val in enumerate(x_values):
        substitutions = {symbols_dict[var]: value if value is not None else x_val for var, value in variable_dict.items()}

        try:
            y_val = right_sym.subs(substitutions).evalf()
            #If value doesnt exist save value for removal
            if y_val.is_real:
                y_values.append(y_val)
            else:
                incorrect_values.append(i)
        except Exception as e:
            print(f"Klaida skaičiuojant {dynamic_var}={x_val}: {e}")
    x_values = np.delete(x_values, incorrect_values)
    if y_values:
        plt.plot(x_values, y_values, marker='o')
        plt.xlabel(f'{dynamic_var} reikšmė' + (f' ({variable_value})' if variable_value else ''))
        plt.ylabel(f'{left} reikšmė' + (f' ({formula_value})' if formula_value else ''))
        #Print formula in latex format
        plt.title(f'{string_to_latex(formula_str)} funkcijos grafikas')
        plt.grid(True)
        plt.show()
    else:
        print("Klaida gaunant Y ašies reikšmės")


# In[83]:


#Function that finds used formula based on variable that should be on the left of the equation
#Prameters: variable string and list of string that contains formulas
#Returns list of string
def get_used_formula(express_variable,expressed_formulas):
    formulas = []
    for formula in expressed_formulas:
        if formula.startswith(express_variable):
            formulas.append(formula)
    return formulas
#Function that iterates through fragments and extracts information from there as well as finds 
#needed information for graph drawing and calls funtion to draw graph
#Prameters: List of text fragments, list of formulas, string for fomula keyword and list of strings that indicates 
#which variable should be on the left side of equation in expressed formula
def read_through_text(text_fragments,formulas,formula_keyword,express_variable, variable_values, formula_values):
    for index, fragment in enumerate(all_text_fragments):
        formulas_dict = {}
        #finds formula from fragment if not found tries to get it form formulas list
        formula = extract_formula(fragment,formula_keyword)
        if formula is None:
            formula = formulas.pop(0)
        #insert * between variables
        formula = normalize_formula(formula)
        #gets variable list
        variables = get_variables_from_formula(formula)
        #expresses formula through every variable
        expressed_formulas = rearrange_formula(formula,variables)
        #finds correct formula to use based on variable in express_variable based on index
        used_formulas = get_used_formula(express_variable[index],expressed_formulas)

        if len(used_formulas) > 0:
            print(f"Formulė rasta")
        else:
            print("Formulė nebuvo rasta su nurodytu " + express_variable[index] + " kintamuoju")

        #creates variable dictionary
        for var in variables:
            if var != express_variable[index]:
                formulas_dict[var] = extract_formula(fragment,"(("+var+"))")
        #draws graph for every formula that is expressed through variable
        for used_formula in used_formulas:
            if index < len(variable_values) and index < len(formula_values):
                draw_graph(used_formula, formulas_dict, variable_values[index], formula_values[index])
            else:
                draw_graph(used_formula, formulas_dict, None, None)


# In[86]:


#Function that read throug file and extracts needed information
#Parameters: File path
#returns full_text, list of formulas, list of express_variable, keyword, end_keyword, formula_keyword
def parse_content(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    full_text = ''
    formulas = []
    express_variable = []
    section = 'text'
    keyword = "((piešti))"
    end_keyword = "((nepiešti))"
    formula_keyword = "((F))"
    formula_values = []
    variable_values = []
    
    keywords = {
        'Pradžios raktažodis:': 'start',
        'Pabaigos raktažodis:': 'end',
        'Tekste nesančios formulės:': 'formulas',
        'Formulės raktažodis:': 'formula_keyword',
        'Nariai išreiškimui:': 'variables',
        'Formulės fizikinis matas:': 'formula_value',
        'Priklausomo nario fizikinis matas:': 'variable_value'
    }

    #Read through lines
    for line in lines:
        line = line.strip()
        #Check if the line is a keyword and set the current section based on the keyword
        if line in keywords: 
            section = keywords[line]
            continue

        #Read data based on the current section
        if section == 'text':
            full_text += line + '\n'
        elif section == 'formulas' and line:
            formulas.append(line)
        elif section == 'variables' and line:
            express_variable.append(line)
        elif section == 'start' and line:
            keyword = (line)
        elif section == 'end' and line:
            end_keyword = (line)
        elif section == 'formula_keyword' and line:
            formula_keyword = (line)
        elif section == 'formula_value' and line:
            formula_values.append(line)
        elif section == 'variable_value' and line:
            variable_values.append(line)

    return full_text, formulas, express_variable, keyword, end_keyword, formula_keyword, variable_values, formula_values

input_instructions = 'Įveskite duomenų failo direktoriją.\nDuomenų failo formatas:\n'
input_instructions+= '-Tekstas sužymėtais raktažodžaiais - pažymėti teksto fragmentai '
input_instructions+= 'pabaigos ir pradžios raktažodžiais, formulės pažymėtos formulės '
input_instructions+= 'raktažodžaiais iš abiejų formulės pusių, konstantų ir nekintamų '
input_instructions+= 'formulės narių reikšmės įrašomos tokiu formatu, ((nario žymėjimas formulėje))'
input_instructions+= 'skaitinė reikšmė((nario žymėjimas formulėje)).\n'
input_instructions+= '-(neprivaloma) Parašyti \"Pradžios raktažodis:\" ir kitoje eilutėje įvesti raktažodį.'
input_instructions+= 'Jei duomenų faile nėra pažymėta, raktažodis laikosmas ((piešti)).\n'
input_instructions+= '-(neprivaloma) Parašyti \"Pabaigos  raktažodis:\" ir kitoje eilutėje įvesti raktažodį.'
input_instructions+= 'Jei duomenų faile nėra pažymėta, raktažodis laikomas ((nepiesti)).\n'
input_instructions+= '-(neprivaloma) Parašyti \"Formulės raktažodis:\" ir kitoje eilutėje įvesti raktažodį.'
input_instructions+= 'Jei duomenų faile nėra pažymėta, raktažodis laikomas ((F)).\n'
input_instructions+= '-(neprivaloma) Parašyti \"Tekte nesančios formules:\" ir kitoje eilutėje įvesti formules, '
input_instructions+= 'kurios tekste nebuvo pažymėtos. Kiekviena formulė rašoma iš naujos eilutės. '
input_instructions+= 'Formulės vedamos iš eilės tiems fragmentams, kurie neturi pažymėtos formulės.\n'
input_instructions+= '-(privaloma) Parašyti \"Nariai išreiškimui:\" ir formulės narius, kurių priklausomybės '
input_instructions+= 'grafikai reikalingi. Nariai rašomi iš naujos eilutės. Kiekvienam fragmentui '
input_instructions+= 'privalo būti po narį, o vedama iš eilės kiekvienam fragmentui.\n'
file_path = input(input_instructions)
text, formulas, express_variable, keyword, end_keyword, formula_keyword, variable_values, formula_values  = parse_content(file_path)

all_text_fragments = extract_text(text, keyword, end_keyword)
read_through_text(all_text_fragments,formulas,formula_keyword,express_variable, variable_values, formula_values)


# In[ ]:





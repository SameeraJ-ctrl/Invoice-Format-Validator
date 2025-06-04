from flask import Flask, render_template, request, redirect, url_for, flash, session
import os
import json
import pandas as pd
from datetime import datetime
from werkzeug.utils import secure_filename

# Set Upload Folder to Project Directory
UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads")
#This is the only allowed extentions (only '.csv' files)
ALLOWED_EXTENSIONS = {'csv'}

#Initializes the flask application
#Defines a directory for static files
app = Flask(__name__, static_folder="static")
app.secret_key = 'supersecretkey'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure uploads folder exists 
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    #If the uploads folder doesnt exist it creates the directory 
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Load user credentials    
def load_users():
    #reads the users.json file and returns the usersnames and the password
    with open('users.json') as f:
        return json.load(f)

# Check file extension if it is only a .csv file 
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Load program rules as per the program ID 
def load_program_rules():
    with open('program_rules.json') as f:
        return json.load(f)

# Column-wise CSV validation
#Retrives the validation rules for the program ID     
def validate_csv_columnwise(filepath, program_id):
    errors = []
    rules = load_program_rules().get(program_id)

    #If the program ID doesnt exist it will return a not found error 
    if not rules:
        return [f"Program ID '{program_id}' not found."], 0, 0
    #retrives the expected colm def from the rules dictionary which is loaded from the program_rules.json file
    expected_columns = rules['columns']

    try:
        #Reads the CSV file as a pandas dataframe + converts the data to string format
        df = pd.read_csv(filepath, dtype=str)
        #replaces any missing valus with empty strings ""
        df.fillna("", inplace=True)
        
        
        #Goes over expected colm defs in validation rules
        for rule in expected_columns:
            pos = rule['position']
            field_name = rule['name']
            expected_type = rule['type']
            required = rule.get('required', False)
            date_format = rule.get('format')

            #Checks if the required columns exist + if missing adds an error 
            if pos >= len(df.columns):
                errors.append(f"Col {pos + 1}: Missing column for '{field_name}'")
                continue

            #Iterates through each value in the colm
            col_values = df.iloc[:, pos]
            for i, val in enumerate(col_values, start=1):
                #Strips whitespaces and checks for req vals 
                val = str(val).strip()
                if val == "":
                    if required:
                        errors.append(f"Col {pos + 1}: Missing required value in row {i}")
                    continue
                #If the expected val is a float it convts to float if needed
                if expected_type == "float":
                    try:
                       float(val)
                    #If the conv fails an error is recorded
                    except ValueError:
                        errors.append(f"Col {pos + 1}: Invalid float value '{val}' in row {i}")
                #Defines possible date formats     
                elif expected_type == "date":
                    format_mapping = {
                        "yyyymmdd": "%Y%m%d",
                        "ddmmyyyy": "%d%m%Y",
                        "mmddyyyy": "%m%d%Y",
                        "yyyy-mm-dd": "%Y-%m-%d",
                        "dd-mm-yyyy": "%d-%m-%Y"
                    }
                    #Matches the user specified datetime format (format in the program_rules.json file) to the python's datetime format 
                    python_date_format = format_mapping.get(date_format.lower())

                    #Tries to convt dates if the format is wrong it recs an error 
                    if not python_date_format:
                        errors.append(f"Col {pos + 1}: Unknown date format '{date_format}' in rules.")
                        continue

                    try:
                        datetime.strptime(val, python_date_format)
                    except ValueError:
                        errors.append(f"Col {pos + 1}: Date format incorrect '{val}' in row {i}. Expected format: {date_format}")
                #Checks if vals are properly formatted as strings 
                elif expected_type == "string":
                    if not isinstance(val, str):
                        errors.append(f"Col {pos + 1}: Value should be a string in row {i}")

        # Return error list + No. of rows and colms checked
        return errors, len(df), len(df.columns)

    except Exception as e:
        return [f"Validation error: {str(e)}"], 0, 0

# Login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    #takes care of login requests + retrives data from the login form
    if request.method == 'POST':
        users = load_users()
        username = request.form['username']
        password = request.form['password']
        #checks if the username and the password entered matches what is in the user.json
        if username in users and users[username] == password:
            session['username'] = username
            return redirect(url_for('index'))
        #If the username and psswd doesnt match returns an error
        else:
            error = 'Invalid username or password'
    #You dont need to define the specific path cause it will auto check the folder titled templates for this file. 4
    #If the file is saved else where the full path has to be put here 
    return render_template('login.html', error=error)

#Logout - clears the sessions and redirects to login.htm 
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

# Main upload + validation page
@app.route('/', methods=['GET', 'POST'])
def index():
    #To ensure only logged in users can access the main page
    if 'username' not in session:
        flash('Incorrect Login')
        return redirect(url_for('login'))

    success = None
    message = ""
    errors = []
    rows_checked = 0
    cols_checked = 0

    if request.method == 'POST':
        program_id = request.form.get('program_id')

        #Checks if the file was uploaded 
        if 'invoice_file' not in request.files:
            flash('No file part')
            return redirect(request.url)

        file = request.files['invoice_file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)


        #Secures the file name and saves the file tp the uploads folder 
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

            #All the conditions to what is happening to the file based on errors and success 
            try:
                file.save(filepath)
                errors, rows_checked, cols_checked = validate_csv_columnwise(filepath, program_id)
                if errors:
                    success = False
                    message = f"File validation completed with errors. Checked {rows_checked} rows and {cols_checked} columns."
                else:
                    success = True
                    message = f"File validated successfully with no errors. Checked {rows_checked} rows and {cols_checked} columns."
            except PermissionError:
                success = False
                message = "Flask doesn't have permission to save files. Try changing folder permissions or running Flask as administrator."
            except Exception as e:
                success = False
                message = f"An unexpected error occurred: {str(e)}"

    return render_template('index.html', success=success, message=message, errors=errors)

# Run the application
if __name__ == '__main__':
    #run in debug mode 
    app.run(debug=True)

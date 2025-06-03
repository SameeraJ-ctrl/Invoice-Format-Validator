from flask import Flask, render_template, request, redirect, url_for, flash, session
import os
import json
import pandas as pd
from datetime import datetime
from werkzeug.utils import secure_filename

# Set Upload Folder to Project Directory Instead of C:/ (Avoids Permission Errors)
UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads")
ALLOWED_EXTENSIONS = {'csv'}

app = Flask(__name__, static_folder="static")
app.secret_key = 'supersecretkey'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the uploads folder exists and has correct permissions
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Load user credentials    
def load_users():
    with open('users.json') as f:
        #Converts JSON data into a python dictionary
        return json.load(f)

# Check file extension
def allowed_file(filename):
    #Splits the file name at the '.' and checks if it is a '.csv' 
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Load rules per program
def load_program_rules():
    with open('program_rules.json') as f:
        #Returns the rules as a python dictionary
        return json.load(f)

# Column-wise CSV validation
def validate_csv_columnwise(filepath, program_id):
    #initializes an empty list  to store the validation issues 
    errors = []
    #fetches the rules of the specific program ID
    rules = load_program_rules().get(program_id)

    #Checks if the .json file has rules for this program ID and returns an error if there isnt one.
    if not rules:
        return [f"Program ID '{program_id}' not found."]

    #Extracts the expected colms for validation
    expected_columns = rules['columns']

    try:
        #Reads the CSV fileee using pandas and replaces missing values with empty strings
        df = pd.read_csv(filepath, dtype=str)
        df.fillna("", inplace=True)

        #Goes over each expected colms and extracts the validation rules
        for rule in expected_columns:
            pos = rule['position']
            field_name = rule['name']
            expected_type = rule['type']
            required = rule.get('required', False)
            date_format = rule.get('format')

            #checks if the colm exists. If not adds an error message
            if pos >= len(df.columns):
                errors.append(f"Col {pos + 1}: Missing column for '{field_name}'")
                continue

            #Goes over all col values checks if the required fields are missing 
            col_values = df.iloc[:, pos]
            for i, val in enumerate(col_values, start=1):
                if str(val).strip() == "":
                    if required:
                        errors.append(f"Col {pos + 1}: Missing required value in row {i}")
                    continue

                #Ensures its a float 
                val = str(val).strip()
                if expected_type == "float":
                    try:
                        float(val)
                    except ValueError:
                        errors.append(f"Col {pos + 1}: Invalid float value '{val}' in row {i}")
                #Checks if its actually a date and checks the fotmat of the date    
                elif expected_type == "date":
                    try:
                        datetime.strptime(val, "%Y%m%d")
                    except ValueError:
                        errors.append(f"Col {pos + 1}: Date format incorrect '{val}' in row {i}")
                #Checks for a string 
                elif expected_type == "string":
                    if not isinstance(val, str):
                        errors.append(f"Col {pos + 1}: Value should be a string in row {i}")

    except Exception as e:
        errors.append(f"Validation error: {str(e)}")

    return errors

# Login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    #initializes error variable for an invalid login attempt 
    error = None
    if request.method == 'POST':
        users = load_users()
        username = request.form['username']
        password = request.form['password']
        #Checks if username and all really does exist 
        if username in users and users[username] == password:
            session['username'] = username
            return redirect(url_for('index'))
        else:
            error = 'Invalid username or password'
    return render_template('login.html', error=error)

# Logout 
#Ends this user's session and redirects to the login page 
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

# Main upload + validation page
@app.route('/', methods=['GET', 'POST'])
def index():
    if 'username' not in session:
        flash('Incorrect Login')
        return redirect(url_for('login'))

    message = None
    if request.method == 'POST':
        program_id = request.form.get('program_id')
        #Checks if thee file has been uploaded 
        if 'invoice_file' not in request.files:
            flash('No file part')
            return redirect(request.url)

        #Makes sure a file is actually selected 
        file = request.files['invoice_file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)

        #Securely saves the file to the folder 
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            try:
                #call the validate function and checks all colms and joins all the errors in the same variable 
                file.save(filepath)
                errors = validate_csv_columnwise(filepath, program_id)
                message = "\n".join(errors) if errors else "File validated successfully with no errors."
            except PermissionError:
                message = "Error: Flask doesn't have permission to save files. Try changing folder permissions or running Flask as administrator."
            except Exception as e:
                message = f"An unexpected error occurred: {str(e)}"

    return render_template('index.html', message=message)

#TO RUN THE APPLICATION 
if __name__ == '__main__':
    app.run(debug=True)

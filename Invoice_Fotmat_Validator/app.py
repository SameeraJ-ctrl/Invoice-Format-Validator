from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory
import os
import json
import pandas as pd
from datetime import datetime
from werkzeug.utils import secure_filename

#Creates a directory to the upload folder
UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads")
#defines where the error reports will be stored 
ERROR_REPORT_FOLDER = os.path.join(os.getcwd(), "error_reports")

#stores the allowed extention (only .csv files)
ALLOWED_EXTENSIONS = {'csv'}

#initializes the flask application and tells where the stlye files are 
app = Flask(__name__, static_folder="static")
app.secret_key = 'supersecretkey'
#creates directories to the uploads and error report folders if they dont already exist  
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['ERROR_REPORT_FOLDER'] = ERROR_REPORT_FOLDER
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['ERROR_REPORT_FOLDER'], exist_ok=True)

#Loads the users.json file with all the user credentials 
def load_users():
    with open('users.json') as f:
        return json.load(f)
#Functions that checks if the uploaded file is of the type we require. That is .csv only 
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

#loads the program_rules.json file with all the rules for the program ID 
def load_program_rules():
    with open('program_rules.json') as f:
        return json.load(f)
#validates the .csv file columnwise 
def validate_csv_columnwise(filepath, program_id):
    errors = []
    rules = load_program_rules().get(program_id)
    #If the program ID isnt therer in the program_rules.json file then returns "Wrong Program ID error"
    if not rules:
        return [f"Program ID '{program_id}' not found."], 0, 0
    expected_columns = rules['columns']
    #reads the .csv file using the pandas dataframe 
    try:
        df = pd.read_csv(filepath, dtype=str)
        #if there is nothing in the space it replaces it with a "" (empty string)
        df.fillna("", inplace=True)
        
        #extracts all field data
        for rule in expected_columns:
            pos = rule['position']
            field_name = rule['name']
            expected_type = rule['type']
            required = rule.get('required', False)
            date_format = rule.get('format')

            #checks if the required column does exist 
            if pos >= len(df.columns):
                errors.append(f"Col {pos + 1}: Missing column for '{field_name}'")
                continue
             #iterates through values and and strips all the white spaces 
            col_values = df.iloc[:, pos]
            for i, val in enumerate(col_values, start=1):
                val = str(val).strip()
                if val == "":
                    if required:
                        errors.append(f"Col {pos + 1}: Missing required value in row {i}")
                    continue

                #checks for it to be float. If it isnt it tries to convert. If it fails to convert then it throws and error
                if expected_type == "float":
                    try:
                        float(val)
                    except ValueError:
                        errors.append(f"Col {pos + 1}: Invalid float value '{val}' in row {i}")

                #checks it is a date
                elif expected_type == "date":
                   #maps all the dates from the .json format to its coressponding python format 
                    format_mapping = {
                        "yyyymmdd": "%Y%m%d",
                        "ddmmyyyy": "%d%m%Y",
                        "mmddyyyy": "%m%d%Y",
                        "yyyy-mm-dd": "%Y-%m-%d",
                        "dd-mm-yyyy": "%d-%m-%Y"
                    }
                    #stores the correct pythoon format for that program ID 
                    python_date_format = format_mapping.get(date_format.lower())
                    #catches the error if it isnt in the date formats 
                    if not python_date_format:
                        errors.append(f"Col {pos + 1}: Unknown date format '{date_format}' in rules.")
                        continue
                    try:
                        datetime.strptime(val, python_date_format)
                    except ValueError:
                        errors.append(f"Col {pos + 1}: Date format incorrect '{val}' in row {i}. Expected format: {date_format}")
                
                #checks the string and adds 
                elif expected_type == "string":
                    if not isinstance(val, str):
                        errors.append(f"Col {pos + 1}: Value should be a string in row {i}")

        return errors, len(df), len(df.columns)

    except Exception as e:
        return [f"Validation error: {str(e)}"], 0, 0

#Stores the validation errors in a .csv file 
def export_error_report(errors, original_filename):
    base_name = os.path.splitext(secure_filename(original_filename))[0]
    report_filename = f"ErrorReport_{base_name}.csv"
    filepath = os.path.join(ERROR_REPORT_FOLDER, report_filename)

    #converts errors into a dataframe and saves as a .csv file 
    df = pd.DataFrame(errors, columns=["Error"])
    df.to_csv(filepath, index=False)
    return report_filename

#Handles the login authentication 
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        users = load_users()
        username = request.form['username']
        password = request.form['password']
        if username in users and users[username] == password:
            session['username'] = username
            return redirect(url_for('index'))
        else:
            error = 'Invalid username or password'
    return render_template('login.html', error=error)

#Handles the logout and redirects to the login page
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/', methods=['GET', 'POST'])
def index():
    if 'username' not in session:
        flash('Incorrect Login')
        return redirect(url_for('login'))

    success = None
    message = ""
    errors = []
    rows_checked = 0
    cols_checked = 0
    error_report_filename = None

    if request.method == 'POST':
        program_id = request.form.get('program_id')

        if 'invoice_file' not in request.files:
            flash('No file part')
            return redirect(request.url)

        file = request.files['invoice_file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

            try:
                file.save(filepath)
                errors, rows_checked, cols_checked = validate_csv_columnwise(filepath, program_id)
                if errors:
                    success = False
                    message = f"File validation completed with errors. Checked {rows_checked} rows and {cols_checked} columns."
                    error_report_filename = export_error_report(errors, filename)
                else:
                    success = True
                    message = f"File validated successfully with no errors. Checked {rows_checked} rows and {cols_checked} columns."
            except PermissionError:
                success = False
                message = "Flask doesn't have permission to save files."
            except Exception as e:
                success = False
                message = f"An unexpected error occurred: {str(e)}"

    return render_template('index.html',
                           success=success,
                           message=message,
                           errors=errors,
                           error_report_filename=error_report_filename)

#handles file uploads and validation 
@app.route('/download/<filename>')
def download_report(filename):
    return send_from_directory(app.config['ERROR_REPORT_FOLDER'], filename, as_attachment=True)

#runs the app 
if __name__ == '__main__':
    app.run(debug=True)

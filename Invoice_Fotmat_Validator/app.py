
from flask import Flask, render_template, request, redirect, url_for, flash, session
import os
import json
from werkzeug.utils import secure_filename



UPLOAD_FOLDER = 'uploads' #Defines the directory where uploaded files will be stored. 
ALLOWED_EXTENSIONS = {'csv'} #Specifies that only '.csv' files are allowed. 


app = Flask(__name__)
app.secret_key = 'supersecretkey' #Flashing messages
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER #Set up Upload file directory. 

# Load user credentials
def load_users():
    with open('users.json') as f:
        return json.load(f)

#Function that checks if the inputted file is an '.csv' file
#It first splits the file's name at the first '.' and then checks for it to the csv
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None  # Initialize error message variable
    if request.method == 'POST':
        users = load_users()
        username = request.form['username']
        password = request.form['password']
        if username in users and users[username] == password:
            session['username'] = username
            return redirect(url_for('index'))
        else:
            error = 'Invalid username or password'  # Set error message
    return render_template('login.html', error=error)  # Pass error to template


# Logout
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))


#Defines the main route that listens for both GET and POST requests 
@app.route('/', methods=['GET', 'POST'])
def index():
    if 'username' not in session:
        flash('Incorrect Login')    
        return redirect(url_for('login'))
    
    # When a POST request is received, it extracts 'program_id' from the form submission. 
    if request.method == 'POST':
        
        program_id = request.form['program_id']
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url) #redirects if there is no file. 
        
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            # Placeholder: you will add validation here later
            return redirect(url_for('index'))
        
    #gives us the index template if its just a GET request.	
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)

# Invoice Format Validator

## Overview

**Invoice Format Validator** is a web-based application built with Flask that enables users to upload invoice CSV files and validate them against program-specific rules. These rules define expected columns, data types, date formats, and required fields for each Program ID. The tool helps ensure that uploaded invoice data is accurate, well-structured, and compliant with predefined formats.

This application is designed to streamline billing validation and reduce manual verification by enforcing strict data quality checks.

---

## Features

* Secure login system for authorized users
* Upload and validate multiple invoice CSV files
* Program-specific validation based on predefined rules
* Validation checks include:

  * Column presence and order
  * Required fields
  * Data type conformity (e.g., string, float, date)
  * Custom date format matching (e.g., `yyyy-mm-dd`, `ddmmyyyy`)
* Summary of rows and columns checked
* Downloadable error report for problematic records

---

## Project Structure

```
invoice-format-validator/
├── app.py                   # Main Flask application logic
├── users.json               # Stores valid usernames and passwords
├── program_rules.json       # Defines validation rules per Program ID
│
├── templates/
│   ├── index.html           # Upload interface
│   └── login.html           # User login form
│
├── static/
│   └── style.css            # CSS for frontend styling (optional)
│
├── uploads/                 # Stores uploaded invoice files temporarily
├── error_reports/           # Stores generated error CSV reports
│
├── README.md                # Project documentation
```

---

## Technologies Used

* **Python 3.x**
* **Flask** – Web framework
* **pandas** – Data processing and validation
* **HTML/CSS** – Frontend
* **JSON** – Configuration storage for rules and users

---

## Installation

1. Clone the repository:

   ```
   git clone https://github.com/your-username/invoice-format-validator.git
   cd invoice-format-validator
   ```

2. Install the required Python packages:

   ```
   pip install flask pandas
   ```

3. Make sure the following folders exist (create if missing):

   ```
   mkdir uploads error_reports
   ```

4. Run the application:

   ```
   python app.py
   ```

5. Access it in your browser at:

   ```
   http://localhost:5000
   ```

---

## Validation Rules Format (`program_rules.json`)

Each program is assigned a set of rules. For example:

```json
{
  "Program123": {
    "columns": [
      {"name": "Invoice ID", "type": "string", "required": true},
      {"name": "Amount", "type": "float", "required": true},
      {"name": "Date", "type": "date", "format": "yyyy-mm-dd", "required": true}
    ]
  }
}
```

---

## Usage Flow

1. User logs in using credentials from `users.json`.
2. Uploads a CSV file.
3. Selects the applicable Program ID.
4. The app validates the file against that program's rules.
5. Results are displayed:

   * If valid, the summary is shown.
   * If invalid, a downloadable CSV error report is provided.

---

## Example User Entry (`users.json`)

```json
{
  "admin": "securepassword123",
  "auditor": "reviewonly"
}

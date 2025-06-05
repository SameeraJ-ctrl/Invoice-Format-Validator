# 📄 Invoice Format Validator

A web-based Flask application that allows team members to upload invoice CSV files and validate them based on predefined program-specific rules (column structure, data types, date formats, etc.). It helps ensure billing data is accurate, well-formatted, and compliant with expectations.

---

## 🚀 Features

- 🔐 Secure login for users
- 📤 Upload and validate CSV invoice files
- ✅ Checks:
  - Column presence and correct position
  - Data types (string, float, date)
  - Required fields
  - Custom date formats (e.g., `yyyy-mm-dd`, `ddmmyyyy`)
- 📊 Shows how many rows and columns were checked
- 📝 Generates downloadable error report if issues are found

---
## 📁 Project Structure

```plaintext
invoice-format-validator/
├── app.py                   # Main Flask application logic
├── users.json               # JSON file storing valid username-password pairs
├── program_rules.json       # JSON file defining validation rules per Program ID
│
├── templates/               # HTML templates for frontend
│   ├── index.html           # Main upload page
│   └── login.html           # Login page
│
├── static/                  # Static files (CSS, JS, images)
│   └── style.css            # Optional styling
│
├── uploads/                 # Folder for storing uploaded invoice CSVs temporarily
├── error_reports/           # Folder for storing generated error report CSVs
│
├── README.md                # Project documentation (this file)


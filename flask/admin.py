from flask import Flask, render_template, request, redirect, url_for
import mysql.connector
from werkzeug.security import check_password_hash

app = Flask(__name__, template_folder='temp')  # Change 'temp' to 'templates'

# Database connection function
def get_db_connection():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='root123',
        database='jms'
    )
# Route for the home page after successful login
@app.route('/')
def first():
    """Render the home page after successful login"""
    return render_template('first.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        admin_id = request.form['admin_id']
        password = request.form['password']

        # Connect to DB
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get the admin details
        query = "SELECT * FROM admin WHERE admin_id = %s"
        cursor.execute(query, (admin_id,))
        result = cursor.fetchone()

        cursor.close()
        conn.close()

        if result and password == result[2]:  # Direct comparison
            return redirect(url_for('index'))
        else:
            return "Invalid login credentials", 403

    # For GET requests, render the login form
    return render_template('adminlog.html')

@app.route('/index')
def index():
    return render_template('index.html')

# Route to add a journal
@app.route('/addjournal', methods=['GET', 'POST'])
def add_journal():
    if request.method == 'POST':
        issn = request.form['issn']
        jname = request.form['jname']
        payment = request.form['payment']
        fee = request.form['fee']
        frequency = request.form['frequency']
        scopus_index = request.form['scopus_index']
        wos_index = request.form['wos_index']
        quality = request.form['quality']
        country = request.form['country']
        impact_factor = request.form['impact_factor']

        try:
            # Connect to the database
            conn = get_db_connection()
            cursor = conn.cursor()

            # Insert query to add journal details
            query = '''
                INSERT INTO jl (issn, jname, payment, fee, frequency, 
                                scopus_index, wos_index, quality, country, impact_factor)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            '''
            values = (issn, jname, payment, fee, frequency, 
                      scopus_index, wos_index, quality, country, impact_factor)

            cursor.execute(query, values)
            conn.commit()

            cursor.close()
            conn.close()

            return redirect(url_for('success'))  # Redirect to a success page

        except Exception as e:
            return f"Error occurred: {e}"

    return render_template('addj.html')  # Your HTML form to add a journal

# Route for success message after journal is added
@app.route('/success')
def success():
    return '<h1>Journal Added Successfully!</h1>'

# Route to delete a journal
@app.route('/delete', methods=['GET', 'POST'])
def delete_journal():
    if request.method == 'POST':
        issn = request.form['issn']

        try:
            # Connect to the database
            conn = get_db_connection()
            cursor = conn.cursor()

            # Prepare and execute the DELETE query
            query = "DELETE FROM jl WHERE issn = %s"
            cursor.execute(query, (issn,))

            conn.commit()

            if cursor.rowcount > 0:
                message = f"Journal with ISSN {issn} has been deleted successfully."
            else:
                message = f"No journal found with ISSN {issn}."

            cursor.close()
            conn.close()

            return render_template('result.html', message=message)

        except Exception as e:
            return f"Error occurred: {e}"

    return render_template('delete.html')  # Show delete journal form

# Route to add a publisher
@app.route('/add_publisher', methods=['GET', 'POST'])
def add_publisher():
    if request.method == 'POST':
        issn = request.form['issn']
        journal_name = request.form['journal_name']
        publisher_name = request.form['publisher_name']
        email = request.form['email']
        contact_number = request.form['contact_number']
        office_address = request.form['office_address']

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Insert query to add publisher details
            query = """
                INSERT INTO publisher (issn, journal_name, publisher_name, email, contact_number, office_address)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            values = (issn, journal_name, publisher_name, email, contact_number, office_address)

            cursor.execute(query, values)
            conn.commit()

            cursor.close()
            conn.close()

            return redirect(url_for('success'))

        except Exception as e:
            return f"Error occurred: {e}"

    return render_template('addp.html')  # Form to add a publisher

# Route to add a paper
@app.route('/add_paper', methods=['GET', 'POST'])
def add_paper():
    if request.method == 'POST':
        paper_title = request.form['paper_title']
        publisher = request.form['publisher']
        issn = request.form.get('issn') or None
        published_year = request.form['published_year']
        volume = request.form.get('volume') or None
        issue = request.form.get('issue') or None
        journal_name = request.form.get('journal_name') or None

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Insert query to add paper details
            query = '''
                INSERT INTO published_papers (paper_title, publisher, issn, published_year, volume, issue, journal_name)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            '''
            values = (paper_title, publisher, issn, published_year, volume, issue, journal_name)

            cursor.execute(query, values)
            conn.commit()

            cursor.close()
            conn.close()

            return redirect(url_for('success'))

        except Exception as e:
            return f"Error occurred: {e}"

    return render_template('addpc.html')  # Form to add a paper

# Route to delete a paper
@app.route('/delete_paper', methods=['GET', 'POST'])
def delete_paper():
    if request.method == 'POST':
        pid = request.form['pid']

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Delete paper by pid (this will cascade delete authors if cascade is enabled)
            cursor.execute("DELETE FROM published_papers WHERE p_id = %s", (pid,))
            conn.commit()

            message = f"Paper with PID {pid} has been deleted successfully." if cursor.rowcount > 0 else "No paper found with that PID."

            cursor.close()
            conn.close()

            return render_template('result.html', message=message)

        except Exception as e:
            return f"Error occurred: {e}"

    return render_template('deletep.html')  # Form to delete a paper

# Route to handle logout and show the login page again
@app.route('/logout')
def logout():
    return render_template('adminlog.html')  # Show login page again

# Starting the Flask app
if __name__ == "__main__":
    app.run(debug=True)

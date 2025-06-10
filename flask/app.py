from flask import Flask, render_template, jsonify, request, redirect, url_for, session
import mysql.connector
import random
from werkzeug.security import generate_password_hash, check_password_hash
import spacy
from mysql.connector import Error
import re


app = Flask(__name__, template_folder='template')  # Ensure correct template folder name
nlp = spacy.load("en_core_web_sm")
app.secret_key = '23456789@23ertyujhgtfdvbgt!@3677HJKKI'  # Secret key for session management

def get_journals_by_quality(user_input):
    # Extract quality tier from the user input using a regular expression
    match = re.search(r"(Q[1-4])", user_input, re.IGNORECASE)

    if match:
        quality_tier = match.group(1).upper()  # Ensure it is uppercase (Q1, Q2, Q3, Q4)
        
        # Query the database for the total number of journals in the specified quality tier
        conn = get_db_connection()
        if conn is None:
            response_text = "Sorry, there was an error connecting to the database."
        else:
            try:
                cursor = conn.cursor()

                # Dynamically build the query to count journals based on the quality tier
                query = f"SELECT COUNT(*) FROM jl WHERE quality = '{quality_tier}'"
                cursor.execute(query)
                result = cursor.fetchone()
                if result:
                    journals_count = result[0]
                    response_text = f"The total number of {quality_tier} journals is {journals_count}."
                else:
                    response_text = f"No {quality_tier} journals found in the database."

                cursor.close()
                conn.close()
            except Error as e:
                response_text = f"Error while querying the database: {e}"
    else:
        response_text = "Could not detect a valid quality tier (Q1, Q2, Q3, or Q4) in your input."

    return response_text

def get_average_impact_factor_by_quality(user_input):
    # Extract quality tier from the user input using a regular expression
    match = re.search(r"(Q[1-4])", user_input, re.IGNORECASE)

    if match:
        quality_tier = match.group(1).upper()  # Ensure it is uppercase (Q1, Q2, Q3, Q4)
        
        # Query the database for the average impact factor of the specified quality tier
        conn = get_db_connection()
        if conn is None:
            response_text = "Sorry, there was an error connecting to the database."
        else:
            try:
                cursor = conn.cursor()

                # Dynamically build the query to calculate the average impact factor based on the quality tier
                query = f"SELECT AVG(impact_factor) FROM jl WHERE quality = '{quality_tier}'"
                cursor.execute(query)
                result = cursor.fetchone()
                if result and result[0] is not None:
                    avg_impact_factor = result[0]
                    response_text = f"The average impact factor of {quality_tier} journals is {avg_impact_factor:.2f}."
                else:
                    response_text = f"No {quality_tier} journals found in the database with an impact factor."

                cursor.close()
                conn.close()
            except Error as e:
                response_text = f"Error while querying the database: {e}"
    else:
        response_text = "Could not detect a valid quality tier (Q1, Q2, Q3, or Q4) in your input."

    return response_text


# Create a global connection to the database
def get_db_connection():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='root123',
        database='jms'
    )

# Get the logged-in user's ID from the session
def get_logged_in_user_id():
    return session.get('user_id')
def get_logged_in_username():
    return session.get('username')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        try:
            con = get_db_connection()
            cursor = con.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE username = %s;", (username,))
            user = cursor.fetchone()

            cursor.close()
            con.close()

            if user and check_password_hash(user['password'], password):
                # User has successfully logged in
                session['user_id'] = user['id']
                session['username'] = user['username']  # Store the username in session

                # Print the user ID and username stored in the session for debugging
                print(f"User ID stored in session: {session.get('user_id')}")
                print(f"Username stored in session: {session.get('username')}")

                return redirect(url_for('dashboard'))
            else:
                return "Invalid credentials, please try again!"
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    return render_template('login.html')




@app.route('/mainpage')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    username = session.get('username')  # Get the username from session
    return render_template('mainpage.html', username=username)

@app.route('/profile')
def profile():
    user_id = get_logged_in_user_id()

    if user_id is None:
        return redirect(url_for('login'))  # Redirect to login if user is not logged in

    # Retrieve user data from the database
    try:
        con = get_db_connection()
        cursor = con.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE id = %s;", (user_id,))
        user = cursor.fetchone()

        cursor.close()
        con.close()

        # Check if the profile is completed
        profile_completed = session.get('profile_completed', False)

        return render_template('profile.html', user=user, profile_completed=profile_completed)  # Pass the flag to template
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    
@app.route('/complete_profile', methods=['GET', 'POST'])
def complete_profile():
    user_id = session.get('user_id')  # Ensure the user is logged in
    if not user_id:
        return redirect('/login')  # Ensure the user is logged in

    if request.method == 'POST':
        # Get form data
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        profession = request.form.get('profession')
        district = request.form.get('district')
        state = request.form.get('state')
        country = request.form.get('country')

        try:
            con = get_db_connection()
            cursor = con.cursor()

            # Update user profile
            cursor.execute(''' 
                UPDATE users
                SET first_name = %s, last_name = %s, profession = %s,
                    district = %s, state = %s, country = %s
                WHERE id = %s  # Use `id` here, which is the correct column name
            ''', (first_name, last_name, profession, district, state, country, user_id))

            con.commit()  # Commit changes to the database
            cursor.close()
            con.close()

            # Set a session variable indicating the profile is complete
            session['profile_completed'] = True
            return redirect('/profile')  # Redirect to the profile page after successful update

        except Exception as e:
            print(f"Error updating profile: {e}")
            return "An error occurred while updating your profile."

    # Render the profile completion form if GET request
    return render_template('complete.html')









@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        # Get data from the form
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        email = request.form['email']  # Example additional field

        # Check if passwords match
        if password != confirm_password:
            return "Passwords do not match, please try again!"

        # Hash the password before saving it in the database
        hashed_password = generate_password_hash(password)

        # Insert the new user into the database
        try:
            con = get_db_connection()
            cursor = con.cursor()

            # Check if the username already exists
            cursor.execute("SELECT * FROM users WHERE username = %s;", (username,))
            existing_user = cursor.fetchone()
            if existing_user:
                return "Username already exists. Please choose another one."

            # Insert new user into the database
            query = """
                INSERT INTO users (username, password, email) 
                VALUES (%s, %s, %s);
            """
            cursor.execute(query, (username, hashed_password, email))
            con.commit()  # Save the changes
            cursor.close()
            con.close()

            return redirect(url_for('login'))  # Redirect to the login page after successful signup
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    return render_template('signup.html')


@app.route('/all_journals')
def all_journals():
    try:
        con = get_db_connection()
        cursor = con.cursor(dictionary=True)
        cursor.execute('SELECT * FROM jl')
        journals = cursor.fetchall()

        cursor.close()
        con.close()

        user_id = get_logged_in_user_id()
        username=get_logged_in_username()
        if user_id is None:
            return redirect(url_for('login'))  # Redirect to login if user is not logged in
        
        return render_template('alljlist.html', journals=journals, user_id=user_id,username=username)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


from flask import session, jsonify, request

@app.route('/bookmark', methods=['POST'])
def bookmark():
    try:
        # Get the user_id from the session
        user_id = session.get('user_id')  # Assuming the user is logged in and has a 'user_id' in the session
        username = session.get('username')  # Retrieve the username from the session
        
        if not user_id or not username:
            return jsonify({'error': 'User not logged in'}), 403

        # Get the data sent from the client (ISSN and journal_name)
        data = request.get_json()
        if not data or not data.get('issn') or not data.get('journal_name'):
            return jsonify({'error': 'Invalid data received'}), 400
        
        issn = data['issn']
        journal_name = data['journal_name']

        # Debugging print to check the received data
        print(f"Received bookmark data: {data}")
        
        # Connect to the database
        con = get_db_connection()
        cursor = con.cursor()

        # Insert the bookmark into the database with the correct user_id and username
        cursor.execute('''
            INSERT INTO bookmark (user_id, username, issn, journal_name)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE user_id=user_id
        ''', (user_id, username, issn, journal_name))  # Using the username from the session
        
        con.commit()  # Commit the changes to the database
        cursor.close()
        con.close()

        return jsonify({'message': 'Bookmark added successfully!'}), 200
    except Exception as e:
        # If an error occurs, return a response with the error message
        print(f"Error in bookmark: {e}")  # Print error to the console for debugging
        return jsonify({'error': str(e)}), 500




@app.route('/selectjournal', methods=['GET', 'POST'])
def selectjournal():
    username=get_logged_in_username()
    if request.method == 'POST':  # If form is submitted
        quality = request.form.get('quality')
        payment = request.form.get('payment')
        scopus_index = request.form.get('scopus_index')
        wos_index = request.form.get('wos_index')

        try:
            con = get_db_connection()  # Reuse the database connection
            cursor = con.cursor(dictionary=True)

            query = "SELECT * FROM jl WHERE quality = %s AND payment = %s AND scopus_index=%s AND wos_index=%s;"
            cursor.execute(query, (quality, payment,scopus_index,wos_index))
            results = cursor.fetchall()
            username=get_logged_in_username()

            cursor.close()
            con.close()

            if not results:
                return render_template('filtered.html', message="No journals found with the selected quality.")
            
            return render_template('filtered.html', journals=results,username=username)

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    return render_template('select.html',username=username)


@app.route('/publishers')
def show_publishers():
    try:
        con = get_db_connection()
        cursor = con.cursor(dictionary=True)
        cursor.execute("SELECT * FROM publisher")
        data = cursor.fetchall()
        username=get_logged_in_username()
        cursor.close()
        con.close()
        return render_template("publisher.html", publishers=data,username=username)
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/chatbot', methods=['GET', 'POST'])
def chatbot():
    response_text = None

    if request.method == 'POST':
        user_input = request.form['message'].strip().lower()

        # Hardcoded responses for specific journal-related questions
        if "hello" in user_input:
            response_text = "Hi, how can I help you?"
        
        elif "what is impact factor" in user_input:
            response_text = "The impact factor is a measure reflecting the yearly average number of citations to articles published in the last two years in a particular journal."
        
        elif "quality of journal" in user_input:
            response_text = "The quality of a journal is typically measured by its impact factor, reputation, and the rigor of its peer review process."
        
        elif "scopus" in user_input:
            response_text = "Scopus is a comprehensive abstract and citation database of peer-reviewed literature, including journals, conference proceedings, and patents."
        
        elif "wos index" in user_input or "web of science" in user_input:
            response_text = "The Web of Science (WoS) is a research database that indexes high-quality academic journals across multiple disciplines."
        
        elif "total number of" in user_input and any(q in user_input for q in ["q1", "q2", "q3", "q4"]):
            # Use the generalized function to get the journal count based on the quality tier
            response_text = get_journals_by_quality(user_input)
        
        elif "impact factor" in user_input and "average" in user_input:
            # Use the generalized function to get the average impact factor based on the quality tier
            response_text = get_average_impact_factor_by_quality(user_input)

        else:
            response_text = "Sorry, I didn't understand that. Can you please rephrase or ask about a journal topic?"

        return jsonify({"response": response_text})

    return render_template('chatbot.html')


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    return redirect(url_for('index'))


@app.route('/journal/<string:issn>')
def journal_details(issn):
    try:
        con = get_db_connection()
        cursor = con.cursor(dictionary=True)

        # Fetch journal by ISSN
        cursor.execute("SELECT * FROM jl WHERE issn = %s;", (issn,))
        journal = cursor.fetchone()

        # Fetch publisher by ISSN (foreign key relationship)
        cursor.execute("SELECT * FROM publisher WHERE issn = %s;", (issn,))
        publisher = cursor.fetchone()

        cursor.close()
        con.close()

        if not journal:
            return "Journal not found", 404

        username = get_logged_in_username()
        return render_template('details.html', journal=journal, publisher=publisher, username=username)

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/bookmark.html')
def view_bookmarks():
    user_id = session.get('user_id')
    username = session.get('username')

    if not user_id:
        return redirect(url_for('login'))

    try:
        con = get_db_connection()
        cursor = con.cursor(dictionary=True)
        cursor.execute("SELECT * FROM bookmark WHERE user_id = %s", (user_id,))
        bookmarks = cursor.fetchall()

        cursor.close()
        con.close()

        return render_template('bookmark.html', bookmarks=bookmarks, username=username)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/update_profile', methods=['GET', 'POST'])
def update_profile():
    user_id = session.get('user_id')  # Get the logged-in user's ID from the session

    if not user_id:
        return redirect(url_for('login'))  # Redirect to login if the user is not logged in

    if request.method == 'POST':
        # Get the updated data from the form
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        profession = request.form.get('profession')
        district = request.form.get('district')
        state = request.form.get('state')
        country = request.form.get('country')

        try:
            con = get_db_connection()  # Connect to the database
            cursor = con.cursor()

            # Update the user profile in the database
            cursor.execute('''
                UPDATE users
                SET first_name = %s, last_name = %s, profession = %s,
                    district = %s, state = %s, country = %s
                WHERE id = %s
            ''', (first_name, last_name, profession, district, state, country, user_id))

            con.commit()  # Commit the changes to the database
            cursor.close()
            con.close()

            return redirect(url_for('profile'))  # Redirect to the profile page after successful update

        except Exception as e:
            print(f"Error updating profile: {e}")
            return jsonify({"error": "An error occurred while updating your profile."}), 500

    # Render the profile update form with the current data (for GET request)
    try:
        con = get_db_connection()  # Connect to the database
        cursor = con.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE id = %s;", (user_id,))
        user = cursor.fetchone()
        cursor.close()
        con.close()

        if not user:
            return jsonify({"error": "User not found."}), 404

        return render_template('update_profile.html', user=user)  # Pass user data to the template for display

    except Exception as e:
        print(f"Error fetching user data: {e}")
        return jsonify({"error": "An error occurred while retrieving your profile."}), 500

@app.route('/delete_bookmark', methods=['POST'])
def delete_bookmark():
    user_id = session.get('user_id')
    issn = request.form.get('issn')

    if not user_id or not issn:
        return '', 400

    try:
        con = get_db_connection()
        cursor = con.cursor()
        cursor.execute("DELETE FROM bookmark WHERE user_id = %s AND issn = %s", (user_id, issn))
        con.commit()
        cursor.close()
        con.close()
        return '', 200
    except Exception as e:
        print("Error deleting bookmark:", e)
        return '', 500

@app.route('/delete_account')
def delete_account():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Use the correct table name (users) and placeholder (%s) for MySQL
        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        conn.commit()

        # Remove the user ID from the session (log them out)
        session.pop('user_id', None)

        return redirect(url_for('index'))  # Redirect to the home page or index page
    except Exception as e:
        conn.rollback()  # Rollback if there is an error
        return f"An error occurred: {e}"
    finally:
        conn.close()  # Always close the connection

@app.route('/papers')
def papers():
    try:
        # Connect to the database
        con = get_db_connection()
        cursor = con.cursor(dictionary=True)
        
        # Fetch all data from the published_papers table
        cursor.execute("SELECT * FROM published_papers")
        papers_data = cursor.fetchall()

        cursor.close()
        con.close()

        # Render the papers.html page and pass the data
        return render_template('papers.html', papers=papers_data)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/paper/<int:pid>/authors')
def see_authors(pid):
    try:
        con = get_db_connection()
        cursor = con.cursor(dictionary=True)

        # Get the paper details
        cursor.execute("SELECT * FROM published_papers WHERE p_id = %s", (pid,))
        paper = cursor.fetchone()
        if not paper:
            return "Paper not found", 404

        # Get all authors for that paper
        cursor.execute("SELECT * FROM author WHERE pid = %s", (pid,))
        authors = cursor.fetchall()

        cursor.close()
        con.close()

        return render_template('author_details.html', paper=paper, authors=authors, username=get_logged_in_username())

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/most")
def most_bookmarked():
    try:
        con = get_db_connection()
        cursor = con.cursor(dictionary=True)

        # Query to get most bookmarked journals and count them
        cursor.execute("""
            SELECT journal_name, issn, COUNT(*) AS bookmark_count
            FROM bookmark
            GROUP BY journal_name, issn
            ORDER BY bookmark_count DESC;
        """)
        journals = cursor.fetchall()

        cursor.close()
        con.close()

        return render_template("most.html", most_bookmarked=journals, username=get_logged_in_username())
    except Exception as e:
        return jsonify({'error': str(e)}), 500








if __name__ == "__main__":
    app.run(debug=True)

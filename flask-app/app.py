from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import os
import csv
from werkzeug.utils import secure_filename

app = Flask(__name__, static_url_path='/static')
app.secret_key = 'abcdkmkfmf'

# Define the folder where user images will be saved
UPLOAD_FOLDER = 'static/user_images'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

class AppData:
    def __init__(self):
        self.credentials_file = "users_and_favorites.csv"
        self.users = {}
        self.user_data = {}
        self.user_info = {}
        self.cities = {
            "istanbul": "istanbul.html",
            "rotorua": "rotorua.html",
            "queenstown": "queenstown.html",
            "dubai": "dubai.html"
        }
        self.load_data()
        
    def load_data(self):
        self.users = {}
        self.user_data = {}
        self.user_info = {}
        if os.path.exists(self.credentials_file):
            with open(self.credentials_file, mode='r', newline='') as file:
                reader = csv.reader(file)
                # Skip the header row
                next(reader, None)
                for row in reader:
                    if len(row) == 7:
                        username, password, email, user_image, sex, age, favorites = row
                        self.users[username] = password
                        self.user_info[username] = {
                            'email': email,
                            'user_image': user_image,
                            'sex': sex,
                            'age': age
                        }
                        self.user_data[username] = favorites.split(',') if favorites else []
                    else:
                        print(f"Ignoring invalid row: {row}")

    def update_csv_file(self):
        with open(self.credentials_file, mode='w', newline='') as file:
            writer = csv.writer(file)
            # Write the header row
            writer.writerow(['username', 'password', 'email', 'user_image', 'sex', 'age', 'favorites'])
            for username, password in self.users.items():
                user_info = self.user_info.get(username, {})
                favorites = ",".join(self.user_data.get(username, []))
                writer.writerow([username, password, user_info.get('email', ''), user_info.get('user_image', ''), user_info.get('sex', ''), user_info.get('age', ''), favorites])

app_data = AppData()

# Check if the uploaded file has an allowed extension
def allowed_file(filename):
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

@app.route('/')
def default():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        sex = request.form['sex']
        age = request.form['age']

        # Handle image upload
        uploaded_image = request.files['user_image']

        if 'user_image' not in request.files:
            error = "Image is required."
        elif uploaded_image.filename == '':
            error = "Image filename is empty."
        elif uploaded_image and allowed_file(uploaded_image.filename):
            filename = secure_filename(uploaded_image.filename)

            # Create the folder if it doesn't exist
            user_folder = os.path.join(app.config['UPLOAD_FOLDER'], username)
            os.makedirs(user_folder, exist_ok=True)

            # Save the uploaded image
            uploaded_image.save(os.path.join(user_folder, filename))
        else:
            error = "Invalid image file format. Allowed formats: png, jpg, jpeg, gif."

        if error is None:
            if username in app_data.users:
                error = "Username already exists. Please choose a different username."
            else:
                app_data.users[username] = password
                app_data.user_data[username] = []
                app_data.user_info[username] = {
                    'email': email,
                    'user_image': filename,
                    'sex': sex,
                    'age': age
                }

                # Check if the CSV file exists
                file_exists = os.path.exists(app_data.credentials_file)

                # Open the CSV file in append mode, creating it if it doesn't exist
                with open(app_data.credentials_file, mode='a', newline='') as file:
                    writer = csv.writer(file)

                    # If the file didn't exist before, write the header row
                    if not file_exists:
                        writer.writerow(['username', 'password', 'email', 'user_image', 'sex', 'age', 'favorites'])

                    # Write the user's data to the CSV file
                    writer.writerow([username, password, email, filename, sex, age, ''])
                return redirect(url_for('login'))

    return render_template('register.html', error=error)

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username in app_data.users:
            stored_password = app_data.users[username]

            if stored_password == password:
                session['username'] = username
                return redirect(url_for('welcome'))

        
        error = "Wrong password. Please try again."

    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/welcome')
def welcome():
    if 'username' in session:
        app_data.load_data()
        user_info = app_data.user_info.get(session['username'], {})
        return render_template('welcome.html', user_info=user_info)
    else:
        return redirect(url_for('login'))




@app.route('/<city_name>')
def city(city_name):
    if city_name in app_data.cities:
        return render_template(app_data.cities[city_name], city_name=city_name)
    else:
        return "City not found."

@app.route('/favorites', methods=['GET', 'POST'])
def favorites():
    if 'username' in session:
        username = session['username']
        
        if request.method == 'POST':
            city_to_add = request.form['city_name']
            
            if city_to_add not in app_data.user_data[username]:
                app_data.user_data[username].append(city_to_add)
                app_data.update_csv_file()
        
        return render_template('favorites.html', favorite_cities=app_data.user_data[username])
    
    return redirect(url_for('login'))

@app.route('/add_to_favorites', methods=['POST'])
def add_to_favorites():
    if 'username' in session:
        username = session['username']
        city_to_add = request.form.get('city_name')

        if city_to_add:
            user_favorites = app_data.user_data.get(username, [])
            if city_to_add in user_favorites:
                response_data = {'error': True, 'message': "This page is already in your favorites."}
            else:
                user_favorites.append(city_to_add)
                app_data.user_data[username] = user_favorites
                app_data.update_csv_file()
                response_data = {'error': False, 'message': "Page added to favorites successfully."}

            return jsonify(response_data)
        else:
            response_data = {'error': True, 'message': "City name not provided."}
            return jsonify(response_data)
    else:
        response_data = {'error': True, 'message': "User not authenticated."}
        return jsonify(response_data)


@app.route('/profile', methods=['GET','POST'])
def profile():
    if 'username' in session:
        app_data.load_data()
        user_info = app_data.user_info.get(session['username'], {})
        print("User info for", session['username'], ":", user_info)
        return render_template('profile.html', user_info=user_info)
    else:
        return redirect(url_for('login'))

@app.route('/update_profile', methods=['POST'])
def update_profile():
    if 'username' in session:
        username = session['username']

        # Verify the current password before making changes
        current_password = request.form['password']
        if app_data.users.get(username) == current_password:
            email = request.form['email']
            sex = request.form['sex']
            age = request.form['age']

            # Handle image upload
            uploaded_image = request.files['user_image']

            if uploaded_image and allowed_file(uploaded_image.filename):
                filename = secure_filename(uploaded_image.filename)

                # Create the folder if it doesn't exist
                user_folder = os.path.join(app.config['UPLOAD_FOLDER'], username)
                os.makedirs(user_folder, exist_ok=True)

                # Delete the old image if it exists
                old_image_path = os.path.join(user_folder, app_data.user_info[username]['user_image'])
                if os.path.exists(old_image_path):
                    os.remove(old_image_path)

                # Save the uploaded image
                uploaded_image.save(os.path.join(user_folder, filename))

                # Update user information
                app_data.user_info[username] = {
                    'email': email,
                    'user_image': filename,
                    'sex': sex,
                    'age': age
                }
                app_data.update_csv_file()

                # Set the 'success' variable to display the success message in profile.html
                success_message = "Profile updated successfully."
                return render_template('profile.html', user_info=app_data.user_info[username], success=success_message)
            else:
                error_message = "Invalid image file format. Allowed formats: png, jpg, jpeg, gif."
                return render_template('profile.html', user_info=app_data.user_info[username], error=error_message)
        else:
            error_message = "Incorrect current password. Profile update failed."
            return render_template('profile.html', user_info=app_data.user_info[username], error=error_message)

    return redirect(url_for('profile'))


@app.route('/validate_password', methods=['POST'])
def validate_password():
    if request.method == 'POST':
        data = request.get_json()
        entered_username = data.get('username')  # Use the correct field name
        entered_password = data.get('password')

        if entered_username in app_data.users:
            stored_password = app_data.users[entered_username]

            if entered_password == stored_password:
                response_data = {'valid': True}
            else:
                response_data = {'valid': False}
        else:
            response_data = {'valid': False}

        return jsonify(response_data)

@app.route('/istanbul')
def istanbul():
    # Your code for displaying the Istanbul page
    return render_template('istanbul.html')

@app.route('/queenstown')
def queenstown():
    # Your code for displaying the Istanbul page
    return render_template('queenstown.html')

@app.route('/dubai')
def dubai():
    # Your code for displaying the Istanbul page
    return render_template('dubai.html')

@app.route('/rotorua')
def rotorua():
    # Your code for displaying the Istanbul page
    return render_template('rotorua.html')


if __name__ == '__main__':
    app.run(debug=True)

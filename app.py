from flask import Flask,render_template,request, session, redirect, url_for,jsonify, url_for # type: ignore,
from pymongo import MongoClient
# Initialize the Flask app
app = Flask(__name__)
MONGO_URI = "mongodb+srv://heinzbinjupaul:HEINZISTHEBEST@cluster0.uhtsv.mongodb.net/"

# Connect to MongoDB
client = MongoClient(MONGO_URI)

# Select the database and collection
db = client["Calorease"]
user_collection = db["user_data"]


def calc_tdee(weight,height,age,gender,activity_level):
    weight = float(weight)  # Convert weight to a float
    height = float(height)  # Convert height to a float
    age = int(age)          # Convert age to an integer
    if gender == "male":
        bmr = (10 * weight) + (6.25 * height) - (5 * age) + 5
    else:
        bmr = (10 * weight) + (6.25 * height) - (5 * age) - 161
    

    activity_multipliers = {
        "sedentary": 1.2,
        "light": 1.375,
        "moderate": 1.55,
        "active": 1.725,
        "very_active": 1.9
    }
    tdee = bmr * activity_multipliers[activity_level]
    return round(tdee,2)

# Define a route
@app.route('/trial', methods=['GET', 'POST'])
def hello1():
    if request.method == "POST":
        name = request.form.get("name")
        password = request.form.get("password")
        return f"Received: Name - {name}, Password - {password}"
        
    return render_template("trial.html")

@app.route('/')
def hello():
    return render_template("landing.html")

@app.route('/firsttimeusers',methods=['POST','GET'])
def firsttime():
    if request.method == "POST":
        data = request.form
        tdee = calc_tdee(weight=data['weight'], 
        height=data['height'], 
        age=data['age'], 
        gender=data['gender'], 
        activity_level=data['activity'])
        return f"Received: Name - {tdee},{data.get('height')},{data.get('weight')},{data.get('age')},{data.get('activity')}"

    
    return render_template("firsttime.html")

@app.route('/guidepage')
def guide():
    return render_template("guide.html")

@app.route('/settings')
def settings():
    return render_template("settings.html")

@app.route('/homepage')
def home():
    return render_template("homepage_refreshing.html")



# Run the app
if __name__ == '__main__':
    app.run(debug=True)

'''{
    "name": "John Doe",
    "password": "hashedpassword",
    "bmr": 1800,
    "tdee": 2200,
    "start_date": "2025-03-14",
    "current_day": 1,
    "calories_to_eat": 2000,
    "calories_currently_eaten": 500,
    "meals": {
        "breakfast": [],
        "lunch": [],
        "dinner": []
    },
    "weight": 75,
    "target_weight": 70,
    "calories_currently_burned": 200,
    "target_weight_loss_end_date": "2025-06-14"
}'''
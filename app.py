from flask import Flask,render_template,request, session, redirect, url_for,jsonify, url_for # type: ignore,
from pymongo import MongoClient
import bcrypt  # Add bcrypt to hash passwords
from bson.objectid import ObjectId
from datetime import datetime
from werkzeug.security import check_password_hash


# Initialize the Flask app
app = Flask(__name__)
app.secret_key = "heinzkuriensandraneha"
MONGO_URI = "mongodb+srv://heinzbinjupaul:HEINZISTHEBEST@cluster0.uhtsv.mongodb.net/"

# Connect to MongoDB
client = MongoClient(MONGO_URI)

# Select the database and collection
db = client["Calorease"]
user_collection = db["user_data"]
user_daily = db["user_daily_data"]
food_details = db["food_info"]

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


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

def calc_cals_to_eat(weight_loss_rate,tdee,gender):
    
        onekg = 7700
        daily_deficit = (onekg*weight_loss_rate)/7
        cals_to_eat=tdee-daily_deficit

        min_calories = 1200 if gender.lower() == "female" else 1500
        cals_to_eat = max(cals_to_eat, min_calories)
        return round(cals_to_eat,0)

def calc_macros_to_eat(cals_to_eat, weight, goal="balanced"):
    """
    Calculate daily macronutrient targets (proteins, fats, fiber, and carbs).

    Args:
        cals_to_eat (float): Daily calorie intake.
        weight (float): Weight in kilograms.
        goal (str): Dietary goal - "balanced", "high_protein", or "low_carb".

    Returns:
        dict: Macronutrient targets in grams.
    """
    weight = float(weight)  # Ensure weight is a float

    # Macronutrient calorie values per gram
    CALS_PER_GRAM_PROTEIN = 4
    CALS_PER_GRAM_CARB = 4
    CALS_PER_GRAM_FAT = 9

    # Macronutrient distribution based on dietary goal
    if goal == "high_protein":
        protein_ratio = 0.35
        fat_ratio = 0.25
        carb_ratio = 0.40
    elif goal == "low_carb":
        protein_ratio = 0.30
        fat_ratio = 0.40
        carb_ratio = 0.30
    else:  # Default to "balanced"
        protein_ratio = 0.30
        fat_ratio = 0.30
        carb_ratio = 0.40

    # Calculate grams of each macronutrient
    protein_grams = (cals_to_eat * protein_ratio) / CALS_PER_GRAM_PROTEIN
    fat_grams = (cals_to_eat * fat_ratio) / CALS_PER_GRAM_FAT
    carb_grams = (cals_to_eat * carb_ratio) / CALS_PER_GRAM_CARB

    # Fiber recommendation (general guideline: 14g per 1000 calories)
    fiber_grams = (cals_to_eat / 1000) * 14

    return {
        "protein_grams": round(protein_grams, 2),
        "fat_grams": round(fat_grams, 2),
        "carb_grams": round(carb_grams, 2),
        "fiber_grams": round(fiber_grams, 2)
    }

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

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    user = user_collection.find_one({"email": email})  # Query MongoDB

    
    if not user:
        return jsonify({"success": False, "message": "User not found"}), 401

    stored_password = user.get("password", "").encode('utf-8')

    if not bcrypt.checkpw(password.encode('utf-8'), stored_password):
        return jsonify({"success": False, "message": "Invalid password"}), 401

    session["user_id"] = str(user["_id"])  # Store user ID in session
    return jsonify({"success": True, "message": "Login successful"})




@app.route('/firsttimeusers', methods=['POST', 'GET'])
def firsttime():
    if request.method == "POST":
        # Collect form data
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm_password = request.form.get("confirmpassword")
        user_id = str(ObjectId())
        goal = request.form.get("diet")
        weight = request.form.get("weight")
        height = request.form.get("height")
        age = request.form.get("age")
        gender = request.form.get("gender")
        activity_level = request.form.get("activity")
        target_weight = request.form.get("goal")
        weight_loss_rate = float(request.form.get("lossperweek"))
        
        today_date = datetime.today().strftime('%Y-%m-%d')


        # Hash the password before saving
        if password != confirm_password:
            return "Passwords do not match"

        hashed_password = hash_password(password)

        # Calculate TDEE
        tdee = calc_tdee(weight=weight, height=height, age=age, gender=gender, activity_level=activity_level)
        #Calculate Calories to eat in a day in order to lose weight
        cals_to_eat = calc_cals_to_eat(weight_loss_rate=weight_loss_rate,tdee=tdee,gender=gender)
        # Create a new user document to insert into MongoDB
        macros_to_eat = calc_macros_to_eat(cals_to_eat=cals_to_eat, weight=weight, goal=goal)
        user_data = {
            "_id":user_id,
            "name": name,
            "email": email,
            "password": hashed_password,
            "weight": weight,
            "height": height,
            "age": age,
            "gender": gender,
            "activity_level": activity_level,
            "tdee": tdee,
            "cals_to_eat":cals_to_eat,
            "proteins_to_eat": macros_to_eat["protein_grams"],
            "fats_to_eat": macros_to_eat["fat_grams"],
            "carbs_to_eat": macros_to_eat["carb_grams"],
            "fiber_to_eat": macros_to_eat["fiber_grams"],
            "target_weight": target_weight
        }
 # Insert the new user into MongoDB
        user_collection.insert_one(user_data)
        
        user_daily_data = {"_id":user_id,
             "name": name,
    "start_date": today_date,  # Assign today's date
    "current_day": 1,
    "cals_to_eat":cals_to_eat,
    "calories_currently_eaten": 0,
    "calories_currently_burned": 0,
    "proteins_currently_eaten": 0,
    "fats_currently_eaten": 0,
    "carbs_currently_eaten": 0,
    "fiber_currently_eaten": 0,
    "meals": {
        "breakfast": [],
        "morning_snack":[],
        "lunch": [],
        "evening_snack":[],
        "dinner": [],
    },
    "starting_weight": weight,
    "weight_log": [
    ]
        }
        user_daily.insert_one(user_daily_data)
        # Redirect or render a success page
        session["user_id"] = str(user_id)
        return redirect(url_for('home'))
    
    return render_template("firsttime.html")

@app.route('/guidepage')
def guide():
    return render_template("guide.html")

@app.route('/settings')
def settings():
    return render_template("settings.html")

@app.route('/suggest')
def suggest():
    return render_template("suggest.html")


@app.route('/homepage')
def home():
    if "user_id" not in session:
        return redirect(url_for("hello"))
    # Assuming the user is logged in and their ID is stored in the session
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('hello'))  # Redirect to login if not logged in
    
    # Fetch the user's data from MongoDB
    user_data = user_collection.find_one({"_id": user_id})
    user_daily_data = user_collection.find_one({"_id": user_id})

    # Get the total calories to eat (cals_to_eat)
    cals_to_eat = user_data.get('cals_to_eat', 0)
    calories_currently_eaten = user_daily_data.get('calories_currently_eaten', 0)

    # Pass the data to the template
    return render_template("homepage_refreshing.html", cals_to_eat=cals_to_eat, calories_currently_eaten=calories_currently_eaten)

@app.route('/api/search_food', methods=['GET'])
def search_food():
    query = request.args.get('q', '').lower()
    if not query:
        return jsonify([])

    # Search for food items in MongoDB and limit to 5 results
    results = food_details.find({"name": {"$regex": query, "$options": "i"}}).limit(5)
    unique_food_items = {}
    for item in results:
        name = item["name"]
        if name not in unique_food_items:
            unique_food_items[name] = {
                "name": item["name"],
                "calories": item["calories_per_unit"],
                "protein": item["protein_per_unit"],
                "fats": item["fats_per_unit"],
                "carbs": item["carbs_per_unit"],
                "fiber": item["fibre_per_unit"],
                "unit": item["unit"]
            }

    # Convert the dictionary values to a list to return as JSON
    food_items = list(unique_food_items.values())

    #OG
    '''food_items = [
        {
            "name": item["name"],
            "calories": item["calories_per_unit"],
            "protein": item["protein_per_unit"],
            "fats": item["fats_per_unit"],
            "carbs": item["carbs_per_unit"],
            "fiber": item["fibre_per_unit"],
            "unit": item["unit"]
        }
        for item in results
    ]'''



    return jsonify(food_items)
import random

@app.route('/api/random_food', methods=['GET'])
def random_food():
    # Fetch all food items and randomly select 8
    food_items = list(food_details.aggregate([{"$sample": {"size": 8}}]))
    random_items = [
        {
            "name": item["name"],
            "calories": item["calories_per_unit"],
            "protein": item["protein_per_unit"],
            "fats": item["fats_per_unit"],
            "carbs": item["carbs_per_unit"],
            "fiber": item["fibre_per_unit"],
            "unit": item["unit"]
        }
        for item in food_items
    ]
    return jsonify(random_items)



@app.route('/api/daily_targets', methods=['GET'])
def get_daily_targets():
    # Get the user ID from the session
    user_id = session.get('user_id')
    print(user_id)
    if not user_id:
        return jsonify({"error": "User not logged in"}), 401

    # Query the database for the user's daily targets
    user = user_collection.find_one({"_id": user_id}, {
        "_id": 0,  # Exclude the _id field
        "proteins_to_eat": 1,
        "fats_to_eat": 1,
        "carbs_to_eat": 1,
        "fiber_to_eat": 1
    })

    if not user:
        return jsonify({"error": "User not found"}), 404

    print("hi I am heinz",user)
    # Return the daily targets as JSON
    return jsonify({
        "protein": user.get("proteins_to_eat", 0),
        "fats": user.get("fats_to_eat", 0),
        "carbs": user.get("carbs_to_eat", 0),
        "fiber": user.get("fiber_to_eat", 0)
    })

# Run the app
if __name__ == '__main__':
    app.run(debug=True)

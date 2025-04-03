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
    "water_glasses":0,
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
    
    user_id = session.get('user_id')
    print(f"User ID from session: {user_id}")  # Debugging log

    if not user_id:
        return redirect(url_for('hello'))  # Redirect to login if not logged in
    
    # Fetch the user's data from MongoDB
    user_data = user_collection.find_one({"_id": user_id})
    print(f"User data: {user_data}")  # Debugging log

    user_daily_data = user_daily.find_one({"_id": user_id})
    print(f"User daily data: {user_daily_data}")  # Debugging log

    if not user_daily_data:
        return redirect(url_for('firsttime'))  # Redirect to first-time setup or show an error page

    # Get the total calories to eat (cals_to_eat)
    cals_to_eat = user_data.get('cals_to_eat', 0)
    carbs_to_eat = user_data.get('carbs_to_eat', 0)
    fats_to_eat = user_data.get('fats_to_eat', 0)
    proteins_to_eat = user_data.get('proteins_to_eat', 0)
    fiber_to_eat = user_data.get('fiber_to_eat', 0)
    calories_currently_eaten = user_daily_data.get('calories_currently_eaten', 0)
    carbs_currently_eaten = user_daily_data.get('carbs_currently_eaten', 0)
    protiens_currently_eaten = user_daily_data.get('proteins_currently_eaten', 0)
    fats_currently_eaten = user_daily_data.get('fats_currently_eaten', 0)
    fiber_currently_eaten = user_daily_data.get('fiber_currently_eaten', 0)


    # Pass the data to the template
    return render_template("homepage_refreshing.html", cals_to_eat=cals_to_eat,
                           carbs_to_eat=carbs_to_eat,
                           fats_to_eat=fats_to_eat,
                           proteins_to_eat=proteins_to_eat,
                           fiber_to_eat=fiber_to_eat,

                           calories_currently_eaten=calories_currently_eaten, 
                           carbs_currently_eaten=carbs_currently_eaten, 
                           protiens_currently_eaten=protiens_currently_eaten, 
                           fats_currently_eaten=fats_currently_eaten,
                           fiber_currently_eaten=fiber_currently_eaten)

   
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


@app.route('/api/add_food', methods=['POST'])
def add_food():
    try:
        # Get the user ID, meal name, and food details from the request
        user_id = session.get('user_id')
        meal_name = request.json.get('meal_name')  # e.g., 'breakfast', 'lunch'
        print("innada meal name",meal_name)
        food_item = request.json.get('food_item')  # e.g., {'name': 'Apple', 'calories': 95}
        print("innada user id",user_id)


        if not user_id or not meal_name or not food_item:
            return jsonify({'error': 'Missing required fields'}), 400

        food_item['calories'] = round(food_item['calories'], 2)
        food_item['protein'] = round(food_item['protein'], 2)
        food_item['fats'] = round(food_item['fats'], 2)
        food_item['carbs'] = round(food_item['carbs'], 2)
        food_item['fiber'] = round(food_item['fiber'], 2)
        result = user_daily.update_one(
    {"_id": user_id},
    {
        "$push": {f"meals.{meal_name}": food_item},  # Add the food item to the meal array
        "$inc": {
            "calories_currently_eaten": food_item['calories'],  # Increment calories
            "proteins_currently_eaten": food_item['protein'],   # Increment proteins
            "fats_currently_eaten": food_item['fats'],          # Increment fats
            "carbs_currently_eaten": food_item['carbs'],        # Increment carbs
            "fiber_currently_eaten": food_item['fiber']         # Increment fiber
        }
    }
)

        # Check if the update was successful
    
        updated_data = user_daily.find_one({"_id": user_id}, {
            "_id": 0,
            "meals": 1,
            "calories_currently_eaten": 1,
            "proteins_currently_eaten": 1,
            "fats_currently_eaten": 1,
            "carbs_currently_eaten": 1,
            "fiber_currently_eaten": 1,
            "cals_to_eat": 1,
            "proteins_to_eat": 1,
            "fats_to_eat": 1,
            "carbs_to_eat": 1,
            "fiber_to_eat": 1
        })

        return jsonify(updated_data), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/get_meals_and_progress', methods=['GET'])
def get_meals_and_progress():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "User not logged in"}), 401

    # Fetch the user's daily data
    user_daily_data = user_daily.find_one({"_id": user_id}, {
        "_id": 0,
        "meals": 1,
        "calories_currently_eaten": 1,
        "proteins_currently_eaten": 1,
        "fats_currently_eaten": 1,
        "carbs_currently_eaten": 1,
        "fiber_currently_eaten": 1,
        "cals_to_eat": 1,
        "proteins_to_eat": 1,
        "fats_to_eat": 1,
        "carbs_to_eat": 1,
        "fiber_to_eat": 1
    })

    if not user_daily_data:
        return jsonify({"error": "User daily data not found"}), 404

     # Round the values to 2 decimal places
    user_daily_data['calories_currently_eaten'] = round(user_daily_data.get('calories_currently_eaten', 0), 0)
    user_daily_data['proteins_currently_eaten'] = round(user_daily_data.get('proteins_currently_eaten', 0), 2)
    user_daily_data['fats_currently_eaten'] = round(user_daily_data.get('fats_currently_eaten', 0), 0)
    user_daily_data['carbs_currently_eaten'] = round(user_daily_data.get('carbs_currently_eaten', 0), 0)
    user_daily_data['fiber_currently_eaten'] = round(user_daily_data.get('fiber_currently_eaten', 0), 0)
    return jsonify(user_daily_data)

@app.route('/api/update_calories_burned', methods=['POST'])
def update_calories_burned():
    try:
        # Get the user ID from the session
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not logged in'}), 401

        # Get the total calories burned from the request
        data = request.json
        total_calories_burned = data.get('total_calories_burned')

        if total_calories_burned is None:
            return jsonify({'error': 'Missing total_calories_burned field'}), 400

        # Update the user's daily data in MongoDB
        result = user_daily.update_one(
            {"_id": user_id},
            {"$set": {"calories_currently_burned": total_calories_burned}}
        )

        if result.modified_count == 0:
            return jsonify({'error': 'Failed to update calories burned'}), 500

        # Fetch the updated data to return to the frontend
        updated_data = user_daily.find_one({"_id": user_id}, {
            "_id": 0,
            "calories_currently_burned": 1
        })

        return jsonify(updated_data), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500



@app.route('/api/update_health_goals', methods=['POST'])
def update_health_goals():
    try:
        # Get the user ID from the session
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"error": "User not logged in"}), 401

        # Get the updated health goals from the request
        data = request.json  # Use request.json to parse JSON data
        if not data:
            return jsonify({"error": "Invalid or missing JSON data"}), 400

        weight = float(data.get('weight'))
        height = float(data.get('height'))
        age = int(data.get('age'))
        gender = data.get('gender')
        activity_level = data.get('activityLevel')
        target_weight = float(data.get('targetWeight'))
        dietary_preferences = data.get('dietaryPreferences')
        weight_loss_rate = float(data.get('lossperweek', 0.5))  # Default to 0.5 kg/week if not provided

        # Recalculate TDEE and daily calorie intake
        tdee = calc_tdee(weight=weight, height=height, age=age, gender=gender, activity_level=activity_level)
        cals_to_eat = calc_cals_to_eat(weight_loss_rate=weight_loss_rate, tdee=tdee, gender=gender)

        # Recalculate macronutrient targets
        macros_to_eat = calc_macros_to_eat(cals_to_eat=cals_to_eat, weight=weight, goal=dietary_preferences)

        # Prepare the updated data
        update_data = {
            "weight": weight,
            "height": height,
            "age": age,
            "gender": gender,
            "activity_level": activity_level,
            "target_weight": target_weight,
            "dietary_preferences": dietary_preferences,
            "tdee": tdee,
            "cals_to_eat": cals_to_eat,
            "proteins_to_eat": macros_to_eat["protein_grams"],
            "fats_to_eat": macros_to_eat["fat_grams"],
            "carbs_to_eat": macros_to_eat["carb_grams"],
            "fiber_to_eat": macros_to_eat["fiber_grams"]
        }

        # Update the user's health goals in the database
        result = user_collection.update_one({"_id": user_id}, {"$set": update_data})

        if result.modified_count == 0:
            return jsonify({"error": "No changes made to user data"}), 400

        return jsonify({"message": "Health goals updated successfully!"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
# Run the app
if __name__ == '__main__':
    app.run(debug=True)
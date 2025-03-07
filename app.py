from flask import Flask,render_template, url_for

# Initialize the Flask app
app = Flask(__name__)

# Define a route
@app.route('/')
def hello():
    return render_template("landing.html")

@app.route('/firsttimeusers')
def firsttime():
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

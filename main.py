from flask import Flask, render_template, request
app = Flask(__name__)

# Simple logic to match KB16 model
def assign_model(feel, style, focus):
    key = f"{feel}_{style}_{focus}"
    model_map = {
        "eager_rockstar_proof": "The Architect",
        "eager_rockstar_process": "The Driver",
        "eager_rockstar_people": "The Facilitator",
        "eager_rockstar_possibilities": "The Creator",
        "eager_roadie_proof": "The Guru",
        "eager_roadie_process": "The Implementer",
        "eager_roadie_people": "The Humanitarian",
        "eager_roadie_possibilities": "The Explorer",
        "cautious_rockstar_proof": "The Sceptic",
        "cautious_rockstar_process": "The Perfectionist",
        "cautious_rockstar_people": "The Preservationist",
        "cautious_rockstar_possibilities": "The Fearful Optimist",
        "cautious_roadie_proof": "The Forecaster",
        "cautious_roadie_process": "The Bureaucrat",
        "cautious_roadie_people": "The Shepherd",
        "cautious_roadie_possibilities": "The Lost Soul"
    }
    return model_map.get(key, "Unknown")

@app.route("/")
def index():
    return render_template("form.html")

@app.route("/submit", methods=["POST"])
def submit():
    feel = request.form["feel"]
    style = request.form["style"]
    focus = request.form["focus"]
    question = request.form["question"]
    model = assign_model(feel, style, focus)
    return render_template("result.html", model=model, question=question)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)

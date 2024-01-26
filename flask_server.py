from flask import Flask, render_template
import os
import checker

serving_address = "localhost"
serving_port = 8000

os.environ["FLASK_APP"] = "flask_server"
os.environ["FLASK_ENV"] = "development"

app = Flask(__name__)
@app.route('/')
def home():
    temp_obj = checker.retrieve_lpar_info.output_getter()
    return render_template("main.html", list_of_frames=(temp_obj.output_getter()))

if __name__ == '__main__':
    app.run(host=serving_address, port=serving_port)
    
from flask import Flask, render_template, request, jsonify
import subprocess
import os

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('home1.html')

@app.route('/criminal-detection', methods=['GET'])
def criminal_detection():
    try:
        # Launch the alexnet_model.py GUI in a separate process
        subprocess.Popen(['python', 'alexnet_model.py'])
        return jsonify({'status': 'success', 'message': 'Criminal Detection GUI launched'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/currency-detection', methods=['GET'])
def currency_detection():
    try:
        # Launch the script.py GUI in a separate process
        subprocess.Popen(['python', 'script.py'])
        return jsonify({'status': 'success', 'message': 'Currency Detection GUI launched'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

if __name__ == '__main__':
    app.run(debug=True)

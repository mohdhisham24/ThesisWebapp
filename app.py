from flask import Flask, render_template, request, redirect, url_for, session
import flask_socketio
import time
import csv
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = flask_socketio.SocketIO(app)

@app.route('/', methods=['GET', 'POST'])
def start():
    if request.method == 'POST':
        participant_name = request.form['participant_name']
        session['participant_name'] = participant_name
        session['start_time'] = time.time()
        return redirect(url_for('experiment'))
    return render_template('start.html')

@app.route('/experiment')
def experiment():
    if 'participant_name' not in session:
        return redirect(url_for('start'))
    return render_template('experiment.html', participant_name=session['participant_name'])

@app.route('/end')
def end():
    if 'participant_name' in session:
        del session['participant_name']
    if 'start_time' in session:
        del session['start_time']
    return redirect(url_for('start'))

@socketio.on('temperature_update')
def handle_temperature_update(json):
    temperature = int(json['temperature'])
    participant_name = session.get('participant_name', 'Unknown')
    start_time = session.get('start_time', time.time())
    log_interaction(participant_name, 'Web Interface', 'Change Temperature', temperature, start_time)
    flask_socketio.emit('temperature_update', {'temperature': temperature}, broadcast=True)

def log_interaction(participant_name, interface, action, temp, start_time):
    filename = f"interactionlog_{participant_name}.csv"
    file_exists = os.path.isfile(filename)
    
    with open(filename, 'a', newline='') as log_file:
        csv_writer = csv.writer(log_file)
        if not file_exists:
            csv_writer.writerow(['Timestamp', 'Interface', 'Action', 'Temperature', 'Elapsed Time'])
        
        elapsed_time = time.time() - start_time
        timestamp = datetime.now().isoformat()
        csv_writer.writerow([timestamp, interface, action, temp, elapsed_time])

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
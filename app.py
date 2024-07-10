from flask import Flask, render_template, request, redirect, url_for, session
from flask_socketio import SocketIO, emit
import time
import csv
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")

current_participant = None
start_time = None
current_temperature = 20

@app.route('/', methods=['GET', 'POST'])
def start():
    global current_participant, start_time
    if request.method == 'POST':
        current_participant = request.form['participant_name']
        start_time = time.time()
        socketio.emit('experiment_started', {'participant': current_participant})
        return redirect(url_for('conductor_panel'))
    return render_template('start.html')

@app.route('/conductor_panel')
def conductor_panel():
    return render_template('conductor_panel.html', participant_name=current_participant)

@app.route('/end')
def end():
    global current_participant, start_time
    if current_participant:
        socketio.emit('experiment_ended', {'participant': current_participant})
        current_participant = None
        start_time = None
    return redirect(url_for('start'))

@socketio.on('temperature_update')
def handle_temperature_update(data):
    global current_temperature
    current_temperature = int(data['temperature'])
    interface = data['interface']
    log_interaction(current_participant, interface, 'Change Temperature', current_temperature, start_time)
    emit('temperature_sync', {'temperature': current_temperature}, broadcast=True)

def log_interaction(participant_name, interface, action, temp, start_time):
    if not participant_name:
        return
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
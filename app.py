from flask import Flask, render_template, request, redirect, url_for
from flask_socketio import SocketIO, emit
import time
import csv
from datetime import datetime
import os
from gpiozero import RotaryEncoder, Button
from threading import Thread

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")

current_participant = None
start_time = None
current_temperature = 20

# Define pin numbers for the rotary encoders
CLK1, DT1, SW1 = 13, 18, 12  # Steering Wheel Knob
CLK2, DT2, SW2 = 4, 5, 3     # Infotainment Knob

# Create RotaryEncoder instances
rotor1 = RotaryEncoder(CLK1, DT1)
button1 = Button(SW1, pull_up=True)
rotor2 = RotaryEncoder(CLK2, DT2)
button2 = Button(SW2, pull_up=True)

def rotary_encoder_thread(rotor, button, interface_name):
    global current_temperature
    last_value = 0

    def rotated():
        global current_temperature
        nonlocal last_value
        current_value = rotor.value
        
        # Restrict temperature to 15-30
        if current_value > last_value:
            if current_temperature < 30:  # Limit to max 30
                current_temperature += 1
        elif current_value < last_value:
            if current_temperature > 15:  # Limit to min 15
                current_temperature -= 1
        
        # Ensure temperature does not go below 15
        current_temperature = max(15, current_temperature)

        if current_value != last_value:
            print(f"Temperature changed to {current_temperature} by {interface_name}")
            socketio.emit('temperature_sync', {'temperature': current_temperature}, broadcast=True)
            log_interaction(current_participant, interface_name, 'Change Temperature', current_temperature, start_time)
        
        last_value = current_value

    def button_pressed():
        print(f"Button pressed on {interface_name}")
        socketio.emit('button_press', {'message': f'Encoder button pressed on {interface_name}'})
        log_interaction(current_participant, interface_name, 'Button Press', current_temperature, start_time)

    rotor.when_rotated = rotated
    button.when_pressed = button_pressed

    print(f"{interface_name} thread initialized. Press CTRL+C to exit.")

    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print(f"\nExiting {interface_name} thread...")

@app.route('/', methods=['GET', 'POST'])
def start():
    global current_participant, start_time
    if request.method == 'POST':
        current_participant = request.form['participant_name']
        start_time = time.time()
        socketio.emit('experiment_started', {'participant': current_participant})
        
        # Log the experiment start timestamp
        log_interaction(current_participant, 'Experiment', 'Start', current_temperature, start_time)
        
        return redirect(url_for('conductor_panel'))
    return render_template('start.html')

@app.route('/conductor_panel')
def conductor_panel():
    return render_template('conductor_panel.html', participant_name=current_participant)

@app.route('/temperature')
def temperature():
    return render_template('temperature.html')

@app.route('/end')
def end():
    global current_participant, start_time
    if current_participant:
        socketio.emit('experiment_ended', {'participant': current_participant})
        
        # Log the experiment end timestamp
        log_interaction(current_participant, 'Experiment', 'End', current_temperature, start_time)
        
        current_participant = None
        start_time = None
    return redirect(url_for('start'))

@socketio.on('temperature_update')
def handle_temperature_update(data):
    global current_temperature
    if 'temperature' in data:
        current_temperature = int(data['temperature'])
    elif 'value' in data:
        current_temperature += int(data['value'])
        # Restrict temperature to 15-30
        current_temperature = max(15, min(30, current_temperature))

    interface = data['interface']
    log_interaction(current_participant, interface, 'Change Temperature', current_temperature, start_time)
    emit('temperature_sync', {'temperature': current_temperature}, broadcast=True)

@socketio.on('play_audio')
def handle_play_audio(data):
    audio_file = data['audio_file']
    log_interaction(current_participant, 'Audio', f'Play {audio_file}', current_temperature, start_time)
    emit('play_audio', {'audio_file': audio_file}, broadcast=True)

@socketio.on('end_experiment')
def handle_end_experiment():
    global current_participant, start_time
    if current_participant:
        socketio.emit('experiment_ended', {'participant': current_participant})
        
        # Log the experiment end timestamp
        log_interaction(current_participant, 'Experiment', 'End', current_temperature, start_time)
        
        current_participant = None
        start_time = None
        # Emit an event to trigger redirection
        emit('redirect', {'url': url_for('start')})

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

@app.route('/raspberry_touch')
@app.route('/raspberry_touch.html')
def raspberry_touch():
    return render_template('raspberry_touch.html')

@app.route('/infotainment_touch')
@app.route('/infotainment_touch.html')
def infotainment_touch():
    return render_template('infotainment_touch.html')

if __name__ == '__main__':
    try:
        print("Starting Rotary Encoder threads")
        encoder_thread1 = Thread(target=rotary_encoder_thread, args=(rotor1, button1, 'Steering Wheel Knob'))
        encoder_thread1.daemon = True
        encoder_thread1.start()

        encoder_thread2 = Thread(target=rotary_encoder_thread, args=(rotor2, button2, 'Infotainment Knob'))
        encoder_thread2.daemon = True
        encoder_thread2.start()
        
        print("Starting Flask application")
        socketio.run(app, host='0.0.0.0', port=5000, debug=False)
    except Exception as e:
        print(f"Error running application: {e}")
    finally:
        if rotor1:
            rotor1.close()
        if button1:
            button1.close()
        if rotor2:
            rotor2.close()
        if button2:
            button2.close()
        print("GPIO cleaned up")
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

# Define pin numbers (BCM numbering)
CLK = 13
DT = 18
SW = 12

# Create a RotaryEncoder instance
rotor = RotaryEncoder(CLK, DT)
button = Button(SW, pull_up=True)

# def rotary_encoder_thread():
#     global current_temperature

#     def rotated():
#         global current_temperature
#         if rotor.value > 0:
#             current_temperature = min(30, current_temperature + 1)
#         else:
#             current_temperature = max(15, current_temperature - 1)
#         print(f"Temperature changed to {current_temperature}")
#         socketio.emit('temperature_sync', {'temperature': current_temperature}, broadcast=True)
#         log_interaction(current_participant, 'Steering Wheel Knob', 'Change Temperature', current_temperature, start_time)

#     def button_pressed():
#         print("Button pressed")
#         socketio.emit('button_press', {'message': 'Encoder button pressed'})
#         log_interaction(current_participant, 'Steering Wheel Knob', 'Button Press', current_temperature, start_time)

#     rotor.when_rotated = rotated
#     button.when_pressed = button_pressed

#     print("Rotary Encoder thread initialized. Press CTRL+C to exit.")

#     try:
#         while True:
#             time.sleep(0.1)
#     except KeyboardInterrupt:
#         print("\nExiting rotary encoder thread...")

def rotary_encoder_thread():
    global current_temperature
    last_value = 0

    def rotated():
        global current_temperature
        nonlocal last_value
        current_value = rotor.value
        
        if current_value > last_value:
            current_temperature = min(30, current_temperature + 1)
        elif current_value < last_value:
            current_temperature = max(15, current_temperature - 1)
        
        if current_value != last_value:
            print(f"Temperature changed to {current_temperature}")
            socketio.emit('temperature_sync', {'temperature': current_temperature}, broadcast=True)
            log_interaction(current_participant, 'Steering Wheel Knob', 'Change Temperature', current_temperature, start_time)
        
        last_value = current_value

    def button_pressed():
        print("Button pressed")
        socketio.emit('button_press', {'message': 'Encoder button pressed'})
        log_interaction(current_participant, 'Steering Wheel Knob', 'Button Press', current_temperature, start_time)

    rotor.when_rotated = rotated
    button.when_pressed = button_pressed

    print("Rotary Encoder thread initialized. Press CTRL+C to exit.")

    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nExiting rotary encoder thread...")


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
    if 'temperature' in data:
        current_temperature = int(data['temperature'])
    elif 'value' in data:
        # For steering wheel touch buttons
        current_temperature += int(data['value'])
        current_temperature = max(15, min(30, current_temperature))
    
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

@app.route('/participant.html')
def participant():
    return render_template('participant.html')

if __name__ == '__main__':
    try:
        print("Starting Rotary Encoder thread")
        encoder_thread = Thread(target=rotary_encoder_thread)
        encoder_thread.daemon = True
        encoder_thread.start()
        
        print("Starting Flask application")
        socketio.run(app, host='0.0.0.0', port=5000, debug=False)
    except Exception as e:
        print(f"Error running application: {e}")
    finally:
        if rotor:
            rotor.close()
        if button:
            button.close()
        print("GPIO cleaned up")

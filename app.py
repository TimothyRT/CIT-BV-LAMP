from flask import Flask, render_template, request,  redirect, url_for, session
from flask_session import Session
import hashlib
import uuid
import os
from qiskit.visualization import plot_histogram
import random
import matplotlib
import matplotlib.pyplot as plt
matplotlib.use('Agg')
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator


app = Flask(__name__)
app.config["SESSION_PERMANENT"] = True
app.config["SESSION_TYPE"] = "filesystem"
app.config['UPLOAD_FOLDER'] = './static/images/'
app.secret_key = "f!#&^rty(*wjf(ijf)!#(*!t(h*!%(*&@)"
Session(app)

secret_number = None
secret_length = None


def apply_oracle(secret):
    num_of_bit = len(secret)
    oracle_circuit = QuantumCircuit(num_of_bit + 1, num_of_bit)
    oracle_circuit.h(range(num_of_bit))
    oracle_circuit.x(num_of_bit)
    oracle_circuit.h(num_of_bit)
    oracle_circuit.barrier()

    for index, number in enumerate(reversed(secret)):
        if number == '1':
            oracle_circuit.cx(index, num_of_bit)

    oracle_circuit.barrier()
    oracle_circuit.h(range(num_of_bit))
    oracle_circuit.barrier()

    return oracle_circuit


def q_circuit_create(secret):
    length = len(secret)
    circuit = QuantumCircuit(length + 1, length)

    oracle = apply_oracle(secret)
    circuit.compose(oracle, range(length + 1), inplace=True)

    circuit.measure(range(length), range(length))

    return circuit


def quantums(n, circuit):
    simulator = AerSimulator()
    compiled_circuit = transpile(circuit, simulator)
    result = simulator.run(compiled_circuit, shots=1).result()
    counts = result.get_counts()
    secret_number = list(counts.keys())[0]
    count = counts[secret_number]
    return secret_number, count, counts


@app.route('/')
def index():
    if request.headers.getlist("X-Forwarded-For"):
        ip = request.headers.getlist("X-Forwarded-For")[0]
    else:
        ip = request.remote_addr
    session["uid"] = hashlib.md5(bytes(ip, 'utf-8')).hexdigest()
    print(session.get("uid"))
    print(ip)
    return render_template('index.html')


@app.route('/homepage')
def process_user_transformation_choice():
    return render_template("quantum_query.html")


@app.route('/process_game_type', methods=["POST", "GET"])
def process_game_type():
    global secret_number
    global secret_length
    if secret_number == None:
        secret_number = request.form["secretNumbers"]
        secret_length = request.form["secretLength"]
    game_type = request.form['gameType']
    
    session['n_length'] = int(secret_length)
    session['s_number'] = secret_number

    return redirect(url_for(game_type))


@app.route('/player_game')
def player_game():
    global secret_number
    global secret_length

    n_length = session.get('n_length')
    s_number = session.get('s_number')
    secret_number = None 
    secret_length = None
    return render_template("player_game.html", n_length=n_length, s_number=s_number)


@app.route("/classic_computer_game")
def classic_computer_game():
    global secret_number
    global secret_length
    n_length = session.get('n_length')
    s_number = session.get('s_number')
    secret_number = None 
    secret_length = None
    return render_template("classic_computer_game.html", n_length=n_length, s_number=s_number)


@app.route("/quantum_computer_game")
def quantum_computer_game():
    global secret_number
    global secret_length
    n_length = session.get('n_length')
    s_number = session.get('s_number')

    if s_number is None or s_number == "":
        s_number = ''.join(random.choice('01') for _ in range(n_length))
    
    detected_secret, tries, counts = quantums(len(s_number), q_circuit_create(s_number))
    
    # Generate a unique filename using UUID
    unique_id = uuid.uuid4().hex
    plot_filename = f"quantum_plot_{unique_id}.png"
    plot_path = f'static/images/{plot_filename}'
    
    save_quantum_plot(s_number, detected_secret, counts, plot_path)
    
    secret_number = None 
    secret_length = None
    return render_template("quantum_computer_game.html", 
                           s_number=detected_secret, 
                           secret_numbers=s_number, 
                           tries=tries, 
                           n_length=n_length, 
                           plot_filename=plot_filename,
                           )


def save_quantum_plot(secret_number, detected_secret, counts, plot_path):
    n_length = len(secret_number)
    all_possible_states = {f"{i:0{n_length}b}": 0 for i in range(2 ** n_length)}
    relevant_states = set()

    if n_length <= 4:
        relevant_states = all_possible_states.keys()
    else:
        relevant_states.add(detected_secret)
        detected_int = int(detected_secret, 2)
        neighbors = set()
        for neighbor in range(max(0, detected_int - 8), min(2 ** n_length, detected_int + 8)):
            neighbors.add(f"{neighbor:0{n_length}b}")
        relevant_states.update(neighbors)
        if len(relevant_states) > 16:
            relevant_states = set(list(relevant_states)[:16])

    for state in relevant_states:
        all_possible_states[state] = counts.get(state, 0)

    filtered_states = {state: all_possible_states[state] for state in relevant_states}

    fig, ax = plt.subplots(figsize=(10, 6))
    plot_histogram(filtered_states, color='lightgrey', ax=ax)
    highlighted_counts = {state: (1 if state == detected_secret else 0) for state in filtered_states}
    plot_histogram(highlighted_counts, color='blue', ax=ax)

    ax.set_title(f"Quantum Circuit Result - Detected Secret ({secret_number})")
    ax.set_xlabel("States")
    ax.set_ylabel("Counts")
    ax.legend(['Relevant States', 'Detected Secret'])

   
    ax.set_xticks(range(len(filtered_states))) 
    ax.set_xticklabels(filtered_states.keys(), rotation=45, ha='right')  

    plt.tight_layout()  
    plt.savefig(plot_path)  
    plt.close(fig)


@app.route("/not_play_again")
def not_play_again():
    return render_template("index.html")


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')

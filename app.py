from flask import Flask, render_template, request,  redirect, url_for, session
from flask_session import Session
import os
import qrcode
import hashlib
import random
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
    return secret_number, count


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
    qr_path = generate_qr_code("user_mob_form")
    return render_template("quantum_query.html", qr_path = qr_path)

@app.route('/process_mobile_input',  methods=["POST"])
def process_mobile_input():
    global secret_number
    global secret_length
    secret_number = request.form.get("secretNumber")
    secret_length = request.form.get("secretLength")
    print("Received secret number:", secret_number)
    if not secret_number:
        print("Error: Secret number not received from the form.")
    else:
        session['secretNumber'] = secret_number
        session['secretLength'] = secret_length
        print("Session Secret Number",session['secretNumber'])
    return render_template('mobile_end.html', secretNumber=secret_number)

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
    if s_number == None or s_number == "":
        s_number = ''.join(random.choice('01') for _ in range(n_length))
    s_number, tries = quantums(len(s_number), q_circuit_create(s_number))
    secret_number = None 
    secret_length = None
    return render_template("quantum_computer_game.html", s_number=s_number, secret_numbers=s_number, tries=tries, n_length=n_length)

@app.route("/not_play_again")
def not_play_again():
    return render_template("index.html")

@app.route('/enchancement')
def enchancement():
    return render_template("image_video.html")

@app.route('/quantum')
def quantum():
    qr_path = generate_qr_code("user_mob_form")
    return render_template("quantum_query.html", qr_path = qr_path)

@app.route('/user_mob_form', methods=["GET"])
def mobile_input():
    return render_template('user_mob.html')

def generate_qr_code(image_path):
    qr_directory = "./static/images/results"
    os.makedirs(qr_directory, exist_ok=True)  

    qr = qrcode.QRCode(
        version=1,
        box_size=10,
        border=4)
    qr.add_data(request.url_root + image_path)
    qr.make(fit=True)
    qr_image = qr.make_image(fill='black', back_color='white')

    qr_path = os.path.join(qr_directory, "qr_gan_results.png")
    qr_image.save(qr_path)
    return qr_path

if __name__ == '__main__':
    app.run(debug=True)

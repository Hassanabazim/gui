from flask import Flask, render_template, request, redirect, url_for
import serial

app = Flask(__name__)

# Example serial setup (modify to match your config)
# ser = serial.Serial('/dev/ttyUSB0', 9600)

# Mockup: 9x9 grid (can be expanded)
GRID_SIZE = 9
highlight_cells = [(0, 0), (2, 4), (7, 3)]  # cells to highlight

@app.route('/')
def index():
    return render_template('index.html', grid_size=GRID_SIZE, highlights=highlight_cells)

@app.route('/send', methods=['POST'])
def send():
    x = int(request.form.get('x'))
    y = int(request.form.get('y'))
    print(f"Button at ({x}, {y}) clicked.")
    
    # Example serial communication
    # ser.write(f"{x},{y}\n".encode())

    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)  # Accessible over local network

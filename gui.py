# Full updated Python code

import tkinter as tk
from tkinter import ttk
import serial
import serial.tools.list_ports

ROWS = 9
COLS = 9
HIGHLIGHTED = {10, 15, 55, 60}

class RemoteChessGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Remote Chess")
        self.serial_port = None
        self.serial_ready = False

        self.commands = [
            ("a 0\r\n", None),
            ("a 2 79 0 100 120 100 300\r\n", None),
            ("a 15 20 0 100 78 0 30 40 0 30 114 100 70 32 100 30 71 100 30 5 170 70 68 170 30 34 170 30 99 240 70 53 240 30 83 240 30 15 310 350 85 310 30 51 310 30\r\n", 10),
            ("a 10 92 0 70 95 10 20 13 70 40 14 80 20 90 110 40 93 120 20 11 150 40 12 160 20 88 190 300 91 200 20\r\n", 60),
            ("a 15 37 0 100 127 0 30 8 0 30 82 100 70 10 100 30 125 100 30 52 170 70 117 170 30 2 170 30 67 240 70 4 240 30 115 240 30 62 310 350 100 310 30 19 310 30\r\n", 15),
            ("a 10 102 0 70 110 10 20 55 70 40 63 80 20 112 110 40 103 120 20 33 150 40 54 160 20 120 190 300 113 200 20\r\n", 55)
        ]
        self.initial_sent = False
        self.loop_index = 2
        self.waiting_for_f = False
        self.moving = False
        self.mode = None  # 'start' or 'demo'

        self.root.configure(bg="#304160")
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TButton", font=("Segoe UI", 10, "bold"), padding=8,
                        relief="flat", background="#3e5476", foreground="white")
        style.map("TButton", background=[("active", "#5b6f95")], foreground=[("active", "white")])

        tk.Label(root, text="REMOTE CHESS", font=("Arial", 28, "bold"),
                 fg="white", bg="#1e2e4f", pady=10).pack(fill=tk.X)

        content_frame = tk.Frame(root, bg="#304160")
        content_frame.pack(fill=tk.BOTH, expand=True)

        self.grid_frame = tk.Frame(content_frame, bg="#304160")
        self.grid_frame.pack(side=tk.LEFT, padx=20, pady=10, anchor=tk.NW)

        self.buttons = {}
        for row in range(ROWS):
            for col in range(COLS):
                index = row * COLS + col
                is_white = (row + col) % 2 == 0
                bg_color = "#cce1ff" if is_white else "#aac7ff"
                if index in HIGHLIGHTED:
                    bg_color = "#e63946"
                btn = tk.Button(self.grid_frame, text=str(index), width=6, height=3,
                                bg=bg_color, fg="black", font=("Arial", 10, "bold"), relief="flat")
                btn.grid(row=row, column=col, padx=1, pady=1)
                self.buttons[index] = btn

        right_frame = tk.Frame(content_frame, bg="#304160")
        right_frame.pack(side=tk.RIGHT, padx=20, pady=10, anchor=tk.NE)

        self.port_var = tk.StringVar()
        self.baud_var = tk.StringVar(value="115200")

        ttk.Label(right_frame, text="Port:", background="#304160", foreground="white").pack(anchor=tk.W)
        self.port_menu = ttk.Combobox(right_frame, textvariable=self.port_var,
                                      values=self.get_ports(), width=15)
        self.port_menu.pack(pady=5)

        ttk.Label(right_frame, text="Baudrate:", background="#304160", foreground="white").pack(anchor=tk.W)
        ttk.Entry(right_frame, textvariable=self.baud_var, width=15).pack(pady=5)

        ttk.Button(right_frame, text="Connect", command=self.connect_serial).pack(pady=5, fill=tk.X)
        ttk.Button(right_frame, text="🔁 Refresh", command=self.refresh_ports).pack(pady=5, fill=tk.X)
        ttk.Button(right_frame, text="▶ Start", command=self.start_movement).pack(pady=5, fill=tk.X)
        ttk.Button(right_frame, text="🎬 Demo Mode", command=self.start_demo).pack(pady=5, fill=tk.X)
        ttk.Button(right_frame, text="⏹ Stop", command=self.stop_all).pack(pady=5, fill=tk.X)
        ttk.Button(right_frame, text="🧹 Clear", command=self.clear_output).pack(pady=5, fill=tk.X)

        self.output = tk.Text(right_frame, height=15, width=40, bg="#1e1e1e",
                              fg="#90ee90", insertbackground="white", font=("Consolas", 10))
        self.output.pack(pady=10)

        self.root.after(100, self.read_serial)

    def get_ports(self):
        return [p.device for p in serial.tools.list_ports.comports()]

    def refresh_ports(self):
        ports = self.get_ports()
        self.port_menu['values'] = ports
        if ports:
            self.port_var.set(ports[0])
        self.output.insert(tk.END, "🔁 Ports refreshed\n")

    def connect_serial(self):
        try:
            self.serial_port = serial.Serial(self.port_var.get(), int(self.baud_var.get()), timeout=0.1)
            self.serial_ready = True
            self.output.insert(tk.END, f"✅ Connected to {self.port_var.get()}\n")
        except Exception as e:
            self.output.insert(tk.END, f"❌ Connection error: {e}\n")

    def start_movement(self):
        if not (self.serial_ready and self.serial_port and self.serial_port.is_open):
            self.output.insert(tk.END, "⚠️ Serial not connected!\n")
            return
        self.stop_all()
        self.mode = "start"
        self.initial_sent = False
        self.moving = True
        self.loop_index = 2
        self.send_initial_commands()

    def send_initial_commands(self):
        self.serial_port.write(self.commands[0][0].encode())
        self.serial_port.write(self.commands[1][0].encode())
        self.output.insert(tk.END, "▶ Sent: Initial setup commands\n")
        self.waiting_for_f = True  # Wait for F to proceed to next

    def execute_next_command(self):
        if not self.moving or self.mode != "start":
            return
        cmd, block = self.commands[self.loop_index]
        try:
            self.serial_port.write(cmd.encode())
            self.output.insert(tk.END, f"▶ Sent: {cmd.strip()}\n")
            if block is not None:
                self.highlight_cell(block)
            self.waiting_for_f = True
            self.loop_index += 1
            if self.loop_index >= len(self.commands):
                self.loop_index = 2  # loop only the main commands
        except Exception as e:
            self.output.insert(tk.END, f"❌ Error: {e}\n")
            self.stop_all()

    def start_demo(self):
        self.stop_all()
        self.mode = "demo"
        self.loop_index = 2
        self.moving = True
        self.run_demo_step()

    def run_demo_step(self):
        if not self.moving or self.mode != "demo":
            return
        _, block = self.commands[self.loop_index]
        if block is not None:
            self.highlight_cell(block)
        self.loop_index += 1
        if self.loop_index >= len(self.commands):
            self.loop_index = 2
        self.root.after(700, self.run_demo_step)

    def stop_all(self):
        self.moving = False
        self.mode = None
        self.loop_index = 2
        self.waiting_for_f = False
        self.initial_sent = False
        self.highlight_cell(None)
        if self.serial_ready and self.serial_port and self.serial_port.is_open:
            self.serial_port.write(b"a 0\r\n")
            self.output.insert(tk.END, "⏹ Sent: a 0\n")
        self.output.insert(tk.END, "⏹ Movement stopped.\n")

    def clear_output(self):
        self.output.delete("1.0", tk.END)

    def read_serial(self):
        if self.serial_ready and self.serial_port and self.serial_port.in_waiting:
            try:
                line = self.serial_port.readline().decode().strip()
                self.output.insert(tk.END, f"📥 {line}\n")
                if self.mode == "start" and self.waiting_for_f and line == "F":
                    self.waiting_for_f = False
                    self.root.after(100, self.execute_next_command)
            except Exception as e:
                self.output.insert(tk.END, f"❗ Read error: {e}\n")
        self.root.after(100, self.read_serial)

    def highlight_cell(self, index):
        for i, btn in self.buttons.items():
            base_color = "#e63946" if i in HIGHLIGHTED else ("#cce1ff" if (i // COLS + i % COLS) % 2 == 0 else "#aac7ff")
            btn.config(bg="#38b000" if i == index else base_color)

if __name__ == "__main__":
    root = tk.Tk()
    app = RemoteChessGUI(root)
    root.mainloop()

#!/usr/bin/env python3
"""Форс-1, Raspberry Pi 5: связь с ESP32 A/B, состояния S0-S11, отчёт о дефектах, веб-панель.

Запуск:  python3 force1.py --a /dev/ttyAMA2 --b /dev/ttyAMA0 [--sim]
Веб-панель: http://<ip-pi>:8080  (кнопки Старт / Стоп / Укрытие / Возврат, график колеи, таблица дефектов)
Зависимости: pyserial; камера - rail_vision.py (picamera2 + OpenCV), MPU-9250 - smbus2.
"""
import argparse, csv, json, math, threading, time, os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

try:
    import serial
except ImportError:
    serial = None

# ---------- параметры 1:2 ----------
GAUGE = 760.0
TIE_PITCH = 272.0
WHEEL_D = 50.0
ENC_PPR = 20                      # импульсов на оборот диска LM393 - уточнить по диску
MM_PER_PULSE = math.pi * WHEEL_D / ENC_PPR
THRESH = dict(gauge=8.0, roll=0.8, wear=8.0, joint=12.0, tie=40.0, obstacle_cm=30)
TELESCOPE_STEPS = 2500            # шаги NEMA17 на ход 80 мм (подобрать: 0,79 об × 3200 ≈ 2530)
OUT_DIR = os.path.dirname(os.path.abspath(__file__))


class Esp:
    """Один ESP32: строки команд и телеметрии по UART."""
    def __init__(self, port, name, sim=False):
        self.name, self.sim = name, sim
        self.tel = {}
        self.events = []
        self.lock = threading.Lock()
        self.ser = None if (sim or serial is None) else serial.Serial(port, 115200, timeout=0.1)
        threading.Thread(target=self._reader, daemon=True).start()

    def send(self, cmd):
        if self.ser:
            with self.lock:
                self.ser.write((cmd + "\n").encode())
        else:
            print(f"[{self.name}] {cmd}")

    def _reader(self):
        while True:
            if not self.ser:
                time.sleep(0.1); continue
            line = self.ser.readline().decode(errors="ignore").strip()
            if not line:
                continue
            if line.startswith("T "):
                parts = line.split()
                self.tel = {k: v for k, v in (p.split("=") for p in parts[2:] if "=" in p)}
            elif line.startswith("EV "):
                self.events.append(line)
            elif line.startswith("WR "):
                self.events.append(line)


class Robot:
    def __init__(self, a, b):
        self.a, self.b = a, b
        self.state = "S0"
        self.x_mm = 0.0
        self.d0 = {"A": None, "B": None}
        self.tie_count = 0
        self.last_tie_x = None
        self.defects = []
        self.gauge_log = []
        self.cmd = None
        self.csv = open(os.path.join(OUT_DIR, "defects.csv"), "a", newline="")
        self.w = csv.writer(self.csv)

    # ---------- низкий уровень ----------
    def both(self, c): self.a.send(c); self.b.send(c)
    def drive(self, pwm): self.both(f"M {pwm}")
    def stop(self): self.both("STOP")

    def defect(self, kind, value, note=""):
        rec = dict(t=time.strftime("%H:%M:%S"), x=round(self.x_mm), type=kind, value=round(value, 1), note=note)
        self.defects.append(rec)
        self.w.writerow(rec.values()); self.csv.flush()
        print("ДЕФЕКТ", rec)

    # ---------- измерения ----------
    def measure(self):
        ta, tb = self.a.tel, self.b.tel
        try:
            enc = (int(ta.get("enc", 0)) + int(tb.get("enc", 0))) / 2
            self.x_mm = enc * MM_PER_PULSE
            g = float(tb.get("gauge", GAUGE))
            self.gauge_log.append((round(self.x_mm), g))
            if abs(g - GAUGE) > THRESH["gauge"]:
                self.defect("колея", g - GAUGE)
            for m, t in (("A", ta), ("B", tb)):
                tof = int(t.get("tof", -1))
                if tof > 0:
                    if self.d0[m] is None:
                        self.d0[m] = tof
                    elif tof - self.d0[m] > THRESH["joint"]:
                        self.defect("стык/провал " + m, tof - self.d0[m])
                    elif tof - self.d0[m] > THRESH["wear"]:
                        self.defect("износ головки " + m, tof - self.d0[m])
            tie = int(ta.get("tie", -1))
            if 0 < tie < 100:                               # шпала под датчиком (85 мм)
                if self.last_tie_x is None or self.x_mm - self.last_tie_x > TIE_PITCH * 0.5:
                    if self.last_tie_x is not None and self.x_mm - self.last_tie_x > TIE_PITCH + THRESH["tie"]:
                        self.defect("пропуск шпалы", self.x_mm - self.last_tie_x)
                    self.last_tie_x = self.x_mm; self.tie_count += 1
        except ValueError:
            pass

    # ---------- режим укрытия ----------
    def shelter(self):
        self.state = "S7"; self.stop(); self.a.send("SKID DN"); time.sleep(2.5); self.b.send("SKID DN"); time.sleep(2.5)
        self.state = "S8"; self.b.send(f"TEL {TELESCOPE_STEPS}"); time.sleep(6)
        self.state = "S9"; self.a.send("SKID UP"); time.sleep(2.5); self.b.send("SKID UP"); time.sleep(2.5)
        self.state = "S10"; self.a.send("CAM 0")

    def unshelter(self):
        self.state = "S11"; self.a.send("CAM 90")
        self.a.send("SKID DN"); time.sleep(2.5); self.b.send("SKID DN"); time.sleep(2.5)
        self.b.send(f"TEL {-TELESCOPE_STEPS}"); time.sleep(6); self.b.send("TEL FREE")
        self.a.send("SKID UP"); time.sleep(2.5); self.b.send("SKID UP"); time.sleep(2.5)
        self.state = "S1"

    # ---------- главный цикл ----------
    def run(self):
        self.state = "S0"; self.both("ENC 0"); self.b.send("TEL FREE"); time.sleep(1); self.b.send("TEL 0")
        self.state = "S1"
        while True:
            c, self.cmd = self.cmd, None
            if c == "start" and self.state == "S1":
                self.state = "S2"; self.drive(120)
            elif c == "stop":
                self.stop(); self.state = "S1"
            elif c == "shelter" and self.state in ("S1", "S2"):
                self.shelter()
            elif c == "return" and self.state == "S10":
                self.unshelter()
            if self.state == "S2":
                self.measure()
                for e in self.a.events + self.b.events:
                    print("EVENT", e)
                self.a.events.clear(); self.b.events.clear()
            time.sleep(0.1)


PAGE = """<!doctype html><meta charset=utf-8><title>Форс-1</title>
<style>body{font-family:sans-serif;margin:20px}button{font-size:18px;margin:4px;padding:8px 16px}
table{border-collapse:collapse}td,th{border:1px solid #999;padding:4px 8px}</style>
<h2>Форс-1 - панель оператора</h2>
<div>Состояние: <b id=st>-</b> &nbsp; x = <b id=x>0</b> мм &nbsp; колея = <b id=g>-</b> мм &nbsp; шпал: <b id=tie>0</b></div>
<p><button onclick="c('start')">Старт</button><button onclick="c('stop')">Стоп</button>
<button onclick="c('shelter')">Укрытие (поезд)</button><button onclick="c('return')">Возврат на путь</button></p>
<canvas id=cv width=800 height=160 style="border:1px solid #ccc"></canvas>
<h3>Дефекты</h3><table id=tb><tr><th>время</th><th>x, мм</th><th>тип</th><th>значение</th></tr></table>
<script>
function c(k){fetch('/cmd?'+k)}
setInterval(async()=>{const s=await (await fetch('/state')).json();
st.textContent=s.state;x.textContent=s.x;g.textContent=s.gauge;tie.textContent=s.ties;
tb.innerHTML='<tr><th>время</th><th>x, мм</th><th>тип</th><th>значение</th></tr>'+s.defects.map(d=>`<tr><td>${d.t}</td><td>${d.x}</td><td>${d.type}</td><td>${d.value}</td></tr>`).join('');
const ctx=cv.getContext('2d');ctx.clearRect(0,0,800,160);ctx.strokeStyle='#999';ctx.beginPath();ctx.moveTo(0,80);ctx.lineTo(800,80);ctx.stroke();
ctx.strokeStyle='#36c';ctx.beginPath();s.gauge_log.slice(-800).forEach((p,i)=>{const y=80-(p[1]-760)*5;i?ctx.lineTo(i,y):ctx.moveTo(i,y)});ctx.stroke();},500);
</script>"""


def serve(robot, port=8080):
    class H(BaseHTTPRequestHandler):
        def log_message(self, *a): pass
        def do_GET(self):
            if self.path.startswith("/cmd?"):
                robot.cmd = self.path[5:]; self.send_response(204); self.end_headers(); return
            if self.path == "/state":
                body = json.dumps(dict(state=robot.state, x=round(robot.x_mm), gauge=robot.b.tel.get("gauge", "-"),
                                       ties=robot.tie_count, defects=robot.defects[-30:], gauge_log=robot.gauge_log[-800:]),
                                  ensure_ascii=False).encode()
                ct = "application/json"
            else:
                body, ct = PAGE.encode(), "text/html; charset=utf-8"
            self.send_response(200); self.send_header("Content-Type", ct); self.end_headers(); self.wfile.write(body)
    ThreadingHTTPServer(("", port), H).serve_forever()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--a", default="/dev/ttyAMA2"); ap.add_argument("--b", default="/dev/ttyAMA0")
    ap.add_argument("--sim", action="store_true", help="без железа: команды печатаются в консоль")
    args = ap.parse_args()
    r = Robot(Esp(args.a, "A", args.sim), Esp(args.b, "B", args.sim))
    threading.Thread(target=serve, args=(r,), daemon=True).start()
    print("веб-панель: http://0.0.0.0:8080")
    r.run()

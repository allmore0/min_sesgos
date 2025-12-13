from flask import Flask, request, jsonify, render_template
import os
import json
import csv
import requests
import io
from encryption import MultiSubstitutionCipher
from model_logic import RecruitmentAI

app = Flask(__name__, static_folder='static', template_folder='templates')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
CSV_PATH = os.path.join(DATA_DIR, 'new_candidates.csv')
JSON_DB_PATH = os.path.join(DATA_DIR, 'database.json')
DATA_DIR = 'data'
ENC_DB_PATH = os.path.join(DATA_DIR, 'encrypted_database.txt')
GITHUB_CSV_URL = "https://raw.githubusercontent.com/allmore0/min_sesgos/main/candidatos.csv"

cipher = MultiSubstitutionCipher()

def get_next_id():
    max_id = 0
    
    # Check Remote
    try:
        url = GITHUB_CSV_URL
        r = requests.get(url)
        if r.status_code != 200:
            url = GITHUB_CSV_URL.replace('main', 'master')
            r = requests.get(url)
        
        if r.status_code == 200:
            lines = r.text.strip().splitlines()
            if len(lines) > 1:
                # Skip header, iterate to find max (assuming strict order is not guaranteed)
                # Or just check last if ordered. Checking last is safer for speed.
                last_line = lines[-1]
                parts = last_line.split(',')
                if parts and parts[0].startswith('DS'):
                     try:
                        uid = int(parts[0].replace("DS", ""))
                        if uid > max_id: max_id = uid
                     except: pass
    except:
        pass

    # Check Local
    if os.path.exists(CSV_PATH):
        try:
            with open(CSV_PATH, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                rows = list(reader)
                if len(rows) > 1:
                    for row in rows[1:]:
                        if row and row[0].startswith('DS'):
                            try:
                                uid = int(row[0].replace("DS", ""))
                                if uid > max_id: max_id = uid
                            except: pass
        except: pass
        
    return f"DS{max_id + 1:02d}"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    try:
        data = request.json
        # 1. Generate ID
        new_id = get_next_id()
        
        # 2. Extract Data from JSON Form
        dp = data.get('datos_personales', {})
        dl = data.get('datos_laborales_y_habilidades', {})
        pc = data.get('porcentajes_conocimiento', {})
        
        # 3. Map to CSV Format
        # Default fillers for missing fields
        row = [
            new_id,
            dl.get('años_experiencia', 0),
            dp.get('nombre', ''),
            dp.get('apellido_paterno', ''),
            dp.get('apellido_materno', ''),
            dp.get('edad', 0),
            dp.get('genero', ''),
            dl.get('titulo_profesional', ''),
            dl.get('habilidades', [{}])[0].get('nombre', '') if dl.get('habilidades') else '',
            dl.get('habilidades', [{}, {}])[1].get('nombre', '') if len(dl.get('habilidades', [])) > 1 else '',
            "Online", # Colonia
            "", # Deporte
            "", # Musica
            "", # Pasatiempo
            "", # Lectura
            "", # Logro
            "Online Univ", # Universidad
            "2024", # Año
            dl.get('certificaciones', [''])[0] if dl.get('certificaciones') else '',
            dl.get('certificaciones', ['', ''])[1] if len(dl.get('certificaciones', [])) > 1 else '',
            float(pc.get('python', 0)) / 100.0,
            float(pc.get('r', 0)) / 100.0,
            float(pc.get('sql', 0)) / 100.0,
            float(pc.get('estadistica_avanzada', 0)) / 100.0,
            30000, # Sueldo Default
            "Inmediata ", # Disp Contratacion
            "No reubicación", # Viaje
            dl.get('idioma', ''),
            dl.get('nivel_idioma', ''),
            "", "", # Idioma 2
            dp.get('religion', ''),
            dp.get('preferencia_politica', ''),
            "C", # NSE
            dp.get('raza', '')
        ]
        
        # 4. Append to CSV
        # Ensure headers exist if new file
        if not os.path.exists(CSV_PATH):
            headers = ["ID","Años de experiencia","Nombre(s)","Apellido_Paterno","Apellido_Materno","Edad","Género","Título_Principal","Habilidades_Personales_1","Habilidades_Personales_2","Colonia","Deporte","Música","Pasatiempo","Lectura","Logro_Profesional","Universidad","Año_Graduación","Certificación_1","Certificación_2","Python_Porcentaje","R_Porcentaje","SQL_Porcentaje","Estadística_Avanzada_Porcentaje","Sueldo_mensual","Disponibilidad_contratación","Disponibilidad_de_viajar","Idioma_1","Nivel_idioma_1","Idioma_2","Nivel_idioma_2","Religión_ficticia","Afiliación_política_ficticia","Nivel_Socio_Económico(NSE_AMAI)","Etnia_(Autodefinición)"]
            with open(CSV_PATH, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(headers)

        with open(CSV_PATH, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(row)
            
        # 5. Append to JSON DB
        db_data = []
        if os.path.exists(JSON_DB_PATH):
            try:
                with open(JSON_DB_PATH, 'r') as f:
                    content = f.read().strip()
                    if content:
                        db_data = json.loads(content)
            except:
                pass
        
        record_with_id = data.copy()
        record_with_id['id'] = new_id
        db_data.append(record_with_id)
        
        with open(JSON_DB_PATH, 'w', encoding='utf-8') as f:
            json.dump(db_data, f, indent=2)
            
        # 6. Encrypt
        encrypted_content = cipher.encrypt(json.dumps(db_data))
        with open(ENC_DB_PATH, 'w', encoding='utf-8') as f:
            f.write(encrypted_content)
            
        # 7. Run AI Model
        model = RecruitmentAI(CSV_PATH, remote_url=GITHUB_CSV_URL)
        results = model.run_analysis(new_id)
        
        return jsonify({
            "status": "success",
            "id": new_id,
            "results": results,
            "is_best": results['current_candidate']['is_best']
        })
        
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)


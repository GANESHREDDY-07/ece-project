import os, sqlite3
from datetime import datetime
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, jsonify, request, send_from_directory, session

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get('MESSMIND_DB_PATH', os.path.join(BASE_DIR, 'messmind.db'))
app = Flask(__name__, static_folder=BASE_DIR, static_url_path='')
app.secret_key = os.environ.get('MESSMIND_SECRET_KEY', 'local-development-only-change-this-secret')
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax', SESSION_COOKIE_SECURE=os.environ.get('COOKIE_SECURE', '0') == '1')

MEMBERS = [
    ('LPU001', 'Ganesh Reddy', 'admin'),
    ('LPU002', 'Rohith', 'student'),
    ('LPU003', 'HarinathReddy', 'student'),
    ('LPU004', 'Tharun', 'student'),
]
INITIAL_PASSWORD = os.environ.get('MESSMIND_INITIAL_PASSWORD', 'ChangeMe@123')

def db():
    c = sqlite3.connect(DB_PATH); c.row_factory = sqlite3.Row; return c

def init_db():
    c = db(); q = c.cursor()
    user_cols = [col[1] for col in q.execute("PRAGMA table_info(users)").fetchall()]
    if user_cols and 'password_hash' not in user_cols:
        q.execute('DROP TABLE users')
    q.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password_hash TEXT NOT NULL, role TEXT NOT NULL, display_name TEXT NOT NULL)''')
    q.execute('''CREATE TABLE IF NOT EXISTS waste_records (id INTEGER PRIMARY KEY AUTOINCREMENT, student_name TEXT NOT NULL, student_id TEXT NOT NULL, meal TEXT NOT NULL, weight REAL NOT NULL, record_date TEXT NOT NULL, record_time TEXT NOT NULL, flag TEXT NOT NULL)''')
    # Fresh install only: create the four agreed project accounts. Existing passwords are never overwritten.
    for uid, name, role in MEMBERS:
        q.execute('SELECT username FROM users WHERE username=?', (uid,))
        if not q.fetchone():
            q.execute('INSERT INTO users VALUES (?,?,?,?)', (uid, generate_password_hash(INITIAL_PASSWORD), role, name))
    c.commit(); c.close()

def login_required(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        if 'username' not in session: return jsonify({'error':'Please sign in'}), 401
        return fn(*args, **kwargs)
    return wrapped

def current_user():
    return {'username':session['username'], 'role':session['role'], 'displayName':session['display_name'], 'studentId':session['username'] if session['role']=='student' else ''}

@app.route('/')
def home(): return send_from_directory(BASE_DIR, 'index.html')
@app.route('/login.html')
def login_page(): return send_from_directory(BASE_DIR, 'login.html')
@app.route('/api/login', methods=['POST'])
def api_login():
    data=request.get_json(silent=True) or {}; username=str(data.get('username','')).strip().upper(); password=str(data.get('password',''))
    c=db(); user=c.execute('SELECT * FROM users WHERE username=?',(username,)).fetchone(); c.close()
    if not user or not check_password_hash(user['password_hash'], password): return jsonify({'error':'Invalid ID or password'}), 401
    session.clear(); session['username']=user['username']; session['role']=user['role']; session['display_name']=user['display_name']
    return jsonify({'status':'success','user':current_user()})

@app.route('/api/me')
@login_required
def me(): return jsonify({'user':current_user()})

@app.route('/api/logout', methods=['POST'])
@login_required
def logout(): session.clear(); return jsonify({'status':'success'})

@app.route('/api/records', methods=['GET','POST'])
@login_required
def records():
    c=db()
    if request.method=='GET':
        if session['role']=='admin': rows=c.execute('SELECT * FROM waste_records ORDER BY id DESC').fetchall()
        else: rows=c.execute('SELECT * FROM waste_records WHERE student_id=? ORDER BY id DESC',(session['username'],)).fetchall()
        c.close(); return jsonify([{'id':r['id'],'name':r['student_name'],'studentId':r['student_id'],'meal':r['meal'],'weight':r['weight'],'date':r['record_date'],'time':r['record_time'],'flag':r['flag']} for r in rows])
    data=request.get_json(silent=True) or {}
    if session['role']=='student': student_id=session['username']
    else: student_id=str(data.get('studentId','')).strip().upper()
    member=next((m for m in MEMBERS if m[0]==student_id),None)
    try: weight=float(data.get('weight',0))
    except (TypeError,ValueError): weight=0
    meal=str(data.get('meal','Lunch')).strip().title()
    if not member or not (0 < weight <= 5000) or meal not in ('Breakfast','Lunch','Dinner'):
        c.close(); return jsonify({'error':'Choose a valid student, meal and weight (1–5000 g)'}),400
    now=datetime.now(); date=now.strftime('%Y-%m-%d'); tm=now.strftime('%I:%M %p'); flag='High' if weight>=250 else 'Recorded'
    cur=c.execute('INSERT INTO waste_records(student_name,student_id,meal,weight,record_date,record_time,flag) VALUES(?,?,?,?,?,?,?)',(member[1],member[0],meal,weight,date,tm,flag)); c.commit(); rid=cur.lastrowid; c.close()
    return jsonify({'status':'success','record':{'id':rid,'name':member[1],'studentId':member[0],'meal':meal,'weight':weight,'date':date,'time':tm,'flag':flag}}),201

@app.route('/api/stats')
@login_required
def stats():
    c=db(); where='' if session['role']=='admin' else ' WHERE student_id=?'; params=() if session['role']=='admin' else (session['username'],)
    rows=c.execute('SELECT weight,student_id,record_date FROM waste_records'+where,params).fetchall(); c.close()
    today=datetime.now().strftime('%Y-%m-%d'); todays=[r for r in rows if r['record_date']==today]; total=sum(r['weight'] for r in todays); all_total=sum(r['weight'] for r in rows)
    return jsonify({'todayTotalGrams':total,'todayTotalKg':round(total/1000,2),'studentCount':len(set(r['student_id'] for r in todays)),'averageWasteGrams':round(total/len(todays)) if todays else 0,'allTotalKg':round(all_total/1000,2),'highestEventGrams':max((r['weight'] for r in rows),default=0)})

if __name__=='__main__':
    init_db(); print('MessMind running at http://127.0.0.1:5000'); app.run(host='0.0.0.0',port=int(os.environ.get('PORT',5000)),debug=False)

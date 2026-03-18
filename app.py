from flask import Flask, render_template, request, redirect, url_for, session, flash
from pathlib import Path
from datetime import datetime, timedelta
import json, shutil, subprocess, sys, re, hashlib
import psutil

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / 'data'
INSTANCES_DIR = BASE_DIR / 'instances'
BASE_SOURCE_DIR = BASE_DIR / 'base_source'
app = Flask(__name__)
app.secret_key = 'Zenith-panel-secret-key'
ADMIN_USERNAME = 'Zenith'
ADMIN_PASSWORD = 'Zenith7777'
DATE_FMT = '%Y-%m-%d %H:%M:%S'

DEFAULT_REPLIES = {
    'help_welcome': '[C][B][33FFF3]\n\n\nاهلا وسهلا  {user_name}\n\n\n',
    'help_menu_1': """[C][B]
[FFFF00]❖━━━╮
        [E4287C][B][C]لجعل السكود إلي :
              [E42217][B][C]@3
              [717D7D][B][C]@5
              [F52887][B][C]@6
╰━━─[FFFF00]─╯""",
    'help_menu_2': """[C][B]
              [FFFF00]❖━━━╮
        [FFD700][B][C]فتح فريق 5 للاعب:
              [00BFFF]@inv <id>
╰━━─[FFFF00]─╯
              [FFFF00]❖━━━╮
        [F62817][B][C]سبام طلبات انضمام للفريق:
              [FFFFFF]@sp <id>
╰━━─[FFFF00]─╯
              [FFFF00]❖━━━╮
        [2B65EC][B][C]سبام طلبات انضمام للروم:
              [FFFFFF]@room <id>
╰━━─[FFFF00]─╯
              [FFFF00]❖━━━╮
        [FFD700][B][C]فحص حالة باند للاعب:
              [306EFF][B][C]@check <id>
╰━━─[FFFF00]─╯
              [FFFF00]❖━━━╮
        [C12869][B][C]عرض معلومات الاعب
              [FFFFFF][B][C]@info
╰━━─[FFFF00]─╯""",
    'help_menu_3': """[C][B]
  
              [FFFF00]❖━━━╮
        [157DEC][B][C]من بسكواد اللاعب:
              [FFFFFF][B][C]@status <id>
╰━━─[FFFF00]─╯
              [FFFF00]❖━━━╮
        [4C7D7E][B][C]دعوة لاعب معك للفريق:
              [FFFFFF]@send <id>
╰━━─[FFFF00]─╯
              [FFFF00]❖━━━╮
        [4AA02C][B][C]لاغ عبر تيم كود:
              [00BFFF]@lag <team cod>
╰━━─[FFFF00]─╯""",
    'help_menu_4': """     [C][B]         [FFFF00]❖━━━╮
        [FFFC17][B][C]لاغ متوسط عبر تيم كود:
              [00BFFF]@lag <team cod> 2
╰━━─[FFFF00]─╯
              [FFFF00]❖━━━╮
        [C35617][B][C]لاغ قوي عبر تيم كود:
              [00BFFF]@lag <team cod> 3
╰━━─[FFFF00]─╯ """,
    'help_menu_5': """   
              [FFFF00]❖━━━╮
        [F62217][B][C]طرد البوت :
              [FFFFFF]@solo
╰━━─[FFFF00]─╯
              [FFFF00]❖━━━╮
        [357EC7][B][C]أراحت البوت 10 ثواني 
              [FFFFFF]@rest
╰━━─[FFFF00]─╯
              [FFFF00]❖━━━╮
        [4CC417][B][C]لمعرفة المطور وتواصل
              [b][c][6C2DC7]@admin
╰━━─[FFFF00]─╯""",
    'admin_reply': """[C][B][F62817]
إذا كنت من محبي لعبة فري فاير وتبحث عن تفوق ؟
نقدم لك عروض ومزايا تجعلك انت الملك !
لشراء بوت او اي شي ول استفسار تواصل معي

[FFFFFF] telegram:[00FF00]@Zenith_7x
 
[b][i][A5E2CF] dev by Zenith """,
}

REPLY_LABELS = {
    'help_welcome': 'ترحيب قائمة @help',
    'help_menu_1': 'تعديل الفريق',
    'help_menu_2': 'فتح سكواد للاعب + سبام + معلومات',
    'help_menu_3': 'فحص سكواد + لاڨ',
    'help_menu_4': 'لاڨ فقط',
    'help_menu_5': 'تحكم في البوت + تواصل ',
    'admin_reply': 'رد الرسالة امر @admin',
}

DEFAULT_COMMANDS = {
    'help': '@help', 'admin': '@admin', 'sp': '@sp', 'status': '@status', 'inv': '@inv',
    'spam': '@spam', 'info': '@info', 'check': '@check', 'lag': '@lag',
    'solo': '@solo', 'rest': '@rest', 'start': '@start', 'spm': '@spm',
    'send': '@send', 'room': '@room',
}

COMMAND_LABELS = {
    'help': 'أمر القائمة', 'admin': 'أمر المطور', 'sp': 'أمر سبام الانضمام', 'status': 'أمر حالة اللاعب',
    'inv': 'أمر فتح فريق', 'spam': 'أمر طلبات الصداقة', 'info': 'أمر المعلومات',
    'check': 'أمر فحص الباند', 'lag': 'أمر اللاغ', 'solo': 'أمر طرد البوت', 'rest': 'أمر الراحة', 'start': 'أمر فورس ستارت', 'spm': 'أمر سبام رسائل الفريق',
    'send': 'أمر الدعوة معك', 'room': 'أمر سبام الروم',
}


def now_dt():
    return datetime.now()


def parse_dt(value):
    try:
        return datetime.strptime(value, DATE_FMT)
    except Exception:
        return None


def fmt_dt(dt):
    return dt.strftime(DATE_FMT)


def read_json(path, default):
    path = Path(path)
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return default


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')


def get_users():
    return read_json(DATA_DIR / 'users.json', [])


def save_users(users):
    write_json(DATA_DIR / 'users.json', users)


def get_defaults():
    return {
        'bot_name': 'Zenith',
        'guest_uid': '',
        'guest_password': '',
        'replies': DEFAULT_REPLIES.copy(),
        'commands': DEFAULT_COMMANDS.copy(),
    }


def sync_accs_txt():
    data = {u['uid']: u['password'] for u in get_users()}
    (BASE_DIR / 'accs.txt').write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')


def normalize_cfg(cfg=None):
    base = get_defaults()
    cfg = cfg or {}
    replies = base['replies'].copy()
    replies.update(cfg.get('replies', {}))
    commands = base['commands'].copy()
    commands.update(cfg.get('commands', {}))
    return {
        'bot_name': cfg.get('bot_name', base['bot_name']) or 'Zenith',
        'guest_uid': str(cfg.get('guest_uid', base['guest_uid']) or '').strip(),
        'guest_password': str(cfg.get('guest_password', base['guest_password']) or '').strip(),
        'replies': replies,
        'commands': commands,
    }


def build_user_record(uid, password, days, old=None):
    days = max(1, int(days))
    start = now_dt()
    created = old['created_at'] if old and old.get('created_at') else fmt_dt(start)
    return {
        'uid': uid,
        'password': password,
        'days': days,
        'created_at': created,
        'expires_at': fmt_dt(start + timedelta(days=days)),
    }


def is_user_expired(user):
    exp = parse_dt(user.get('expires_at', ''))
    return not exp or now_dt() > exp


def days_left(user):
    exp = parse_dt(user.get('expires_at', ''))
    if not exp:
        return 0
    delta = exp - now_dt()
    if delta.total_seconds() <= 0:
        return 0
    return delta.days + (1 if delta.seconds > 0 else 0)


def replace_command_tokens(text, commands):
    for key, default in DEFAULT_COMMANDS.items():
        new = commands.get(key, default)
        if new and new != default:
            text = text.replace(default, new)
    return text


def patch_main_source(src, cfg):
    src = src.replace('by Zenith', f"by {cfg.get('bot_name', 'Zenith')}")
    src = src.replace('dev by Zenith', f"dev by {cfg.get('bot_name', 'Zenith')}")

    def _fmt(value):
        return replace_command_tokens(value, cfg['commands'])

    src = re.sub(
        r'(if "1200" in data\.hex\(\)\[0:4\] and b"@admin" in data:.*?self\.GenResponsMsg\(\s*)f""".*?"""(, uid\s*\)\s*\)\s*\))',
        lambda m: m.group(1) + 'f"""' + _fmt(cfg['replies']['admin_reply']) + '"""' + m.group(2),
        src,
        count=1,
        flags=re.S,
    )

    help_start = src.find('Started Help\\n")')
    help_end = src.find('if "1200" in data.hex()[0:4] and b"/ai" in data:', help_start)
    if help_start != -1 and help_end != -1:
        section = src[help_start:help_end]
        payloads = [
            cfg['replies']['help_welcome'],
            cfg['replies']['help_menu_1'],
            cfg['replies']['help_menu_2'],
            cfg['replies']['help_menu_3'],
            cfg['replies']['help_menu_4'],
            cfg['replies']['help_menu_5'],
        ]
        payloads = [_fmt(x) for x in payloads]
        idx = {'i': 0}
        patt = re.compile(r'f""".*?"""\s*,uid', re.S)

        def repl(mm):
            i = idx['i']
            if i >= len(payloads):
                return mm.group(0)
            idx['i'] += 1
            return 'f"""' + payloads[i] + '""",uid'

        section = patt.sub(repl, section)
        src = src[:help_start] + section + src[help_end:]

    src = replace_command_tokens(src, cfg['commands'])

    src = re.sub(
        r"with open\('accs\.txt', 'r'\) as file:\n\s*data = json\.load\(file\)\nids_passwords = list\(data\.items\(\)\)",
        "with open(os.path.join(os.path.dirname(__file__), 'accs.txt'), 'r', encoding='utf-8') as file:\n    data = json.load(file)\nids_passwords = list(data.items())",
        src,
    )

    src = re.sub(
        r'if __name__ == "__main__":\n\s*try:\n\s*client_thread = FF_CLIENT\(id=.*?restart_program\(\)',
        'if __name__ == "__main__":\n    pass',
        src,
        flags=re.S,
    )
    return src


def build_instance_info(uid, password, cfg, user):
    return {
        'uid': uid,
        'password_sha256': hashlib.sha256(password.encode('utf-8')).hexdigest(),
        'source_dir': f'instances/{uid}',
        'base_source_dir': 'base_source',
        'isolated': True,
        'bot_name': cfg.get('bot_name', 'Zenith'),
        'guest_uid': cfg.get('guest_uid', ''),
        'days': user.get('days', 0),
        'expires_at': user.get('expires_at', ''),
        'editable_replies': list(cfg.get('replies', {}).keys()),
        'editable_commands': list(cfg.get('commands', {}).keys()),
    }


def ensure_instance(uid, password, cfg, user):
    cfg = normalize_cfg(cfg)
    target = INSTANCES_DIR / uid
    target.mkdir(parents=True, exist_ok=True)

    for item in BASE_SOURCE_DIR.iterdir():
        if not item.is_file():
            continue
        destination = target / item.name
        if item.name == 'main.py':
            source_text = item.read_text(encoding='utf-8', errors='ignore')
            destination.write_text(patch_main_source(source_text, cfg), encoding='utf-8')
        else:
            shutil.copy2(item, destination)

    guest_uid = cfg.get('guest_uid', '').strip() or uid
    guest_password = cfg.get('guest_password', '').strip() or password
    (target / 'accs.txt').write_text(json.dumps({guest_uid: guest_password}, ensure_ascii=False, indent=2), encoding='utf-8')
    write_json(target / 'bot_config.json', cfg)
    write_json(target / 'instance_info.json', build_instance_info(uid, password, cfg, user))
    (target / 'run.py').write_text(
        'import subprocess, sys, pathlib\n'
        'base = pathlib.Path(__file__).resolve().parent\n'
        'subprocess.run([sys.executable, str(base / "main.py")], cwd=str(base))\n',
        encoding='utf-8'
    )


def find_user(uid):
    for u in get_users():
        if u['uid'] == uid:
            return u
    return None


def user_online(uid):
    pid = read_json(DATA_DIR / 'runtime.json', {}).get(uid, {}).get('pid')
    try:
        return bool(pid) and psutil.pid_exists(pid) and psutil.Process(pid).is_running()
    except Exception:
        return False


def start_bot(uid):
    user = find_user(uid)
    if not user:
        return False, 'الحساب غير موجود'
    if is_user_expired(user):
        return False, 'انتهت مدة الحساب، لازم الأدمن يجدد الأيام'
    target = INSTANCES_DIR / uid
    if not target.exists():
        return False, 'مجلد السورس غير موجود'
    if user_online(uid):
        return True, 'البوت شغال بالفعل'
    proc = subprocess.Popen([sys.executable, 'main.py'], cwd=str(target), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    rt = read_json(DATA_DIR / 'runtime.json', {})
    rt[uid] = {'pid': proc.pid}
    write_json(DATA_DIR / 'runtime.json', rt)
    return True, f'تم تشغيل البوت يا اخي '


def stop_bot(uid):
    rt = read_json(DATA_DIR / 'runtime.json', {})
    pid = rt.get(uid, {}).get('pid')
    if not pid:
        return False, 'لا يوجد PID'
    try:
        p = psutil.Process(pid)
        p.terminate()
        try:
            p.wait(timeout=5)
        except psutil.TimeoutExpired:
            p.kill()
    except Exception as e:
        rt[uid] = {'pid': None}
        write_json(DATA_DIR / 'runtime.json', rt)
        return False, f'تعذر الإيقاف: {e}'
    rt[uid] = {'pid': None}
    write_json(DATA_DIR / 'runtime.json', rt)
    return True, 'تم إيقاف البوت'


def get_cfg_for_uid(uid):
    return normalize_cfg(read_json(INSTANCES_DIR / uid / 'bot_config.json', get_defaults()))


def collect_cfg_from_form(form, current=None):
    cfg = normalize_cfg(current)
    cfg['bot_name'] = form.get('bot_name', cfg['bot_name']).strip() or 'Zenith'
    cfg['guest_uid'] = form.get('guest_uid', cfg['guest_uid']).strip()
    cfg['guest_password'] = form.get('guest_password', cfg['guest_password']).strip()

    replies = cfg['replies'].copy()
    for key in DEFAULT_REPLIES:
        replies[key] = form.get(f'reply__{key}', replies[key])
    cfg['replies'] = replies

    commands = cfg['commands'].copy()
    for key in DEFAULT_COMMANDS:
        value = form.get(f'cmd__{key}', commands[key]).strip()
        commands[key] = value if value.startswith('@') else ('@' + value.lstrip('@') if value else DEFAULT_COMMANDS[key])
    cfg['commands'] = commands
    return cfg


@app.context_processor
def inject_helpers():
    return {'reply_labels': REPLY_LABELS, 'command_labels': COMMAND_LABELS}


@app.route('/')
def index():
    return render_template('login.html')


@app.route('/login', methods=['POST'])
def login():
    uid = request.form.get('uid', '').strip()
    password = request.form.get('password', '').strip()
    if uid == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        session['admin'] = True
        session['uid'] = uid
        return redirect(url_for('admin'))
    user = find_user(uid)
    if user and user['password'] == password:
        if is_user_expired(user):
            flash('انتهت مدة هذا الحساب. تواصل مع الأدمن للتجديد.')
            return redirect(url_for('index'))
        session['admin'] = False
        session['uid'] = uid
        return redirect(url_for('dashboard'))
    flash('بيانات الدخول غير صحيحة')
    return redirect(url_for('index'))


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


@app.route('/admin')
def admin():
    if not session.get('admin'):
        return redirect(url_for('index'))
    users = []
    for u in get_users():
        users.append({
            **u,
            'online': user_online(u['uid']),
            'expired': is_user_expired(u),
            'days_left': days_left(u),
            'source_dir': f'instances/{u["uid"]}',
        })
    return render_template('admin.html', users=users, default_cfg=get_defaults())


@app.route('/admin/create', methods=['POST'])
def create_account():
    if not session.get('admin'):
        return redirect(url_for('index'))
    uid = request.form.get('uid', '').strip()
    password = request.form.get('password', '').strip()
    days = request.form.get('days', '30').strip() or '30'
    if not uid or not password:
        flash('لازم UID و Password')
        return redirect(url_for('admin'))
    users = get_users()
    if any(u['uid'] == uid for u in users):
        flash('الحساب موجود بالفعل')
        return redirect(url_for('admin'))
    user = build_user_record(uid, password, days)
    users.append(user)
    save_users(users)
    sync_accs_txt()
    cfg = collect_cfg_from_form(request.form, get_defaults())
    ensure_instance(uid, password, cfg, user)
    flash(f'تم إنشاء حساب موقع + لوحة تحكم + سورس مستقل للحساب {uid}')
    return redirect(url_for('admin'))


@app.route('/admin/user/<uid>', methods=['GET', 'POST'])
def edit_user(uid):
    if not session.get('admin'):
        return redirect(url_for('index'))
    user = find_user(uid)
    if not user:
        flash('الحساب غير موجود')
        return redirect(url_for('admin'))
    cfg = get_cfg_for_uid(uid)
    if request.method == 'POST':
        new_uid = request.form.get('uid', '').strip()
        new_password = request.form.get('password', '').strip()
        days = request.form.get('days', str(user.get('days', 30))).strip() or '30'
        if not new_uid or not new_password:
            flash('UID و Password مطلوبين')
            return redirect(url_for('edit_user', uid=uid))
        users = get_users()
        for i, u in enumerate(users):
            if u['uid'] == uid:
                users[i] = build_user_record(new_uid, new_password, days, old=u)
                user = users[i]
                break
        save_users(users)
        sync_accs_txt()
        cfg = collect_cfg_from_form(request.form, cfg)
        if new_uid != uid:
            old = INSTANCES_DIR / uid
            new = INSTANCES_DIR / new_uid
            if old.exists():
                if new.exists():
                    shutil.rmtree(new)
                old.rename(new)
            runtime = read_json(DATA_DIR / 'runtime.json', {})
            if uid in runtime:
                runtime[new_uid] = runtime.pop(uid)
                write_json(DATA_DIR / 'runtime.json', runtime)
            if session.get('uid') == uid:
                session['uid'] = new_uid
            uid = new_uid
        ensure_instance(uid, new_password, cfg, user)
        flash('تم تحديث الحساب وبيانات الضيف والأوامر والقائمة')
        return redirect(url_for('edit_user', uid=uid))
    return render_template('edit_user.html', uid=uid, user=user, cfg=cfg, days_left=days_left(user), expired=is_user_expired(user))


@app.route('/dashboard')
def dashboard():
    uid = session.get('uid')
    if not uid:
        return redirect(url_for('index'))
    if session.get('admin'):
        return redirect(url_for('admin'))
    user = find_user(uid)
    if not user:
        session.clear()
        return redirect(url_for('index'))
    if is_user_expired(user):
        session.clear()
        flash('انتهت مدة الحساب')
        return redirect(url_for('index'))
    cfg = get_cfg_for_uid(uid)
    return render_template(
        'dashboard.html',
        uid=uid,
        user=user,
        cfg=cfg,
        online=user_online(uid),
        source_dir=f'instances/{uid}',
        instance_info=read_json(INSTANCES_DIR / uid / 'instance_info.json', {}),
        days_left=days_left(user),
    )


@app.route('/dashboard/save', methods=['POST'])
def user_save():
    uid = session.get('uid')
    if not uid or session.get('admin'):
        return redirect(url_for('index'))
    user = find_user(uid)
    if not user or is_user_expired(user):
        session.clear()
        return redirect(url_for('index'))
    cfg = collect_cfg_from_form(request.form, get_cfg_for_uid(uid))
    ensure_instance(uid, user['password'], cfg, user)
    flash('تم الحفظ')
    return redirect(url_for('dashboard'))


@app.route('/bot/<uid>/<action>', methods=['POST'])
def toggle_bot(uid, action):
    if not session.get('uid'):
        return redirect(url_for('index'))
    if not session.get('admin') and session.get('uid') != uid:
        return redirect(url_for('dashboard'))
    ok, msg = start_bot(uid) if action == 'start' else stop_bot(uid)
    flash(msg)
    return redirect(url_for('admin' if session.get('admin') else 'dashboard'))


def bootstrap():
    DATA_DIR.mkdir(exist_ok=True)
    INSTANCES_DIR.mkdir(exist_ok=True)
    users = get_users()
    changed = False
    upgraded = []
    for u in users:
        if 'days' not in u or 'expires_at' not in u or 'created_at' not in u:
            u = build_user_record(u['uid'], u['password'], u.get('days', 30), old=u)
            changed = True
        upgraded.append(u)
    if changed:
        save_users(upgraded)
    if not users and (BASE_DIR / 'base_source' / 'accs.txt').exists():
        accs = read_json(BASE_DIR / 'base_source' / 'accs.txt', {})
        upgraded = [build_user_record(k, v, 30) for k, v in accs.items()]
        save_users(upgraded)
    if not (DATA_DIR / 'runtime.json').exists():
        write_json(DATA_DIR / 'runtime.json', {})
    sync_accs_txt()
    for user in get_users():
        cfg = normalize_cfg(read_json(INSTANCES_DIR / user['uid'] / 'bot_config.json', get_defaults()))
        ensure_instance(user['uid'], user['password'], cfg, user)


bootstrap()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

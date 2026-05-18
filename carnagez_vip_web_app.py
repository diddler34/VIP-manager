from flask import Flask, request, redirect, url_for, session, render_template_string
from datetime import datetime, timedelta
import json
import os

# ============================================================
# CARNAGE Z VIP WEB MANAGER
# Beginner-friendly version: one Python file.
# ============================================================

app = Flask(__name__)

# Change this secret to anything random before deploying online.
app.secret_key = "CHANGE_THIS_SECRET_KEY_CARNAGEZ"

# -----------------------------
# SETTINGS YOU CAN CHANGE
# -----------------------------
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "1234"
ACTIVATION_CODE = "CZP2026"
RENEWAL_DAYS = 30
INSURANCE_REDEEM_COOLDOWN_HOURS = 30

APP_FOLDER = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(APP_FOLDER, "carnagez_data.json")


# ============================================================
# DATA FUNCTIONS
# ============================================================
def load_data():
    starter_data = {
        "vip": [],
        "insurance": []
    }

    if not os.path.exists(DATA_FILE):
        save_data(starter_data)
        return starter_data

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)

        if not isinstance(data, dict):
            data = starter_data

        data.setdefault("vip", [])
        data.setdefault("insurance", [])
        return data

    except Exception:
        save_data(starter_data)
        return starter_data


def save_data(data):
    data.setdefault("vip", [])
    data.setdefault("insurance", [])

    with open(DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)

    print(f"Data saved to: {DATA_FILE}")


def calculate_days_left(expires_string):
    try:
        expires_date = datetime.strptime(expires_string, "%Y-%m-%d").date()
        today = datetime.now().date()
        return (expires_date - today).days
    except Exception:
        return -1


def get_redeem_cooldown(person):
    redeem_time = person.get("redeem_cooldown")

    if not redeem_time:
        return None

    try:
        cooldown_end = datetime.fromisoformat(redeem_time)
        now = datetime.now()

        if now >= cooldown_end:
            return None

        remaining = cooldown_end - now
        total_seconds = int(remaining.total_seconds())

        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60

        return f"{hours:02}:{minutes:02}:{seconds:02}"

    except Exception:
        return None


def login_required():
    return session.get("logged_in") is True


# ============================================================
# LANGUAGE
# ============================================================
def get_lang():
    return session.get("lang", "en")


TEXT = {
    "en": {
        "login_title": "Carnage Z Control Panel",
        "username": "Username",
        "password": "Password",
        "login": "Login",
        "wrong_login": "Wrong username or password.",
        "dashboard": "Dashboard",
        "vip_tab": "VIP Members",
        "insurance_tab": "Car Insurance",
        "add_person": "Add Person",
        "logout": "Logout",
        "language": "Português",
        "name": "Name",
        "discord": "Discord Username",
        "steam_id": "Steam ID",
        "days_left": "Days Left",
        "expires": "Expires",
        "status": "Status",
        "active": "Active",
        "expired": "Expired",
        "actions": "Actions",
        "redeem": "Redeem",
        "cooldown": "Cooldown",
        "details": "Details",
        "confirm_payment": "+30 Days",
        "alter_time": "Alter Time",
        "delete_vip": "Delete VIP",
        "activation_code": "Activation Code",
        "new_days_left": "New Days Left",
        "save": "Save",
        "cancel": "Cancel",
        "wrong_code": "Wrong activation code.",
        "empty_fields": "Please fill all fields.",
        "saved": "Saved successfully.",
        "renewed": "Payment confirmed. 30 days added.",
        "deleted": "Deleted successfully.",
        "time_updated": "Time updated successfully.",
        "add_new": "Add New Person",
        "vip_description": "Manage paid VIP memberships for your DayZ server.",
        "insurance_description": "Manage car insurance renewals and expiration dates.",
    },
    "pt": {
        "login_title": "Painel Carnage Z",
        "username": "Usuário",
        "password": "Senha",
        "login": "Entrar",
        "wrong_login": "Usuário ou senha incorretos.",
        "dashboard": "Painel Principal",
        "vip_tab": "Membros VIP",
        "insurance_tab": "Seguro de Carro",
        "add_person": "Adicionar Pessoa",
        "logout": "Sair",
        "language": "English",
        "name": "Nome",
        "discord": "Usuário do Discord",
        "steam_id": "Steam ID",
        "days_left": "Dias Restantes",
        "expires": "Expira em",
        "status": "Status",
        "active": "Ativo",
        "expired": "Expirado",
        "actions": "Ações",
        "redeem": "Resgatar",
        "cooldown": "Cooldown",
        "details": "Detalhes",
        "confirm_payment": "+30 Dias",
        "alter_time": "Alterar Tempo",
        "delete_vip": "Deletar VIP",
        "activation_code": "Código de Ativação",
        "new_days_left": "Novos Dias Restantes",
        "save": "Salvar",
        "cancel": "Cancelar",
        "wrong_code": "Código de ativação incorreto.",
        "empty_fields": "Preencha todos os campos.",
        "saved": "Salvo com sucesso.",
        "renewed": "Pagamento confirmado. 30 dias adicionados.",
        "deleted": "Deletado com sucesso.",
        "time_updated": "Tempo atualizado com sucesso.",
        "add_new": "Adicionar Nova Pessoa",
        "vip_description": "Gerencie os VIPs pagos do seu servidor DayZ.",
        "insurance_description": "Gerencie seguros de carro e datas de expiração.",
    }
}


def t(key):
    return TEXT[get_lang()].get(key, key)


# ============================================================
# HTML TEMPLATE
# ============================================================
HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Carnage Z Manager</title>

    <style>
        * {
            box-sizing: border-box;
        }

        body {
            margin: 0;
            background: #0B0F14;
            color: #F2F2F2;
            font-family: Arial, Helvetica, sans-serif;
        }

        a {
            color: inherit;
            text-decoration: none;
        }

        .login-page {
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }

        .login-card {
            width: 100%;
            max-width: 420px;
            background: #121821;
            border: 1px solid #273142;
            border-radius: 18px;
            padding: 35px;
            box-shadow: 0 20px 50px rgba(0,0,0,0.45);
        }

        .login-card h1 {
            margin: 0 0 25px 0;
            font-size: 28px;
        }

        .label {
            display: block;
            margin-bottom: 7px;
            color: #9CA3AF;
            font-size: 14px;
        }

        .input {
            width: 100%;
            background: #0F141B;
            border: 1px solid #273142;
            color: #F2F2F2;
            border-radius: 10px;
            padding: 13px;
            margin-bottom: 18px;
            outline: none;
        }

        .input:focus {
            border-color: #B30000;
        }

        .btn {
            border: none;
            border-radius: 10px;
            padding: 11px 14px;
            cursor: pointer;
            font-weight: bold;
            color: white;
            background: #B30000;
            transition: 0.15s ease;
            display: inline-block;
            text-align: center;
        }

        .btn:hover {
            background: #E00000;
        }

        .btn-dark {
            background: #161E29;
            border: 1px solid #273142;
        }

        .btn-dark:hover {
            background: #273142;
        }

        .btn-red {
            background: #EF4444;
        }

        .btn-green {
            background: #22C55E;
        }

        .btn-yellow {
            background: #F59E0B;
            color: #0B0F14;
        }

        .btn-small {
            padding: 8px 10px;
            font-size: 13px;
            min-width: 95px;
        }

        .topbar {
            height: 72px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 28px;
            border-bottom: 1px solid #273142;
            background: #0B0F14;
            position: sticky;
            top: 0;
            z-index: 10;
        }

        .topbar h1 {
            margin: 0;
            font-size: 26px;
        }

        .top-actions {
            display: flex;
            gap: 10px;
            align-items: center;
        }

        .container {
            padding: 25px;
            max-width: 1250px;
            margin: 0 auto;
        }

        .tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 18px;
        }

        .tab {
            padding: 12px 18px;
            border-radius: 12px;
            background: #121821;
            color: #F2F2F2;
            border: 1px solid #273142;
            font-weight: bold;
        }

        .tab.active {
            background: #B30000;
            border-color: #B30000;
        }

        .panel {
            background: #121821;
            border: 1px solid #273142;
            border-radius: 18px;
            padding: 20px;
            box-shadow: 0 20px 50px rgba(0,0,0,0.25);
        }

        .panel-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 15px;
            margin-bottom: 18px;
        }

        .description {
            color: #9CA3AF;
            margin: 0;
        }

        .table-wrap {
            overflow: auto;
            max-height: 66vh;
            border-radius: 14px;
            border: 1px solid #273142;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            min-width: 900px;
        }

        th {
            position: sticky;
            top: 0;
            z-index: 2;
            background: #161E29;
            color: #F2F2F2;
            text-align: center;
            padding: 14px 10px;
            font-size: 14px;
        }

        td {
            padding: 13px 10px;
            border-top: 1px solid #273142;
            text-align: center;
            vertical-align: middle;
        }

        td.name-cell {
            text-align: left;
            font-weight: bold;
            font-size: 16px;
        }

        .active-name {
            color: #22C55E;
        }

        .expired-name {
            color: #EF4444;
        }

        .status-active {
            color: #22C55E;
            font-weight: bold;
        }

        .status-expired {
            color: #EF4444;
            font-weight: bold;
        }

        .actions {
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            gap: 8px;
        }

        .message {
            background: #161E29;
            border: 1px solid #273142;
            border-left: 4px solid #B30000;
            padding: 12px 14px;
            border-radius: 10px;
            margin-bottom: 18px;
            color: #F2F2F2;
        }

        .form-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 18px;
        }

        .form-card {
            background: #121821;
            border: 1px solid #273142;
            border-radius: 18px;
            padding: 20px;
            margin-bottom: 18px;
        }

        .form-card h2 {
            margin-top: 0;
        }

        .details-card {
            display: grid;
            gap: 10px;
            background: #161E29;
            border: 1px solid #273142;
            border-radius: 14px;
            padding: 16px;
            margin-bottom: 18px;
        }

        .detail-line {
            display: flex;
            justify-content: space-between;
            gap: 20px;
            border-bottom: 1px solid #273142;
            padding-bottom: 8px;
        }

        .detail-line:last-child {
            border-bottom: none;
            padding-bottom: 0;
        }

        .muted {
            color: #9CA3AF;
        }

        @media (max-width: 800px) {
            .topbar {
                height: auto;
                padding: 18px;
                flex-direction: column;
                align-items: flex-start;
                gap: 12px;
            }

            .panel-header {
                align-items: flex-start;
                flex-direction: column;
            }

            .form-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>

    <script>
        // Auto-refresh every 60 seconds so countdown/status stays updated.
        setTimeout(function() {
            window.location.reload();
        }, 1000);

        function confirmDelete() {
            return confirm("Are you sure you want to delete this person?");
        }
    </script>
</head>
<body>

{% if page == "login" %}
    <div class="login-page">
        <form class="login-card" method="POST" action="{{ url_for('login') }}">
            <h1>{{ t('login_title') }}</h1>

            {% if message %}
                <div class="message">{{ message }}</div>
            {% endif %}

            <label class="label">{{ t('username') }}</label>
            <input class="input" name="username" required>

            <label class="label">{{ t('password') }}</label>
            <input class="input" name="password" type="password" required>

            <button class="btn" style="width: 100%;" type="submit">{{ t('login') }}</button>

            <p class="muted" style="margin-top: 18px; text-align: center;">Default: admin / 1234</p>
        </form>
    </div>
{% else %}
    <div class="topbar">
        <h1>{{ t('dashboard') }}</h1>
        <div class="top-actions">
            <a class="btn btn-dark" href="{{ url_for('toggle_language') }}">{{ t('language') }}</a>
            <a class="btn btn-dark" href="{{ url_for('logout') }}">{{ t('logout') }}</a>
        </div>
    </div>

    <main class="container">
        <div class="tabs">
            <a class="tab {% if tab == 'vip' %}active{% endif %}" href="{{ url_for('dashboard', tab='vip') }}">{{ t('vip_tab') }}</a>
            <a class="tab {% if tab == 'insurance' %}active{% endif %}" href="{{ url_for('dashboard', tab='insurance') }}">{{ t('insurance_tab') }}</a>
        </div>

        {% if message %}
            <div class="message">{{ message }}</div>
        {% endif %}

        {% if page == "dashboard" %}
            <section class="panel">
                <div class="panel-header">
                    <p class="description">
                        {% if tab == 'vip' %}
                            {{ t('vip_description') }}
                        {% else %}
                            {{ t('insurance_description') }}
                        {% endif %}
                    </p>
                    <a class="btn" href="{{ url_for('add_person', tab=tab) }}">{{ t('add_person') }}</a>
                </div>

                <div class="table-wrap">
                    <table>
                        <thead>
                            <tr>
                                <th>{{ t('name') }}</th>
                                <th>{{ t('days_left') }}</th>
                                <th>{{ t('expires') }}</th>
                                <th>{{ t('status') }}</th>
                                {% if tab == 'insurance' %}
                                <th>{{ t('cooldown') }}</th>
                            {% endif %}
                            <th>{{ t('actions') }}</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for person in people %}
                                {% set days = calculate_days_left(person.expires) %}
                                {% set active = days >= 0 %}
                                <tr>
                                    <td class="name-cell {% if active %}active-name{% else %}expired-name{% endif %}">
                                        {{ person.name }}
                                    </td>
                                    <td>{{ days if active else 0 }}</td>
                                    <td>{{ person.expires }}</td>
                                    <td class="{% if active %}status-active{% else %}status-expired{% endif %}">
                                        {{ t('active') if active else t('expired') }}
                                    </td>

                                    {% if tab == 'insurance' %}
                                        <td>
                                            {% set cooldown = get_redeem_cooldown(person) %}
                                            {% if cooldown %}
                                                <span style="color:#F59E0B;font-weight:bold;">{{ cooldown }}</span>
                                            {% else %}
                                                <span style="color:#22C55E;font-weight:bold;">READY</span>
                                            {% endif %}
                                        </td>
                                    {% endif %}

                                    <td>
                                        <div class="actions">
                                            <a class="btn btn-small btn-dark" href="{{ url_for('details', tab=tab, index=loop.index0) }}">{{ t('details') }}</a>

                                            <form method="POST" action="{{ url_for('renew', tab=tab, index=loop.index0) }}">
                                                <button class="btn btn-small btn-green" type="submit">{{ t('confirm_payment') }}</button>
                                            </form>

                                            <a class="btn btn-small btn-yellow" href="{{ url_for('alter_time', tab=tab, index=loop.index0) }}">{{ t('alter_time') }}</a>

                                            {% if tab == 'insurance' %}
                                                <form method="POST" action="{{ url_for('redeem_insurance', index=loop.index0) }}">
                                                    <button class="btn btn-small btn-dark" type="submit">{{ t('redeem') }}</button>
                                                </form>
                                            {% endif %}

                                            <form method="POST" action="{{ url_for('delete_person', tab=tab, index=loop.index0) }}" onsubmit="return confirmDelete();">
                                                <button class="btn btn-small btn-red" type="submit">{{ t('delete_vip') }}</button>
                                            </form>
                                        </div>
                                    </td>
                                </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </section>
        {% endif %}

        {% if page == "add" %}
            <section class="form-card">
                <h2>{{ t('add_new') }}</h2>

                <form method="POST">
                    <div class="form-grid">
                        <div>
                            <label class="label">{{ t('activation_code') }}</label>
                            <input class="input" name="activation_code" type="password" required>
                        </div>

                        <div>
                            <label class="label">{{ t('name') }}</label>
                            <input class="input" name="name" required>
                        </div>

                        <div>
                            <label class="label">{{ t('discord') }}</label>
                            <input class="input" name="discord" required>
                        </div>

                        <div>
                            <label class="label">{{ t('steam_id') }}</label>
                            <input class="input" name="steam_id" required>
                        </div>

                        <div>
                            <label class="label">{{ t('new_days_left') }}</label>
                            <input class="input" name="days_left" type="number" min="0" value="30" required>
                        </div>
                    </div>

                    <button class="btn" type="submit">{{ t('save') }}</button>
                    <a class="btn btn-dark" href="{{ url_for('dashboard', tab=tab) }}">{{ t('cancel') }}</a>
                </form>
            </section>
        {% endif %}

        {% if page == "details" %}
            <section class="form-card">
                <h2>{{ person.name }}</h2>

                {% set days = calculate_days_left(person.expires) %}
                {% set active = days >= 0 %}

                <div class="details-card">
                    <div class="detail-line"><span class="muted">{{ t('discord') }}</span><strong>{{ person.discord }}</strong></div>
                    <div class="detail-line"><span class="muted">{{ t('steam_id') }}</span><strong>{{ person.steam_id }}</strong></div>
                    <div class="detail-line"><span class="muted">{{ t('expires') }}</span><strong>{{ person.expires }}</strong></div>
                    <div class="detail-line"><span class="muted">{{ t('days_left') }}</span><strong>{{ days if active else 0 }}</strong></div>
                    <div class="detail-line"><span class="muted">{{ t('status') }}</span><strong class="{% if active %}status-active{% else %}status-expired{% endif %}">{{ t('active') if active else t('expired') }}</strong></div>
                </div>

                <a class="btn btn-dark" href="{{ url_for('dashboard', tab=tab) }}">{{ t('cancel') }}</a>
            </section>
        {% endif %}

        {% if page == "alter" %}
            <section class="form-card">
                <h2>{{ t('alter_time') }} - {{ person.name }}</h2>

                <form method="POST">
                    <label class="label">{{ t('activation_code') }}</label>
                    <input class="input" name="activation_code" type="password" required>

                    <label class="label">{{ t('new_days_left') }}</label>
                    <input class="input" name="days_left" type="number" min="0" value="{{ current_days }}" required>

                    <button class="btn" type="submit">{{ t('save') }}</button>
                    <a class="btn btn-dark" href="{{ url_for('dashboard', tab=tab) }}">{{ t('cancel') }}</a>
                </form>
            </section>
        {% endif %}
    </main>
{% endif %}

</body>
</html>
"""


# ============================================================
# ROUTES
# ============================================================
@app.route("/", methods=["GET"])
def home():
    if login_required():
        return redirect(url_for("dashboard", tab="vip"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    message = ""

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["logged_in"] = True
            return redirect(url_for("dashboard", tab="vip"))
        else:
            message = t("wrong_login")

    return render_template_string(HTML, page="login", message=message, t=t)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/language")
def toggle_language():
    session["lang"] = "pt" if get_lang() == "en" else "en"
    return redirect(request.referrer or url_for("dashboard", tab="vip"))


@app.route("/dashboard/<tab>")
def dashboard(tab):
    if not login_required():
        return redirect(url_for("login"))

    if tab not in ["vip", "insurance"]:
        tab = "vip"

    data = load_data()
    people = data.get(tab, [])
    people = sorted(people, key=lambda person: person.get("name", "").lower())

    message = request.args.get("message", "")

    return render_template_string(
        HTML,
        page="dashboard",
        tab=tab,
        people=people,
        message=message,
        t=t,
        calculate_days_left=calculate_days_left,
        get_redeem_cooldown=get_redeem_cooldown
    )


@app.route("/add/<tab>", methods=["GET", "POST"])
def add_person(tab):
    if not login_required():
        return redirect(url_for("login"))

    if tab not in ["vip", "insurance"]:
        tab = "vip"

    message = ""

    if request.method == "POST":
        activation_code = request.form.get("activation_code", "").strip()
        name = request.form.get("name", "").strip()
        discord = request.form.get("discord", "").strip()
        steam_id = request.form.get("steam_id", "").strip()
        days_left = request.form.get("days_left", "30").strip()

        if activation_code != ACTIVATION_CODE:
            message = t("wrong_code")
        elif not name or not discord or not steam_id or not days_left:
            message = t("empty_fields")
        else:
            try:
                days_left_int = int(days_left)
                if days_left_int < 0:
                    raise ValueError
            except ValueError:
                message = t("empty_fields")
            else:
                data = load_data()
                expires = (datetime.now().date() + timedelta(days=days_left_int)).strftime("%Y-%m-%d")

                new_person = {
                    "name": name,
                    "discord": discord,
                    "steam_id": steam_id,
                    "expires": expires
                }

                data.setdefault(tab, [])
                data[tab].append(new_person)
                save_data(data)

                return redirect(url_for("dashboard", tab=tab, message=t("saved")))

    return render_template_string(
        HTML,
        page="add",
        tab=tab,
        message=message,
        t=t,
        calculate_days_left=calculate_days_left,
        get_redeem_cooldown=get_redeem_cooldown
    )


@app.route("/details/<tab>/<int:index>")
def details(tab, index):
    if not login_required():
        return redirect(url_for("login"))

    data = load_data()

    try:
        person = data[tab][index]
    except Exception:
        return redirect(url_for("dashboard", tab="vip"))

    return render_template_string(
        HTML,
        page="details",
        tab=tab,
        person=person,
        message="",
        t=t,
        calculate_days_left=calculate_days_left,
        get_redeem_cooldown=get_redeem_cooldown
    )


@app.route("/renew/<tab>/<int:index>", methods=["POST"])
def renew(tab, index):
    if not login_required():
        return redirect(url_for("login"))

    data = load_data()

    try:
        person = data[tab][index]
        today = datetime.now().date()
        current_expiration = datetime.strptime(person["expires"], "%Y-%m-%d").date()
        start_date = current_expiration if current_expiration >= today else today
        new_expiration = start_date + timedelta(days=RENEWAL_DAYS)
        person["expires"] = new_expiration.strftime("%Y-%m-%d")
        save_data(data)
    except Exception:
        pass

    return redirect(url_for("dashboard", tab=tab, message=t("renewed")))


@app.route("/alter/<tab>/<int:index>", methods=["GET", "POST"])
def alter_time(tab, index):
    if not login_required():
        return redirect(url_for("login"))

    data = load_data()

    try:
        person = data[tab][index]
    except Exception:
        return redirect(url_for("dashboard", tab="vip"))

    current_days = calculate_days_left(person["expires"])
    if current_days < 0:
        current_days = 0

    message = ""

    if request.method == "POST":
        activation_code = request.form.get("activation_code", "").strip()
        days_left = request.form.get("days_left", "0").strip()

        if activation_code != ACTIVATION_CODE:
            message = t("wrong_code")
        else:
            try:
                days_left_int = int(days_left)
                if days_left_int < 0:
                    raise ValueError
            except ValueError:
                message = t("empty_fields")
            else:
                new_expiration = datetime.now().date() + timedelta(days=days_left_int)
                person["expires"] = new_expiration.strftime("%Y-%m-%d")
                save_data(data)
                return redirect(url_for("dashboard", tab=tab, message=t("time_updated")))

    return render_template_string(
        HTML,
        page="alter",
        tab=tab,
        person=person,
        current_days=current_days,
        message=message,
        t=t,
        calculate_days_left=calculate_days_left,
        get_redeem_cooldown=get_redeem_cooldown
    )


@app.route("/delete/<tab>/<int:index>", methods=["POST"])
def delete_person(tab, index):
    if not login_required():
        return redirect(url_for("login"))

    data = load_data()

    try:
        del data[tab][index]
        save_data(data)
    except Exception:
        pass

    return redirect(url_for("dashboard", tab=tab, message=t("deleted")))


@app.route("/redeem/<int:index>", methods=["POST"])
def redeem_insurance(index):
    if not login_required():
        return redirect(url_for("login"))

    data = load_data()

    try:
        person = data["insurance"][index]

        existing_cooldown = get_redeem_cooldown(person)

        # Prevent redeeming again while cooldown is active.
        if existing_cooldown:
            return redirect(url_for("dashboard", tab="insurance"))

        cooldown_end = datetime.now() + timedelta(hours=INSURANCE_REDEEM_COOLDOWN_HOURS)
        person["redeem_cooldown"] = cooldown_end.isoformat()

        save_data(data)

    except Exception:
        pass

    return redirect(url_for("dashboard", tab="insurance"))


# ============================================================
# RUN APP LOCALLY
# ============================================================
if __name__ == "__main__":
    # Railway provides the PORT automatically online.
    # Locally, it will still use 5000.
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)


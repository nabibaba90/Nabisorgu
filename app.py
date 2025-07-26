import random
import string
from flask import Flask, render_template, request, redirect, url_for, session, flash
import requests
from functools import wraps
from datetime import timedelta

app = Flask(__name__)
app.secret_key = "neonabi_super_secret_key"
app.permanent_session_lifetime = timedelta(hours=2)

# Kullanıcılar
USERS = {
    "admin": {"password": "123456", "vip": True},
    "freeuser": {"password": "1234", "vip": False}
}

def generate_captcha(length=6):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "username" not in session:
            flash("Lütfen giriş yapınız!", "error")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper

def vip_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        user = session.get("username")
        if not user or not USERS.get(user, {}).get("vip", False):
            flash("VIP erişim gerekiyor.", "error")
            return redirect(url_for("abonelik"))
        return f(*args, **kwargs)
    return wrapper

@app.route("/")
@login_required
def index():
    return render_template("index.html")

@app.route("/abonelik")
@login_required
def abonelik():
    return render_template("abonelik.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        captcha_input = request.form.get("captcha", "").strip().upper()

        if captcha_input != session.get("captcha_code"):
            flash("Captcha kodu yanlış!", "error")
            session["captcha_code"] = generate_captcha()
            return render_template("login.html", captcha=session["captcha_code"])

        user = USERS.get(username)
        if user and user["password"] == password:
            session["username"] = username
            session.permanent = True
            flash("Giriş başarılı!", "success")
            return redirect(url_for("index") if user["vip"] else url_for("abonelik"))
        else:
            flash("Kullanıcı adı veya şifre hatalı!", "error")

    session["captcha_code"] = generate_captcha()
    return render_template("login.html", captcha=session["captcha_code"])

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password1 = request.form.get("password", "")
        password2 = request.form.get("password2", "")

        if not username or not password1 or not password2:
            flash("Tüm alanları doldurun!", "error")
        elif password1 != password2:
            flash("Şifreler eşleşmiyor!", "error")
        elif username in USERS:
            flash("Bu kullanıcı zaten mevcut!", "error")
        else:
            USERS[username] = {"password": password1, "vip": False}
            flash("Kayıt başarılı! Giriş yapabilirsiniz.", "success")
            return redirect(url_for("login"))

    return render_template("register.html")

@app.route("/logout")
@login_required
def logout():
    session.pop("username", None)
    flash("Çıkış yapıldı.", "success")
    return redirect(url_for("login"))

@app.route("/sorgu", methods=["GET", "POST"])
@login_required
@vip_required
def sorgu():
    sorgu_tipi = request.args.get("s", "")
    sonuc = None

    if request.method == "POST":
        captcha_input = request.form.get("captcha", "").strip().upper()
        if captcha_input != session.get("captcha_code"):
            flash("Güvenlik kodu yanlış!", "error")
            return redirect(request.url)

        try:
            form = request.form
            url = ""

            if sorgu_tipi in ["Ad Soyad → TC", "Ad Soyad → GSM"]:
                adsoyad = form.get("adSoyad", "")
                try:
                    ad, soyad = adsoyad.strip().split(" ", 1)
                except ValueError:
                    flash("Lütfen 'Ad Soyad' şeklinde girin.", "error")
                    return redirect(request.url)
                url = f"https://api.hexnox.pro/sowixapi/adsoyadilice.php?ad={ad}&soyad={soyad}"

            elif sorgu_tipi == "TC → Ad Soyad":
                tc = form.get("tcNo", "")
                url = f"https://api.hexnox.pro/sowixapi/tc.php?tc={tc}"

            elif sorgu_tipi == "GSM → Ad Soyad":
                gsm = form.get("gsmNo", "")
                url = f"https://api.hexnox.pro/sowixapi/gsm.php?gsm={gsm}"

            elif sorgu_tipi == "TC Pro":
                tc = form.get("tcNo", "")
                url = f"https://api.hexnox.pro/sowixapi/tcpro.php?tc={tc}"

            elif sorgu_tipi == "Tapu Sorgu":
                tc = form.get("parselNo", "")
                url = f"https://api.hexnox.pro/sowixapi/tapu.php?tc={tc}"

            elif sorgu_tipi == "Adres Sorgu":
                tc = form.get("adres", "")
                url = f"https://api.hexnox.pro/sowixapi/adres.php?tc={tc}"

            elif sorgu_tipi == "Okul No Sorgu":
                tc = form.get("okulNo", "")
                url = f"https://api.hexnox.pro/sowixapi/okulno.php?tc={tc}"

            elif sorgu_tipi == "Aile Sorgu":
                tc = form.get("aileNo", "")
                url = f"https://api.hexnox.pro/sowixapi/aile.php?tc={tc}"

            elif sorgu_tipi == "Sülale Sorgu":
                tc = form.get("sulaleAdi", "")
                url = f"https://api.hexnox.pro/sowixapi/sulale.php?tc={tc}"

            elif sorgu_tipi == "SGK Yetkili Sorgu":
                tc = form.get("tcNo", "")
                url = f"https://api.hexnox.pro/sowixapi/isyeriyetkili.php?tc={tc}"

            elif sorgu_tipi == "İş Yeri Sorgu":
                tc = form.get("isYeriAdi", "")
                url = f"https://api.hexnox.pro/sowixapi/isyeri.php?tc={tc}"

            elif sorgu_tipi == "Hane Sorgu":
                tc = form.get("adres", "")
                url = f"https://api.hexnox.pro/sowixapi/hane.php?tc={tc}"

            elif sorgu_tipi == "Baba Sorgu":
                tc = form.get("babaAdi", "")
                url = f"https://api.hexnox.pro/sowixapi/baba.php?tc={tc}"

            elif sorgu_tipi == "Anne Sorgu":
                tc = form.get("anneAdi", "")
                url = f"https://api.hexnox.pro/sowixapi/anne.php?tc={tc}"

            elif sorgu_tipi == "GSM Detay":
                gsm = form.get("gsmNo", "")
                url = f"https://api.hexnox.pro/sowixapi/gsmdetay.php?gsm={gsm}"

            else:
                flash("Geçersiz sorgu tipi!", "error")
                return redirect(url_for("index"))

            r = requests.get(url)
            sonuc = r.text

        except Exception as e:
            flash(f"Hata: {str(e)}", "error")

    session["captcha_code"] = generate_captcha()
    return render_template("sorgu.html", sorgu_tipi=sorgu_tipi, sonuc=sonuc, captcha=session["captcha_code"])

@app.route("/free-login", methods=["POST"])
def free_login():
    session["username"] = "freeuser"
    session.permanent = True
    flash("Ücretsiz kullanıcı olarak giriş yapıldı.", "success")
    return redirect(url_for("abonelik"))

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5000)

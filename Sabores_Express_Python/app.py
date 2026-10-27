from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
app=Flask(__name__); app.secret_key="CAMBIA-ESTA-CLAVE"; DB="sabores.db"
def db():
 c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; return c
def init():
 with db() as c:
  c.executescript("""CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY,name TEXT,email TEXT UNIQUE,password TEXT,role TEXT DEFAULT 'cliente');
  CREATE TABLE IF NOT EXISTS foods(id INTEGER PRIMARY KEY,name TEXT,category TEXT,description TEXT,price INTEGER,emoji TEXT);
  CREATE TABLE IF NOT EXISTS news(id INTEGER PRIMARY KEY,kind TEXT,title TEXT,description TEXT,detail TEXT,emoji TEXT);""")
  if not c.execute("SELECT count(*) FROM foods").fetchone()[0]:
   c.executemany("INSERT INTO foods(name,category,description,price,emoji) VALUES(?,?,?,?,?)",[
   ("Hamburguesa clásica","Hamburguesas","Carne, queso, lechuga y tomate.",18900,"🍔"),("Perro caliente","Comida rápida","Salchicha, queso y salsas.",14500,"🌭"),("Bandeja paisa","Colombiana","Fríjoles, arroz, carne, chicharrón, huevo, arepa y aguacate.",28900,"🍛"),("Ajiaco santafereño","Colombiana","Sopa de pollo y papas con mazorca.",23000,"🥣"),("Empanadas x3","Entradas","Tres empanadas con ají.",9000,"🥟"),("Pizza personal","Pizza","Queso, tomate y pepperoni.",19900,"🍕"),("Arepa con queso","Colombiana","Arepa de maíz rellena de queso.",7500,"🫓"),("Limonada natural","Bebidas","Limón, agua y hielo.",6500,"🍋"),("Brownie con helado","Postres","Brownie de chocolate y helado.",11000,"🍨"),("Salchipapa","Comida rápida","Papas, salchicha, queso y salsas.",16900,"🍟")])
  if not c.execute("SELECT count(*) FROM news").fetchone()[0]:
   c.executemany("INSERT INTO news(kind,title,description,detail,emoji) VALUES(?,?,?,?,?)",[("Promoción","Combo de la casa","Hamburguesa + papas + limonada.","Precio de ejemplo: $27.900","🎁"),("Evento","Viernes de antojos","Comparte algo rico con amigos.","Evento de ejemplo · Viernes","🎉")])
  if not c.execute("SELECT id FROM users WHERE email='admin@saboresexpress.demo'").fetchone():
   c.execute("INSERT INTO users(name,email,password,role) VALUES(?,?,?,?)",("Administrador","admin@saboresexpress.demo",generate_password_hash("Admin123!"),"admin"))
@app.template_filter("cop")
def cop(n): return "$"+f"{int(n):,}".replace(",",".")
def admin_only(fn):
 @wraps(fn)
 def w(*a,**k):
  if session.get("role")!="admin": flash("Inicia sesión como administrador.","error"); return redirect(url_for("login"))
  return fn(*a,**k)
 return w
@app.route("/")
def home():
 with db() as c: foods=c.execute("SELECT * FROM foods ORDER BY id").fetchall(); news=c.execute("SELECT * FROM news ORDER BY id DESC").fetchall()
 return render_template("index.html",foods=foods,news=news)
@app.route("/registro",methods=["GET","POST"])
def register():
 if request.method=="POST":
  name=request.form["name"].strip(); email=request.form["email"].strip().lower(); pw=request.form["password"]
  if not name or len(pw)<6: flash("Completa los datos; contraseña de 6 caracteres mínimo.","error")
  else:
   try:
    with db() as c: c.execute("INSERT INTO users(name,email,password) VALUES(?,?,?)",(name,email,generate_password_hash(pw)))
    flash("Cuenta creada. Ya puedes iniciar sesión.","ok"); return redirect(url_for("login"))
   except sqlite3.IntegrityError: flash("Ese correo ya está registrado.","error")
 return render_template("auth.html",mode="Registro")
@app.route("/login",methods=["GET","POST"])
def login():
 if request.method=="POST":
  with db() as c: u=c.execute("SELECT * FROM users WHERE email=?",(request.form["email"].strip().lower(),)).fetchone()
  if u and check_password_hash(u["password"],request.form["password"]):
   session.clear(); session.update(uid=u["id"],name=u["name"],role=u["role"],cart={})
   return redirect(url_for("admin") if u["role"]=="admin" else url_for("home"))
  flash("Correo o contraseña incorrectos.","error")
 return render_template("auth.html",mode="Iniciar sesión")
@app.route("/salir")
def logout(): session.clear(); return redirect(url_for("home"))
@app.route("/agregar/<int:pid>",methods=["POST"])
def add(pid):
 with db() as c: ok=c.execute("SELECT id FROM foods WHERE id=?",(pid,)).fetchone()
 if ok:
  cart=session.get("cart",{}); cart[str(pid)]=int(cart.get(str(pid),0))+1; session["cart"]=cart; flash("Añadido al carrito.","ok")
 return redirect(url_for("home"))
@app.route("/carrito")
def cart():
 cart=session.get("cart",{}); items=[]; total=0
 with db() as c:
  for pid,q in cart.items():
   f=c.execute("SELECT * FROM foods WHERE id=?",(int(pid),)).fetchone()
   if f: items.append((f,int(q),f["price"]*int(q))); total+=f["price"]*int(q)
 return render_template("cart.html",items=items,total=total)
@app.route("/quitar/<int:pid>",methods=["POST"])
def remove(pid):
 cart=session.get("cart",{}); cart.pop(str(pid),None); session["cart"]=cart; return redirect(url_for("cart"))
@app.route("/pedido",methods=["POST"])
def order():
 if not session.get("uid"): return redirect(url_for("login"))
 session["cart"]={}; flash("Pedido de demostración; no se envió ni se cobró.","ok"); return redirect(url_for("home"))
@app.route("/admin")
@admin_only
def admin():
 with db() as c: foods=c.execute("SELECT * FROM foods ORDER BY id DESC").fetchall(); news=c.execute("SELECT * FROM news ORDER BY id DESC").fetchall()
 return render_template("admin.html",foods=foods,news=news)
@app.route("/admin/food",methods=["POST"])
@admin_only
def save_food():
 try:
  vals=(request.form["name"].strip(),request.form["category"].strip(),request.form["description"].strip(),int(request.form["price"]),request.form.get("emoji","🍽️"))
  if not all(vals[:3]) or vals[3]<0: raise ValueError()
  pid=request.form.get("id")
  with db() as c:
   if pid: c.execute("UPDATE foods SET name=?,category=?,description=?,price=?,emoji=? WHERE id=?",(*vals,int(pid)))
   else: c.execute("INSERT INTO foods(name,category,description,price,emoji) VALUES(?,?,?,?,?)",vals)
  flash("Producto guardado.","ok")
 except (ValueError,KeyError): flash("Revisa los datos y el precio.","error")
 return redirect(url_for("admin"))
@app.route("/admin/news",methods=["POST"])
@admin_only
def save_news():
 try:
  vals=(request.form["kind"],request.form["title"].strip(),request.form["description"].strip(),request.form.get("detail",""),request.form.get("emoji","✨"))
  if vals[0] not in ("Promoción","Evento") or not vals[1] or not vals[2]: raise ValueError()
  aid=request.form.get("id")
  with db() as c:
   if aid: c.execute("UPDATE news SET kind=?,title=?,description=?,detail=?,emoji=? WHERE id=?",(*vals,int(aid)))
   else: c.execute("INSERT INTO news(kind,title,description,detail,emoji) VALUES(?,?,?,?,?)",vals)
  flash("Promoción o evento guardado.","ok")
 except (ValueError,KeyError): flash("Revisa el formulario.","error")
 return redirect(url_for("admin"))
@app.route("/admin/news/delete/<int:aid>",methods=["POST"])
@admin_only
def delete_news(aid):
 with db() as c: c.execute("DELETE FROM news WHERE id=?",(aid,))
 return redirect(url_for("admin"))
if __name__=="__main__": init(); app.run(debug=True)

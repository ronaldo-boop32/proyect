SABORES EXPRESS EN PYTHON + FLASK
Windows:
1. Instala Python 3.10 o posterior.
2. Abre CMD/PowerShell en esta carpeta.
3. py -m venv .venv
4. Activa: .venv\\Scripts\\activate (CMD) o .\\.venv\\Scripts\\Activate.ps1 (PowerShell)
5. py -m pip install -r requirements.txt
6. py app.py
7. Abre http://127.0.0.1:5000

Mac/Linux: python3 -m venv .venv; source .venv/bin/activate; pip install -r requirements.txt; python app.py
Admin de prueba: admin@saboresexpress.demo / Admin123!
La base sabores.db se crea automáticamente. Cambia app.secret_key antes de publicar.
Proyecto académico: no procesa pagos ni envía pedidos reales. No afiliado a DiDi Food.
Para producción desactiva debug, configura HTTPS, protección CSRF y seguridad adicional.

from flask import Flask, render_template


app = Flask(__name__)

# Por ahora los servicios y sus precios se guardan en Python.
# Más adelante se podrán obtener desde una base de datos.
SERVICIOS = [
    {"nombre": "Corte clásico", "precio": 8000},
    {"nombre": "Corte + ceja", "precio": 8500},
    {"nombre": "Tintura", "precio": 25000},
]


@app.route("/")
def inicio():
    """Muestra la página principal de la peluquería."""
    return render_template("index.html", servicios=SERVICIOS)


if __name__ == "__main__":
    app.run(debug=True)

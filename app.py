from flask import Flask, render_template


app = Flask(__name__)

# Por ahora los servicios se guardan en una lista de Python.
# Más adelante se podrán obtener desde una base de datos.
SERVICIOS = [
    "Corte clásico",
    "Corte + ceja",
    "Tintura",
]


@app.route("/")
def inicio():
    """Muestra la página principal de la peluquería."""
    return render_template("index.html", servicios=SERVICIOS)


if __name__ == "__main__":
    app.run(debug=True)

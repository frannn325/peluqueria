from flask import Flask, render_template

from database import inicializar_base_de_datos, obtener_servicios


app = Flask(__name__)
inicializar_base_de_datos()


@app.route("/")
def inicio():
    """Muestra la página principal de la peluquería."""
    servicios = obtener_servicios()
    return render_template("index.html", servicios=servicios)


if __name__ == "__main__":
    app.run(debug=True)

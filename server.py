from flask import Flask, request, jsonify

app = Flask(__name__)

#Route GET
@app.route('/', methods=['GET'])
def home():
    return jsonify({"message": "Serveur en ligne !"})

#Route POST
@app.route('/', methods=['POST'])
def post_data():
    data = request.json  # Récupérer les données envoyées
    return jsonify({"message": "Données reçues", "data": data})

#Route DELETE
@app.route('/', methods=['DELETE'])
def delete_data():
    return jsonify({"message": "Donnée supprimée !"})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
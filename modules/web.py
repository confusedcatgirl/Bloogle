from flask import Flask, Response, jsonify

app = Flask(__name__)

@app.route("/")
def hello_world():
    return jsonify({
        'data': ['https://github.githubassets.com/favicons/favicon-dark.svg|||https://github.com/|||Github|||Github Page.',
                 'https://github.githubassets.com/favicons/favicon-dark.svg|||https://github.com/|||Github|||Github Page.']
    })
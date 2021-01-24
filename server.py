#!/usr/bin/python3

import graphene
from flask import Flask
from flask_graphql import GraphQLView
from models.api import DemucsServiceAPI
from flask_cors import CORS


app = Flask(__name__)
CORS(app)
schema = graphene.Schema(query=DemucsServiceAPI)


@app.route('/')
def hello():
    return 'This is demucs web!'


app.add_url_rule(
    '/graphql',
    view_func=GraphQLView.as_view(
        'graphql',
        schema=schema,
        graphiql=True
    )
)

if __name__ == "__main__": 
    app.run(host='0.0.0.0', port=5000) 
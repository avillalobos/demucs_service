#!/usr/bin/python3

import graphene
from flask import Flask
from flask_graphql import GraphQLView
from models.api import DemucsServiceAPI


app = Flask(__name__)
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

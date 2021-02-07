#!/usr/bin/python3

import lib.utils as utils
import logging
import graphene
from flask import Flask, send_file, after_this_request
from flask_graphql import GraphQLView
from models.api import DemucsServiceAPI
from pathlib import Path
from flask_cors import CORS
from typing import Optional


app = Flask(__name__)
CORS(app)
schema = graphene.Schema(query=DemucsServiceAPI)


@app.route('/')
def hello():
    return 'This is demucs web!'


@app.route('/download/<token>')
def gen_download(token):
    try:
        logging.info(f"Received download request for: {token}")
        download_file: Optional[Path] = utils.get_download_file(token)
        utils.disable_download(token)
        if download_file:
            @after_this_request
            def remove_file(response):
                utils.remove_download_file(download_file)
                return response
            return send_file(
                download_file,
                as_attachment=True,
                attachment_filename=download_file.name,
                mimetype='application/zip'
            )
        else:
            return "Download not found!"
        # utils.remove_download_file(download_file)
    except Exception as e:
        logging.error(f"Download doesn't exist or is already disabled! {e}")


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

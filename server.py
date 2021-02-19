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


class DemucsInternalException(Exception):

    def __init__(self, msg):
        super().__init__(msg)


app = Flask(__name__)
CORS(app)
schema = graphene.Schema(query=DemucsServiceAPI)


@app.errorhandler(FileNotFoundError)
def file_not_found(err):
    # app.logger.exception(err)
    return "The file you are trying to access is not longer available", 404


@app.errorhandler(DemucsInternalException)
def internal_error(err):
    # app.logger.exception(err)
    return "The file you are trying to access is not longer available", 500


@app.route('/download/<token>')
def gen_download(token):
    logging.info(f"Received download request for: {token}")
    download_file: Optional[Path] = utils.get_download_file(token)
    if download_file:
        try:
            # if download_file is not None, then this token
            # was found on the DB
            utils.disable_download(token)
            failed = False

            @after_this_request
            def remove_file(response):
                if not failed:
                    try:
                        utils.remove_download_file(download_file)
                    except Exception as e:
                        logging.error(f"Unable to remove the download: {e}")
                return response

            return send_file(
                download_file,
                as_attachment=True,
                attachment_filename=download_file.name,
                mimetype='application/zip'
            )
        except Exception as e:
            failed = True
            logging.error(f"An error ocurred while handling your request {e}")
            raise DemucsInternalException(e) from e
    else:
        raise FileNotFoundError("The download request is not longer available")


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

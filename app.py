from flask import Flask, request
from flask_restful import Resource, Api

import logging
import reusables

from libs.fct_lod import LoD, Ls, LoF
from libs.fct_zip import ZfS, UzU
from libs.fct_output import Output
from libs.fct_inputs import ValidateInput
from libs.fct_auth import Auth
from libs.fct_config import ConfigFile

from libs.flask_stats.flask_stats import Stats

# Changed from get_logger, deprecation warning
log = reusables.setup_logger("main", level=logging.DEBUG)

debug = True

conf = ConfigFile("config.json")


app = Flask(__name__)
api = Api(app)
Stats(app)
auth = Auth(conf.auth)


class callfct(Resource):
    def run(self, fct, request):
        output = Output()
        if debug:
            log.debug(request.args)

        validate = ValidateInput(request.args, auth, ttl=conf.ttl)
        if validate.validate() and validate.isok():
            if debug:
                log.debug("request is valid")

                Ccommand = fct(
                    conf, request.args["payload"], request.files
                )  # changed for each commands

                if Ccommand.isok():
                    payload = Ccommand.GetPayload()
                    print("Payload fetched")
                else:
                    payload = None
                    print("Payload is None")

                if Ccommand.isok():
                    if debug:
                        log.debug("payload ok")
                    output.SetStatus(Ccommand.GetStatus())
                    output.SetPayload(payload)
                    return output.generate()
                else:
                    if debug:
                        log.debug(
                            "error with payload in callfct: {0}".format(Ccommand.status)
                        )
                        log.debug("Payload: {0}".format(payload))
                    output.SetStatus(Ccommand.GetStatus())
                    return output.generate()

        else:
            if debug:
                log.debug("request is invalid")
            output.SetStatus(validate.GetStatus())
            return output.generate()


# api.add_resource(Root, '/')


@app.route("/")
def hello():
    output = Output()
    output.SetStatus(status={"code": 0, "status": "OK"})
    return output.generate()


@app.route("/healthz")
def healthz():
    return "OK"


@app.route("/ls", methods=["GET"])
def get_ls():
    cfct = callfct()
    return cfct.run(Ls, request)


@app.route("/lof", methods=["GET"])
def get_lof():
    cfct = callfct()
    return cfct.run(LoF, request)


@app.route("/lod", methods=["GET"])
def get_lod():
    cfct = callfct()
    return cfct.run(LoD, request)


@app.route("/zfs", methods=["GET"])
def get_zfs():
    cfct = callfct()
    return cfct.run(ZfS, request)


@app.route("/uzu", methods=["POST"])
def post_uzu():
    cfct = callfct()
    return cfct.run(UzU, request)


if __name__ == "__main__":  # pragma: nocover
    app.run()

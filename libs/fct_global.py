import base64
import hashlib
import hmac
import os

# Try imports specific to EPFL environment
#
# Access to identity management
try:
    from notouser import notoUser
except ImportError:
    from libs.dummyUser import notoUser
# User path information
try:
    from notouser import notoDiskInfo

    dynamic_root_available = True
except ImportError:
    dynamic_root_available = False
# External logging facility
try:
    from cedelogger import cedeLogger

    customLogger = True  # pragma: no cover
except ImportError:
    customLogger = False

import logging

log = logging.getLogger("globals")


class DynamicRoot:
    """
    This class is used to manage dynamic root on the file server
    The notoDiskInfo class is used to get information on the user's home location - IF available.
    If the notoDiskInfo class is not available, the default "root" configuration item is used
    """

    ndi = None
    root = None

    def __init__(self, conf):
        if dynamic_root_available and conf.dynamic_root:
            self.ndi = notoDiskInfo()
            if self.ndi is None:
                log.error("notoDiskInfo failed")
        else:
            self.ndi = None
            self.root = conf.homeroot

    def get_root(self, username):
        if self.ndi is not None:
            return self.ndi.get_root(username)
        else:
            exists = os.path.isdir(os.path.join(self.root, username))
            return {"exists": exists, "root": self.root}

    def get_invalid_path(self):
        return os.path.join(os.sep, "invalid_path")


class CalcHmac:
    """
    This class is used to calculate the HMAC-SHA256 key for authentication
    """

    def __init__(self, request, key):
        """
        Initiate the CalcHmac class
        :param request: dict with request arguments
        :param key: secret key for this user
        """

        self.payload = request["payload"]
        self.user = request["user"]
        self.key = key
        self.timestamp = request["timestamp"]
        self.md5_payload = base64.b64encode(
            hashlib.md5(self.payload.encode("utf-8")).digest()  # nosec
        ).decode("utf-8")
        self.hmac = None

    def get_hmac(self):
        """
        This function calculate the hmac sha256 using the key
        :return: the base64 hmac of self.user + self.timestamp + self.save_md5_payload
        """

        string = self.user + self.timestamp + self.md5_payload
        self.hmac = base64.b64encode(
            hmac.new(
                self.key.encode("utf-8"),
                string.encode("utf-8"),
                digestmod=hashlib.sha256,
            ).digest()
        )

        return self.hmac.decode("utf-8")


class CalcMd5:
    """
    This class is used for calculating md5 values for payload and key verification
    """

    def __init__(self, request, key=None):
        """
        Initiate the CalcMd5 class
        :param request: dict with request arguments
        :param key: secret key for this user
        """
        self.md5 = ""
        self.payload = request["payload"]

    def md5_payload(self):
        """
        Calculate the md5 of the payload
        :return: base64 md5(payload)
        """
        self.md5 = base64.b64encode(
            hashlib.md5(self.payload.encode("utf-8")).digest()  # nosec
        )
        return self.md5.decode("utf-8")


class moodle2notouser:
    """
    This class is used to do operation on login info from moodle into noto
    """

    def __init__(self, userpayload):
        try:
            self.id = userpayload["id"]
            self.tuid = userpayload["tuid"]
            self.email = userpayload["primary_email"]
            self.auth_meth = userpayload["auth_method"]
        except Exception as e:
            self.status = "Error with user payload: {0}".format(e)
            self.errcode = 510
        n = notoUser()
        try:
            self.NotoUser = n.userFromAPI(self.tuid, self.email)
            self.status = "OK"
            self.errcode = 0
        except Exception as e:
            self.status = "Error with notoUser: {0}".format(e)
            self.errcode = 515

    def getNotoUser(self):
        return self.NotoUser["normalised"]

    def getNotoUserid(self):
        return self.NotoUser["uid"]


class SendLog:
    """
    This class is used to send log to noto syslog if available
    """

    def __init__(self):
        if customLogger:
            self.logger = cedeLogger(tag="fsapi")  # pragma: no cover
        # else:
        #     self.logger = logging.getLogger()

    def write(self, event, action, userid):
        if customLogger:
            self.logger.log(
                {"event": event, "action": action, "uid": userid},
                level=logging.CRITICAL,
            )  # pragma: no cover

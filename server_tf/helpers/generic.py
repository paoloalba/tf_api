import os
from datetime import datetime

class Timer:
    def __init__(self):
        self.reset()
        self.day_time_format =      "{days:2d} days {hours:2d}:{minutes:2d}:{seconds:2d}"
        self.hours_time_format =    "{hours:2d} hrs, {minutes:2d} mins"
        self.min_time_format =      "{minutes:2d} mins, {seconds:2d} sec"
        self.sec_time_format =      "{feconds:2.03f} secs"
    
    def reset(self):
        self.t0 = datetime.now()

    def str_timedelta(self):
        return self.strfdelta(datetime.now() - self.t0)

    def _get_time_dict(self, tdelta):
        input_seconds = tdelta.total_seconds()
        d = {}
        d["days"], rem =   divmod(input_seconds, 3600 * 24)
        d["hours"], rem =   divmod(rem, 3600)
        d["minutes"], d["feconds"] =   divmod(rem, 60)
        d["seconds"] =   int(d["feconds"])

        d["days"] =     int(d["days"])
        d["hours"] =    int(d["hours"])
        d["minutes"] =  int(d["minutes"])

        return d

    def strfdelta(self, tdelta):
        d = self._get_time_dict(tdelta)
        if d["days"] > 0:
            fmt = self.day_time_format
        elif d["hours"] > 0:
            fmt = self.hours_time_format
        elif d["minutes"] > 0:
            fmt = self.min_time_format
        else:
            fmt = self.sec_time_format

        return fmt.format(**d)

class EnvVarParser:

    def __init__(self):
        self.postgres_user_key = "POSTGRES_USER"
        self.postgres_password_key = "POSTGRES_PASSWORD"
        self.postgres_host_key = "POSTGRES_HOST"
        self.postgres_dbname_key = "POSTGRES_DBNAME"

        self.postgres_dict = {}

    @staticmethod
    def get_double_from_env(env_string, default_val=None):
        os_env_val = os.getenv(env_string, default_val)
        return float(os_env_val)
    @staticmethod
    def get_int_from_env(env_string, default_val=None):
        os_env_val = os.getenv(env_string, default_val)
        return int(os_env_val)
    @staticmethod
    def get_boolean_from_env(env_string, default_val=None):
        os_env_val = os.getenv(env_string, default_val)
        if 'y' in os_env_val.lower():
            return True
        elif 'n' in os_env_val.lower():
            return False
        else:
            raise Exception("Unparsable boolean from env variable: {0} -> {1}".format(env_string, os_env_val))

    def get_postgres_info(self):
        self.postgres_dict["user"] =     os.getenv(self.postgres_user_key, None)
        self.postgres_dict["password"] = os.getenv(self.postgres_password_key, None)
        self.postgres_dict["host"] =     os.getenv(self.postgres_host_key, None)
        self.postgres_dict["name"] =     os.getenv(self.postgres_dbname_key, None)

        return self.postgres_dict


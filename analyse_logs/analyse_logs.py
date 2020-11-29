import os
import re
import json

from enum import Enum
from json import JSONEncoder
from datetime import datetime

logs_dir = "logs"

class MyJSONEncoder(JSONEncoder):
    def default(self, o):
        return o.__dict__  

class LogKeys(Enum):
    timestamp = 1
    level = 2
    module = 3
    msg = 4
class ServerLogKeys(Enum):
    timestamp = 1
    level = 2
    module = 3

    ip_address = 4
    method = 5
    http_address = 6
    src_http_address = 7
class TracebackLogKeys(Enum):
    timestamp = 1
    level = 2
    module = 3

    tb_msg = 4
    msg = 5
    src_log = 6

class LogLine:
    def __init__(self, input_match, base_enum_keys):
        for kkk in base_enum_keys:
            try:
                ggg = input_match.group(kkk.name)
                setattr(self, kkk.name, ggg)
            except IndexError as excp:
                setattr(self, kkk.name, None)

class LogAnalyser:

    def __init__(self):
        self.ts_key = LogKeys.timestamp.name
        self.level_key = LogKeys.level.name
        self.module_key = LogKeys.module.name
        self.msg_key = LogKeys.msg.name

        self.ip_address_key = ServerLogKeys.ip_address.name
        self.method_key = ServerLogKeys.method.name
        self.http_address_key = ServerLogKeys.http_address.name
        self.src_http_address_key = ServerLogKeys.src_http_address.name

        self.ts_pattern = "?P<{}>".format(self.ts_key) + "\[\d{4}-\d{1,2}-\d{1,2} \d{2}:\d{2}:\d{2},\d{3}\]"
        self.level_pattern = "?P<{}>[A-Z]+".format(self.level_key)
        self.module_pattern = "?P<{}>\w+".format(self.module_key)

        self.logbase_pattern = "({0}) ({1}) in ({2}):".format(self.ts_pattern, self.level_pattern, self.module_pattern)
        self.logbase_with_msg_pattern = "{0} (?P<{1}>.*)".format(self.logbase_pattern, self.msg_key)

        self.tb_pattern = "{} (Error traceback ->|Exception in worker process)".format(self.logbase_pattern)

        self.ip_pattern = "?P<{}>".format(self.ip_address_key) + "\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}"
        self.req_method_pattern = "?P<{}>POST|GET".format(self.method_key)
        self.http_address_pattern = "?P<{}>.*?".format(self.http_address_key)
        self.src_http_address_pattern = "?P<{}>(.+?)".format(self.src_http_address_key)

        self.server_log_pattern = '{0} ({1}) .+ "({2}) ({3})" .+ "({4})" ".+"'.format(
                                                                            self.logbase_pattern,
                                                                            self.ip_pattern,
                                                                            self.req_method_pattern,
                                                                            self.http_address_pattern,
                                                                            self.src_http_address_pattern)

        self.msg_filters = []
        self.msg_filters.append("Game .+? is started")
        self.msg_filters.append("Received image with shape")
        self.msg_filters.append("Image processed in")
        self.msg_filters.append("Processed image saved")
        self.msg_filters.append("Game .+? was updated to step")
        self.msg_filters.append("Game .+? was ended")
        self.msg_filters.append("round_filter")
        self.msg_filters.append("Logging is initialised to")
        self.msg_filters.append("Generating new fontManager")
        self.msg_filters.append("Building model efficientnet")
        self.msg_filters.append("TF model initialised with")
        self.msg_filters.append("EfficientDet EfficientNet backbone version")


        self.msg_filters.append("Server is ready to detect")
        self.msg_filters.append("EfficientDet BiFPN num filters")
        self.msg_filters.append("EfficientDet BiFPN num iterations")
        self.msg_filters.append("round_filter")

        self.msg_filters.append("405 Method Not Allowed")
        self.msg_filters.append("404 Not Found")
        self.msg_filters.append("400 Bad Request")

        ### line filtering by property

        self.allowed_dict = {}

        self.denied_dict = {}
        self.denied_dict[ServerLogKeys.ip_address.name] = []
        self.denied_dict[ServerLogKeys.http_address.name] = ["/ HTTP/1.0"]

        self.date_fmt = "[%Y-%m-%d %H:%M:%S,%f]"
        self.low_time = datetime.min
        self.up_time = datetime.max
        # self.low_time = datetime(2020, 11, 12, 14, 1)
        # self.up_time = datetime(2020, 11, 12, 16)

    @staticmethod
    def match_at_least_one(input_value, input_list):
        is_match = False

        for lll in input_list:
            is_match = is_match or re.match(lll, input_value)

        return is_match

    def line_is_valid(self, logline):

        if logline is None:
            return False

        conv_timestamp = datetime.strptime(logline.timestamp, self.date_fmt)

        if conv_timestamp > self.low_time and conv_timestamp < self.up_time:
            log_line_dict = logline.__dict__

            is_valid = True
            for kkk, vvv in log_line_dict.items():
                if not kkk == "timestamp":
                    if kkk in self.allowed_dict.keys():
                        allowed_list = self.allowed_dict[kkk]
                        if len(allowed_list) > 0:
                            is_valid = is_valid and self.match_at_least_one(vvv, allowed_list)

                    if kkk in self.denied_dict.keys():
                        denied_list = self.denied_dict[kkk]
                        if len(denied_list) > 0:
                            is_valid = is_valid and (not self.match_at_least_one(vvv, denied_list))
            
            return is_valid
        else:
            return False

    def analyse_logs(self, input_file_path):
        with open(input_file_path, "r") as f:
            cnt = f.readlines()

        filtered_lines = []

        unrec_lines = []
        srv_log_lines = []
        tb_lines = []

        is_traceback = False
        tb_log_line = None
        for lll in cnt:
            basic_log_line_match = re.match(self.logbase_with_msg_pattern, lll)
            if basic_log_line_match:
                basic_log_line = LogLine(basic_log_line_match, LogKeys)
                tb_line = re.match(self.tb_pattern, lll)
                srv_log_line = re.match(self.server_log_pattern, lll)

                if self.line_is_valid(basic_log_line):
                    filtered_lines.append(lll)

                if srv_log_line:
                    log_line = LogLine(srv_log_line, ServerLogKeys)
                    if is_traceback:
                        tb_log_line.src_log = log_line
                        tb_lines.append(tb_log_line)
                        filtered_lines.extend(tb_log_line.tb_msg)
                        is_traceback = False
                    else:
                        if self.line_is_valid(log_line):
                            srv_log_lines.append(log_line)
                elif tb_line:
                    tb_log_line = LogLine(tb_line, TracebackLogKeys)
                    tb_log_line.tb_msg = []
                    is_traceback = True
                elif is_traceback:
                    tb_log_line.msg = basic_log_line.msg
                else:
                    unrec_lines.append(basic_log_line)
            else:
                if is_traceback:
                    tb_log_line.tb_msg.append(lll)
                else:
                    print(input_file_path)
                    print(lll)
                    raise Exception("Breaking pattern: {0}".format(lll))
        
        print(len(unrec_lines))
        print(len(srv_log_lines))
        print(len(tb_lines))

        input_base_name = os.path.basename(input_file_path).replace(".log", "")
        print(input_base_name)

        filtered_log_file_path = "-".join([input_base_name,"filtered.log"])
        with open(filtered_log_file_path, "w") as f:
            f.writelines(filtered_lines)

        unrec_file_path = "-".join([input_base_name, "unrec_lines.json"])
        with open(unrec_file_path, "w") as f:
            json.dump(self.aggregate_by_level_module_msg(unrec_lines), f, indent=4, cls=MyJSONEncoder)

        tb_file_path = "-".join([input_base_name,"tb_lines.json"])
        with open(tb_file_path, "w") as f:
            json.dump(self.aggregate_by_level_module_msg(tb_lines), f, indent=4, cls=MyJSONEncoder)
        tb_file_path = "-".join([input_base_name, "tb_lines_by_ip.json"])
        with open(tb_file_path, "w") as f:
            json.dump(self.aggregate_by_ip_http_method(tb_lines, is_derived_line=True), f, indent=4, cls=MyJSONEncoder)

        srv_log_file_path = "-".join([input_base_name, "srv_log_lines.json"])
        with open(srv_log_file_path, "w") as f:
            json.dump(self.aggregate_by_ip_http_method(srv_log_lines), f, indent=4, cls=MyJSONEncoder)

    def aggregate_by_ip_http_method(self, input_list, is_derived_line=False):
        out_dict = {}
        for lll in input_list:
            if is_derived_line:
                l_dict = lll.src_log.__dict__
                l_dict["tb_msg"] = lll.tb_msg
                l_dict["err_msg"] = lll.msg
            else:
                l_dict = lll.__dict__
            ip_address = l_dict.pop(ServerLogKeys.ip_address.name, None)
            http_address = l_dict.pop(ServerLogKeys.http_address.name, None)
            method = l_dict.pop(ServerLogKeys.method.name, None)
            if not (ip_address in out_dict.keys()):
                out_dict[ip_address] = {}
                out_dict[ip_address]["count"] = 0
            
            if not (http_address in out_dict[ip_address].keys()):
                out_dict[ip_address][http_address] = {}
                out_dict[ip_address][http_address]["dict"] = {}
                out_dict[ip_address][http_address]["count"] = 0

            if not (method in out_dict[ip_address][http_address]["dict"].keys()):
                out_dict[ip_address][http_address]["dict"][method] = {}
                out_dict[ip_address][http_address]["dict"][method]["list"] = []
                out_dict[ip_address][http_address]["dict"][method]["count"] = 0
            out_dict[ip_address][http_address]["dict"][method]["list"].append(l_dict)
            out_dict[ip_address][http_address]["dict"][method]["count"] += 1

            out_dict[ip_address]["count"] += 1
            out_dict[ip_address][http_address]["count"] += 1
        
        return out_dict
    def aggregate_by_level_module_msg(self, input_list):
        out_dict = {}
        for lll in input_list:
            l_dict = lll.__dict__
            level = l_dict.pop(LogKeys.level.name, None)
            module = l_dict.pop(LogKeys.module.name, None)
            msg = l_dict[LogKeys.msg.name]
            if not (level in out_dict.keys()):
                out_dict[level] = {}
            
            unfiltered_key = "unfiltered"
            if not (module in out_dict[level].keys()):
                out_dict[level][module] = {}
                out_dict[level][module]["dict"] = {}
                out_dict[level][module]["count"] = 0

            match_filter = unfiltered_key
            for fff in self.msg_filters:
                mmm = re.match(fff, msg)
                if mmm:
                    match_filter = fff
                    break
            
            if not (match_filter in out_dict[level][module]["dict"].keys()):
                out_dict[level][module]["dict"][match_filter] = {}
                out_dict[level][module]["dict"][match_filter]["list"] = []
                out_dict[level][module]["dict"][match_filter]["count"] = 0
            out_dict[level][module]["dict"][match_filter]["list"].append(l_dict)
            out_dict[level][module]["dict"][match_filter]["count"] += 1

            out_dict[level][module]["count"] += 1
        
        return out_dict

lg_analyser = LogAnalyser()

for fff in os.listdir(logs_dir):
    file_path = os.path.join(logs_dir, fff)
    lg_analyser.analyse_logs(file_path)

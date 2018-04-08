import json
from typing import Dict, Union

import requests


class Interpreter(object):

    def __init__(self):
        self.variables: Dict[str, object] = {}
        self.methods: Dict[str, object] = {}
        self.proxy_methods: Dict[str, callable] = {}
        self._register_proxies()

    def _register_proxies(self):
        self.proxy_methods["set"] = self.set_value

    def run_file(self, path: str):
        with open(path, encoding="utf8") as f:
            statements = json.load(f)
            self.execute_statements(statements)

    def run_url(self, url: str):
        resp = requests.get(url)
        self.execute_statements(resp.json())

    def set_value(self, name: str, value):
        if isinstance(value, dict):
            self.execute_statements([value])
            self.variables[name] = self.variables.get("RETVAL", None)
        else:
            self.variables[name] = value

    def execute_statements(self, statements: Union[list, object], parameters=None):
        if parameters is None:
            parameters = {}
        for statement in statements:
            if statement["operation"] == "define":
                name = statement["args"]["name"]
                code = statement["args"]["code"]
                self.methods[name] = code

            elif statement["operation"] == "get":
                name = statement["args"]["name"]
                if name in parameters:
                    self.variables["RETVAL"] = parameters[name]
                else:
                    self.variables["RETVAL"] = self.variables.get(name, None)

            elif statement["operation"] in self.methods:
                self.execute_statements(self.methods[statement["operation"]], statement.get("args", {}))

            elif statement["operation"] in self.proxy_methods:
                self.proxy_methods[statement["operation"]](**statement.get("args", {}))
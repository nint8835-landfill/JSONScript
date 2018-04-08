import json
from typing import Dict, Union

import requests


class Interpreter(object):

    def __init__(self) -> None:
        self.variables: Dict[str, object] = {}
        self.methods: Dict[str, object] = {}
        self.proxy_methods: Dict[str, callable] = {}
        self._register_proxies()

    def _register_proxies(self) -> None:
        """
        Registers all JSON to Python proxy methods
        """
        self.proxy_methods["set"] = self.set_value
        self.proxy_methods["return"] = self.return_value
        self.proxy_methods["import"] = self.import_file

        self.proxy_methods["add"] = self.add
        self.proxy_methods["subtract"] = self.subtract
        self.proxy_methods["multiply"] = self.multiply
        self.proxy_methods["divide"] = self.divide

    def run(self, path: str) -> None:
        """
        Runs a program from a path. Can be either a file or a URL
        :param path: The path to run the program from
        """
        if path.startswith("http://") or path.startswith("https://"):
            self.run_url(path)
        else:
            self.run_file(path)

    def run_file(self, path: str) -> None:
        """
        Loads a file and runs it
        :param path: The path to the file
        """
        with open(path, encoding="utf8") as f:
            statements = json.load(f)
            self.execute_statements(statements)

    def run_url(self, url: str) -> None:
        """
        Loads a URL and runs it
        :param url: The URL to load
        """
        resp = requests.get(url)
        self.execute_statements(resp.json())

    def process_value(self, value, arguments):
        """
        Processes a value. Executes it if it is a statement, otherwise returns the value
        :param value: The value to process
        :param arguments: The current arguments
        :return: The processed value
        """
        # Execute the value if it is a statement
        if isinstance(value, dict):
            self.execute_statements([value], arguments)
            return self.variables.get("RETVAL", None)
        # Otherwise, return the value
        return value

    def set_value(self, args) -> None:
        """
        Sets a variable to a given value
        """
        self.variables[args["name"]] = self.process_value(args["value"], args)

    def return_value(self, args):
        """
        Returns a certain value
        """
        return self.process_value(args["return_value"], args)

    def add(self, args):
        """
        Adds two values together
        """
        left = self.process_value(args["left"], args)
        right = self.process_value(args["right"], args)
        return left + right

    def subtract(self, args):
        """
        Subtracts one value from another
        """
        left = self.process_value(args["left"], args)
        right = self.process_value(args["right"], args)
        return left - right

    def multiply(self, args):
        """
        Multiplies two values
        """
        left = self.process_value(args["left"], args)
        right = self.process_value(args["right"], args)
        return left * right

    def divide(self, args):
        """
        Divides two values
        """
        left = self.process_value(args["left"], args)
        right = self.process_value(args["right"], args)
        return left / right

    def import_file(self, args):
        """
        Executes a file to import all methods and variables defined within it
        """
        self.run(args["path"])

    def execute_statements(self, statements: Union[list, object], arguments=None) -> None:
        """
        Executes a list of statements
        :param statements: The list of statements to execute
        :param arguments: A dict of arguments to be used, if this is a method call
        """
        if arguments is None:
            arguments = {}

        for statement in statements:

            for key in arguments:
                if key not in statement.get("args", {}) and key not in self.variables:
                    statement.get("args", {})[key] = arguments[key]

            if statement["operation"] == "define":
                # If the user is attempting to define a method, add this statement's code list to the methods dict
                name = statement["args"]["name"]
                code = statement["args"]["code"]
                self.methods[name] = code

            elif statement["operation"] == "get":
                # Sets the return value to the value of a variable
                name = statement["args"]["name"]
                self.variables["RETVAL"] = self.variables.get(name, None)

            elif statement["operation"] == "getarg":
                self.variables["RETVAL"] = arguments[statement["args"]["name"]]

            # If the operation is a method that has been declared, execute that method
            elif statement["operation"] in self.methods:
                self.execute_statements(self.methods[statement["operation"]], statement["args"])

            # If the operation is a proxy method that has been declared, call that method
            elif statement["operation"] in self.proxy_methods:
                result = self.proxy_methods[statement["operation"]](statement["args"])
                if result is not None:
                    self.variables["RETVAL"] = result

from jsonscript import Interpreter

interpreter = Interpreter()
interpreter.run_file("test.json")
print(interpreter.variables["RETVAL"])

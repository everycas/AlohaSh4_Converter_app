class Ini:
    """ Get / Set section & param from specified ini file.
    With possible reading/writing errors logging to specified log-file."""

    def __init__(self):
        from configparser import ConfigParser
        import datetime as dt

        self.ini = ConfigParser()
        self.now = dt.datetime.now

    def get(self, log: str, ini: str, section: str, param: str):
        """ Get ini parameter meaning. Params: log: name of log if errors, ini: ini file name,
            section: ini section name, param: ini parameter name. """
        try:
            self.ini.read(ini)
        except Exception as Argument:
            with open(log, "a") as log_file:
                log_file.write(f"{self.now}: INI ERROR (SET): {str(Argument)}")
        else:
            data = self.ini[section][param]
            return data

    def set(self, log: str, ini: str, section: str, param: str, data: str):
        """ Set ini section or parameter meaning. Params: log: name of log if errors, ini: ini file name,
            section: ini section name, param: ini parameter name, data: parameter meaning. """
        try:
            self.ini.read(ini)
        except Exception as Argument:
            with open(log, "a") as log_file:
                log_file.write(f"{self.now}: SET INI ERROR: {str(Argument)}")
        else:
            self.ini.set(section, param, data)
            with open(ini, 'w') as ini_file:
                self.ini.write(ini_file)

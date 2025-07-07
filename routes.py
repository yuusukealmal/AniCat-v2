from enum import Enum


class color(Enum):
    RED = "{} \033[1;31m{}\033[0m"
    GREEN = "{} \033[32m{}\033[0m"
    YELLOW = "{} \033[33m{}\033[0m"
    BLUE = "{} \033[34m{}\033[0m"
    MAGENTA = "{} \033[35m{}\033[0m"
    CYAN = "{} \033[36m{}\033[0m"
    WHITE = "{} \033[37m{}\033[0m"
    RESET = "{} \033[0m{}\033[0m"

    def format(self, prefix, text):
        print(self.value.format(prefix, text))

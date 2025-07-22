# Базовый класс для всех парсеров


class BaseParser:
    name = "BaseParser"
    url = "url"

    def parse(self, orderno, driver):
        raise NotImplementedError("Этот метод должен быть переопределён в подклассах.")

    def process_delivered_info(self, info):
        raise NotImplementedError("Этот метод должен быть переопределён в подклассах.")

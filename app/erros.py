class DadosInvalidos(Exception):
    def __init__(self, erros):
        super().__init__("dados inválidos")
        self.erros = erros

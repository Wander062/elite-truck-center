PERFIL_ADMINISTRADOR = "administrador"
PERFIL_ESCRITORIO = "escritorio"
PERFIS_PAINEL = (PERFIL_ADMINISTRADOR, PERFIL_ESCRITORIO)

STATUS_PENDENTE = "pendente"
STATUS_EM_ATENDIMENTO = "em_atendimento"
STATUS_CONCLUIDA = "concluida"
STATUS_SOLICITACAO = (
    (STATUS_PENDENTE, "Pendente"),
    (STATUS_EM_ATENDIMENTO, "Em atendimento"),
    (STATUS_CONCLUIDA, "Concluída"),
)
STATUS_VALIDOS = {valor for valor, _rotulo in STATUS_SOLICITACAO}

TIPO_CAMINHAO = "caminhao"
TIPO_ONIBUS = "onibus"
TIPO_OUTRO = "outro"
TIPOS_VEICULO = (
    (TIPO_CAMINHAO, "Caminhão"),
    (TIPO_ONIBUS, "Ônibus"),
    (TIPO_OUTRO, "Outro"),
)
TIPOS_VALIDOS = {valor for valor, _rotulo in TIPOS_VEICULO}

UNIDADES = (
    ("", "Não informar"),
    ("UN", "Unidade"),
    ("PC", "Peça"),
    ("KG", "Quilograma"),
    ("G", "Grama"),
    ("L", "Litro"),
    ("ML", "Mililitro"),
    ("M", "Metro"),
    ("CM", "Centímetro"),
    ("PAR", "Par"),
    ("JOGO", "Jogo"),
    ("CX", "Caixa"),
    ("KIT", "Kit"),
)
UNIDADES_VALIDAS = {valor for valor, _rotulo in UNIDADES}

MAX_ITENS = 30
POR_PAGINA = 20
MAX_MARCA = 80
MAX_MODELO = 80
MAX_IDENTIFICACAO = 120
MAX_RESPONSAVEL = 120
MAX_OBSERVACOES = 2000
MAX_DESCRICAO_PECA = 200
MAX_OBSERVACAO_PECA = 500
MAX_PLACA = 30

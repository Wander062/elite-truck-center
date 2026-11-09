from app.extensions import db
from app.tempo import agora_utc


class Solicitacao(db.Model):
    __tablename__ = "solicitacoes"

    id = db.Column(db.Integer, primary_key=True)
    chave_envio = db.Column(db.String(36), nullable=False, unique=True)
    placa = db.Column(db.String(30), nullable=False, index=True)
    placa_fora_padrao = db.Column(db.Boolean, nullable=False, default=False)
    tipo_veiculo = db.Column(db.String(20), nullable=False)
    marca = db.Column(db.String(80), nullable=False)
    modelo = db.Column(db.String(80), nullable=False)
    identificacao_adicional = db.Column(db.String(120))
    responsavel_nome = db.Column(db.String(120), nullable=False)
    observacoes_gerais = db.Column(db.Text)
    status = db.Column(db.String(32), nullable=False, default="pendente", index=True)
    criado_em = db.Column(db.DateTime, nullable=False, default=agora_utc, index=True)
    atualizado_em = db.Column(db.DateTime, nullable=False, default=agora_utc, onupdate=agora_utc)

    itens = db.relationship(
        "ItemSolicitacao",
        back_populates="solicitacao",
        cascade="all, delete-orphan",
        order_by="ItemSolicitacao.id",
    )
    historico = db.relationship(
        "HistoricoStatus",
        back_populates="solicitacao",
        cascade="all, delete-orphan",
        order_by="HistoricoStatus.id",
    )

    @property
    def protocolo(self):
        if self.id is None:
            return ""
        return f"SOL-{self.id:06d}"

    def __repr__(self):
        return f"<Solicitacao {self.id} {self.status}>"


class ItemSolicitacao(db.Model):
    __tablename__ = "itens_solicitacao"

    id = db.Column(db.Integer, primary_key=True)
    solicitacao_id = db.Column(
        db.Integer,
        db.ForeignKey("solicitacoes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    descricao = db.Column(db.String(200), nullable=False)
    quantidade = db.Column(db.Numeric(10, 3), nullable=False)
    unidade = db.Column(db.String(20))
    observacao = db.Column(db.String(500))

    solicitacao = db.relationship("Solicitacao", back_populates="itens")


class HistoricoStatus(db.Model):
    __tablename__ = "historico_status"

    id = db.Column(db.Integer, primary_key=True)
    solicitacao_id = db.Column(
        db.Integer,
        db.ForeignKey("solicitacoes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status_anterior = db.Column(db.String(32), nullable=False)
    status_novo = db.Column(db.String(32), nullable=False)
    usuario_id = db.Column(
        db.Integer,
        db.ForeignKey("usuarios.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    criado_em = db.Column(db.DateTime, nullable=False, default=agora_utc)

    solicitacao = db.relationship("Solicitacao", back_populates="historico")
    usuario = db.relationship("Usuario")

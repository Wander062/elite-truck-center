# Solicitação de peças

Aplicação web para a oficina de caminhões e ônibus substituir o formulário de papel. O responsável preenche a solicitação no celular. O escritório consulta os dados no computador e lança a ordem de serviço no Premium TSI.

O sistema **não** substitui o Premium TSI, **não** integra com ele e **não** dá baixa de estoque.

## Tecnologias

- Python 3.11 ou superior (no Windows, o pacote `tzdata` entra nas dependências para o fuso de São Paulo)
- Flask, Flask-SQLAlchemy, Flask-Login, Flask-WTF e Flask-Migrate
- MySQL 8 (ou MariaDB 10.5+) com PyMySQL
- HTML, CSS, JavaScript e Bootstrap 5.3 (arquivo local, sem depender de CDN na oficina)

## Decisões desta versão

- O formulário do pátio não pede login. Quem alcança o endereço na rede da oficina pode enviar uma solicitação, mas não consegue listar nem abrir pedidos de outras pessoas. A página de confirmação usa um identificador aleatório, impossível de percorrer em sequência.
- O painel exige login. Os perfis `administrador` e `escritorio` consultam, pesquisam e alteram status. Não há tela de cadastro de usuários: os acessos são criados pelo comando `flask criar-usuario`.
- Cada mudança de status pede confirmação e grava quem alterou, o status anterior, o novo e o horário.
- A placa aceita o padrão antigo (`ABC-1234`) e o Mercosul (`ABC1D23`). Se o veículo não tiver placa nesse formato, a pessoa marca a opção e informa outra identificação.
- O protocolo exibido é `SOL-000001`, gerado a partir do identificador da solicitação.
- O envio passa por uma revisão. Uma chave única impede que o mesmo envio seja gravado duas vezes.
- Data e hora são gravadas em UTC e mostradas no fuso `America/Sao_Paulo`.
- Uma solicitação enviada não pode ser editada. Correção se faz com um novo envio, avisando o escritório.

## Pré-requisitos

- Python 3.11+
- MySQL 8 em execução
- Computador do escritório e celulares na mesma rede, se o formulário for aberto pelo telefone

## Banco de dados

No cliente MySQL, crie um banco e um usuário só para esta aplicação. Troque a senha:

```sql
CREATE DATABASE oficina_pecas CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'oficina'@'localhost' IDENTIFIED BY 'escolha-uma-senha';
GRANT ALL PRIVILEGES ON oficina_pecas.* TO 'oficina'@'localhost';
FLUSH PRIVILEGES;
```

Para o teste opcional de integração:

```sql
CREATE DATABASE oficina_pecas_test CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
GRANT ALL PRIVILEGES ON oficina_pecas_test.* TO 'oficina'@'localhost';
FLUSH PRIVILEGES;
```

O teste apaga as tabelas desse banco. Use somente `oficina_pecas_test`, nunca o banco de trabalho.

## Instalação

No PowerShell, na pasta do projeto:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Edite o `.env`:

- `SECRET_KEY`: cole a chave gerada acima
- `DATABASE_URL`: usuário, senha e banco reais, no formato  
  `mysql+pymysql://oficina:escolha-uma-senha@127.0.0.1:3306/oficina_pecas?charset=utf8mb4`
- `SESSION_COOKIE_SECURE`: deixe `0` enquanto o acesso for HTTP na rede interna. Use `1` somente se todo o acesso passar por HTTPS

O arquivo `.env` não deve ser versionado.

## Migrations

```powershell
flask --app run.py db upgrade
```

Para criar o primeiro administrador:

```powershell
flask --app run.py criar-usuario --nome "Nome do Administrador" --usuario "admin" --senha "uma-senha-forte" --perfil administrador
```

Outro acesso de escritório usa `--perfil escritorio`. A senha precisa ter de 8 a 128 caracteres. O login aceita usuário ou e-mail, gravado em minúsculas, sem espaços.

Para bloquear um acesso sem apagar o histórico:

```sql
UPDATE usuarios SET ativo = 0 WHERE usuario = 'admin';
```

## Execução

```powershell
python run.py
```

- Formulário: `http://127.0.0.1:5000/`
- Painel: `http://127.0.0.1:5000/entrar`

No celular, use o IP do computador (`ipconfig`), por exemplo `http://192.168.0.10:5000/`. Libere a porta no firewall do Windows. Mantenha o servidor apenas na rede da oficina: o formulário é público de propósito, para o preenchimento ser rápido, e não deve ficar exposto na internet.

Não ligue `FLASK_DEBUG=1` em uma máquina acessível por outras pessoas. O depurador do Flask pode executar código.

Faça backup periódico do banco `oficina_pecas`.

## Testes

Os testes automáticos usam SQLite em memória e cobrem envio, várias peças, campos obrigatórios, duplicidade, login, permissão, pesquisa, período e status. A suíte sobe o mesmo esquema relacional usado no MySQL.

```powershell
python -m pytest
```

Para exercitar o MySQL de verdade, com o banco `oficina_pecas_test` vazio:

```powershell
$env:TEST_DATABASE_URL = "mysql+pymysql://oficina:escolha-uma-senha@127.0.0.1:3306/oficina_pecas_test?charset=utf8mb4"
python -m pytest -m mysql
```

Sem essa variável, o teste de MySQL aparece como ignorado.

## Uso

1. O responsável abre o formulário, informa veículo, nome e peças e segue para a revisão.
2. Confere os dados e envia. A tela mostra o protocolo `SOL-000001`.
3. No escritório, entre no painel, pesquise pela placa ou pelo período e abra a solicitação.
4. Confira peça por peça e lance a ordem de serviço no Premium TSI.
5. Altere o status (Pendente, Em atendimento ou Concluída). A mudança só grava depois da confirmação.

## Estrutura

```text
app/
├── models/          usuários, solicitações, itens e histórico de status
├── routes/          formulário público, login e painel
├── services/        regras de gravação, consulta e acesso
├── forms/           login com CSRF
├── templates/
└── static/
migrations/
tests/
config.py
run.py
```

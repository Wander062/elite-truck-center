def registrar_rotas(app):
    from app.routes.auth import bp as auth_bp
    from app.routes.painel import bp as painel_bp
    from app.routes.publico import bp as publico_bp

    app.register_blueprint(publico_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(painel_bp)

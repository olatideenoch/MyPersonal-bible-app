"""Blueprint registry.

Each blueprint owns a slice of the URL map:

    main    -> home, search, contact, install
    reader  -> books/chapters/verses/versions, compare, commentary, audio
    study   -> reading plans, topics, quiz, devotional, memorize
    user    -> OAuth, sync, streaks, Bible-in-a-Year, profile, export
    push    -> daily verse reminder subscriptions
    meta    -> robots, sitemap, health, offline page, service worker
"""


def register_blueprints(app) -> None:
    from .main import bp as main_bp
    from .meta import bp as meta_bp
    from .push import bp as push_bp
    from .reader import bp as reader_bp
    from .study import bp as study_bp
    from .user import bp as user_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(reader_bp)
    app.register_blueprint(study_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(push_bp)
    app.register_blueprint(meta_bp)

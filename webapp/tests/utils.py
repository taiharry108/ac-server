from sqlalchemy.orm import Session
from webapp.models.db_models import User, History, Manga, MangaSite, Chapter, Page


def delete_all(session: Session) -> bool:
    session.query(Page).delete()
    session.query(Chapter).delete()

    for user in session.query(User).all():
        user.fav_mangas = []
        user.history = []
    session.commit()
    session.query(History).delete()
    session.query(Manga).delete()
    session.query(User).delete()
    session.query(MangaSite).delete()
    session.commit()
    return True

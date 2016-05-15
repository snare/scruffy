"""
State
-----

Classes for storing a program's state.
"""
import os
import yaml

try:
    from sqlalchemy import create_engine, Column, Integer, String
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.orm import sessionmaker, reconstructor
    Base = declarative_base()
    HAVE_SQL_ALCHEMY = True
except:
    HAVE_SQL_ALCHEMY = False


class State(object):
    """
    A program's state.

    Contains a dictionary that can be periodically saved and restored at startup.

    Maybe later this will be subclassed with database connectors and whatnot,
    but for now it'll just save to a yaml file.
    """
    @classmethod
    def state(cls, *args, **kwargs):
        return cls(*args, **kwargs)

    def __init__(self, path=None):
        self.path = path
        self.d = {}
        self.load()

    def __enter__(self):
        self.load()
        return self

    def __exit__(self, type, value, traceback):
        self.save()

    def __getitem__(self, key):
        try:
            return self.d[key]
        except KeyError:
            return None

    def __setitem__(self, key, value):
        self.d[key] = value

    def save(self):
        """
        Save the state to a file.
        """
        with open(self.path, 'w') as f:
            f.write(yaml.dump(dict(self.d)))

    def load(self):
        """
        Load a saved state file.
        """
        if os.path.exists(self.path):
            with open(self.path, 'r') as f:
                self.d = yaml.safe_load(f.read().replace('\t', ' '*4))

    def cleanup(self):
        """
        Clean up the saved state.
        """
        if os.path.exists(self.path):
            os.remove(self.path)


if HAVE_SQL_ALCHEMY:
    class DBState(State, Base):
        """
        State stored in a database, using SQLAlchemy.
        """
        __tablename__ = 'state'

        id = Column(Integer, primary_key=True)
        data = Column(String)

        session = None

        @classmethod
        def state(cls, url=None, *args, **kwargs):
            if not cls.session:
                engine = create_engine(url, echo=False)
                Base.metadata.create_all(engine)
                Session = sessionmaker(bind=engine)
                cls.session = Session()

            inst = cls.session.query(DBState).first()
            if inst:
                return inst
            else:
                return cls(*args, **kwargs)

        def __init__(self, *args, **kwargs):
            super(DBState, self).__init__(*args, **kwargs)
            self.d = {}
            self.data = '{}'

        def save(self):
            self.data = yaml.dump(self.d)
            self.session.add(self)
            self.session.commit()

        @reconstructor
        def load(self):
            if self.data:
                self.d = yaml.safe_load(self.data)

        def cleanup(self):
            self.d = {}
            self.save()

import sys, importlib

sys.path.insert(0, r"{{PROJECT}}")
store = importlib.import_module("{{PKG}}.store")
seed = importlib.import_module("{{PKG}}.seed")

db = store.connect()
try:
    seed.reset(db)
    db.commit()
    n = db.execute("SELECT COUNT(*) AS n FROM berms").fetchone()["n"]
    print("reset ok, berms =", n)
finally:
    db.close()

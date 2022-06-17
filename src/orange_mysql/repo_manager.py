class Repo:
  def __init__(self):
    pass

repo:Repo = None

def reg_repo():
  global repo
  repo= Repo()
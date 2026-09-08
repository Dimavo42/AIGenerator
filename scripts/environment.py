
import os
from pathlib import Path

class Environment:
   ENVIRONMENT_PATH = str(Path(__file__).resolve().parent.parent / ".env")
   _enviorment_keys = {}
   _is_loaded = False

   @classmethod
   def is_file_created(cls, output_file_path=None):
      return os.path.exists(output_file_path or cls.ENVIRONMENT_PATH)

   @classmethod
   def save_all(cls, values):
      cls._enviorment_keys = {k.strip(): v for k, v in values.items() if k.strip()}
      with open(cls.ENVIRONMENT_PATH, "w") as file:
         for key, value in cls._enviorment_keys.items():
            file.write(f"{key}={value}\n")

   @classmethod
   def _load_from_env(cls):
      cls._enviorment_keys = {}
      if not cls.is_file_created():
         cls.create_enviorment_file()
      with open(cls.ENVIRONMENT_PATH, "r") as file:
         for line in file:
            line = line.strip()
            if not line or "=" not in line:
               continue
            key, value = line.split("=",1)
            cls._enviorment_keys[key.strip()] = value.strip()
      cls._is_loaded = True
   
   @classmethod
   def create_enviorment_file(cls):
      Path(cls.ENVIRONMENT_PATH).touch()

   @classmethod
   def get_all_enviorment(cls):
      if cls._is_loaded == False:
         cls._load_from_env()
      return cls._enviorment_keys

      


      
    
   







    
    
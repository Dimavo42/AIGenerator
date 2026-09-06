
import os
from pathlib import Path

class Environment:
   ENVIRONMENT_PATH = str(Path(__file__).resolve().parent.parent / ".env")
   _enviorment_keys = {}

   @classmethod
   def is_file_created(cls, output_file_path=None):
      return os.path.exists(output_file_path or cls.ENVIRONMENT_PATH)

   @classmethod
   def write_to_file(cls, key,value):
      if not cls.is_file_created():
         cls.create_enviorment_file()
      cls._enviorment_keys[key] = value
      with open(cls.ENVIRONMENT_PATH, "a") as file:
         file.write(f"{key}={value}\n")

   @classmethod
   def save_all(cls, values):
      """Rewrite the whole file from a key -> value mapping (blank keys dropped)."""
      cls._enviorment_keys = {k.strip(): v for k, v in values.items() if k.strip()}
      with open(cls.ENVIRONMENT_PATH, "w") as file:
         for key, value in cls._enviorment_keys.items():
            file.write(f"{key}={value}\n")

   @classmethod
   def load_from_env(cls):
      cls._enviorment_keys = {}
      if not cls.is_file_created():
         return cls._enviorment_keys
      with open(cls.ENVIRONMENT_PATH, "r") as file:
         for line in file:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
               continue
            key, value = line.split("=",1)
            cls._enviorment_keys[key.strip()] = value.strip()
      return cls._enviorment_keys
   
   @classmethod
   def create_enviorment_file(cls):
      Path(cls.ENVIRONMENT_PATH).touch()

   @classmethod
   def get_enviorment_key(cls,key):
      return cls._enviorment_keys.get(key)

   @classmethod
   def get_all_enviorment(cls):
      return cls._enviorment_keys

      


      
    
   







    
    
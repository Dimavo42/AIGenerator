
import json
import os
from pathlib import Path

class Environment:
   ROOT_PATH = Path(__file__).resolve().parent.parent
   ENVIRONMENT_PATH = ROOT_PATH / ".env"
   DATA_PATH = ROOT_PATH / "app_data.json"
   _environment_keys = {}
   _data = {}
   _is_loaded = False
   _is_data_loaded = False

   # =========================================================
   # ENVIRONMENT
   # =========================================================

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
      return cls._enviorment_keys.copy()

   # =========================================================
   # SERIALIZATION / JSON
   # =========================================================
   @classmethod
   def _load_data(cls):
      if not cls.DATA_PATH.exists():
         cls.DATA_PATH.write_text("{}",encoding="utf-8")
         return
      try:
         with cls.DATA_PATH.open("r") as file:
            cls._data = json.load(file)
      except json.JSONDecodeError:
         cls._data = {}
      cls._is_data_loaded = True

   @classmethod
   def _save_data(cls):
      with open(cls.DATA_PATH,"w",encoding="utf-8") as file:
         json.dump(cls._data,file,indent=4,ensure_ascii=False)

   @classmethod
   def get_data(cls, key, default=None):
      if not cls._is_data_loaded:
         cls._load_data()
      return cls._data.get(key, default)

   @classmethod
   def get_all_data(cls):
      if not cls._is_data_loaded:
         cls._load_data()
      return cls._data.copy()

   @classmethod
   def remove_data(cls, key):
      if not cls._is_data_loaded:
         cls._load_data()
      if key in cls._data:
         del cls._data[key]
         cls._save_data()




      





         


   
   
      


      
    
   







    
    
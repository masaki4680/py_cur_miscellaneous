# .env ファイルをロードして環境変数へ反映
from dotenv import load_dotenv
load_dotenv()

# 環境変数を参照
import os
GMO_API_KEY = os.getenv('GMO_API_KEY')
GMO_API_SECRET = os.getenv('GMO_API_SECRET')
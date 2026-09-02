import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent/"backend"))

from llm_client import generate_response

result = generate_response("Say hello in one sentence")
print(result)
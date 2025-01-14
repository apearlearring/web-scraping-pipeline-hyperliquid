from typing import Dict

def process_funding_history(funding_history : Dict) -> Dict:

    return {k: v for k, v in funding_history.items() if k != 'coin'}



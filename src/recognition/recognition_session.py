from dataclasses import dataclass, field
from datetime import datetime
@dataclass
class RecognitionSession:
    tool:str
    started_at:datetime=field(default_factory=datetime.now)
    seed_count:int=0
    preview_active:bool=False
    metadata:dict=field(default_factory=dict)

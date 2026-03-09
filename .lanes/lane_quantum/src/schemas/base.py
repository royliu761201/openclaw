import json
from typing import Type, TypeVar, Optional
from pydantic import BaseModel

T = TypeVar("T", bound="PersistableModel")

class PersistableModel(BaseModel):
    """
    Mixin pattern for Auto-Save/Load capabilities on Pydantic Models.
    """
    
    def save(self, path: str):
        """Save schema to JSON file."""
        with open(path, "w") as f:
            f.write(self.model_dump_json(indent=2))
            
    @classmethod
    def load(cls: Type[T], path: str) -> Optional[T]:
        """Load schema from JSON file."""
        try:
            with open(path, "r") as f:
                return cls.model_validate_json(f.read())
        except FileNotFoundError:
            return None

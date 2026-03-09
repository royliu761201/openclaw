from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .engine import MedTimeEngine


@dataclass
class AnchoredEvent:
    """
    Standardized Clinical Event with Textual Anchoring
    """

    e: str
    t: Any  # Union[str, List[str]]
    n: str = "P"
    r: str = ""
    trigger: str = ""
    context: str = ""
    start: int = -1
    end: int = -1

    def anchor_to_text(self, text: str) -> bool:
        """Verbatim anchoring logic from MedTime v8"""
        import re

        # Auto-generate context if not provided
        if not self.context:
            # Try trigger first, then fall back to e
            self.context = self.trigger if self.trigger else (self.e[:20] if self.e else "")

        if not self.context:
            return False

        def build_relax_pattern(s):
            if not s:
                return None
            chars = [re.escape(c) for c in s if re.match(r"[a-zA-Z0-9\u4e00-\u9fa5]", c)]
            if not chars:
                return None
            gap = r".{0,12}?".replace("\\", "\\\\")
            return gap.join(chars)

        try:
            ctx_pat = build_relax_pattern(self.context)
            if not ctx_pat:
                return False

            match = re.search(ctx_pat, text, re.IGNORECASE | re.DOTALL)
            if not match:
                ctx_pat_short = build_relax_pattern(self.context[:12])
                match = re.search(ctx_pat_short, text, re.IGNORECASE | re.DOTALL)

            if not match:
                self.start, self.end = -1, -1
                return False

            c_start = match.start()
            c_end = match.end()
            matched_content = match.group()

            if self.trigger:
                trig_pat = build_relax_pattern(self.trigger)
                if trig_pat:
                    trig_match = re.search(trig_pat, matched_content, re.IGNORECASE | re.DOTALL)
                    if trig_match:
                        self.start = c_start + trig_match.start()
                        self.end = c_start + trig_match.end()
                        return True

            self.start, self.end = c_start, c_end
            return True
        except:
            self.start, self.end = -1, -1
            return False

    def to_dict(self):
        return {
            "e": self.e,
            "t": self.t,
            "n": self.n,
            "r": self.r,
            "trigger": self.trigger,
            "context": self.context,
            "start": self.start,
            "end": self.end,
        }


@dataclass
class Trajectory:
    """
    Patient Clinical Trajectory with Registry Support
    """

    id: str
    meta: Dict[str, Any]
    text: str = ""
    skeleton: str = ""
    timeline: List[AnchoredEvent] = field(default_factory=list)
    status: str = "PENDING"
    score: int = 0
    audit_feedback: str = ""
    vr_score: float = -1.0
    provenance: List[str] = field(default_factory=list)

    def to_registry(self) -> Dict[str, Any]:
        from dataclasses import asdict

        data = asdict(self)
        data.pop("id")
        if not self.skeleton:
            data.pop("skeleton", None)
        return data

    @classmethod
    def from_registry(cls, tid: str, data: Dict[str, Any]):
        nodes = [AnchoredEvent(**n) for n in data.get("timeline", []) if isinstance(n, dict)]
        return cls(
            id=tid,
            text=data.get("text") or data.get("raw_text", ""),
            skeleton=data.get("skeleton", ""),
            meta=data.get("meta", {}),
            timeline=nodes,
            status=data.get("status", "PENDING"),
            score=data.get("score") or data.get("audit_score", 0),
            audit_feedback=data.get("audit_feedback", ""),
            vr_score=data.get("vr_score", -1.0),
            provenance=data.get("provenance", []),
        )


class ClinicalValidator:
    """
    Clinical Logic Validator
    """

    @staticmethod
    def validate_schema(data: List[Dict]) -> bool:
        """Check if list of dicts conforms to event schema"""
        if not isinstance(data, list):
            return False
        for item in data:
            if not isinstance(item, dict):
                return False
            if "trigger" not in item or "e" not in item:
                return False
        return True

    @staticmethod
    def calculate_violation_rate(events: List[Dict]) -> float:
        """Calculate temporal violation rate for timeline"""
        return MedTimeEngine.Data.calculate_violation_rate(events)

    @staticmethod
    def check_temporal_consistency(events: List[Dict]) -> float:
        """Wrapper for Engine's violation rate"""
        return MedTimeEngine.Data.calculate_violation_rate(events)

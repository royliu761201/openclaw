import json
import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class MedTimeEngine:
    """
    Core Logic Engine for MedTime System.
    Handles component-level logic (Temporal, Text, Clinical).
    """

    EVENT_TRIGGERS = [
        {"pattern": re.compile(r"手术|术后|切除|surgery|operation|resection|debridement|excision|biopsy|transplant|amputation", re.I), "type": "Procedure"},
        {"pattern": re.compile(r"化疗|放疗|治疗|药|treat|chemo|radio|therapy|medication|drug|dose|prescrib|administer|inject|infus|radiotherapy", re.I), "type": "Treatment"},
        {"pattern": re.compile(r"确诊|诊断|检查|CT|MRI|diagnos|exam|imaging|scan|biopsy|ultrasound|x-ray|test|lab|blood|analysis|assess|evaluation|investigation", re.I), "type": "Diagnosis"},
        {"pattern": re.compile(r"出院|入院|死亡|就诊|咨询|admission|discharge|referred|presented|consulted|death|died|transfer|seen|visit|clinic|hospital", re.I), "type": "Admin"},
        {"pattern": re.compile(r"复发|转移|恶化|好转|progression|recurrence|metastasis|worsen|improve|resolv|remission|relapse", re.I), "type": "Progression"},
    ]

    INTERVAL_KEYWORDS = ["持续", "期间", "至今", "开始", "for", "during"]

    class Text:
        SENT_REGEX = re.compile(
            r"([^。！？；\n\r]+[。！？；\n\r]?|[^.!?;\n\r]+[.!?;\n\r]?)"
        )

        @classmethod
        def split_sentences(cls, text: str) -> List[Tuple[int, int, str]]:
            if not text:
                return []
            return [
                (m.start(), m.end(), m.group().strip())
                for m in cls.SENT_REGEX.finditer(text)
                if m.group().strip()
            ]

        @staticmethod
        def clean_medical_text(text: str) -> str:
            """
            High intensity cleansing from production notebook.
            Removes AI markers, Markdown bolding, and categoric headers.
            """
            if not text:
                return ""
            
            # 1. Remove Markdown bolding
            text = text.replace("**", "")
            
            # 2. Remove classification headers (A. B. C. or 1. 2. 3.)
            text = re.sub(r'^[A-Za-z0-9]\.?\s*.*?(记录|小结|会诊|转诊|报告|病历).*?([\n\r]+)', '', text, flags=re.IGNORECASE | re.MULTILINE)
            text = re.sub(r'^[A-Za-z0-9]\.?\s*.*?(记录|小结|会诊|转诊|报告|病历)\s*', '', text, flags=re.IGNORECASE)
            
            # 3. Remove all types of quotes
            for q in ["'", '"', "‘", "’", "“", "”"]:
                text = text.replace(q, "")
            
            # 4. Normalize whitespace
            text = re.sub(r'\n\s*\n', '\n', text)
            
            return text.strip()

        @staticmethod
        def normalize_medical(text: str) -> str:
            """Remove punctuation and spaces for robust comparison"""
            if not text:
                return ""
            return re.sub(r"[^\w\u4e00-\u9fa5]", "", str(text)).lower()

    class Temporal:

        @classmethod
        def extract_all_dates(
            cls, text: str, default_year: int = 2024, return_raw: bool = False
        ) -> List[Any]:
            """
            Ultimate Date Extractor:
            1. Support English/Chinese formats.
            2. Lighthouse Year detection support.
            3. Deduplication and strictly ordered.
            """
            if not isinstance(text, str):
                text = str(text)

            # Map for English months
            month_map = {
                "jan": 1,
                "feb": 2,
                "mar": 3,
                "apr": 4,
                "may": 5,
                "jun": 6,
                "jul": 7,
                "aug": 8,
                "sep": 9,
                "oct": 10,
                "nov": 11,
                "dec": 12,
                "january": 1,
                "february": 2,
                "march": 3,
                "april": 4,
                "june": 6,
                "july": 7,
                "august": 8,
                "september": 9,
                "october": 10,
                "november": 11,
                "december": 12,
            }

            s = text.lower().replace("20xx", str(default_year))
            results = []
            seen_pos = set()

            def add_res(dt, start, end, fix_needed=False):
                if start in seen_pos:
                    return
                label = "FIX_ME" if (dt.year == default_year or fix_needed) else "STD"
                # Always store full tuple internally for overlap logic
                results.append((label, dt, start, end))
                seen_pos.add(start)

            # 1. English Months (Oct 2019, Oct 12, 2019)
            month_patt = r"(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)"
            for m in re.finditer(month_patt + r"\.?\s*(?:(\d{1,2})[,\s]+)?(\d{4})", s):
                try:
                    m_idx = month_map.get(m.group(1)[:3].lower(), 1)
                    y_val = int(m.group(3))
                    d_val = int(m.group(2)) if m.group(2) else 1
                    # print(f"DEBUG: Found {m.groups()} -> {y_val}-{m_idx}-{d_val}")
                    add_res(datetime(y_val, m_idx, d_val), m.start(), m.end())
                except Exception as e:
                    # print(f"DEBUG: Error {e}")
                    continue

            # 2. Strict YMD (2015-03-01, 01/02/2015)
            for m in re.finditer(r"(\d{2,4})[./\-](\d{1,2})[./\-](\d{2,4})", s):
                try:
                    v1, v2, v3 = m.group(1), m.group(2), m.group(3)
                    if len(v1) == 4:
                        add_res(datetime(int(v1), int(v2), int(v3)), m.start(), m.end())
                    elif len(v3) == 4:
                        add_res(datetime(int(v3), int(v1), int(v2)), m.start(), m.end())
                except:
                    continue

            # 3. YM with 4-digit year (2015-03)
            for m in re.finditer(r"(?<!\d)(\d{4})[./\-](\d{1,2})(?!\d)", s):
                try:
                    add_res(
                        datetime(int(m.group(1)), int(m.group(2)), 1),
                        m.start(),
                        m.end(),
                    )
                except:
                    continue

            # 4. Chinese Formats
            for m in re.finditer(r"(\d{4})年(\d{1,2})月(\d{1,2})", s):
                try:
                    add_res(
                        datetime(int(m.group(1)), int(m.group(2)), int(m.group(3))),
                        m.start(),
                        m.end(),
                    )
                except:
                    continue
            for m in re.finditer(r"(\d{1,2})月(\d{1,2})[日号]", s):
                try:
                    add_res(
                        datetime(default_year, int(m.group(1)), int(m.group(2))),
                        m.start(),
                        m.end(),
                        fix_needed=True,
                    )
                except:
                    continue

            # 5. Standalone Years (2010-2024) - fallback for context detection
            for m in re.finditer(r"(?<!\d)(201[0-9]|202[0-4])(?!\d)", s):
                try:
                    # [FIX] Overlap Check: Don't add if already covered by a better match
                    is_covered = any(start <= m.start() and end >= m.end() for _, _, start, end in results if end - start > 4)
                    if not is_covered:
                         add_res(datetime(int(m.group(1)), 1, 1), m.start(), m.end())
                except:
                    continue
            
            # [FIX] Sort by position first to respect text order, or Keep Chronological?
            # Original intent: Chronological.
            # But for `parse_date` (conversion), we probably want the 'main' date.
            
            decoded = [r[1] for r in results]
            if return_raw:
                return sorted(results, key=lambda x: x[2])
            else:
                return sorted(list(set(decoded)))

        @staticmethod
        def resolve_relative(text: str, anchor: datetime) -> List[datetime]:
            """Improved relative time resolution for Day X, Week X, and Month X"""
            if not anchor: return []
            from datetime import timedelta as py_timedelta
            
            text = text.lower()
            res = []
            
            # 1. Day X (e.g., 'Day 28', '28th day')
            day_match = re.search(r"day\s*(\d+)|(\d+)(?:st|nd|rd|th)\s*day", text)
            if day_match:
                d_val = int(day_match.group(1) or day_match.group(2))
                res.append(anchor + py_timedelta(days=d_val - 1)) # Day 1 is anchor
                
            # 2. Week X (e.g., 'Week 2')
            week_match = re.search(r"week\s*(\d+)", text)
            if week_match:
                w_val = int(week_match.group(1))
                res.append(anchor + py_timedelta(weeks=w_val - 1))
            
            # 3. Native relative (X days before/after admission)
            offset_match = re.search(r"(\d+)\s*days?\s*(before|after)", text)
            if offset_match:
                val = int(offset_match.group(1))
                if "before" in offset_match.group(2):
                    res.append(anchor - py_timedelta(days=val))
                else:
                    res.append(anchor + py_timedelta(days=val))
                    
            return res

        @staticmethod
        def to_timestamp(d_obj) -> Optional[float]:
            try:
                if isinstance(d_obj, str):
                    d_obj = MedTimeEngine.Temporal.parse_date(d_obj)
                if d_obj:
                    return d_obj.timestamp()
            except:
                pass
            return None

        @staticmethod
        def parse_date(date_str: str) -> Optional[datetime]:
            """Parse various date formats into datetime object (ISO + NL Fallback)."""
            if not date_str or not isinstance(date_str, str):
                return None
            
            # 1. Try Strict ISO (Fast)
            for fmt in ("%Y-%m-%d", "%Y-%m", "%Y/%m/%d", "%Y.%m.%d"):
                try:
                    dt = datetime.strptime(date_str[:10], fmt)
                    # Year sanity check (1900-2100)
                    if 1900 < dt.year < 2100: return dt
                except:
                    continue
            
            # 2. Try Semantic Extraction (Robust English/Chinese)
            try:
                found = MedTimeEngine.Temporal.extract_all_dates(date_str)
                if found:
                    return found[0] # Return first valid date found
            except Exception:
                pass
                
            return None

        @staticmethod
        def parse_meta_date(meta: Dict) -> Optional[datetime]:
            """Extract base_date or similar from metadata."""
            if not meta:
                return None
            date_str = meta.get("base_date") or meta.get("date")
            return MedTimeEngine.Temporal.parse_date(date_str) if date_str else None

    class Data:
        @staticmethod
        def safe_json_extract(text: str) -> Any:
            """Ultimate JSON Parser: 剥离 Markdown, 修复未转义引号, 处理中文标点"""
            if not isinstance(text, str) or not text.strip():
                return {}

            # A. Strip Markdown
            clean_text = re.sub(r"```(?:json)?\s*([\s\S]*?)\s*```", r"\1", text).strip()

            # B. Match core JSON
            match = re.search(r"(\{[ \s\S]*\}|\[[\s\S]*\])", clean_text)
            if not match:
                return {}

            json_str = match.group(1)

            # C. Preliminary Repair
            json_str = (
                json_str.replace("，", ",")
                .replace("：", ":")
                .replace("“", "'")
                .replace("”", "'")
            )

            try:
                return json.loads(json_str)
            except Exception:
                # D. Deep Repair heuristic (Quotes and Delimiters)
                try:
                    # Replace Chinese quotes with single quotes for literal_eval support
                    repair_str = (
                        json_str.replace("“", "'")
                        .replace("”", "'")
                        .replace("‘", "'")
                        .replace("’", "'")
                    )
                    # Normalize newlines
                    repair_str = re.sub(r"\n", " ", repair_str)
                    # Try ast.literal_eval
                    import ast
                    return ast.literal_eval(repair_str)
                except Exception as e:
                    try:
                        # Final attempt: regex-based quote escaping
                        fixed_str = re.sub(
                            r'(?<=[:\s])"(.*?)"(?=[,\]\}])',
                            lambda m: '"' + m.group(1).replace('"', "'") + '"',
                            json_str,
                        )
                        return json.loads(fixed_str)
                    except Exception as e2:
                        logger.warning(f"JSON Deep Repair Failed: {e2}")
                        return {}

        @staticmethod
        def calculate_violation_rate(timeline: List[Any]) -> float:
            """Simple temporal sequence violation (pre-sort)"""
            if not isinstance(timeline, list) or len(timeline) < 2:
                return 0.0

            def get_ts(node):
                t = node.get("t") if isinstance(node, dict) else getattr(node, "t", None)
                return MedTimeEngine.Temporal.to_timestamp(t)

            v_count, pairs = 0, 0
            for i in range(len(timeline)):
                for j in range(i + 1, len(timeline)):
                    ts_i = get_ts(timeline[i])
                    ts_j = get_ts(timeline[j])
                    if ts_i and ts_j and ts_i > ts_j:
                        v_count += 1
                    pairs += 1
            return v_count / (pairs + 1e-6)

        @staticmethod
        def calculate_cmc(timeline: List[Any]) -> float:
            """
            Clinical Milestone Consistency (CMC):
            Validates medical logic constraints:
            1. Diagnosis <= Treatment
            2. Diagnosis <= Progression
            3. Admission <= Discharge
            """
            if not isinstance(timeline, list) or len(timeline) < 2:
                return 1.0 # No nodes to violate
            
            def get_cat(node):
                desc = str(node.get("e", "") + " " + node.get("trigger", "")).lower()
                for trigger_cfg in MedTimeEngine.EVENT_TRIGGERS:
                    if trigger_cfg["pattern"].search(desc):
                        return trigger_cfg["type"]
                return "Unknown"

            def get_ts(node):
                t = node.get("t")
                return MedTimeEngine.Temporal.to_timestamp(t)

            nodes = [n for n in timeline if get_ts(n)]
            if len(nodes) < 2: return 1.0

            violations = 0
            checks = 0
            
            for i in range(len(nodes)):
                for j in range(len(nodes)):
                    if i == j: continue
                    ni, nj = nodes[i], nodes[j]
                    ti, tj = get_ts(ni), get_ts(nj)
                    ci, cj = get_cat(ni), get_cat(nj)
                    
                    # Logic 1: Diagnosis must precede Treatment or Procedure (DX <= TX/PX)
                    if ci == "Diagnosis" and (cj == "Treatment" or cj == "Procedure"):
                        checks += 1
                        if ti > tj: violations += 1
                    
                    # Logic 2: Diagnosis must precede Progression (DX <= SX)
                    # Note: We use "Diagnosis" vs "Sputum/Pathology" etc. 
                    # If cj contains '转移' or '进展' (SX tokens not in default but we can check)
                    if ci == "Diagnosis" and "进展" in str(nj.get("e","")):
                        checks += 1
                        if ti > tj: violations += 1

                    # Logic 3: Admission <= Discharge
                    if "入院" in str(ni.get("e","")) and "出院" in str(nj.get("e","")):
                        checks += 1
                        if ti > tj: violations += 1
            
            return 1.0 - (violations / (checks + 1e-6)) if checks > 0 else 1.0

        @classmethod
        def auto_fix_timeline(cls, timeline: List[Dict]) -> List[Dict]:
            if isinstance(timeline, dict):
                timeline = [timeline]
            if not isinstance(timeline, list):
                return []
            fixed = []
            for node in timeline:
                if not isinstance(node, dict) or not node.get("e"):
                    continue
                new_node = dict(node)
                t = new_node.get("t")
                if isinstance(t, list) and len(t) >= 2:
                    ts0 = MedTimeEngine.Temporal.to_timestamp(t[0])
                    ts1 = MedTimeEngine.Temporal.to_timestamp(t[1])
                    if ts0 and ts1 and ts0 > ts1:
                        new_node["t"] = [t[1], t[0]]
                if "n" not in new_node or not new_node["n"]:
                    new_node["n"] = "I" if isinstance(new_node.get("t"), list) else "P"
                new_node["_ts"] = (
                    MedTimeEngine.Temporal.to_timestamp(new_node.get("t")) or 0
                )
                fixed.append(new_node)
            fixed.sort(key=lambda x: (x["_ts"], x.get("e", "")))
            for n in fixed:
                n.pop("_ts", None)
            return fixed

        @staticmethod
        def normalize_id(pid: Any) -> str:
            """Normalize ID for matching: remove prefix, spaces, lowercase"""
            s = str(pid).strip().lower()
            return s.split("_")[-1] if "_" in s else s

    class PostProcess:
        @staticmethod
        def safe_fix_timeline(
            raw_nodes: List[Dict], document_text: str, meta_info: Dict = None
        ) -> List[Dict]:
            """Ported from production: Lighthouse Year Recovery + Deep Cleaning"""
            if not isinstance(raw_nodes, list):
                return []

            # 1. Lighthouse Year detection
            # Priority: Voting (non-2024) > Anchor > Default(2022)
            raw_dts = MedTimeEngine.Temporal.extract_all_dates(document_text)
            doc_years = [d.year for d in raw_dts if 2010 <= d.year < 2024]
            anchor_dt = MedTimeEngine.Temporal.parse_meta_date(meta_info)

            if doc_years:
                lh_year = max(set(doc_years), key=doc_years.count)
            elif anchor_dt:
                lh_year = anchor_dt.year
            else:
                lh_year = 2022

            valid = []
            for node in raw_nodes:
                if not isinstance(node, dict):
                    continue
                # A. Clean Trigger
                node["trigger"] = re.sub(
                    r"[^\u4e00-\u9fa5a-zA-Z0-9]", "", str(node.get("trigger", ""))
                )
                # B. Year Recovery
                t_val = node.get("t")
                if t_val:
                    found_clean = MedTimeEngine.Temporal.extract_all_dates(str(t_val))
                    if found_clean:
                        best_dt = found_clean[0]
                        if best_dt.year >= 2024:
                            try:
                                best_dt = best_dt.replace(year=lh_year)
                            except:
                                pass
                        node["t"] = best_dt.date().isoformat()
                    else:
                        m = re.search(r"(20[12]\d)", str(t_val))
                        node["t"] = f"{m.group(1)}-01-01" if m else None

                if node.get("trigger") or node.get("e"):
                    valid.append(node)

            return MedTimeEngine.Data.auto_fix_timeline(valid)

    class Clinical:
        @staticmethod
        def get_semantic_sim(gold_e: str, pred_e: str) -> float:
            """Multi-dimensional semantic comparison"""
            if not gold_e or not pred_e:
                return 0.0
            from rapidfuzz import fuzz

            score = fuzz.partial_ratio(gold_e, pred_e) / 100.0
            # Trigger Pattern Reward
            for trigger in MedTimeEngine.EVENT_TRIGGERS:
                if trigger["pattern"].search(gold_e) and trigger["pattern"].search(
                    pred_e
                ):
                    score += 0.25
            return min(1.0, score)

    def __init__(self):
        pass

    def process_trajectory(self, raw_data: List[Dict]) -> List[Dict]:
        """Process a list of raw clinical events"""
        clean_events = []
        for item in raw_data:
            if self.Clinical.is_valid_event(item):
                item["description"] = self.Text.clean(item["description"])
                clean_events.append(item)
        return sorted(clean_events, key=lambda x: x.get("date", ""))

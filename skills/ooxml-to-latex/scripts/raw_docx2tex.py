#!/usr/bin/env python3
"""
raw_docx2tex.py - High-fidelity Word→LaTeX converter via direct OOXML parsing.
Fixes applied:
  1. Image embed namespace (generic regex instead of r:embed)
  2. Page margins from sectPr
  3. Exact line spacing from w:spacing
  4. First-line indent from w:ind
  5. Implicit table column spans (tcW-based)
  6. Multi-column signature area alignment
"""

import zipfile
import xml.etree.ElementTree as ET
import sys
import os
import re

WNS = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
RNS = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'

def ns(tag):
    return f'{{{WNS}}}{tag}'

def escape_latex(text):
    if not text: return ""
    chars = {
        '&': r'\&', '%': r'\%', '$': r'\$', '#': r'\#', '_': r'\_',
        '{': r'\{', '}': r'\}', '~': r'\textasciitilde{}',
        '^': r'\textasciicircum{}', '\\': r'\textbackslash{}'
    }
    result = "".join(chars.get(c, c) for c in text)
    # Wrap long digit sequences (>10 chars) with seqsplit for line breaking
    result = re.sub(r'(\d{10,})', r'\\seqsplit{\1}', result)
    return result

# ─── Font size mapping ───────────────────────────────────────────────

def get_font_size_pt(p_elem):
    """Get font size in pt from paragraph rPr. Word sz = half-points."""
    pPr = p_elem.find(ns('pPr'))
    if pPr is not None:
        rPr = pPr.find(ns('rPr'))
        if rPr is not None:
            sz = rPr.find(ns('sz'))
            if sz is not None:
                return int(sz.get(ns('val'))) / 2.0
    # Fallback: check first run
    for r in p_elem.findall(ns('r')):
        rPr = r.find(ns('rPr'))
        if rPr is not None:
            sz = rPr.find(ns('sz'))
            if sz is not None:
                return int(sz.get(ns('val'))) / 2.0
    return None

def get_line_spacing(p_elem):
    """Get line spacing from w:spacing. Returns (value_pt, rule)."""
    pPr = p_elem.find(ns('pPr'))
    if pPr is not None:
        sp = pPr.find(ns('spacing'))
        if sp is not None:
            line = sp.get(ns('line'))
            rule = sp.get(ns('lineRule'), 'auto')
            if line:
                return int(line) / 20.0, rule  # twips/20 = pt
    return None, None

def get_first_indent(p_elem):
    """Get first-line indent in pt."""
    pPr = p_elem.find(ns('pPr'))
    if pPr is not None:
        ind = pPr.find(ns('ind'))
        if ind is not None:
            fl = ind.get(ns('firstLine'))
            if fl:
                return int(fl) / 20.0  # twips to pt
            flc = ind.get(ns('firstLineChars'))
            if flc:
                return None  # handled by \parindent
    return None

def get_alignment(p_elem):
    pPr = p_elem.find(ns('pPr'))
    if pPr is not None:
        jc = pPr.find(ns('jc'))
        if jc is not None:
            return jc.get(ns('val'))
    return None

def has_page_break(p_elem):
    for br in p_elem.iter(ns('br')):
        if br.get(ns('type')) == 'page':
            return True
    return False

def get_image_rids(p_elem):
    """Find all embedded image rIds using generic regex (handles any namespace prefix)."""
    rids = []
    for dwg_tag in ['drawing', 'pict']:
        for dwg in p_elem.iter(ns(dwg_tag)):
            xml_str = ET.tostring(dwg, encoding='unicode')
            # Generic: match embed="rIdN" regardless of namespace prefix
            for rId in re.findall(r'embed="(rId\d+)"', xml_str):
                if rId not in rids:
                    rids.append(rId)
    # Also check for wp:inline / a:blip in other namespaces
    full_xml = ET.tostring(p_elem, encoding='unicode')
    for rId in re.findall(r'embed="(rId\d+)"', full_xml):
        if rId not in rids:
            rids.append(rId)
    return rids

# ─── Run/text parsing ────────────────────────────────────────────────

def parse_runs(p_elem):
    """Extract text from runs with bold/italic formatting."""
    runs = []
    for r_elem in p_elem.findall(ns('r')):
        rPr = r_elem.find(ns('rPr'))
        is_bold = rPr is not None and rPr.find(ns('b')) is not None
        is_italic = rPr is not None and rPr.find(ns('i')) is not None

        t_elem = r_elem.find(ns('t'))
        if t_elem is not None and t_elem.text:
            t = escape_latex(t_elem.text)
            if is_bold: t = f"\\textbf{{{t}}}"
            if is_italic: t = f"\\textit{{{t}}}"
            runs.append(t)
    return "".join(runs)

def pt_to_latex_size(pt, line_spacing_pt=None):
    """Map Word point size to LaTeX \\fontsize command with proper baselineskip."""
    if pt is None: return ""
    bl = line_spacing_pt if line_spacing_pt else pt * 1.2
    if pt >= 36:
        return f"\\fontsize{{{pt:.0f}pt}}{{{bl:.0f}pt}}\\selectfont "
    if pt >= 14:
        return f"\\fontsize{{{pt:.0f}pt}}{{{bl:.0f}pt}}\\selectfont "
    if pt >= 12:
        return f"\\fontsize{{{pt:.0f}pt}}{{{bl:.0f}pt}}\\selectfont "
    return ""

# ─── Paragraph conversion ───────────────────────────────────────────

def parse_paragraph(p_elem, image_map, default_font_pt=14):
    """Convert a paragraph element to LaTeX."""
    latex_parts = []

    # Page break
    if has_page_break(p_elem):
        latex_parts.append("\\newpage\n")

    # Images
    for rId in get_image_rids(p_elem):
        if rId in image_map:
            img_name = image_map[rId]
            latex_parts.append(
                f"\\begin{{center}}\\includegraphics[width=0.5\\textwidth]"
                f"{{media/{img_name}}}\\end{{center}}\n"
            )

    # Text
    text = parse_runs(p_elem)
    if not text.strip():
        if not latex_parts:
            return "\\vspace{0.5\\baselineskip}\n"
        return "".join(latex_parts)

    # Formatting
    font_sz = get_font_size_pt(p_elem) or default_font_pt
    line_sp, line_rule = get_line_spacing(p_elem)
    align = get_alignment(p_elem)
    size_cmd = pt_to_latex_size(font_sz, line_sp)

    # ── Handle explicit first-line indent from Word ──
    indent_cmd = ""
    pPr = p_elem.find(ns('pPr'))
    if pPr is not None:
        ind = pPr.find(ns('ind'))
        if ind is not None:
            flc = ind.get(ns('firstLineChars'))
            if flc:
                em_val = int(flc) / 100.0
                if em_val > 0:
                    indent_cmd = f"\\hspace*{{{em_val}em}}"

    # ── Helper: strip formatting for pattern detection ──
    raw = text.replace('\\textbf{', '').replace('\\textit{', '').replace('}', '').replace('\\&', '&')
    raw_stripped = raw.strip()

    # ── Detect multi-column signature patterns ──
    segs = re.split(r'\s{3,}', raw_stripped)
    segs = [s.strip() for s in segs if s.strip()]

    if len(segs) >= 3:
        if all(len(s) <= 20 for s in segs):
            fmt = re.split(r'(?<=[^\s])\s{3,}(?=[^\s])', text.strip())
            fmt = [s.strip() for s in fmt if s.strip()]
            if len(fmt) >= 3:
                cw = f"{14.0 / len(fmt):.1f}cm"
                boxes = "".join(f"\\makebox[{cw}][l]{{{s}}}" for s in fmt)
                latex_parts.append(f"\n\\noindent {{{size_cmd}{indent_cmd}{boxes}}}\n\n")
                return "".join(latex_parts)

    # ── Build paragraph ──
    if align == 'center':
        latex_parts.append(f"\\begin{{center}}{size_cmd}{text}\\end{{center}}\n")
    elif align == 'right':
        latex_parts.append(f"\\begin{{flushright}}{size_cmd}{text}\\end{{flushright}}\n")
    else:
        prefix = "\\noindent "
        if size_cmd:
            latex_parts.append(f"{prefix}{{{size_cmd}{indent_cmd}{text}}}\n\n")
        else:
            latex_parts.append(f"{prefix}{indent_cmd}{text}\n\n")

    return "".join(latex_parts)

# ─── Table conversion ────────────────────────────────────────────────

def parse_table(tbl_elem, image_map):
    """Convert a Word table to LaTeX tblr using 2D matrix for merged cells."""
    grid_el = tbl_elem.find(ns('tblGrid'))
    cols = []
    if grid_el is not None:
        for gc in grid_el.findall(ns('gridCol')):
            w = gc.get(ns('w'))
            cols.append(float(w) if w else 0.0)

    col_count = len(cols)
    if col_count == 0: return ""

    rows = tbl_elem.findall(ns('tr'))
    num_rows = len(rows)

    # ── Build 2D matrix ──
    matrix = [[{'text': "", 'rs': 1, 'cs': 1, 'covered_by': None}
               for _ in range(col_count)] for _ in range(num_rows)]

    for r_idx, tr in enumerate(rows):
        tc_elems = tr.findall(ns('tc'))
        c_grid = 0  # current position in grid
        tc_idx = 0

        while c_grid < col_count and tc_idx < len(tc_elems):
            # Skip covered cells
            while c_grid < col_count and matrix[r_idx][c_grid]['covered_by'] is not None:
                c_grid += 1
            if c_grid >= col_count: break

            tc = tc_elems[tc_idx]
            tc_idx += 1

            tcPr = tc.find(ns('tcPr'))
            gridSpan = 1
            vMerge = None
            if tcPr is not None:
                gs = tcPr.find(ns('gridSpan'))
                if gs is not None:
                    gridSpan = int(gs.get(ns('val')))
                # Word XML bug workaround: if row has only 1 cell, force it to span the rest of the row
                if len(tc_elems) == 1:
                    gridSpan = max(gridSpan, col_count - c_grid)
                vm = tcPr.find(ns('vMerge'))
                if vm is not None:
                    vMerge = vm.get(ns('val'), 'continue')

                # Fix 5: Implicit column span — if no gridSpan, infer from tcW
                if gs is None:
                    tcW = tcPr.find(ns('tcW'))
                    if tcW is not None:
                        cell_w = float(tcW.get(ns('w'), '0'))
                        if cell_w > 0:
                            # Count how many grid columns this width covers
                            accumulated = 0
                            span = 0
                            for ci in range(c_grid, col_count):
                                accumulated += cols[ci]
                                span += 1
                                # If accumulated width matches cell width (within tolerance)
                                if abs(accumulated - cell_w) < 50:  # 50 twip tolerance
                                    break
                                if accumulated > cell_w + 50:
                                    break
                            if span > 1:
                                gridSpan = span

            gridSpan = min(gridSpan, col_count - c_grid)

            # Cell content
            parts = []
            for p in tc.findall(ns('p')):
                for rId in get_image_rids(p):
                    if rId in image_map:
                        parts.append(f"\\includegraphics[width=0.9\\linewidth]{{media/{image_map[rId]}}}")
                p_runs = []
                for r_el in p.findall(ns('r')):
                    rPr = r_el.find(ns('rPr'))
                    is_bold = rPr is not None and rPr.find(ns('b')) is not None
                    t_el = r_el.find(ns('t'))
                    if t_el is not None and t_el.text:
                        t = escape_latex(t_el.text)
                        if is_bold: t = f"\\textbf{{{t}}}"
                        p_runs.append(t)
                run_text = "".join(p_runs).strip()
                if run_text: parts.append(run_text)
            cell_text = " ".join(parts)
            cell_text = re.sub(r'\s+', ' ', cell_text).strip()

            if vMerge == 'continue':
                for peek_r in range(r_idx - 1, -1, -1):
                    if matrix[peek_r][c_grid]['covered_by'] is None:
                        matrix[peek_r][c_grid]['rs'] += 1
                        for cs in range(gridSpan):
                            if c_grid + cs < col_count:
                                matrix[r_idx][c_grid + cs]['covered_by'] = (peek_r, c_grid)
                        break
            else:
                matrix[r_idx][c_grid]['text'] = cell_text
                matrix[r_idx][c_grid]['cs'] = gridSpan
                for cs in range(gridSpan):
                    if cs > 0 and c_grid + cs < col_count:
                        matrix[r_idx][c_grid + cs]['covered_by'] = (r_idx, c_grid)

            c_grid += gridSpan

    # ── Colspec: use X columns with proportional weights ──
    # This lets tabularray auto-fit the table to \textwidth
    total_w = sum(cols) or 1.0
    avail_cm = 14.0  # reference for parbox calculations
    col_widths = []
    spec_parts = []
    for w in cols:
        # Proportional weight, minimum 0.01 for phantom columns
        weight = max(0.01, w / total_w)
        w_cm = weight * avail_cm
        col_widths.append(w_cm)
        # Use X[weight,l] for auto-distributed columns
        spec_parts.append(f"X[{weight:.3f},l]")

    latex = "{\\small\n"  # Slightly smaller font for table
    latex += "\\begin{tblr}{\n"
    latex += f"  width = \\textwidth,\n"
    latex += "  colspec = {|" + "|".join(spec_parts) + "|},\n"
    latex += "  hlines, vlines,\n"
    latex += "  colsep = 3pt,\n"  # Reduce column separator padding
    latex += "  rowsep = 2pt,\n"  # Reduce row padding
    latex += "}\n"

    for r in range(num_rows):
        row_cells = []
        c = 0
        while c < col_count:
            cell = matrix[r][c]
            if cell['covered_by'] is not None:
                row_cells.append("")
                c += 1
            else:
                rs, cs, text = cell['rs'], cell['cs'], cell['text']
                # Parbox for wide spans with long text
                if cs > col_count // 2 and len(text) > 50:
                    # Use a fraction of textwidth for the parbox
                    frac = min(0.92, sum(col_widths[c:c+cs]) / avail_cm) if c+cs <= len(col_widths) else 0.9
                    text = f"\\parbox{{{frac:.2f}\\textwidth}}{{\\vspace{{6pt}}\\linespread{{1.5}}\\selectfont\\justifying {text}\\vspace{{6pt}}}}"
                opts = []
                if rs > 1: opts.append(f"r={rs}")
                if cs > 1: opts.append(f"c={cs}")
                if opts:
                    row_cells.append(f"\\SetCell[{','.join(opts)}]{{l,m}} {text}")
                else:
                    row_cells.append(text)
                row_cells.extend([""] * (cs - 1))
                c += cs

        while len(row_cells) < col_count:
            row_cells.append("")
        latex += "  " + " & ".join(row_cells[:col_count]) + " \\\\\n"

    latex += "\\end{tblr}\n}\n"  # Close \small scope
    return latex

# ─── Main ────────────────────────────────────────────────────────────

def main(docx_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    media_dir = os.path.join(output_dir, 'media')
    os.makedirs(media_dir, exist_ok=True)

    image_map = {}

    with zipfile.ZipFile(docx_path, 'r') as doc:
        # Extract media files
        for info in doc.infolist():
            if info.filename.startswith('word/media/') and not info.is_dir():
                basename = os.path.basename(info.filename)
                if basename:
                    with open(os.path.join(media_dir, basename), 'wb') as f:
                        f.write(doc.read(info.filename))

        # Parse relationships for image rIds
        try:
            rels_xml = doc.read('word/_rels/document.xml.rels')
            for rel in ET.fromstring(rels_xml):
                target = rel.get('Target', '')
                if 'media/' in target:
                    image_map[rel.get('Id')] = os.path.basename(target)
        except KeyError:
            pass

        doc_xml = doc.read('word/document.xml')

    root = ET.fromstring(doc_xml)
    body = root.find(ns('body'))

    # ── Fix 2: Extract page margins from sectPr ──
    top_m, bot_m, left_m, right_m = 2.54, 2.54, 3.17, 3.17
    sectPr = body.find(ns('sectPr'))
    if sectPr is not None:
        pgMar = sectPr.find(ns('pgMar'))
        if pgMar is not None:
            for attr, default, target in [
                ('top', 1440, 'top_m'), ('bottom', 1440, 'bot_m'),
                ('left', 1800, 'left_m'), ('right', 1800, 'right_m')
            ]:
                val = pgMar.get(ns(attr))
                if val:
                    locals()[target]  # just for clarity
                    if attr == 'top': top_m = int(val) / 567.0
                    elif attr == 'bottom': bot_m = int(val) / 567.0
                    elif attr == 'left': left_m = int(val) / 567.0
                    elif attr == 'right': right_m = int(val) / 567.0

    # ── Generate main.tex ──
    main_tex = f"""\\documentclass[a4paper,zihao=-4]{{ctexart}}
\\usepackage{{graphicx}}
\\usepackage{{geometry}}
\\geometry{{top={top_m:.2f}cm, bottom={bot_m:.2f}cm, left={left_m:.2f}cm, right={right_m:.2f}cm}}
\\usepackage{{setspace}}
\\usepackage{{tabularray}}
\\usepackage{{ragged2e}}
\\usepackage{{indentfirst}}
\\usepackage{{seqsplit}}
\\setlength{{\\parindent}}{{0pt}}

\\begin{{document}}
\\input{{content.tex}}
\\end{{document}}
"""
    with open(os.path.join(output_dir, 'main.tex'), 'w', encoding='utf-8') as f:
        f.write(main_tex)

    # ── Generate content.tex ──
    out = []
    for elem in body:
        tag = elem.tag.split('}')[1] if '}' in elem.tag else elem.tag
        if tag == 'p':
            out.append(parse_paragraph(elem, image_map))
        elif tag == 'tbl':
            out.append(parse_table(elem, image_map))

    with open(os.path.join(output_dir, 'content.tex'), 'w', encoding='utf-8') as f:
        f.write("".join(out))

    print(f"Generated: {output_dir}/main.tex + content.tex")
    print(f"Margins: T={top_m:.2f} B={bot_m:.2f} L={left_m:.2f} R={right_m:.2f} cm")
    print(f"Images found: {image_map}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} input.docx output_dir")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])

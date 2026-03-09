import os
import shutil
import sys
# Add src to path
sys.path.append(os.path.abspath("src"))

from agents.latex_architect import LatexArchitect
from agents.latex_writer import LatexWriter

def test_latex_pipeline():
    print("=== Testing LaTeX Pipeline ===")
    
    test_dir = "tests/test_paper_build"
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
    
    # 1. Test Architect (Scaffolding)
    print("\n[Test 1: Architect Scaffolding]")
    architect = LatexArchitect()
    paths = architect.scaffold_paper("idea_001", "Test Paper Title", test_dir)
    
    assert os.path.exists(paths["main"])
    assert os.path.exists(paths["macros"])
    assert os.path.exists(os.path.join(test_dir, "sections", "00_abstract.tex"))
    print("✓ Paper structure created successfully")
    
    # Verify macros init
    with open(paths["macros"], "r") as f:
        content = f.read()
    assert r"\newcommand{\AccuracyResult}{PENDING}" in content
    print("✓ Macros initialized with PENDING")

    # 2. Test Writer (Data Filling)
    print("\n[Test 2: Writer Data Filling]")
    writer = LatexWriter()
    
    new_results = {
        "AccuracyResult": "99.9\%",
        "SpeedupResult": "10x"
    }
    
    writer.update_result_macros(paths["macros"], new_results)
    
    with open(paths["macros"], "r") as f:
        updated_content = f.read()
    
    assert r"\newcommand{\AccuracyResult}{99.9\%}" in updated_content
    assert r"\newcommand{\SpeedupResult}{10x}" in updated_content
    assert "PENDING" not in updated_content
    print("✓ Macros updated with experimental results")
    
    # 3. Test Compilation (Mock)
    print("\n[Test 3: Compilation (Mock)]")
    pdf_path = writer.compile_pdf(test_dir)
    assert os.path.exists(pdf_path)
    print("✓ PDF compilation mocked successfully")
    
    # Cleanup
    # shutil.rmtree(test_dir) 

if __name__ == "__main__":
    test_latex_pipeline()

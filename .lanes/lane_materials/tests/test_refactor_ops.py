
import unittest
import os
import shutil
from utils.file_ops import write_text, read_text
from skills import reflection_ops, task_ops
from schemas.experiment import ExperimentConfig, validationLevel

class TestRefactoredOps(unittest.TestCase):
    
    def setUp(self):
        self.test_dir = "tests/temp_data"
        os.makedirs(self.test_dir, exist_ok=True)
        # Mock global paths by updating arguments or monkeypatching if needed
        # But our Ops take paths as arguments, making them easy to test!
        
    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_file_ops_basic(self):
        """Test basic IO utils"""
        p = os.path.join(self.test_dir, "hello.txt")
        write_text(p, "Hello World")
        content = read_text(p)
        self.assertEqual(content, "Hello World")

    def test_reflection_ops(self):
        """Test Memory Logic independent of Core"""
        p = os.path.join(self.test_dir, "experience.md")
        reflection_ops.append_insight("Insight 1", path=p) 
        reflection_ops.append_insight("Insight 2", path=p)
        
        hist = reflection_ops.read_history(path=p)
        self.assertIn("Insight 1", hist)
        self.assertIn("Insight 2", hist)
        print("✅ Reflection Ops Verified")

    def test_experiment_schema(self):
        """Test Pydantic Schema Validation & Save/Load"""
        conf = ExperimentConfig(
            idea_id="idea_1",
            task_id="task_1",
            cmd="python run.py",
            env_name="local",
            output_dir="./out",
            validation_level=validationLevel.T2_PROXY
        )
        # Test Persistable Mixin
        json_path = os.path.join(self.test_dir, "config.json")
        conf.save(json_path)
        
        loaded = ExperimentConfig.load(json_path)
        self.assertEqual(loaded.validation_level, validationLevel.T2_PROXY)
        print("✅ Schema Ops Verified")

if __name__ == '__main__':
    unittest.main()

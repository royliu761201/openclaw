# Research Experience Cookbook (Self-Evolving Knowledge Base)

This file records successful strategies ("Recipes") and failed paths ("Negative Constraints").
The Autonomous Scientist reads this file before every task to avoid repeating mistakes and to reuse working code.

## 1. Successful Recipes (Cookbook)
*Format: [Problem] -> [Context] -> [Solution]*

- **Example**: [Plotting] -> [3D Scatter Plot] -> `from mpl_toolkits.mplot3d import Axes3D` is required even if unused directly.

## 2. Negative Constraints (Anti-Patterns)
*Format: [Task] -> [Avoid] -> [Reason]*

- **Example**: [Dependency] -> [pip install torch] -> Do not reinstall torch in the pre-configured environment; check `pip list` first.

## 3. Reflection Log (Daily Summary)
*(Appended automatically by Reflection Node)*


### Update (Success)
```python
print('Test')
```

### Update (Failure)\n```python
print('Test')
```

### Update (Failure)\n```python
print('Test')
```

### Update (Failure)\n```python
print('Test')
```

### Update (Failure)\n```python
print('Test')
```

### Update (Failure)\n```python
print('Test')
```

### Update (Failure)\n```python
print('Test')
```

### Update (Failure)\n```python
print('Test')
```

### Update (Failure)\n```python
print('Test')
```

### Update (Failure)\n```python
print('Test')
```

### Update (Failure)\n```python
print('Test')
```

### Update (Failure)\n```python
print('Test')
```

### Update (Failure)\n```python
print('Test')
```

### Update (Failure)\n[Constraint] -> Internal Git index corruption or malformed path entries (e.g., `./` prefixes) can trigger fatal bugs in Git's `unpack-trees.c` logic, causing automated version control operations like `git stash` to crash with a SIGABRT (Exit Code -6); autonomous systems must verify repository integrity or perform a clean index reset if such low-level internal errors occur.

### Update (Failure)\n[Type] -> [Constraint]

[Insight] -> Avoid performing automated Git operations (like `git stash`) if the repository index contains entries with explicit relative path prefixes (e.g., `./.gitignore`). This triggers a known internal Git assertion failure (`BUG: unpack-trees.c`) where the index position tracking fails, leading to a fatal crash (Exit Code -6). Ensure the environment uses a stable Git version and that the index is normalized/cleaned before programmatically switching branches.

### Update (Failure)\n[Constraint] -> Ensure experiment management objects (e.g., loggers or trainers) are properly instantiated before invoking lifecycle methods like `init_run`; this error typically arises from failing to handle cases where these objects remain `None` due to missing environment configurations or conditional initialization flags.

### Update (Failure)\n[Constraint] -> Ensure experiment management objects (e.g., `wandb` or custom `Runner` classes) are explicitly instantiated and verified against `None` before invoking lifecycle methods like `init_run`, particularly when running in environments where API keys or configurations might be missing.

### Update (Failure)\n[Constraint] -> **Strict Null-Check for Execution Managers**: Avoid calling lifecycle methods (e.g., `init_run`) on conditionally instantiated experiment trackers or runner objects without explicit validation or the use of a "Null Object" pattern; failure to initialize the core execution controller leads to immediate runtime crashes.

### Update (Failure)\n[Constraint] -> **Null-Safety in Component Lifecycle**: Avoid calling lifecycle or initialization methods (e.g., `init_run`) on optional objects (like loggers or experiment trackers) without explicit null-checks or "No-Op" fallbacks, particularly when component instantiation is conditional on configuration flags.

### Update (Failure)\n[Constraint] -> **Defensive Initialization of Experiment Trackers**: Ensure that any object returned by a setup or factory function (such as a logger or experiment manager) is explicitly checked for `None` before calling lifecycle methods like `init_run`. Always provide a functional "Null Object" or mock fallback when environment-specific tracking (e.g., WandB, MLFlow) is disabled or fails to instantiate.

### Update (Failure)\n[Constraint] -> **Uninitialized Lifecycle Hooks**: Avoid calling lifecycle methods (e.g., `init_run`) on tracker or logger objects without first verifying successful instantiation. This error typically occurs when an experiment tracking module (like WandB or a custom wrapper) is disabled or fails to initialize, returning `None`, yet the subsequent execution logic assumes the object exists. Always implement a null-check or a dummy-object pattern for optional logging components.

### Update (Failure)\n[Type] -> Constraint

[Insight] -> **Attribute Access on Uninitialized Experiment Trackers**: The error `'NoneType' object has no attribute 'init_run'` indicates a failure to verify the instantiation of a logger or experiment runner (likely a `wandb` or custom wrapper) before use. **Constraint**: Always implement explicit null-checks or use a "Null Object" pattern when handling experiment initializers, especially when initialization is conditional on environment variables or configuration flags. Ensure the object returned by the setup function is validated before calling lifecycle methods like `init_run`.

### Update (Failure)\n[Type] -> Constraint

[Insight] -> **Object Initialization Guard**: Always verify that factory methods or setup functions (e.g., for loggers or experiment trackers) have successfully returned a valid instance before calling lifecycle methods like `init_run`. A `NoneType` error here indicates a silent failure in the configuration or environment setup phase that must be caught via explicit validation or robust error handling.

### Update (Failure)\n[Constraint] -> Ensure all experiment tracking or runner objects are explicitly initialized or implemented with a "Null Object" pattern before calling lifecycle methods (e.g., `init_run`); avoid assuming that configuration flags or optional modules have correctly populated the handler object.

### Update (Failure)\n[Constraint] -> Avoid calling lifecycle methods (e.g., `init_run`) on experiment managers or loggers without prior verification of successful instantiation; ensure factory functions or setup utilities return a valid object (or a functional mock) rather than `None` when configuration fails.

### Update (Failure)\n[Constraint] -> **Defensive Initialization**: Ensure that experiment management objects (e.g., loggers or trackers) are explicitly instantiated and verified before calling lifecycle methods like `init_run`; avoid returning `None` for optional components without implementing a "Null Object" pattern to prevent attribute errors.

### Update (Failure)\n[Constraint] -> Ensure that experimental components (such as loggers, trainers, or environment wrappers) are explicitly instantiated and verified before calling initialization methods; specifically, avoid assuming that optional tracking modules are non-null in execution loops.

### Update (Failure)\n[Constraint] -> Ensure experiment management objects (e.g., loggers or runners) are explicitly instantiated before calling setup methods like `init_run`; avoid calling methods on variables that may remain `None` due to conditional initialization or environment configuration failures.
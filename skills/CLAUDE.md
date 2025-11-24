# Skills Cookbook - Claude Code Guide

## Project Overview

This is a comprehensive Jupyter notebook cookbook demonstrating Claude's Skills feature for document generation (Excel, PowerPoint, PDF). It's designed for developers learning to integrate Skills into their applications.

## Quick Start Commands

### Environment Setup
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies (MUST use local whl for Skills support)
pip install -r requirements.txt

# Configure API key
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

### Running Notebooks
```bash
# Launch Jupyter
jupyter notebook

# Or use VSCode with Jupyter extension
# Make sure to select the venv kernel in VSCode: Cmd+Shift+P → "Python: Select Interpreter"
```

### Testing & Verification
```bash
# Verify environment and SDK version
python -c "import anthropic; print(f'SDK Version: {anthropic.__version__}')"

# Check outputs directory for generated files
ls -lh outputs/
```

## Architecture Overview

### Directory Structure
```
skills/
├── notebooks/              # 3 progressive Jupyter notebooks
│   ├── 01_skills_introduction.ipynb
│   ├── 02_skills_financial_applications.ipynb  # WIP
│   └── 03_skills_custom_development.ipynb      # WIP
├── sample_data/           # Financial datasets for examples
├── custom_skills/         # Custom skill development area
├── outputs/               # Generated files (xlsx, pptx, pdf)
├── file_utils.py          # Files API helper functions
└── docs/                  # Implementation tracking
```

### Key Technical Details

**Beta API Requirements:**
- All Skills functionality uses `client.beta.*` namespace
- Required beta headers: `code-execution-2025-08-25`, `files-api-2025-04-14`, `skills-2025-10-02`
- Must use `client.beta.messages.create()` with `container` parameter
- Code execution tool (`code_execution_20250825`) is REQUIRED
- Use pre-built Agent skills by referencing their `skill_id` or create and upload your own via the Skills API

**Files API Integration:**
- Skills generate files and return `file_id` attributes
- Must use `client.beta.files.download()` to download files
- Must use `client.beta.files.retrieve_metadata()` to get file info
- Helper functions in `file_utils.py` handle extraction and download

**Built-in Skills:**
- `xlsx` - Excel workbooks with formulas and charts
- `pptx` - PowerPoint presentations
- `pdf` - PDF documents
- `docx` - Word documents

## Development Gotchas

### 1. SDK Version
**Important**: Ensure you have the Anthropic SDK version 0.71.0 or later with Skills support
```bash
pip install anthropic>=0.71.0
# Restart Jupyter kernel after installation if upgrading!
```

### 2. Beta Namespace Required
**Problem**: `container` parameter not recognized, files API fails
**Solution**: Use `client.beta.messages.create()` and `client.beta.files.*`
```python
# ❌ Wrong
response = client.messages.create(container={...})
content = client.files.content(file_id)

# ✅ Correct
response = client.beta.messages.create(container={...})
content = client.beta.files.content(file_id)
```

### 3. Beta Headers Placement
**Problem**: Setting Skills beta in default_headers requires code_execution on ALL requests
**Solution**: Use `betas` parameter per-request instead
```python
# ❌ Wrong (affects all requests)
client = Anthropic(default_headers={"anthropic-beta": "skills-2025-10-02"})

# ✅ Correct (per-request)
response = client.beta.messages.create(
    betas=["code-execution-2025-08-25", "files-api-2025-04-14", "skills-2025-10-02"],
    ...
)
```

### 4. File ID Extraction
**Problem**: Response structure differs from standard Messages API
**Solution**: File IDs in `bash_code_execution_tool_result.content.content[0].file_id`
```python
# Use file_utils.extract_file_ids() - handles beta response structure
from file_utils import extract_file_ids, download_all_files
file_ids = extract_file_ids(response)
```

### 5. Files API Response Objects
**Problem**: `'BinaryAPIResponse' object has no attribute 'content'`, `'FileMetadata' object has no attribute 'size'`
**Solution**: Use `.read()` for file content and `.size_bytes` for file size
```python
# ❌ Wrong
file_content = client.beta.files.download(file_id)
with open(path, 'wb') as f:
    f.write(file_content.content)  # No .content attribute!

# ✅ Correct
file_content = client.beta.files.download(file_id)
with open(path, 'wb') as f:
    f.write(file_content.read())  # Use .read()

# FileMetadata fields: id, filename, size_bytes (not size), mime_type, created_at, type, downloadable
metadata = client.beta.files.retrieve_metadata(file_id)
print(f"Size: {metadata.size_bytes} bytes")  # Use size_bytes, not size
```

### 6. Jupyter Kernel Selection
**Problem**: Wrong Python interpreter = wrong dependencies
**Solution**: Always select venv kernel in VSCode/Jupyter
- VSCode: Cmd+Shift+P → "Python: Select Interpreter" → select venv
- Jupyter: Kernel → Change Kernel → select venv

### 7. Module Reload Required
**Problem**: Changes to `file_utils.py` not reflected in running notebooks
**Solution**: Restart kernel or reload module
```python
import importlib
importlib.reload(file_utils)
```

### 8. Document Generation Times
**Problem**: File creation takes longer than typical API calls, users may think cell is frozen
**Actual Observed Times:**
- Excel: ~2 minutes
- PowerPoint: ~1-2 minutes (simple 2-3 slide presentations)
- PDF: ~1-2 minutes

**Solution**: Add clear timing expectations before file creation cells
```markdown
**⏱️ Note**: Excel generation typically takes 1-2 minutes.
Be patient - the cell will show [*] while running!
```
**Important**: Keep examples simple and focused. Generation times are consistent at 1-2 minutes for well-scoped examples.

## Common Tasks

### Adding a New Notebook Section
1. Follow existing structure in `01_skills_introduction.ipynb`
2. Include setup cell with imports and beta headers
3. Show API call, response handling, file download
4. Add error handling examples
5. Update `docs/skills_cookbook_plan.md` checklist

### Creating Sample Data
1. Add realistic financial data to `sample_data/`
2. Use CSV for tabular, JSON for structured
3. Include headers and proper formatting
4. Reference in notebook with pandas
5. Keep file sizes reasonable (<100KB)

### Testing File Download
1. Run notebook cell to generate file
2. Check response for file_id
3. Use `download_all_files()` helper
4. Verify file in `outputs/` directory
5. Open file in native app to validate

**Note**: Files are overwritten by default. You'll see `[overwritten]` in the download summary when a file already existed. Set `overwrite=False` to prevent this.

### Debugging API Errors
1. Check SDK version: `anthropic.__version__` should be `0.69.0`
2. Verify beta headers are passed per-request
3. Ensure code_execution tool is included
4. Check response structure with `print(response)`
5. Look for error details in `response.stop_reason`

## Testing Checklist

Before committing notebook changes:
- [ ] Restart kernel and run all cells
- [ ] Verify all file downloads work
- [ ] Check outputs/ for generated files
- [ ] Validate files open correctly in native apps
- [ ] Update skills_cookbook_plan.md checklist
- [ ] Test in fresh virtual environment

## Resources

- **API Reference**: https://docs.claude.com/en/api/messages
- **Files API**: https://docs.claude.com/en/api/files-content
- **Skills Documentation**: https://docs.claude.com/en/docs/agents-and-tools/agent-skills/overview

## Project-Specific Notes

- **Focus Domain**: Finance & Analytics with practical business applications
- **Target Audience**: Intermediate developers and business analysts
- **Notebook 1**: Complete and tested (file downloads working)
- **Notebook 2**: Financial Applications - next priority
- **Notebook 3**: Custom Skills Development - after Notebook 2

## Environment Variables

Required in `.env`:
```bash
ANTHROPIC_API_KEY=your-api-key-here
```

Optional (for advanced examples):
```bash
ANTHROPIC_BASE_URL=https://api.anthropic.com  # If using proxy
```

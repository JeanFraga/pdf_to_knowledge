# Integration Test Fixtures

This folder contains sample PDF files for integration testing.

## ⚠️ Important: Do Not Commit PDFs

PDF files in this folder are **gitignored** because they may be:
- Copyright protected
- Too large for version control
- User-provided test materials

## Usage

1. Place your test PDF file(s) in this folder
2. Run integration tests:
   ```bash
   cd agents/ingestion-agent
   pytest tests/integration/ -v
   ```

## Expected Files

| Filename | Purpose |
|----------|---------|
| `sample.pdf` | General integration test PDF |

## Providing Test PDFs

Ask a team member for sample PDFs or use your own documents for testing.
The integration tests will skip gracefully if no PDF files are present.

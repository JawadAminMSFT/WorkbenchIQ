# Batch APS Document Processing Script

Automates processing of APS (Attending Physician Statement) documents through the WorkbenchIQ API using large document processing mode.

## Features

- **Sequential Processing** - One document at a time to avoid overwhelming Azure OpenAI
- **Idempotent** - Resumes from where it stopped if interrupted
- **Human Review Output** - Consolidated CSV with extracted fields, LLM outputs, and risk analysis
- **Cleanup Support** - Easy cleanup of created applications if something goes wrong

## Prerequisites

1. Backend API server running at `http://localhost:8000`
2. APS PDF documents in the `underwriting-aps-docs/` folder
3. [uv](https://docs.astral.sh/uv/) installed (handles Python and dependencies automatically)

## Usage

### Dry Run (Preview)

See what would be processed without making changes:

```bash
uv run scripts/batch_process_aps.py --dry-run
```

### Run Processing

Process all documents:

```bash
uv run scripts/batch_process_aps.py
```

### Cleanup (If Something Breaks)

Delete all applications created by the script and clear local output files:

```bash
uv run scripts/batch_process_aps.py --cleanup
```

### Reset Progress Only

Clear the progress tracker but keep applications (useful for re-exporting CSVs):

```bash
uv run scripts/batch_process_aps.py --reset
```

## Command Line Options

| Option | Default | Description |
|--------|---------|-------------|
| `--api-url` | `http://localhost:8000` | Backend API URL |
| `--source-folder` | `underwriting-aps-docs` | Folder containing APS PDFs |
| `--output-folder` | `batch-review-output` | Output folder for review CSVs |
| `--poll-interval` | `10` | Seconds between status polls |
| `--timeout` | `1800` | Max seconds to wait per document (30 min) |
| `--dry-run` | - | List documents without processing |
| `--reset` | - | Clear progress tracker only |
| `--cleanup` | - | Delete all created applications and outputs |

## Output Structure

```
batch-review-output/
├── progress_tracker.csv      # Tracks processing state (deleted when all complete)
├── 008BMOAPS119/
│   └── review_output.csv     # Consolidated review file
├── 025BMOAPS169/
│   └── review_output.csv
└── ...
```

## Review CSV Format

Each `review_output.csv` contains all outputs in one file:

| Column | Description |
|--------|-------------|
| `category` | `extracted_field`, `llm_output`, or `risk_analysis` |
| `section` | Section name (e.g., `medical_summary`) |
| `subsection` | Field or subsection name |
| `value` | Extracted value or LLM summary |
| `confidence` | CU confidence score (for extracted fields) |
| `source_page` | Page number |
| `source_file` | Source document |
| `risk_level` | Risk assessment level |
| `underwriting_action` | Recommended action |
| `policy_citations` | Referenced policy IDs |
| `accuracy_rating` | **[TO FILL]** 1-5 rating by reviewer |
| `issues_found` | **[TO FILL]** Any errors found |
| `corrections` | **[TO FILL]** Suggested corrections |
| `reviewer_notes` | **[TO FILL]** Additional notes |

## Processing Pipeline

For each document, the script:

1. **Upload** - Creates application via `POST /api/applications`
2. **Process** - Starts large document processing via `POST /api/applications/{id}/process`
3. **Poll** - Waits for extraction and analysis to complete
4. **Risk Analysis** - Runs policy-based risk analysis via `POST /api/applications/{id}/risk-analysis`
5. **Export** - Generates consolidated review CSV
6. **Track** - Updates progress tracker

## Error Handling

- If a document fails, the script logs the error and continues to the next document
- On restart, completed documents are skipped automatically
- Use `--cleanup` to remove everything and start fresh

## Idempotency States

| Status | Description |
|--------|-------------|
| `pending` | Not started |
| `uploaded` | Application created, processing not started |
| `processing` | Extraction and analysis running |
| `running_risk` | Risk analysis running |
| `completed` | All done, CSV exported |
| `error` | Failed at some step |

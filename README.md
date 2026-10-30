# Guarded Coding Assistant

I built this project to try out NVIDIA NeMo Guardrails with a coding assistant. It uses Groq for model responses and adds a small Python check for secrets that might appear in them.

## What it checks

- **Before generation:** NeMo reviews the user's message for requests involving malware, credential theft, exploits, or attempts to bypass the assistant's instructions.
- **After generation:** NeMo reviews the response, and a Python action looks for common API key formats, password and secret fields, and long, high-entropy strings.

These checks are a useful extra layer, not a guarantee that every unsafe request or secret will be caught.

## Run it locally

You'll need Python and a Groq API key. From the project folder, create and activate a virtual environment, then install the dependencies:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Create a `.env` file in the project folder with your key:

```env
GROQ_API_KEY=your_groq_api_key
```

Keep the key private. The `.env` file is ignored by Git.

Start the command-line assistant:

```powershell
python guarded_assistant.py
```

Type `exit` or `quit` to end the session.

## Tests and benchmark

Run the local secrets-detector checks with:

```powershell
python test_secrets_detector.py
```

The benchmark sends the prompts in `tests/adversarial_prompts.json` to the model and saves its results to `tests/results.json`. It makes API calls and pauses between prompts, so it takes time and may use your Groq quota:

```powershell
python run_benchmark.py
```

The checked-in results are from one run of ten prompts. They are a small sample, not a guarantee of how the assistant will behave on other inputs.

`basic_assistant.py` is an unguarded version kept as a baseline for comparison.

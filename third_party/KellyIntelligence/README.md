# Kelly Intelligence <> Claude Cookbooks

[Kelly Intelligence](https://api.thedailylesson.com) exposes a public, no-auth vocabulary API backed by a 162,253-word database with translations across 47 languages, IPA pronunciations, etymologies, mnemonics, and a related-word graph. It is built and maintained by [Lesson of the Day, PBC](https://lotdpbc.com), a public benefit corporation building learning infrastructure.

This cookbook shows how to give Claude a vocabulary lookup tool and turn it into a personalized vocabulary tutor — no Kelly account or API key required. Only an Anthropic API key is needed to run the notebook.

## What's Included

* **[Vocabulary Tutor with Claude Notebook](./vocabulary_tutor_with_claude.ipynb)** — An interactive walkthrough that gives Claude a `lookup_word` tool backed by Kelly's `/v1/word/{word}` endpoint, then uses Claude tool use to build a tutor that explains a word, gives translations, and tests the learner with a follow-up question.

## How to Use This Cookbook

### Step 1: Set Up Your Environment

1. **Create a virtual environment:**
   ```bash
   cd third_party/KellyIntelligence
   python -m venv venv
   source venv/bin/activate    # macOS/Linux
   # OR
   venv\Scripts\activate       # Windows
   ```

2. **Get your Anthropic API key:**
   - [console.anthropic.com/settings/keys](https://console.anthropic.com/settings/keys)

   Kelly Intelligence's `/v1/word/{word}` endpoint is public and rate-limited per IP (60 requests/hour), so no Kelly account is required to run this notebook.

3. **Configure your environment:**
   ```bash
   cp .env.example .env
   ```

   Edit `.env` and add your Anthropic key:
   ```
   ANTHROPIC_API_KEY=sk-ant-api03-...
   ```

4. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

### Step 2: Work Through the Notebook

Open **[vocabulary_tutor_with_claude.ipynb](./vocabulary_tutor_with_claude.ipynb)** in Jupyter or VS Code. The notebook walks through:

- Calling Kelly's `/v1/word/{word}` endpoint directly with `requests`
- Defining a `lookup_word` tool for Claude with a clean input schema
- Using Claude's tool-use loop to answer learner questions about vocabulary
- Building a full mini-tutor that defines a word, gives translations, and quizzes the learner

The notebook uses `claude-haiku-4-5` for the live demo because vocabulary tutoring is a fast-feedback loop; you can swap in `claude-sonnet-4-6` or `claude-opus-4-6` for richer explanations.

## About the Kelly `/v1/word` Endpoint

The endpoint is a single GET request that returns a JSON document for any word in the Kelly vocabulary database:

```bash
curl "https://api.thedailylesson.com/v1/word/ephemeral?translations=ES,FR,DE,JA"
```

Response shape:

```json
{
  "word": "ephemeral",
  "part_of_speech": "adjective",
  "ipa": "/ɪˈfɛmərəl/",
  "definition": "Lasting for a very short time; transitory or fleeting...",
  "etymology": "From Greek 'ephemeros', meaning 'lasting only a day'...",
  "mnemonic": "Think of a mayfly that lives for just one day...",
  "translations": {
    "es": { "word": "efímero",  "pronunciation": "eˈfimɛɾo" },
    "fr": { "word": "éphémère", "pronunciation": "/e.fe.mɛʁ/" },
    "de": { "word": "flüchtig", "pronunciation": "/ˈflyːçtɪç/" },
    "ja": { "word": "エフェメラル", "pronunciation": "efemeralu" }
  },
  "related": [
    { "word": "transient" },
    { "word": "fleeting" },
    { "word": "permanent" }
  ],
  "lookups": 6,
  "source": {
    "provider": "Kelly Intelligence",
    "database": "Orb Platform",
    "total_words": 162253,
    "total_languages": 47
  }
}
```

**Query parameters:**

| Param          | Description                                                | Default        |
| -------------- | ---------------------------------------------------------- | -------------- |
| `translations` | Comma-separated ISO language codes, max 10                 | `ES,FR,DE`     |

**Supported language codes:** ES, FR, DE, IT, PT, JA, ZH, KO, AR, RU, HI, TR, PL, NL, SV, VI, ID, TH, HE, EL, CS, DA, FI, NO, RO, HU, UK, TA, BN, MS, TL, FA, UR, MY, KM, SW, AM, YO, ZU, TE, MR, PA, CA, HA, IG, GU, KK.

**Rate limit:** 60 requests/hour per IP. Responses are cached at the edge for 1 hour.

## Troubleshooting

### `ANTHROPIC_API_KEY` not found

Make sure you have copied `.env.example` to `.env` and added your real key, and that you call `dotenv.load_dotenv()` at the top of the notebook (the first code cell already does this).

### `Word "..." not found in vocabulary database`

The Kelly database contains 162,253 English headwords. Some inflected forms or very rare words may not be present — try the base form (e.g. `running` → `run`).

### Rate limit exceeded

The endpoint is limited to 60 requests/hour per IP. Wait for the next hour or run the notebook from a different network.

## Project Ideas

Once you understand the pattern, here are some projects you can build:

- **Language-learning flashcards** — Give Claude a list of words a learner is studying and have it generate spaced-repetition flashcards with example sentences in the target language.
- **Reading-level analyzer** — Pass Claude a paragraph; have it identify rare or advanced vocabulary, look each word up via the tool, and produce a vocabulary glossary for younger readers.
- **Contextual translation helper** — Give Claude a sentence in English; have it translate, then use the tool to attach IPA pronunciations and short definitions for any word the learner highlights.
- **Etymology explorer** — Build a "word origins" agent that follows the etymology field across related words to teach historical roots.

## More About Kelly Intelligence

- [Kelly Intelligence Playground](https://api.thedailylesson.com) — try the API live
- [Integrations directory](https://api.thedailylesson.com/integrations) — drop-in configs for 25+ developer tools
- [OpenAPI 3.1 spec](https://api.thedailylesson.com/openapi.json)
- [Lesson of the Day, PBC](https://lotdpbc.com) — the public benefit corporation behind Kelly

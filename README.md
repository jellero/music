# Codex Music Studio

Ambiente musicale locale controllabile da **Codex** tramite MCP, CLI e REST API. Consente di creare e modificare composizioni, visualizzare spartito e piano roll, sintetizzare audio e produrre file WAV, MIDI e MusicXML senza dipendere da una DAW esterna.

## Funzioni incluse

- studio web con spartito SVG, piano roll, mixer, transport e download artefatti;
- composizione deterministica multi-traccia (`piano`, `strings`, `bass` e altri timbri);
- editing di note e sostituzione di singole battute;
- armonizzazione di una traccia melodica;
- sintetizzatore stereo locale con rendering WAV;
- esportazione Standard MIDI File e MusicXML;
- server MCP con tool dedicati per Codex;
- CLI completa per automazioni e script;
- API FastAPI documentata automaticamente;
- Docker Compose, test e istruzioni operative per Codex.

## Avvio rapido con Docker

```bash
cp .env.example .env
docker compose up --build -d
```

Apri `http://localhost:8000`.

Per vedere i log:

```bash
docker compose logs -f studio
```

Per fermare l'ambiente:

```bash
docker compose down
```

I progetti vengono salvati in `./data` e rimangono disponibili dopo il riavvio.

## Avvio locale senza Docker

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
music-studio start --reload
```

## Collegamento a Codex tramite MCP

Il server MCP usa il trasporto `stdio`. Dopo l'installazione locale, aggiungi questa configurazione a `~/.codex/config.toml`:

```toml
[mcp_servers.music-studio]
command = "music-studio-mcp"
enabled = true

[mcp_servers.music-studio.env]
MUSIC_STUDIO_DATA = "/percorso/assoluto/al/repository/data"
```

In alternativa, eseguilo nel container:

```toml
[mcp_servers.music-studio]
command = "docker"
args = ["compose", "run", "--rm", "-T", "studio", "music-studio-mcp"]
cwd = "/percorso/assoluto/al/repository"
enabled = true
```

Il file `.codex/config.toml.example` contiene entrambe le varianti.

### Esempi di richieste a Codex

```text
Avvia lo studio musicale, crea un progetto chiamato Notturno a 82 BPM in Re minore,
componi 16 battute per pianoforte, archi e basso, genera WAV, MIDI e MusicXML.
```

```text
Nel progetto notturno sostituisci la battuta 5 della melodia con quattro semiminime:
D4, F4, A4, C5. Armonizza e rigenera tutti gli artefatti.
```

```text
Porta gli archi al 55% di volume, spostali leggermente a destra e renderizza di nuovo.
```

## Tool MCP disponibili

| Tool | Scopo |
|---|---|
| `list_projects` | Elenca i progetti |
| `create_project` | Crea un progetto vuoto |
| `get_project` | Legge score, tracce e artefatti |
| `compose_project` | Genera una composizione multi-traccia |
| `add_note` | Inserisce una nota MIDI |
| `replace_measure` | Sostituisce una battuta completa |
| `harmonize_project` | Genera una voce armonica |
| `set_track_mix` | Modifica volume, pan e timbro |
| `render_project` | Produce WAV, MIDI e MusicXML |

## CLI

```bash
music-studio create "Tema principale" --tempo 96 --key "E minor" --bars 8
music-studio compose tema-principale --style classical --seed 42
music-studio add-note tema-principale melody 72 4 1 --velocity 105
music-studio harmonize tema-principale
music-studio render tema-principale
music-studio show tema-principale
```

Tutti i comandi restituiscono JSON, così Codex può interpretarli e concatenarli in modo affidabile.

## API

Con lo studio avviato:

- interfaccia: `http://localhost:8000`;
- OpenAPI/Swagger: `http://localhost:8000/docs`;
- health check: `http://localhost:8000/api/health`.

Esempio:

```bash
curl -X POST http://localhost:8000/api/projects \
  -H 'Content-Type: application/json' \
  -d '{"name":"Studio 1","tempo":100,"key":"C minor","bars":8}'
```

## Sviluppo e test

```bash
pip install -e '.[dev]'
ruff check .
pytest
```

Oppure:

```bash
make check
```

## Struttura

```text
music_studio/
  api.py          API FastAPI e studio web
  cli.py          interfaccia a riga di comando
  mcp_server.py   tool MCP per Codex
  models.py       modello progetto/tracce/note
  render.py       sintesi WAV, MIDI e MusicXML
  service.py      casi d'uso applicativi
  storage.py      persistenza JSON e artefatti
  theory.py       tonalità, scale, composizione e armonia
  static/         interfaccia web
```

## Limiti attuali

Questa prima versione è una workstation programmabile completa, non una DAW professionale. La notazione web è una rappresentazione SVG semplificata; il MusicXML esportato può essere aperto in MuseScore o software compatibili per impaginazioni avanzate. Il sintetizzatore incluso è intenzionalmente leggero e non carica VST o soundfont.

## Licenza

MIT.

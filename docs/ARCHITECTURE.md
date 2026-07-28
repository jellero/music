# Architettura

## Obiettivo

Codex Music Studio separa il **controllo** dalla **rappresentazione musicale**. Codex chiama tool MCP o comandi CLI; questi invocano lo stesso service applicativo usato dall'API e dall'interfaccia web.

```text
Codex ── MCP/CLI ─┐
                  ├── MusicStudioService ── project.json
Browser ─ REST ───┘          │
                              ├── WAV
                              ├── MIDI
                              └── MusicXML
```

## Fonte canonica

Ogni progetto è memorizzato in:

```text
data/<project-id>/project.json
```

Gli artefatti derivati sono in:

```text
data/<project-id>/artifacts/
```

Il modello usa beat di semiminima come unità temporale. `start=4` indica l'inizio del quinto beat; `duration=0.5` indica una croma.

## Moduli

- `models.py`: validazione Pydantic;
- `storage.py`: confini filesystem e scritture atomiche;
- `theory.py`: tonalità, scale, composizione e armonizzazione;
- `render.py`: sintesi audio, encoder MIDI e serializzazione MusicXML;
- `service.py`: API applicativa unica;
- `api.py`: REST e file statici;
- `mcp_server.py`: adattatore MCP;
- `cli.py`: adattatore CLI.

## Sicurezza locale

Gli ID vengono normalizzati e gli artefatti accettano solo nomi base. Il service non deve accedere a percorsi esterni a `MUSIC_STUDIO_DATA`. Il server non include autenticazione perché è pensato per uso locale; non esporlo direttamente su Internet.

## Estensioni previste

- importazione MusicXML e MIDI;
- registrazione microfono/Web MIDI;
- soundfont e FluidSynth opzionali;
- undo/redo e versioni di progetto;
- analisi armonica e rilevamento collisioni;
- trasporto MCP Streamable HTTP autenticato;
- editing visuale delle note dal piano roll.

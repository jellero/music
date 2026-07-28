# AGENTS.md — Codex Music Studio

## Missione

Mantieni questo repository come ambiente musicale controllabile in modo deterministico da Codex. Ogni operazione importante deve essere accessibile almeno da uno fra MCP, CLI o REST; le operazioni principali devono restare disponibili in tutti e tre i canali.

## Regole operative

1. Non introdurre una dipendenza obbligatoria da una DAW grafica.
2. Mantieni `project.json` come fonte canonica della composizione.
3. Tratta `data/` come stato runtime: non commettere progetti o audio generati.
4. Dopo modifiche a modelli, service o rendering, esegui `pytest`.
5. Dopo modifiche Python, esegui `ruff check .`.
6. Non rompere i nomi dei tool MCP senza aggiornare README e test.
7. Ogni modifica strutturale allo score deve essere seguita da `render_project` quando l'obiettivo include ascolto o esportazione.
8. Preferisci output JSON stabili nei comandi CLI.
9. Valida sempre ID progetto, nomi artefatto, pitch, tempo e durate.
10. Non leggere o scrivere fuori dalla directory configurata con `MUSIC_STUDIO_DATA`.

## Comandi utili

```bash
make install
make dev
make test
make lint
make check
make demo
```

## Flusso consigliato per Codex

1. `list_projects`
2. `create_project` oppure `get_project`
3. `compose_project`, `add_note`, `replace_measure`, `harmonize_project` o `set_track_mix`
4. `render_project`
5. `get_project` per verificare manifest e URL degli artefatti

## Criteri di completamento

Una modifica è completa quando:

- i test passano;
- il server parte;
- lo studio web carica `/api/health` e `/api/projects`;
- gli artefatti dichiarati nel manifest esistono;
- README e tool MCP riflettono il comportamento effettivo.

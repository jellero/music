# Uso con Codex

## Responsabilità di Codex

Codex è il controller principale: crea lo score, applica modifiche, genera artefatti e verifica il risultato. Il browser serve per ispezionare e ascoltare lo stato corrente, non è necessario per l'automazione.

## Sessione tipica

```text
1. list_projects
2. create_project(name="Tema", tempo=100, key="C minor", bars=8)
3. compose_project(project_id="tema", style="minimal", instruments=["piano","strings","bass"])
4. render_project(project_id="tema")
5. get_project(project_id="tema")
```

## Editing preciso

Le note usano pitch MIDI:

- C4 = 60
- D4 = 62
- E4 = 64
- F4 = 65
- G4 = 67
- A4 = 69
- B4 = 71
- C5 = 72

`replace_measure` riceve start relativi alla battuta:

```json
{
  "project_id": "tema",
  "measure": 3,
  "track": "melody",
  "notes": [
    {"pitch": 60, "start": 0, "duration": 1, "velocity": 96},
    {"pitch": 64, "start": 1, "duration": 1, "velocity": 96},
    {"pitch": 67, "start": 2, "duration": 2, "velocity": 100}
  ]
}
```

## Verifica

Dopo ogni render, controlla che il manifest contenga gli artefatti richiesti e dimensioni maggiori di zero. Per verifiche strutturali usa `pytest`; per un controllo HTTP usa `/api/health`.

# Eval clasificación: claude-haiku-4-5_v2_repro1_n10 (2026-10-14)

- Issues evaluados: 40 (errores técnicos excluidos: 0)
- Accuracy: 90.00%
- F1 macro: 0.899
- needs_human: 70.0%
- Latencia media: 19.2 s

## Matriz de confusión (filas = real, columnas = predicción)
```
orden: Bug, Docs, Enhancement, Usage Question
[[10  0  0  0]
 [ 0  9  0  1]
 [ 0  0 10  0]
 [ 3  0  0  7]]
```

```
                precision    recall  f1-score   support

           Bug       0.77      1.00      0.87        10
          Docs       1.00      0.90      0.95        10
   Enhancement       1.00      1.00      1.00        10
Usage Question       0.88      0.70      0.78        10

      accuracy                           0.90        40
     macro avg       0.91      0.90      0.90        40
  weighted avg       0.91      0.90      0.90        40

```
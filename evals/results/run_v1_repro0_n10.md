# Eval clasificación: v1_repro0_n10 (2026-10-14)

- Issues evaluados: 40
- Accuracy: 27.50%
- F1 macro: 0.320
- needs_human: 72.5%
- Latencia media: 1153.6 s
- Costo: USD 0 (modelo local)

## Matriz de confusión (filas = real, columnas = predicción)
```
orden: Bug, Docs, Enhancement, Usage Question, ERROR
[[ 9  0  0  0  1]
 [ 0  0  0  0 10]
 [ 0  0  2  0  8]
 [ 0  0  0  0 10]
 [ 0  0  0  0  0]]
```

```
                precision    recall  f1-score   support

           Bug       1.00      0.90      0.95        10
          Docs       0.00      0.00      0.00        10
   Enhancement       1.00      0.20      0.33        10
Usage Question       0.00      0.00      0.00        10

     micro avg       1.00      0.28      0.43        40
     macro avg       0.50      0.28      0.32        40
  weighted avg       0.50      0.28      0.32        40

```
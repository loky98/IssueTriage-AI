from app.guardrails import GuardrailError, check_input, mask_pii

print(mask_pii("Escríbeme a diego@example.com, token ghp_" + "a" * 36))
try:
    check_input("My car won't start", "The engine makes a strange noise")
except GuardrailError as e:
    print("Rechazado:", e)
print("Aceptado:", check_input("read_csv bug", "pd.read_csv fails with sep")[0])
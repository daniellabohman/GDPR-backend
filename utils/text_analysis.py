def analyze_policy_text(text):
    suggestions = []

    if "cookie" not in text.lower():
        suggestions.append("Tilføj en sektion om cookies og cookie-banner.")
    if "rettigheder" not in text.lower():
        suggestions.append("Beskriv brugernes rettigheder i henhold til GDPR.")
    if "databehandler" not in text.lower():
        suggestions.append("Angiv eventuelle databehandlere og formål.")
    if "opbevaring" not in text.lower():
        suggestions.append("Forklar hvor længe data opbevares og hvorfor.")

    if not suggestions:
        suggestions.append("Alt ser godt ud – men dobbelttjek altid med en jurist.")

    return suggestions

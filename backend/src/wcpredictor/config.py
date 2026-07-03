"""Shared configuration for the prediction engine."""

TOURNAMENT_TIER: dict[str, str] = {
    "Friendly": "friendly",
    "International Friendly": "friendly",
    "World Cup": "wc",
    "FIFA World Cup": "wc",
    "World Cup qualification": "qualifier",
    "WCQ": "qualifier",
    "UEFA Euro": "continental",
    "European Championship": "continental",
    "Copa America": "continental",
    "Africa Cup of Nations": "continental",
    "AFC Asian Cup": "continental",
    "CONCACAF Gold Cup": "continental",
    "OFC Nations Cup": "continental",
    "UEFA Nations League": "nations_league",
    "CONCACAF Nations League": "nations_league",
    "Confederations Cup": "continental",
}

ELO_START = 1500
ELO_HOME_ADV = 80

TEAM_ALIASES: dict[str, str] = {
    "USA": "United States", "United States": "United States",
    "Côte d'Ivoire": "Ivory Coast", "Cote d'Ivoire": "Ivory Coast", "Ivory Coast": "Ivory Coast",
    "Bosnia & Herzegovina": "Bosnia and Herzegovina", "Bosnia and Herzegovina": "Bosnia and Herzegovina",
    "Congo DR": "DR Congo", "DR Congo": "DR Congo",
    "South Korea": "South Korea", "Korea Republic": "South Korea",
    "Cape Verde": "Cape Verde", "Cabo Verde": "Cape Verde",
    "North Macedonia": "North Macedonia",
}

def canonical(name: str) -> str:
    return TEAM_ALIASES.get(name, name)

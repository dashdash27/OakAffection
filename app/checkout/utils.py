def pluralize(number, titles):
    cases = [2, 0, 1, 1, 1, 2]
    if 4 < number % 100 < 20:
        idx = 2
    else:
        idx = cases[min(number % 10, 5)]
    return f"{number} {titles[idx]}"

def format_delivery_days(api_days):
    try:
        # 1. Если API прислало число (например, 7)
        min_days = int(api_days)
        max_days = min_days + 1  # Твой запас для безопасности
        
        # 2. Склоняем по максимальному числу
        word = ["день", "дня", "дней"]
        
        if min_days == max_days:
             return pluralize(min_days, word)
             
        # Возвращаем красивую строку: "7-8 дней"
        day_word = pluralize(max_days, word).split()[-1] 
        return f"{min_days}-{max_days} {day_word}"
        
    except (ValueError, TypeError):
        return "срок уточняется"
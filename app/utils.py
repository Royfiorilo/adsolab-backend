ROUND_DIGIT = 4

def round_list_numbers(numbers, round = ROUND_DIGIT):
    return [round_number(num, round) for num in numbers]

def round_number(number, round_digit = ROUND_DIGIT):
    return round(number, round_digit)
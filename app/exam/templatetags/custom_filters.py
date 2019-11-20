from django.template.defaulttags import register



@register.filter(name='memory_force_value')
def memory_force_value(all_memory_force_values,current_exam_name):
    """Take memory force value dictionary and return current object value"""
    memory_force_value = all_memory_force_values[current_exam_name]
    if memory_force_value == "low":
        color="red"
    elif memory_force_value == "high":
        color="green"
    else:
        color="yellow"
    return color


@register.filter(name='memory_force_title')
def memory_force_title(all_memory_force_values,current_exam_name):
    """Take memory force value dictionary and return current object value"""
    return all_memory_force_values[current_exam_name]


def lambda_handler(event, context):
    return f"Version 1: {type(event)}, {type(context)}"

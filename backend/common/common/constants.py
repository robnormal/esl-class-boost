USERS_TABLE = "history_learning_users"
SUBMISSIONS_TABLE = "history_learning_submissions"
VOCABULARY_TABLE = "history_learning_vocabulary"
SUMMARIES_TABLE = "history_learning_summaries"

PARAGRAPHS_QUEUE = 'history-learning-paragraphs'
VOCABULARY_QUEUE = 'history-learning-vocabulary'
SUMMARIES_QUEUE = 'history-learning-summaries'

# Maximum number of items that can be inserted/updated at once
DYNAMODB_MAX_BATCH_SIZE = 25

# Limit the paragraphs we'll summarize for any document
SUMMARIES_PER_SUBMISSION_LIMIT = 100

PARAGRAPH_INTRO_WORDS = 10

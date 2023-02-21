from transformers import pipeline

# Load the BART model
model = pipeline('summarization', model='facebook/bart-large-cnn')

# Print the summary

def summarize_text(text):
    summary = model(text[:3000], max_length=3000, min_length=10, do_sample=False)
    return summary[0]['summary_text']

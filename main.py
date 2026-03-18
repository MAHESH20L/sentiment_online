from fastapi import FastAPI, UploadFile, File, Body
from fastapi.middleware.cors import CORSMiddleware
from transformers import AutoTokenizer, AutoModelForSequenceClassification

import torch
import pandas as pd
import re
import numpy as np
import matplotlib.pyplot as plt
import io, base64

import requests
from io import StringIO

app = FastAPI()

# =============================
# CORS
# =============================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================
# LOAD MODEL
# =============================
MODEL_NAME = "PattimaniM/updated_sentiment"

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
model.eval()

labels = {
    0: "Negative 😡",
    1: "Neutral 😐",
    2: "Positive 😊"
}

# =============================
# CLEAN TEXT
# =============================
def clean_text(text):

    text = str(text)

    text = re.sub(r"http\S+", "", text)
    text = re.sub(r"@\w+", "", text)
    text = re.sub(r"#", "", text)

    text = re.sub(r"\s+", " ", text).strip()

    return text


# =============================
# TEXT COLUMN DETECTOR
# =============================
def detect_text_column(df):

    keywords = [
        "tweet","text","review","comment",
        "content","message","feedback","post"
    ]

    for col in df.columns:
        name = col.lower()

        if any(k in name for k in keywords):
            return col

    best_col = None
    best_score = 0

    for col in df.columns:

        try:
            sample = df[col].dropna().astype(str).head(50)

            if len(sample) == 0:
                continue

            avg_len = sample.apply(len).mean()

            if avg_len > best_score:
                best_score = avg_len
                best_col = col

        except:
            continue

    return best_col


# =============================
# TOPIC DETECTION
# =============================
def detect_topic(text):

    text = str(text).lower()

    if any(w in text for w in [
        "price","pricing","cost","expensive","cheap","offer","discount"
    ]):
        return "Pricing"

    elif any(w in text for w in [
        "delivery","shipping","late","delay","courier","order","shipment"
    ]):
        return "Delivery"

    elif any(w in text for w in [
        "quality","product","broken","damaged","defective","material"
    ]):
        return "Product Quality"

    elif any(w in text for w in [
        "support","service","customer","help","refund","staff"
    ]):
        return "Customer Service"

    elif any(w in text for w in [
        "app","website","login","bug","error","payment"
    ]):
        return "Technical/App Issues"

    elif any(w in text for w in [
        "movie","film","cinema","actor","actress","director"
    ]):
        return "Films"

    elif any(w in text for w in [
        "music","song","album","singer","band"
    ]):
        return "Music"

    elif any(w in text for w in [
        "doctor","clinic","physician","appointment"
    ]):
        return "Doctor"

    elif any(w in text for w in [
        "health","hospital","medicine","disease","treatment"
    ]):
        return "Health"

    elif any(w in text for w in [
        "shopping","buy","purchase","store","checkout"
    ]):
        return "Shopping"

    elif any(w in text for w in [
        "finance","bank","loan","credit","investment"
    ]):
        return "Finance"

    else:
        return "General"


# =============================
# SENTIMENT PIPELINE
# =============================
def analyze_dataframe(df):

    text_column = detect_text_column(df)

    if text_column is None:
        return {"error": "Could not detect text column automatically"}

    df = df.head(200)

    results = []
    sentiments = []
    topic_sentiments = []

    for text in df[text_column]:

        text_clean = clean_text(text)
        topic = detect_topic(text)

        inputs = tokenizer(
            text_clean,
            return_tensors="pt",
            truncation=True,
            padding=True
        )

        with torch.no_grad():
            outputs = model(**inputs)
            probs = torch.softmax(outputs.logits, dim=1).numpy()[0]

        pred_id = int(np.argmax(probs))
        sentiment = labels[pred_id]

        sentiments.append(sentiment)
        topic_sentiments.append((topic, sentiment))

        results.append({
            "tweet": text,
            "topic": topic,
            "sentiment": sentiment,
            "confidence": round(float(probs[pred_id]),3)
        })


    # =============================
    # OVERALL SENTIMENT CHART
    # =============================
    counts = pd.Series(sentiments).value_counts()

    plt.figure(figsize=(8,5))

    counts.plot(kind="bar", color=["red","orange","green"])

    plt.title("Overall Sentiment Distribution")
    plt.ylabel("Number of Reviews")

    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)

    overall_chart = base64.b64encode(buf.read()).decode("utf-8")
    plt.close()


    # =============================
    # TOPIC SENTIMENT CHART
    # =============================
    topic_df = pd.DataFrame(topic_sentiments, columns=["topic","sentiment"])

    pivot = pd.crosstab(topic_df["topic"], topic_df["sentiment"])

    pivot.plot(
        kind="bar",
        stacked=True,
        figsize=(10,6)
    )

    plt.title("Topic-wise Sentiment Analysis")

    buf2 = io.BytesIO()
    plt.savefig(buf2, format="png")
    buf2.seek(0)

    topic_chart = base64.b64encode(buf2.read()).decode("utf-8")
    plt.close()
    # =============================
    # NEGATIVE ISSUES RANKING CHART
    # =============================
    neg_counts = topic_df[topic_df["sentiment"]=="Negative 😡"]["topic"].value_counts()
    plt.figure(figsize=(8,5))
    if len(neg_counts) > 0:
        neg_counts.plot(kind="bar")
        plt.title("Top Negative Issues")
        plt.ylabel("Number of Complaints")
    else:
        plt.text(0.5, 0.5, "No Negative Issues 🎉", ha='center', va='center')
    plt.tight_layout()
    buf3 = io.BytesIO()
    plt.savefig(buf3, format="png")
    buf3.seek(0)
    negative_chart = base64.b64encode(buf3.read()).decode("utf-8")
    plt.close()

    # =============================
    # AI RECOMMENDATIONS
    # =============================
    recommendations = []

    neg_topics = topic_df[topic_df["sentiment"]=="Negative 😡"]["topic"].value_counts()

    for topic in neg_topics.index:

        if topic == "Pricing":
            recommendations.append("Customers complain about pricing. Consider discounts.")

        elif topic == "Delivery":
            recommendations.append("Delivery delays detected. Improve shipping process.")

        elif topic == "Product Quality":
            recommendations.append("Improve product quality and inspection.")

        elif topic == "Customer Service":
            recommendations.append("Improve support response time.")

        elif topic == "Technical/App Issues":
            recommendations.append("Fix technical bugs and improve app reliability.")

        else:
            recommendations.append(f"Negative feedback detected in {topic}")

    if len(recommendations) == 0:
        recommendations.append("Overall sentiment is positive.")

    return {
        "detected_column": text_column,
        "results": results,
        "overall_sentiment_chart": overall_chart,
        "topic_sentiment_chart": topic_chart,
        "negative_topics_chart": negative_chart,
        "recommendations": recommendations
    }


# =============================
# MANUAL CSV UPLOAD
# =============================
@app.post("/predict-csv")
async def predict_csv(file: UploadFile = File(...)):

    df = pd.read_csv(file.file)

    return analyze_dataframe(df)


# =============================
# CSV LINK SUPPORT
# =============================
@app.post("/predict-csv-link")
async def predict_csv_link(data: dict = Body(...)):

    url = data.get("url")

    if not url:
        return {"error": "CSV URL not provided"}

    try:

        response = requests.get(url)

        if response.status_code != 200:
            return {"error": "Could not download CSV"}

        df = pd.read_csv(StringIO(response.text))

    except Exception as e:
        return {"error": f"Failed to read CSV: {str(e)}"}

    return analyze_dataframe(df)

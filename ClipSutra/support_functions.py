import time
import os
import re
from dotenv import load_dotenv
load_dotenv()
from youtube_transcript_api import YouTubeTranscriptApi

from langchain_text_splitters import RecursiveCharacterTextSplitter

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate


import os

key = os.getenv("GOOGLE_API_KEY")

print("Gemini API key loaded:", bool(key))
print("Gemini API key length:", len(key) if key else 0)

_GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
if not _GOOGLE_API_KEY:
    print("WARNING: GOOGLE_API_KEY not found in environment. "
          "Please set it in your .env file. Gemini API calls will fail.")

TRANSCRIPT_CACHE = {}


def extract_video_id(url):
    """
    Extracts the YouTube video ID from any valid YouTube URL.
    """
    if not url:
        return None
    match = re.search(r"(?:v=|\/|youtu\.be\/)([0-9A-Za-z_-]{11})", url)
    if match:
        return match.group(1)
    return None


def get_video_title(video_id_or_url):
    try:
        import urllib.request
        import json
        if "youtube.com" in video_id_or_url or "youtu.be" in video_id_or_url:
            clean_url = video_id_or_url
        else:
            clean_url = f"https://www.youtube.com/watch?v={video_id_or_url}"
        oembed_url = f"https://www.youtube.com/oembed?url={clean_url}&format=json"
        req = urllib.request.Request(oembed_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            return data.get('title', 'YouTube Video')
    except Exception:
        return "YouTube Video"


def get_transcript(video_id, language="en"):
    ytt_api = YouTubeTranscriptApi()
    try:
        transcript = ytt_api.fetch(video_id, languages=[language])
        full_transcript = " ".join([i.text for i in transcript])
        return full_transcript
    except Exception as e:
        # Fallback: try default fetch without language constraint if specified language fails
        try:
            transcript = ytt_api.fetch(video_id)
            full_transcript = " ".join([i.text for i in transcript])
            return full_transcript
        except Exception:
            raise RuntimeError(f"Error fetching transcript: {e}")


# LLM instance initialized safely with explicit API key
def get_llm():
    api_key = os.getenv("GOOGLE_API_KEY")

    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY not found in .env file")

    return ChatGoogleGenerativeAI(
        model="gemini-3.5-flash-lite",
        google_api_key=api_key
    )


def translate_transcript(transcript):
    try:
        llm = get_llm()
        prompt = ChatPromptTemplate.from_template("""
        You are an expert translator with deep cultural and linguistic knowledge.
        I will provide you with a transcript. Your task is to translate it into English with absolute accuracy, preserving:
        - Full meaning and context (no omissions, no additions).
        - Tone and style (formal/informal, emotional/neutral as in original).
        - Nuances, idioms, and cultural expressions (adapt appropriately while keeping intent).
        - Speaker’s voice (same perspective, no rewriting into third-person).
        Do not summarize or simplify. The translation should read naturally in the target language but stay as close as possible to the original intent.

        Transcript:
        {transcript}
        """)

        chain = prompt | llm

        response = chain.invoke({"transcript": transcript})
        return response.content
    except Exception as e:
        raise RuntimeError(f"Error translating transcript: {e}")


def get_important_topics(transcript):
    try:
        llm = get_llm()
        prompt = ChatPromptTemplate.from_template("""
               You are an assistant that extracts the 5 most important topics discussed in a video transcript or summary.

               Rules:
               - Summarize into exactly 5 major points.
               - Each point should represent a key topic or concept, not small details.
               - Keep wording concise and focused on the technical content.
               - Do not phrase them as questions or opinions.
               - Output should be a numbered list.
               - show only points that are discussed in the transcript.
               Here is the transcript:
               {transcript}
               """)

        chain = prompt | llm

        response = chain.invoke({"transcript": transcript})
        return response.content

    except Exception as e:
        raise RuntimeError(f"Error getting important topics: {e}")


def generate_notes(transcript):
    try:
        llm = get_llm()
        prompt = ChatPromptTemplate.from_template("""
                You are an AI note-taker. Your task is to read the following YouTube video transcript 
                and produce well-structured, concise notes.

                ⚡ Requirements:
                - Present the output as **bulleted points**, grouped into clear sections.
                - Highlight key takeaways, important facts, and examples.
                - Use **short, clear sentences** (no long paragraphs).
                - If the transcript includes multiple themes, organize them under **subheadings**.
                - Do not add information that is not present in the transcript.

                Here is the transcript:
                {transcript}
                """)

        chain = prompt | llm

        response = chain.invoke({"transcript": transcript})
        return response.content

    except Exception as e:
        raise RuntimeError(f"Error generating notes: {e}")


def create_chunks(transcript):
    text_splitters = RecursiveCharacterTextSplitter(chunk_size=10000, chunk_overlap=1000)
    doc = text_splitters.create_documents([transcript])
    return doc


def create_vector_store(docs):
    embedding = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
    vector_store = Chroma.from_documents(docs, embedding)
    return vector_store


def rag_answer(question, vectorstore):
    try:
        results = vectorstore.similarity_search(question, k=4)
        context_text = "\n".join([i.page_content for i in results])

        llm = get_llm()
        prompt = ChatPromptTemplate.from_template("""
                    You are a kind, polite, and precise assistant.
                    - Begin with a warm and respectful greeting (avoid repeating greetings every turn).
                    - Understand the user’s intent even with typos or grammatical mistakes.
                    - Answer ONLY using the retrieved context.
                    - If answer not in context, say:
                      "I couldn’t find that information in the database. Could you please rephrase or ask something else?"
                    - Keep answers clear, concise, and friendly.

                    Context:
                    {context}

                    User Question:
                    {question}

                    Answer:
                    """)

        chain = prompt | llm
        response = chain.invoke({"context": context_text, "question": question})
        return response.content
    except Exception as e:
        raise RuntimeError(f"Error generating answer: {e}")

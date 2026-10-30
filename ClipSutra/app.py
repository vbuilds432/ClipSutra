import os
import uuid
import re
from flask import Flask, render_template, request, jsonify, send_file, session
from dotenv import load_dotenv
load_dotenv()
from support_functions import (
    extract_video_id,
    get_video_title,
    get_transcript,
    translate_transcript,
    generate_notes,
    get_important_topics,
    create_chunks,
    create_vector_store,
    rag_answer
)
from pdf_generator import build_notes_pdf



app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "yt-synthesizer-secret-session-key-2026")

VIDEO_SESSIONS = {}


@app.route("/")
def index():
    if "user_session_id" not in session:
        session["user_session_id"] = str(uuid.uuid4())
    return render_template("index.html")


@app.route("/api/process", methods=["POST"])
def process_video():
    """
    Endpoint to process YouTube URL:
    - Extracts transcript
    - Translates if needed
    - Extracts key topics & structured notes
    - Builds RAG vector store for instant chatbot readiness
    """
    data = request.get_json() or {}
    url = (data.get("url") or "").strip()
    language = (data.get("language") or "en").strip()

    if not url:
        return jsonify({"status": "error", "message": "Please enter a YouTube video URL."}), 400

    video_id = extract_video_id(url)
    if not video_id:
        return jsonify({"status": "error", "message": "Invalid YouTube URL. Please provide a valid YouTube video link."}), 400

    user_sid = session.get("user_session_id")
    if not user_sid:
        user_sid = str(uuid.uuid4())
        session["user_session_id"] = user_sid

    try:
        title = get_video_title(url)

        full_transcript = get_transcript(video_id, language=language)
        if not full_transcript:
            return jsonify({"status": "error", "message": "Could not extract transcript for this video. Captions might be disabled."}), 400

        if language.lower() not in ["en", "english"]:
            full_transcript = translate_transcript(full_transcript)

        topics = get_important_topics(full_transcript)
        notes = generate_notes(full_transcript)

        chunks = create_chunks(full_transcript)
        vector_store = create_vector_store(chunks)

        VIDEO_SESSIONS[user_sid] = {
            "video_id": video_id,
            "url": url,
            "title": title,
            "language": language,
            "topics": topics,
            "notes": notes,
            "vector_store": vector_store,
            "messages": []
        }

        return jsonify({
            "status": "success",
            "data": {
                "videoId": video_id,
                "title": title,
                "url": url,
                "topics": topics,
                "notes": notes
            }
        })

    except Exception as e:
        import traceback
        traceback.print_exc()

        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
        return jsonify({"status": "error", "message": error_msg}), 500


@app.route("/api/chat", methods=["POST"])
def chat():
    """
    RAG Chatbot query endpoint
    """
    data = request.get_json() or {}
    question = (data.get("question") or "").strip()

    if not question:
        return jsonify({"status": "error", "message": "Question cannot be empty."}), 400

    user_sid = session.get("user_session_id")
    sess_data = VIDEO_SESSIONS.get(user_sid)

    if not sess_data or "vector_store" not in sess_data:
        return jsonify({
            "status": "error",
            "message": "Please process a YouTube video first before chatting."
        }), 400

    try:
        vector_store = sess_data["vector_store"]
        answer = rag_answer(question, vector_store)

        sess_data.setdefault("messages", []).append({"role": "user", "content": question})
        sess_data["messages"].append({"role": "assistant", "content": answer})

        return jsonify({
            "status": "success",
            "question": question,
            "answer": answer
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/download-pdf", methods=["POST", "GET"])
def download_pdf():
    """
    Generates and downloads styled PDF with notes and video title.
    Supports both POST with custom payload and GET using session state.
    """
    user_sid = session.get("user_session_id")
    sess_data = VIDEO_SESSIONS.get(user_sid, {})

    title = sess_data.get("title", "YouTube Video Notes")
    notes = sess_data.get("notes", "")
    topics = sess_data.get("topics", "")
    url = sess_data.get("url", "")

    if request.method == "POST":
        body = request.get_json() or {}
        if body.get("title"):
            title = body.get("title")
        if body.get("notes"):
            notes = body.get("notes")
        if body.get("topics"):
            topics = body.get("topics")
        if body.get("url"):
            url = body.get("url")

    if not notes and not topics:
        return jsonify({"status": "error", "message": "No notes available to export as PDF."}), 400

    try:
        pdf_buffer = build_notes_pdf(
            title=title,
            notes_text=notes,
            topics_text=topics,
            video_url=url
        )

        safe_title = re.sub(r'[^a-zA-Z0-9_\-\s]', '', title).strip()
        safe_title = re.sub(r'\s+', '_', safe_title)[:45] or "YouTube_Notes"
        filename = f"{safe_title}_Notes.pdf"

        return send_file(
            pdf_buffer,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        return jsonify({"status": "error", "message": f"PDF Generation Error: {str(e)}"}), 500


@app.route("/api/reset", methods=["POST"])
def reset_session():
    user_sid = session.get("user_session_id")
    if user_sid and user_sid in VIDEO_SESSIONS:
        del VIDEO_SESSIONS[user_sid]
    return jsonify({"status": "success", "message": "Session reset."})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(
        host="0.0.0.0",
        port=port,
        debug=True,
        use_reloader=False
    )
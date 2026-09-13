import re
import sounddevice as sd
import speech_recognition as sr
import webbrowser
import pyttsx3
import sounddevice as sd
import http.server
import socketserver
import threading
from urllib.parse import quote
from yt_dlp import YoutubeDL
import pyttsx3

SAMPLE_RATE = 16000
CHANNELS = 1
COMMAND_DURATION = 3  # seconds — bump this if commands still get cut off
SERVER_PORT = 8000

recognizer = sr.Recognizer()
engine = pyttsx3.init()


def speak(text):
    print("CARAX:", text)
    engine.say(text)
    engine.runAndWait()


def start_server(port=SERVER_PORT):
    """Starts a background HTTP server so YouTube embeds don't hit file:// origin errors."""
    handler = http.server.SimpleHTTPRequestHandler
    httpd = socketserver.TCPServer(("", port), handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    return port


def play_video(video_id):
    html = f"""
    <html><body style="margin:0">
    <div id="player" style="width:100%;height:100vh;"></div>
    <script src="https://www.youtube.com/iframe_api"></script>
    <script>
      var player;
      function onYouTubeIframeAPIReady() {{
        player = new YT.Player('player', {{
          height: '100%',
          width: '100%',
          videoId: '{video_id}',
          playerVars: {{ autoplay: 0, mute: 0 }},
          events: {{
            onReady: function(event) {{
              event.target.playVideo();
              setTimeout(function() {{ event.target.unMute(); event.target.setVolume(100); }}, 500);
            }}
          }}
        }});
      }}
    </script>
    </body></html>
    """
    with open("play.html", "w") as f:
        f.write(html)
    webbrowser.open(f"http://localhost:{SERVER_PORT}/play.html")


def get_top_video_id(query):
    ydl_opts = {"quiet": True, "no_warnings": True, "default_search": "ytsearch1", "noplaylist": True}
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(query, download=False)
        if "entries" in info and info["entries"]:
            return info["entries"][0]["id"]
    return None


def record_audio(duration=COMMAND_DURATION, sample_rate=SAMPLE_RATE):
    """Records audio from the default mic and returns raw bytes."""
    speak("listening....")
    recording = sd.rec(int(duration * sample_rate), samplerate=sample_rate,
                        channels=CHANNELS, dtype='int16')
    sd.wait()
    return recording.tobytes()


def extract_query(command, *keywords):
    """Removes trigger words (whole-word match) and returns the leftover search term."""
    query = command
    for kw in keywords:
        query = re.sub(rf"\b{re.escape(kw)}\b", "", query)
    return " ".join(query.split()).strip()


def process_command(command):
    command = command.lower()

    if "hello" in command or "hi" in command:
        speak("Hello there! I'm Carax, your assistant. How can I help you today?")

    elif "how are you" in command:
        speak("I'm doing great, thanks for asking! How about you?")

    elif "open google" in command:
        speak("Sure, opening Google for you right now.")
        webbrowser.open("https://www.google.com")

    elif "open youtube" in command:
        speak("Got it, opening YouTube for you.")
        webbrowser.open("https://www.youtube.com")

    elif "open github" in command:
        speak("Alright, opening GitHub now.")
        webbrowser.open("https://www.github.com")

    elif "open linkedin" in command:
        speak("Opening LinkedIn for you.")
        webbrowser.open("https://www.linkedin.com")

    elif "python dictionary" in command:
        speak("Sure thing, pulling up the Python documentation for you.")
        webbrowser.open("https://www.python.org/doc/")

    elif "open chatgpt" in command or "open chat gpt" in command:
        speak("Opening ChatGPT for you.")
        webbrowser.open("https://chat.openai.com/")

    elif "open stackoverflow" in command:
        speak("Opening Stack Overflow for you.")
        webbrowser.open("https://stackoverflow.com/")

    elif "open claude" in command:
        speak("Opening Claude for you.")
        webbrowser.open("https://claude.ai/")

    # ----------- Generic "open <site>" handler (FIXED) -----------
    # Previously this always ran a Google *search* for the query instead of
    # actually opening the site. Now: single-word site names ("open amazon",
    # "open netflix", "open reddit") are opened directly as www.<site>.com.
    # Multi-word phrases ("open the weather forecast") fall back to a Google
    # search, since there's no reliable domain to guess from those.
    elif "open" in command:
        query = extract_query(command, "open")
        if query:
            if " " not in query:
                speak(f"Opening {query} for you.")
                webbrowser.open(f"https://www.{query}.com")
            else:
                speak(f"I don't know the exact site for {query}, searching instead.")
                webbrowser.open(f"https://www.google.com/search?q={quote(query)}")
        else:
            speak("I couldn't tell what you want me to open. Please try again.")

    # ----------- Play a video/song on YouTube -----------
    elif "play" in command:
        query = extract_query(command, "play", "video", "song", "on", "youtube")
        if query:
            video_id = get_top_video_id(query)
            if video_id:
                speak(f"Playing {query} on YouTube.")
                play_video(video_id)
            else:
                speak(f"I couldn't find a video for {query}.")
        else:
            speak("I couldn't tell what you want me to play. Please try again.")

    # ----------- Search on Amazon (check before generic search) -----------
    elif "amazon" in command and ("search" in command or "find" in command or "buy" in command):
        query = extract_query(command, "search", "find", "buy", "on", "amazon", "for")
        if query:
            speak(f"Searching Amazon for {query}")
            webbrowser.open(f"https://www.amazon.com/s?k={quote(query)}")
        else:
            speak("What would you like me to search on Amazon?")

    # ----------- Search on YouTube (check before generic search) -----------
    elif "youtube" in command and ("search" in command or "find" in command):
        query = extract_query(command, "search", "find", "on", "youtube", "for")
        if query:
            speak(f"Searching YouTube for {query}")
            webbrowser.open(f"https://www.youtube.com/results?search_query={quote(query)}")
        else:
            speak("What would you like me to search on YouTube?")

    # ----------- Search on Google (generic fallback for search/find) -----------
    elif "google" in command or "search" in command or "find" in command:
        query = extract_query(command, "search", "find", "on", "google", "for")
        if query:
            speak(f"Searching for {query} on Google.")
            webbrowser.open(f"https://www.google.com/search?q={quote(query)}")
        else:
            speak("I couldn't find the information you requested. Please try again.")

    elif "stop" in command:
        speak("Alright, shutting down now. Goodbye!")
        return False

    else:
        speak(f"I heard you say: {command}. I'm not sure how to help with that yet.")

    return True


if __name__ == "__main__":
    start_server()  # start local server once, before the loop
    speak("Initializing Carax.....")

    running = True
    while running:
        r = sr.Recognizer()
        raw_audio = record_audio()
        audio = sr.AudioData(raw_audio, SAMPLE_RATE, 2)

        try:
            command = r.recognize_google(audio)
            speak(command)
            running = process_command(command)
        except sr.UnknownValueError:
            speak("Carax could not understand audio")
        except sr.RequestError as e:
            speak("Carax error; {0}".format(e))
from flask import Flask, request, jsonify
import google.generativeai as genai

app = Flask(__name__)

genai.configure(api_key="AIzaSyDVMgYyDpA3ROnUAA4BSk9WIA4GfJx0WIw")

model = genai.GenerativeModel("gemini-2.5-flash")

@app.route("/explain", methods=["POST"])
def explain():
    try:
        data = request.json
        error = data.get("error", "")

        prompt = f"""
You are a terminal assistant.

Explain this error:
{error}

Give:
1. Why it failed
2. Fix command
3. Tip
"""

        response = model.generate_content(prompt)

        return jsonify({"response": response.text})

    except Exception as e:
        return jsonify({"response": "Error: " + str(e)})

if __name__ == "__main__":
    app.run(port=5000, debug=True)
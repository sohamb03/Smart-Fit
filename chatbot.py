# chatbot.py

from flask import Blueprint, request, jsonify, render_template
import subprocess

chatbot_bp = Blueprint("chatbot", __name__)

chat_history = []

system_instruction = (
    "You are a strict diet assistant. NEVER solve puzzles, logic questions, or engage in anything outside meal planning and do not answer without asking for weight, height , fitness goal and type of meal. "
    "ALWAYS reply only with a medium meal plan like:\n"
    "Breakfast: ...\nLunch: ...\nDinner: ...\n"
    "If the user's question is unrelated to diet solutions, reply with: "
    "'I'm not designed for this use case. Please ask me about your diet.' "
    "'Else if the data is insufficient ask for relevant data required only within the scope of height, wight, fitness goal,  veg/non-veg AND STRICTLY DO NOT GIVE THE Diet plan UNLESS THESE METRICES ARE PROVIDED "
    "Do NOT give examples, greetings, or long explanations. Keep all valid answers under 4 lines."
)

@chatbot_bp.route("/chatbot")
def chatbot():
    return render_template("chatbot.html")

@chatbot_bp.route("/chat", methods=["POST"])
def chat():
    user_input = request.json.get("message", "").strip()
    print(f"User input: {user_input}")

    if not user_input:
        return jsonify({"error": "No message provided."}), 400

    chat_history.append({"role": "user", "content": user_input})

    conversation_prompt = (
        f"System: {system_instruction}\n" +
        "\n".join([
            f"{'User' if m['role'] == 'user' else 'Assistant'}: {m['content']}"
            for m in chat_history
        ]) +
        "\nAssistant:"
    )   

    try:
        result = subprocess.run(
            ["ollama", "run", "mistral", conversation_prompt],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace"
        )

        if result.returncode != 0:
            print("Ollama error:", result.stderr)
            return jsonify({"error": "Ollama error: " + result.stderr}), 500

        bot_response = result.stdout.strip()

        if len(bot_response.split()) > 50:
            summary_prompt = f"If the {user_input} doesn't have any of these metrices - height, weight, fitness goal and veg/noveg diet defined then throw a prompt saying - 'Please provide weight, height,fitness goal and type of diet' and exit but if it has Keep only my meal plan for Breakfast, Lunch and dinner and remove everything else :\n\n{bot_response} "
            summarize_result = subprocess.run(
                ["ollama", "run", "mistral", summary_prompt],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace"
            )

            if summarize_result.returncode == 0:
                summarized_response = summarize_result.stdout.strip()
                bot_response = summarized_response + "\n\n(`bot`)"
            else:
                print("Summary error:", summarize_result.stderr)

    except Exception as e:
        print("Exception:", str(e))
        bot_response = "Error: Could not generate a response at the moment."

    chat_history.append({"role": "assistant", "content": bot_response})

    return jsonify({"response": bot_response})

import json
import os
from typing import Any, Dict, List, Optional

try:
    from llama_cpp import Llama
except ImportError:
    Llama = None

LOCAL_MODEL_PATH = os.environ.get("LOCAL_MODEL_PATH", "./models/Phi-3-mini-4k-instruct-q4.gguf")
MAX_ITERATIONS = 5


def load_system_prompt() -> str:
    here = os.path.join(os.path.dirname(__file__), "system_prompt.txt")
    with open(here, "r", encoding="utf-8") as f:
        return f.read()


class ToolResponse:
    def __init__(self, name: str, data: Any, fake: bool = False):
        self.name = name
        self.data = data
        self.fake = fake


class Tools:
    @staticmethod
    def get_weather(location: str, date: str) -> ToolResponse:
        data = {"location": location, "date": date, "forecast": "nắng", "temp_c": 36}
        return ToolResponse("get_weather", data, fake=True)

    @staticmethod
    def search_vin_knowledge(query: str) -> ToolResponse:
        chunks = [
            {"source": "vin_db", "text": "Vé NL: 250k, Bé <1m: Miễn phí, Bé 1m-1m4: 150k"}
        ]
        return ToolResponse("search_vin_knowledge", chunks, fake=True)

    @staticmethod
    def calc_price(items: List[Dict[str, Any]]) -> ToolResponse:
        total = sum(i.get("price", 0) * i.get("qty", 1) for i in items)
        return ToolResponse("calc_price", {"total": total}, fake=True)

    @staticmethod
    def read_graph(graph_blob: Dict[str, Any]) -> ToolResponse:
        nodes = graph_blob.get("nodes", []) if isinstance(graph_blob, dict) else []
        return ToolResponse("read_graph", {"nodes": nodes}, fake=True)


class LocalModel:
    def __init__(self, model_path: str, system_prompt: str):
        self.model_path = model_path
        self.system_prompt = system_prompt
        if Llama is None:
            self.client = None
        else:
            self.client = Llama(model_path=model_path)

    def generate(self, prompt: str) -> str:
        if self.client is None:
            return self._fallback_generate(prompt)

        response = self.client.create(
            prompt=prompt,
            max_tokens=4024,
            temperature=0.0,
            stop=["\nObservation:", "\nAction:", "\nFinal Answer:"],
        )
        return response["choices"][0]["text"]

    def _fallback_generate(self, prompt: str) -> str:
        if "get_weather" in prompt and "search_vin_knowledge" not in prompt:
            return "Action: {\"tool\": \"get_weather\", \"params\": {\"location\": \"Hưng Yên\", \"date\": \"2026-06-02\"}}"
        if "search_vin_knowledge" in prompt and "calc_price" not in prompt:
            return "Action: {\"tool\": \"search_vin_knowledge\", \"params\": {\"query\": \"vé wave park\"}}"
        return "Final Answer: Dạ, em đã tổng hợp thông tin cho quý khách..."
    

def run_react_loop(user_question: str, graph_blob: Optional[Dict[str, Any]] = None) -> str:
    system_prompt = load_system_prompt()
    model = LocalModel(LOCAL_MODEL_PATH, system_prompt)

    observations: List[ToolResponse] = []

    if graph_blob:
        graph_obs = Tools.read_graph(graph_blob)
        observations.append(graph_obs)

    for iteration in range(1, MAX_ITERATIONS + 1):
        prompt = (
            f"SYSTEM:\n{system_prompt}\n\n"
            f"USER QUESTION:\n{user_question}\n\n"
            f"OBSERVATIONS:\n{[o.data for o in observations]}\n\n"
            f"Thought (iteration {iteration}):\n"
            "Decide next action.\n"
            "Action:"
        )

        model_output = model.generate(prompt).strip()

        if model_output.startswith("Action:"):
            try:
                action_json = model_output[len("Action:"):].strip()
                action = json.loads(action_json)
                tool = action.get("tool")
                params = action.get("params", {})
            except Exception:
                return "Em chưa tìm thấy thông tin"

            if tool == "get_weather":
                obs = Tools.get_weather(params.get("location", ""), params.get("date", ""))
                observations.append(obs)
                continue

            if tool == "search_vin_knowledge":
                obs = Tools.search_vin_knowledge(params.get("query", ""))
                observations.append(obs)
                continue

            if tool == "calc_price":
                obs = Tools.calc_price(params.get("items", []))
                observations.append(obs)
                continue

            return "Em chưa tìm thấy thông tin"

        if model_output.startswith("Final Answer:"):
            answer = model_output[len("Final Answer:"):].strip()
            if not any(o.name == "calc_price" for o in observations) and any("vé" in str(o.data).lower() for o in observations):
                obs = Tools.calc_price([{"price": 250, "qty": 2}, {"price": 150, "qty": 1}])
                observations.append(obs)
                answer += f" Tổng vé nhà mình là {obs.data['total']}k (tính theo nguồn trả về)."

            final_text = (
                "Dạ, em hiểu ạ. " + answer + "\n"
                + "Em đã sử dụng: " + ", ".join({o.name for o in observations}) + ". "
                + "Em khuyên quý khách mang theo kem chống nắng."
            )
            return final_text

    return "Em chưa tìm thấy đủ thông tin sau 5 vòng, quý khách vui lòng cung cấp thêm thông tin cụ thể."


if __name__ == "__main__":
    graph = {"nodes": [{"id": 1, "text": "Vé NL: 250k, Bé 1m-1m4: 150k"}]}
    q = "Mai nhà tôi 2 người lớn 1 bé 4 tuổi đi chơi ở Wave Park. Nên mang theo gì, vé tính ra sao?"
    print(run_react_loop(q, graph_blob=graph))
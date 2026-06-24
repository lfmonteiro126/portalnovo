import requests

class AIClient:
    def __init__(self, endpoint="http://localhost:11434", model="llama3.2"):
        self.endpoint = endpoint.rstrip('/')
        self.model = model
    
    def test_connection(self):
        try:
            response = requests.get(f"{self.endpoint}/api/tags", timeout=5)
            if response.ok:
                data = response.json()
                models = [m['name'] for m in data.get('models', [])]
                return True, models
            return False, []
        except Exception as e:
            return False, [str(e)]
    
    def ask(self, prompt):
        try:
            response = requests.post(
                f"{self.endpoint}/api/generate",
                json={"model": self.model, "prompt": prompt, "stream": False},
                timeout=60
            )
            if response.ok:
                return response.json().get('response', '(sem resposta)')
            return f"Erro HTTP {response.status_code}"
        except Exception as e:
            return f"Erro: {str(e)}"
    
    def explain_event(self, event_id, source, message):
        prompt = f"""Especialista em Windows Server. Analise:
Event ID: {event_id}
Fonte: {source}
Mensagem: {message}

Forneça: 1) Causa, 2) Passos (3-5), 3) Comandos. PT-BR."""
        return self.ask(prompt)
